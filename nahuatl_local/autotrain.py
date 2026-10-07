"""Entrenamiento local por etapas: presupuesto, reanudación y parada automática."""
import argparse
import contextlib
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]

def portable(path):
    path = Path(path).resolve()
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)

def read(path):
    return json.loads(Path(path).read_text())

def write(path, value):
    path = Path(path)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    temp.replace(path)

def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def hashes(data):
    return {s: digest(Path(data) / (s + '.jsonl')) for s in ('train', 'validation', 'test')}

def advance_policy(policy, loss, min_delta):
    if not math.isfinite(loss):
        raise ValueError('Pérdida de validación no finita')
    if policy['best'] - loss >= min_delta:
        return {'best': loss, 'stale_stages': 0}
    return {'best': policy['best'], 'stale_stages': policy['stale_stages'] + 1}

def progress(run):
    # El JSON dentro de last se publica junto con los pesos y el optimizador.
    from .train import recover
    recover(run / 'last')
    recover(run / 'best')
    path = run / 'last/progress.json'
    if not path.exists():
        path = run / 'training-report.json'
    return read(path) if path.exists() else None

@contextlib.contextmanager
def lock(path):
    import fcntl  # macOS y Linux
    with path.open('a') as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError('Ya hay un entrenamiento usando este directorio') from None
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)

def execute(module, args, logfile):
    command = [sys.executable, '-m', module, *map(str, args)]
    print('Ejecutando:', ' '.join(command), flush=True)
    with logfile.open('a') as log:
        subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)

def prepare():
    # Descargas solo por solicitud explícita. Nunca durante entrenamiento.
    sources = read(ROOT / 'configs/sources.json')
    from .data import default_corpus_path, prepare as prepare_data
    try:
        corpus = default_corpus_path()
    except FileNotFoundError:
        corpus = None
    if corpus is None:
        subprocess.run([sys.executable, '-m', 'nahuatl_local.download', '--only', 'corpus'], check=True)
        corpus = default_corpus_path()
    if any(not (ROOT / 'models/base' / f).exists() for f in sources['model']['files']):
        subprocess.run([sys.executable, '-m', 'nahuatl_local.download', '--only', 'model'], check=True)
    if not all((ROOT / 'data/prepared' / (s + '.jsonl')).exists() for s in ('train', 'validation', 'test')):
        prepare_data(corpus, ROOT / 'data/prepared', tokenizer_dir=ROOT / 'models/base')

def choose_dtype(device):
    # No se presupone soporte BF16 en todos los equipos.
    flags = Path('/proc/cpuinfo')
    if device == 'cpu' and flags.exists() and 'avx512_bf16' in flags.read_text():
        return 'bfloat16'
    return 'float32'

def initialize(a, out):
    from transformers import AutoTokenizer
    from .runtime import encode_pair, choose_device
    from .data import load_rows
    c = read(a.config)
    c.update(output=portable(out / 'run'), device=choose_device(a.device), validation_examples=a.validation_examples,
             eval_every=min(100, a.stage_steps))
    c['dtype'] = choose_dtype(c['device']) if a.dtype == 'auto' else a.dtype
    tok = AutoTokenizer.from_pretrained(c['base_model'], local_files_only=True, trust_remote_code=False)
    usable = sum(encode_pair(tok, row, c['max_length']) is not None for row in load_rows(Path(c['data']) / 'train.jsonl'))
    if usable == 0:
        raise ValueError('Ningún par de entrenamiento cabe en el límite')
    max_steps = math.ceil(a.epochs * usable / c['gradient_accumulation'])
    c['steps'] = max_steps
    parent = Path(a.inherit_order_from) if a.inherit_order_from else None
    if parent is None and Path(a.init_adapter).name == 'best' and Path(c['data']).resolve() == (ROOT / 'data/prepared').resolve():
        candidate = Path(a.init_adapter).resolve().parent / 'last'
        if (candidate / 'state.pt').exists():parent = candidate
    write(out / 'train-config.json', c)
    return dict(schema_version=1, config=c, config_sha256=digest(out / 'train-config.json'),
                dataset_sha256=hashes(c['data']), initial_adapter=portable(a.init_adapter),
                initial_adapter_sha256=digest(Path(a.init_adapter) / 'adapter_model.safetensors'),
                inherited_order_from=portable(parent) if parent else None,
                usable_training_rows=usable, max_steps=max_steps, stage_steps=a.stage_steps,
                patience=a.patience, min_delta=a.min_delta, generation_examples=a.generation_examples,
                next_target=min(a.stage_steps, max_steps), policy=None, history=[], status='ready',
                generation_best_step=None, created_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))

def generation(out, state, adapter, name):
    config = state['config']
    target = out / (name + '-full.json')
    execute('nahuatl_local.benchmark', ['--split', 'validation', '--limit', state['generation_examples'],
            '--adapter', adapter, '--data', config['data'], '--base', config['base_model'],
            '--device', config['device'], '--output', target], out / 'generation.log')
    return read(out / (name + '.json'))

def generation_guard(before, after):
    """Freno conservador de regresiones visibles; no valida corrección lingüística."""
    if before['ids'] != after['ids'] or before['dataset_sha256'] != after['dataset_sha256']:
        raise ValueError('Las muestras de validación no coinciden')
    return (after['chrF_plus_plus'] >= before['chrF_plus_plus']
            and after['truncated'] <= before['truncated']
            and after['repeated_trigram_fraction'] <= before['repeated_trigram_fraction'] + .05)

def default_adapter():
    """Admite solo generaciones sin regresión y checkpoints con cursor coincidente."""
    for name in ('continued-unseen', 'automatic'):
        root = ROOT / 'outputs' / name
        state_path = root / 'automation.json'
        if not state_path.exists() or read(state_path).get('generation_guard_passed') is not True:
            continue
        best, last = root / 'run/best', root / 'run/last'
        progress_path = last / 'progress.json'
        if not progress_path.exists():
            continue
        p = read(progress_path)
        if (p['best_step'] == p['completed_steps']
                and digest(best / 'adapter_model.safetensors') == digest(last / 'adapter_model.safetensors')):
            return best
    return ROOT / 'outputs/classical-v2/best'

def summary(out, state, report):
    rows = ['# Entrenamiento automático', '', 'Estado: ' + state['status'], '',
            'La selección y parada usan validación; el conjunto de prueba no se evalúa ni se modifica.',
            'Las métricas no certifican corrección lingüística. No se utiliza una API externa.', '']
    if report:
        rows += [f"Pasos adicionales desde el adaptador inicial: {report['completed_steps']}.",
                 f"NLL inicial: {report['validation_loss_before']:.4f}; mejor: {report['best_validation_loss']:.4f}.",
                 f"Checkpoint mejor: {report['best_step']}; validación: {report['validation_rows']} pares.", '']
        if report['best_step'] == 0:
            rows += ['Ningún checkpoint nuevo superó la pérdida inicial. `best` conserva el adaptador inicial; `last` permite continuar el entrenamiento adicional.', '']
    before, after = out / 'generation-before.json', out / 'generation-after.json'
    if before.exists() and after.exists():
        b, e = read(before), read(after)
        guard = generation_guard(b, e)
        rows += ['| Medida de validación | Inicial | Mejor por NLL |', '|---|---:|---:|',
                 f"| chrF++ | {b['chrF_plus_plus']:.2f} | {e['chrF_plus_plus']:.2f} |",
                 f"| Salidas al límite de tokens | {b['truncated']} | {e['truncated']} |",
                 f"| Fracción media de trigramas repetidos | {b['repeated_trigram_fraction']:.3f} | {e['repeated_trigram_fraction']:.3f} |", '',
                 'La generación se inspecciona al iniciar y al finalizar cada invocación; no decide la parada ni el checkpoint.',
                 'El mejor checkpoint por NLL puede empeorar en generación. No hay promoción automática a la aplicación.',
                 f"Sugerencia conservadora para experimentar: `{state.get('suggested_adapter', state['initial_adapter'] if not guard else portable(out / 'run/best'))}`.",
                 'Este filtro usa una muestra pequeña; no acredita traducciones correctas.', '']
    rows += ['Continuar: `python -m nahuatl_local.autotrain --output ' + portable(out) + ' --budget-minutes 60`', '']
    (out / 'SUMMARY.md').write_text('\n'.join(rows))

def finish(out, state):
    report = progress(out / 'run')
    if report and (state['generation_best_step'] != report['best_step'] or not (out / 'generation-after.json').exists()):
        generation(out, state, out / 'run/best', 'generation-after')
        state['generation_best_step'] = report['best_step']
        write(out / 'automation.json', state)
    before, after = out / 'generation-before.json', out / 'generation-after.json'
    if before.exists() and after.exists():
        passed = generation_guard(read(before), read(after))
        state['generation_guard_passed'] = passed
        state['suggested_adapter'] = portable(out / 'run/best') if passed else state['initial_adapter']
        write(out / 'automation.json', state)
    summary(out, state, report)
    print('Resultado:', out / 'SUMMARY.md', flush=True)

def run(a):
    out = Path(a.output).resolve()
    out.mkdir(parents=True, exist_ok=True)
    with lock(out / 'autotrain.lock'):
        state_path = out / 'automation.json'
        if state_path.exists():
            state = read(state_path)
            if digest(out / 'train-config.json') != state['config_sha256']:
                raise ValueError('La configuración guardada cambió; utiliza otro --output')
            if hashes(state['config']['data']) != state['dataset_sha256']:
                raise ValueError('El corpus cambió; utiliza otro --output')
            if digest(Path(state['initial_adapter']) / 'adapter_model.safetensors') != state['initial_adapter_sha256']:
                raise ValueError('Cambió el adaptador inicial')
            print('Reanudación: se conserva la configuración original; solo cambia el presupuesto de tiempo.', flush=True)
        else:
            if any(p.name != 'autotrain.lock' for p in out.iterdir()):
                raise ValueError('Directorio ocupado sin automation.json; utiliza otro --output')
            state = initialize(a, out)
            write(state_path, state)
        if state['status'] in ('early_stopped', 'completed'):
            finish(out, state)
            print('Ejecución terminada:', state['status'], flush=True)
            return
        run_dir = out / 'run'
        if not (out / 'generation-before.json').exists():
            generation(out, state, state['initial_adapter'], 'generation-before')
        previous = progress(run_dir)
        if previous and state['generation_best_step'] != previous['best_step']:
            finish(out, state)
        # El presupuesto cubre las etapas de entrenamiento. Preparación y generación son adicionales.
        deadline = time.monotonic() + a.budget_minutes * 60
        state['status'] = 'training'
        state.pop('last_error', None)
        write(state_path, state)
        try:
            while time.monotonic() < deadline:
                report = progress(run_dir)
                step = report['completed_steps'] if report else 0
                target = state['next_target']
                if step < target:
                    args = ['--config', out / 'train-config.json', '--steps', target,
                            '--max-seconds', max(.01, deadline - time.monotonic())]
                    if report:
                        args += ['--resume', run_dir]
                    else:
                        if run_dir.exists():
                            # Solo la subcarpeta propia de esta ejecución, antes del primer checkpoint.
                            # Conserva la inicialización interrumpida para inspección.
                            backup = out / 'interrupted-initialization'
                            if backup.exists():
                                raise RuntimeError('Inicialización interrumpida repetida; inspecciona interrupted-initialization')
                            run_dir.rename(backup)
                        args += ['--init-adapter', state['initial_adapter']]
                        if state.get('inherited_order_from'):
                            args += ['--inherit-order-from', state['inherited_order_from']]
                    execute('nahuatl_local.train', args, out / 'train.log')
                    report = progress(run_dir)
                    if report is None:
                        raise RuntimeError('El entrenador terminó sin checkpoint')
                    step = report['completed_steps']
                if state['policy'] is None:
                    state['policy'] = {'best': report['validation_loss_before'], 'stale_stages': 0}
                if step < target:
                    state['status'] = 'paused_budget'
                    break
                # Si se interrumpió entre checkpoint y actualización de estado, se reconcilia aquí.
                loss = report['validation'][-1]['loss']
                state['policy'] = advance_policy(state['policy'], loss, state['min_delta'])
                state['history'].append({'step': step, 'loss': loss, **state['policy']})
                state['next_target'] = min(step + state['stage_steps'], state['max_steps'])
                print('Etapa completada:', state['history'][-1], flush=True)
                if state['policy']['stale_stages'] >= state['patience']:
                    state['status'] = 'early_stopped'
                elif step >= state['max_steps']:
                    state['status'] = 'completed'
                write(state_path, state)
                if state['status'] != 'training':
                    break
            if state['status'] == 'training':
                state['status'] = 'paused_budget'
        except KeyboardInterrupt:
            state['status'] = 'interrupted'
            write(state_path, state)
            summary(out, state, progress(run_dir))
            print('Interrumpido. El mismo comando reanuda el último checkpoint completo.', flush=True)
            return
        except Exception as error:
            state['status'] = 'failed'
            state['last_error'] = type(error).__name__ + ': ' + str(error)
            write(state_path, state)
            summary(out, state, progress(run_dir))
            raise
        write(state_path, state)
        finish(out, state)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', default='outputs/local-training')
    p.add_argument('--config', default='configs/train.json')
    p.add_argument('--init-adapter', default=None)
    p.add_argument('--inherit-order-from',help='Estado last del adaptador inicial best para no repetir los mismos pares')
    p.add_argument('--prepare', action='store_true', help='Descargar recursos faltantes y preparar el corpus; requiere internet inicialmente')
    p.add_argument('--budget-minutes', type=float, default=60)
    p.add_argument('--epochs', type=float, default=3, help='Pasadas adicionales máximas, fijadas al crear la ejecución')
    p.add_argument('--stage-steps', type=int, default=250)
    p.add_argument('--patience', type=int, default=3)
    p.add_argument('--min-delta', type=float, default=.01)
    p.add_argument('--validation-examples', type=int, default=128)
    p.add_argument('--generation-examples', type=int, default=12)
    p.add_argument('--device', choices=['auto', 'cpu', 'mps', 'cuda'], default='auto')
    p.add_argument('--dtype', choices=['auto', 'float32', 'bfloat16'], default='auto')
    a = p.parse_args()
    if min(a.budget_minutes, a.epochs, a.stage_steps, a.patience, a.validation_examples, a.generation_examples, a.min_delta) <= 0:
        p.error('Los límites deben ser positivos')
    os.chdir(ROOT)
    if a.init_adapter is None:
        a.init_adapter = str(default_adapter())
    if a.prepare:
        prepare()
    run(a)

if __name__ == '__main__':
    main()
