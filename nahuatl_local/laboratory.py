"""Informes del laboratorio, sin cargar pesos ni iniciar entrenamiento."""
import hashlib
import json
from pathlib import Path
from .community import ROOT
from .model_status import DEFAULT_ADAPTER

REPORTS = {
    'training': 'outputs/continued-unseen/run/training-report.json',
    'before': 'outputs/continued-unseen/generation-before.json',
    'after': 'outputs/continued-unseen/generation-after.json',
    'retrieval': 'reports/benchmark-retrieval-validation-current.json',
    'smoke': 'reports/webapp-model-smoke.json',
}


def read_object(path):
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def digest(path):
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def snapshot(capability, adapter=None, root=ROOT):
    root = Path(root)
    training = read_object(root / REPORTS['training'])
    before = read_object(root / REPORTS['before'])
    after = read_object(root / REPORTS['after'])
    retrieval = read_object(root / REPORTS['retrieval'])
    automation = read_object(root / 'outputs/continued-unseen/automation.json')
    manifest = read_object(root / 'data/prepared/manifest.json')
    smoke = read_object(root / REPORTS['smoke'])
    hashes = {s: digest(root / f'data/prepared/{s}.jsonl') for s in ('train', 'validation')}
    trained_hashes = training.get('dataset_sha256', {})
    matches = all(hashes[s] and hashes[s] == trained_hashes.get(s) for s in hashes) if trained_hashes else None
    comparable = bool(before.get('ids') and all(before.get(k) is not None for k in
        ('dataset_sha256', 'split', 'metric_signature', 'rag')) and all(before.get(k) == after.get(k)
        for k in ('ids', 'dataset_sha256', 'split', 'metric_signature', 'rag')))
    active = Path(adapter or DEFAULT_ADAPTER).resolve()
    reference = (root / 'outputs/continued-unseen/run/best').resolve()
    history = [dict(step=v['step'], loss=v['loss']) for v in training.get('validation', [])
               if isinstance(v, dict) and isinstance(v.get('step'), (int, float))
               and isinstance(v.get('loss'), (int, float))]
    return dict(
        model=capability, reference_adapter='outputs/continued-unseen/run/best',
        active_is_reference=active == reference,
        training=dict(available=bool(training), status=automation.get('status'),
            recorded_at=automation.get('created_at'),
            parameters=training.get('trainable_parameters'),
            inherited_steps=training.get('inherited_prior_steps'),
            completed_steps=training.get('completed_steps'), best_step=training.get('best_step'),
            usable_rows=training.get('usable_training_rows'), validation_rows=training.get('validation_rows'),
            before_loss=training.get('validation_loss_before'), best_loss=training.get('best_validation_loss'),
            history=history, current_data_matches=matches),
        generation=dict(available=bool(before and after), comparable=comparable,
            examples=len(before.get('ids', [])), split=before.get('split'),
            before_chrf=before.get('chrF_plus_plus'), after_chrf=after.get('chrF_plus_plus'),
            before_repetition=before.get('repeated_trigram_fraction'), after_repetition=after.get('repeated_trigram_fraction')),
        current_data=dict(retained=manifest.get('retained'),
            normalization=manifest.get('normalization', {}).get('version'),
            splits={k:v.get('rows') for k,v in manifest.get('splits', {}).items()}),
        retrieval=dict(available=bool(retrieval), examples=retrieval.get('n'),
            chrf=retrieval.get('chrF_plus_plus'), split=retrieval.get('split'),
            current_data_matches=bool(hashes['train'] and hashes['validation'] and
                retrieval.get('train_sha256') == hashes['train'] and
                retrieval.get('dataset_sha256') == hashes['validation'])),
        recorded_example=dict(available=bool(smoke), input=smoke.get('input'),
            output=''.join(s.get('text', '') for s in smoke.get('result', {}).get('segments', [])),
            elapsed_seconds=smoke.get('elapsed_seconds')),
        reports=[dict(id=k, path=v, url=f'/api/laboratory/reports/{k}')
                 for k,v in REPORTS.items() if (root / v).is_file()])
