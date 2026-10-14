"""Prepare an immutable handoff for one public reading; never apply human decisions."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import tempfile

from .community import ROOT
from .corpus import CorpusStore
from .editorial_pipeline import encoded
from .iteration import (PUBLIC_PREFIXES, diagnose, evidence_hashes, queue_from_state,
                        reconcile, source_manifest, validate_state)
from .learning import Learning
from .lesson_audit import fingerprint
from .pictography import load_catalog
from .research import Archive

EXTRA_SOURCES = ('nahuatl_local/lesson_review_packet.py', 'nahuatl_local/editorial_pipeline.py',
                 'nahuatl_local/platform_web/project.js', 'docs/REVISION_LECTURA.md',
                 'docs/PILOTO_INSTITUCIONAL.md', 'docs/FUENTES.md', 'THIRD_PARTY_NOTICES.md')
LIMITS = [
    'Preparación técnica pendiente de revisión humana; no hay cotejo ni prueba con personas registrados por este paquete.',
    'Las claves y explicaciones reproducen la lectura publicada; no son nuevas respuestas ni una rúbrica de comprensión.',
    'Las preguntas de comprensión actuales se apoyan en la traducción de origen; no demuestran comprensión independiente del náhuatl.',
    'Una referencia visual conserva su contexto documental: no acredita la lectura de todo el pasaje, una especie ni una regla de número.',
    'Las URLs son referencias sin descarga ni verificación remota. Exportar no concede permisos nuevos; training:false permanece.',
    'Antes de una prueba humana, acordar alcance, responsables, reconocimiento, permisos, custodia y retiro según el protocolo enlazado.',
]


def safe_path(path, output=False):
    """Reject private paths and every symlink before resolving or opening anything."""
    path = Path(path)
    if '..' in path.parts:
        raise ValueError('No se permiten rutas con .. .')
    if not path.is_absolute():
        path = ROOT / path
    try:
        relative = path.relative_to(ROOT)
    except ValueError:
        raise ValueError('Usa rutas públicas dentro del proyecto.') from None
    if (not relative.parts or relative.parts[0] not in PUBLIC_PREFIXES
            and str(relative) != 'THIRD_PARTY_NOTICES.md'):
        raise ValueError('Ruta privada o fuera del alcance público.')
    if output and (relative.parts[0] != 'reports' or len(relative.parts) < 2):
        raise ValueError('Guarda el paquete en una subcarpeta nueva de reports/.')
    for candidate in (path, *path.parents):
        if candidate.is_symlink():
            raise ValueError('No se permiten enlaces simbólicos.')
        if candidate == ROOT:
            break
    return path


def read_json(path):
    return json.loads(safe_path(path).read_text(encoding='utf-8'))


def checked_hashes(hashes):
    if not isinstance(hashes, dict) or not hashes:
        raise ValueError('Faltan hashes de fuentes públicas.')
    for reference, expected in hashes.items():
        path = safe_path(reference)
        if not isinstance(expected, str) or not path.is_file() or digest(path.read_bytes()) != expected:
            raise ValueError('Fuente obsoleta o ausente: ' + reference)
    return hashes


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def collect_records(lesson, source_id, records):
    senses = set(lesson['sense_ids']) | {a['sense_id'] for e in lesson['examples'] for a in e['annotations']}
    chosen = {source_id, lesson['cover_glyph']} | senses
    chosen.update(r['id'] for r in records.values() if r.get('sense_id') in senses)
    chosen.update(a['glyph_id'] for e in lesson['examples'] for a in e['annotations'] if a.get('glyph_id'))
    def refs(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key.endswith('_id') and isinstance(item, str) and item in records:
                    yield item
                yield from refs(item)
        elif isinstance(value, list):
            for item in value:
                yield from refs(item)
    while True:
        added = {ref for rid in chosen for ref in refs(records[rid])} - chosen
        if not added:
            break
        chosen.update(added)
    result = [copy.deepcopy(records[rid]) for rid in sorted(chosen)]
    if any(not r['rights']['public'] or r.get('withdrawn') for r in result):
        raise ValueError('El paquete solo admite registros públicos vigentes.')
    return result


def build(lesson_id, inventory_path, queue_path, state_path):
    if not isinstance(lesson_id, str) or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]*', lesson_id):
        raise ValueError('ID de lectura inválido.')
    inventory = read_json(inventory_path)
    queue = read_json(queue_path)
    state = validate_state(read_json(state_path))
    sources = checked_hashes(inventory.get('sources'))
    if sources != source_manifest():
        raise ValueError('El inventario es obsoleto; vuelve a ejecutar iteration.')
    extra = {name: digest(safe_path(name).read_bytes()) for name in EXTRA_SOURCES}
    inputs = {str(safe_path(p).relative_to(ROOT)): digest(safe_path(p).read_bytes())
              for p in (inventory_path, queue_path, state_path)}
    # Check persisted decision references before the pure reconciliation reads them.
    for row in state['tasks'].values():
        if row.get('decision', {}).get('evidence'):
            evidence_hashes(row['decision']['evidence'])
    decisions = read_json('editorial/lesson-decisions.json')['decisions']
    with tempfile.TemporaryDirectory(prefix='amoxcalli-reading-review-') as directory:
        records = CorpusStore(Path(directory) / 'public.sqlite3').public_records()
        learning = Learning(Archive())
        report, tasks = diagnose(records, learning, load_catalog(), sources, decisions,
                                 inventory['proposed_occurrence_target'], inventory['proposed_lesson_target'])
        current_state = reconcile(tasks, state, report['diagnostic_fingerprint'], decisions)
        if (inventory['diagnostic_fingerprint'] != report['diagnostic_fingerprint']
                or queue.get('diagnostic_fingerprint') != report['diagnostic_fingerprint']
                or current_state != state or queue.get('tasks') != queue_from_state(state)):
            raise ValueError('Inventario, cola o estado obsoletos/inconsistentes; repite el diagnóstico.')
        lesson = next((l for l in learning.catalog(records)['lessons'] if l['id'] == lesson_id), None)
        if lesson is None:
            raise ValueError('La lectura no está disponible en el catálogo público.')
        senses = set(lesson['sense_ids']) | {a['sense_id'] for e in lesson['examples'] for a in e['annotations']}
        selected = []
        for item in queue['tasks']:
            reason = ('lecture' if item.get('lesson_id') == lesson_id else
                      'visual_scope' if item['id'] in {'word-' + sid + '-glyph-scope' for sid in senses} else
                      'shared_visual_policy' if item['id'] == 'batch-visual-policy' else None)
            if reason:
                selected.append(dict(selection_reason=reason, task=copy.deepcopy(item)))
        package = dict(schema_version=1, kind='reading_review_handoff', status='pending',
                       learning_id=learning.data['id'], learning_version=learning.data['version'],
                       variant=learning.data['variant'], editorial_status=learning.data['review_status'],
                       diagnostic_fingerprint=report['diagnostic_fingerprint'],
                       diagnostic_inputs=dict(inventory=str(safe_path(inventory_path).relative_to(ROOT)),
                                              queue=str(safe_path(queue_path).relative_to(ROOT)),
                                              state=str(safe_path(state_path).relative_to(ROOT))), lesson=lesson,
                       tasks=selected, catalog_records=collect_records(lesson, learning.data['source_id'], records),
                       protocol='docs/PILOTO_INSTITUCIONAL.md', workshop_route='#taller/' + lesson_id,
                       limits=LIMITS, llm_calls=0, network_requests=0)
    all_hashes = {**sources, **extra, **inputs}
    checked_hashes(all_hashes)
    return package, dict(sorted(all_hashes.items()))


def render(package):
    lesson = package['lesson']
    lines = ['# Revisión pendiente · ' + lesson['title'], '', lesson['objective'], '',
             f"Lectura `{lesson['id']}` · contenido {lesson['version']} · práctica {lesson['practice_version']} · {package['editorial_status']}.",
             '', 'Preparado desde archivos públicos. Las decisiones están vacías; no acredita revisión ni aprendizaje.', '',
             f"Ficha de taller: `{package['workshop_route']}`. Protocolo existente: `docs/PILOTO_INSTITUCIONAL.md` (ruta desde la raíz del proyecto).", '',
             '## Tareas actuales', '']
    for entry in package['tasks']:
        task = entry['task']
        reason = {'lecture': 'tarea de esta lectura', 'visual_scope': 'alcance de una referencia visual de esta lectura',
                  'shared_visual_policy': 'criterio visual compartido aplicable a esta lectura'}[entry['selection_reason']]
        lines.extend([f"### {task['id']} · {task['status']}", '', task['title'], '',
                      f"Fingerprint actual: `{task['fingerprint']}`. Hallazgo editorial: `{task['finding_fingerprint']}`.", '',
                      task['acceptance'], '', f"Motivo de inclusión: {reason}; evidencia completa en package.json.", ''])
    lines.extend(['## Ayudas publicadas', '', *lesson.get('reading_tips', []), ''])
    for e in lesson['examples']:
        p = e['passage']
        lines.extend(['## ' + e['archive_id'] + ' · ' + p['document'], '', p['nah'], '', p['es'], '',
                      f"Fuente: {p['locator']} · [distribución]({p['source_url']}).", '',
                      f"SHA-256 del par nah + NUL + es: `{e['source_hash']}`.", '',
                      p['verification'], '', p['rights_note'], '', e.get('context', ''), '',
                      'Formas para explorar: ' + ', '.join(e.get('explore_words', [])), ''])
        for field in ('exercise', 'comprehension'):
            if field not in e:
                continue
            ex = e[field]
            heading = {'exercise': 'Reconocimiento de la forma', 'comprehension': 'Comprensión del contexto'}[field]
            lines.extend(['### ' + heading + ' · clave editorial pendiente de revisión', '', ex['question'], ''])
            lines.extend(f"{i + 1}. {option}" for i, option in enumerate(ex['options']))
            lines.extend(['', f"Clave existente (índice {ex['answer']}): {ex['options'][ex['answer']]}", '', ex['explanation'], ''])
        for a in e['annotations']:
            lines.extend([f"Anotación «{a['quote']}» → `{a['sense_id']}`; relación textual `{a.get('relation', 'full_word')}`; referencia `{a.get('glyph_id', '')}`; índices UTF-16 {a['start']}–{a['end']}.", '', a['note'], ''])
    lines.extend(['## Relaciones visuales y permisos', ''])
    for record in package['catalog_records']:
        if record['kind'] != 'glyph':
            continue
        lines.extend(['### ' + record['id'], '', f"Estado `{record.get('glyph_status')}` · verificación `{record['verification']}`.", '',
                      record.get('context', ''), '', record.get('notes', ''), '',
                      f"[Ficha]({record.get('url', '')}) · [manuscrito]({record.get('manuscript_url', '')}).", '',
                      record.get('image_credit', ''), '', 'Imagen: ' + record.get('image', ''), '',
                      'Evidencia conservada:', '', '```json', json.dumps(record.get('evidence', []), ensure_ascii=False, sort_keys=True, indent=2), '```', '',
                      'Permisos conservados:', '', '```json', json.dumps(record['rights'], ensure_ascii=False, sort_keys=True, indent=2), '```', ''])
    lines.extend(['## Límites y entrega humana', ''])
    lines.extend('- ' + limit for limit in package['limits'])
    lines.extend(['', 'Verifica el paquete antes de usarlo. Copia human-decisions.blank.json a un archivo nuevo para registrar una revisión real; conserva el paquete original. Los campos reviewer/date/evidence/resolution/notes están vacíos y todos los estados son pending. No se importan ni aplican desde este comando.', ''])
    return '\n'.join(lines)


def blank_decisions(package):
    return dict(schema_version=1, kind='reading_review_notes_template', status='pending',
                lesson_id=package['lesson']['id'], diagnostic_fingerprint=package['diagnostic_fingerprint'],
                decisions=[dict(task_id=e['task']['id'], fingerprint=e['task']['fingerprint'], status='pending',
                                reviewer='', date='', evidence=[], resolution='', notes='') for e in package['tasks']],
                comprehension_trial=dict(status='pending', agreed_task='', agreed_rubric='', observations=[], results=[],
                                         facilitator='', date='', agreements=[]))


def file_contents(package, sources):
    files = {'package.json': encoded(package), 'package.md': render(package).encode(),
             'human-decisions.blank.json': encoded(blank_decisions(package))}
    manifest = dict(schema_version=1, kind='reading_review_manifest', sources=sources,
                    diagnostic_fingerprint=package['diagnostic_fingerprint'], lesson_id=package['lesson']['id'],
                    files={name: digest(raw) for name, raw in files.items()})
    files['manifest.json'] = encoded(manifest)
    return files


def check_directory(output, files):
    output = safe_path(output, output=True)
    if not output.is_dir() or {p.name for p in output.iterdir()} != set(files):
        raise ValueError('El paquete existe con archivos distintos; usa una carpeta nueva.')
    if any(safe_path(output / name).read_bytes() != raw for name, raw in files.items()):
        raise ValueError('El paquete o sus decisiones cambiaron; no se sobrescriben. Usa una carpeta nueva.')


def prepare(lesson_id, inventory, queue, state, output):
    output = safe_path(output, output=True)
    package, sources = build(lesson_id, inventory, queue, state)
    files = file_contents(package, sources)
    if output.exists():
        check_directory(output, files)
        return 'unchanged'
    checked_hashes(sources)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent, prefix='.reading-review-') as directory:
        staging = Path(directory) / 'packet'
        staging.mkdir()
        for name, raw in files.items():
            (staging / name).write_bytes(raw)
        safe_path(output, output=True)
        if output.exists():
            raise ValueError('El destino apareció durante la preparación; no se sobrescribe.')
        staging.rename(output)
    return 'prepared'


def verify(output):
    output = safe_path(output, output=True)
    manifest = read_json(output / 'manifest.json')
    if (set(manifest) != {'schema_version', 'kind', 'sources', 'diagnostic_fingerprint', 'lesson_id', 'files'}
            or manifest.get('schema_version') != 1 or manifest.get('kind') != 'reading_review_manifest'
            or not isinstance(manifest.get('files'), dict)
            or set(manifest['files']) != {'package.json', 'package.md', 'human-decisions.blank.json'}):
        raise ValueError('Manifiesto de revisión inválido.')
    checked_hashes(manifest.get('sources'))
    package = read_json(output / 'package.json')
    expected = file_contents(package, manifest['sources'])
    check_directory(output, expected)
    # Reconstruct from the original diagnosis/state to validate content, not just a self-supplied hash.
    inputs = package.get('diagnostic_inputs', {})
    if set(inputs) != {'inventory', 'queue', 'state'} or any(path not in manifest['sources'] for path in inputs.values()):
        raise ValueError('Referencias de diagnóstico inválidas.')
    rebuilt, sources = build(manifest['lesson_id'], inputs['inventory'], inputs['queue'], inputs['state'])
    check_directory(output, file_contents(rebuilt, sources))
    return 'valid'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    prep = sub.add_parser('prepare')
    prep.add_argument('--lesson', default='aves')
    prep.add_argument('--diagnosis', type=Path, required=True)
    prep.add_argument('--state', type=Path, default=ROOT / 'reports/iterations/state.json')
    prep.add_argument('--output', type=Path, required=True)
    check = sub.add_parser('verify')
    check.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    result = (prepare(args.lesson, args.diagnosis / 'inventory.json', args.diagnosis / 'queue.json', args.state, args.output)
              if args.command == 'prepare' else verify(args.output))
    print(json.dumps(dict(state=result, output=str(safe_path(args.output, output=True)), network_requests=0, llm_calls=0)))


if __name__ == '__main__':
    main()
