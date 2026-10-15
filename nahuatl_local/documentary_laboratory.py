"""Reproducible documentary comparison; no model, image, reserve keys or network.

The artifact binds only to measured inputs (ranker, data, battery, evaluator) and to
an independently replayed retrieval measurement. Presentation (platform, JS, CSS) is
checked by the DOM suite (scripts/test-platform-ui.py), never by hashes here.
"""
import argparse
from collections import OrderedDict
import copy
import hashlib
import json
from pathlib import Path
from threading import RLock
from urllib.parse import quote

from .community import ROOT
from .documentary_evaluation import FIXED as EVALUATION_INPUTS
from .documentary_retrieval import digest, public_path
from .documentary_retrieval_evaluation import REPORT as RETRIEVAL_REPORT, validate_report as validate_retrieval

REPORT = 'reports/documentary-laboratory-v1.json'
BATTERY = 'configs/documentary-evaluation-v1.json'
BATTERY_VALIDATION = 'reports/documentary-evaluation-validation-v1.json'
# The comparison contract is recomputed from code on every validation, so only the
# battery validation is hashed here; the replayed retrieval report carries the rest.
SOURCES = (BATTERY_VALIDATION,)
RIGHTS = dict(local_documentary_fields='authorized_local_scope', evaluation=False, training=False,
              image_model_input=False, image_copy=False, external_send=False)
SCOPE = 'known_record_queries_local_documentary_fields_only'
LIMIT = ('Consultas parametrizadas sobre fichas conocidas: no mide comprensión general, traducción '
         'ni reconocimiento de imágenes. Las referencias son documentales, sin revisión humana nueva.')
REASONS = {
    'textual_model': 'Qwen3-0.6B + LoRA no se ejecutó sobre esta batería documental. Las métricas históricas de traducción usan otras muestras y no son comparables. Este ciclo no carga pesos ni entrena.',
    'multimodal_candidate': 'Qwen3-VL-4B-Instruct es un candidato documentado, sin descarga de pesos ni ejecución. Los permisos de entrada/evaluación de imágenes siguen pendientes; su ficha no acredita competencia en náhuatl.',
}
LABELS = {'retrieval': 'Recuperación documental local', 'textual_model': 'Qwen3-0.6B + LoRA',
          'multimodal_candidate': 'Qwen3-VL-4B-Instruct · candidato'}

# Only validated public projections are retained. The lock also coalesces first
# requests: another thread cannot start a second replay for the same inputs.
_SUMMARY_CACHE_LIMIT = 4
_SUMMARY_CACHE = OrderedDict()
_SUMMARY_LOCK = RLock()


def read(relative, root=ROOT):
    value = json.loads(public_path(root, relative).read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise ValueError('Se requiere un informe objeto.')
    return value


def sha(relative, root=ROOT):
    return hashlib.sha256(public_path(root, relative).read_bytes()).hexdigest()


def manifest(retrieval, root=ROOT):
    # No own report: no self-referential hashes.
    paths = set(retrieval['input_hashes']) | set(SOURCES) | {RETRIEVAL_REPORT}
    return dict(sorted((p, sha(p, root)) for p in paths))


def failures(retrieval):
    """Only observed development outcomes; never export oracle fields/IDs/URLs."""
    return [dict(query_id=r['query_id'], query=r['query'], category=r['category'],
                 errors=r['errors'], matched_fields=r['exact_fields']['matched'],
                 required_field_count=r['exact_fields']['required'],
                 returned_ids=[h['id'] for h in r['response']['results']],
                 consult_url='#consultar/' + quote(r['query'], safe=''))
            for r in retrieval['results'] if r['category'] != 'complete']


def contract(retrieval, root=ROOT):
    """Derive all declared results from the single current measured report."""
    counts = read(BATTERY_VALIDATION, root)['counts']
    return dict(schema_version=1, comparison='documentary-development-v1',
                evaluation_fingerprint=retrieval['evaluation_fingerprint'],
                battery=dict(path=BATTERY, sha256=sha(BATTERY, root), counts=counts,
                             evaluated_split='development', evaluated_modality='textual', reserve_used=False),
                input_hashes=manifest(retrieval, root), scope=SCOPE, limitation=LIMIT,
                rights=copy.deepcopy(RIGHTS), human_review='pending',
                runs=[dict(method='retrieval', label=LABELS['retrieval'], status='measured',
                           report_hashes={RETRIEVAL_REPORT: sha(RETRIEVAL_REPORT, root)},
                           metrics=copy.deepcopy(retrieval['metrics']), failures=failures(retrieval),
                           cost=dict(elapsed_seconds=retrieval['elapsed_seconds'],
                                     timing=copy.deepcopy(retrieval['timing']), memory=copy.deepcopy(retrieval['memory']),
                                     model_calls=retrieval['model_calls'], network_requests=retrieval['network_requests'],
                                     image_downloads=retrieval['image_downloads'], monetary_cost=None,
                                     context='perf_counter; index and queries with tracemalloc enabled; sources loaded before tracing; monetary cost not measured'))]
                    + [dict(method=m, label=LABELS[m], status='not_run', reason=REASONS[m],
                            metrics=None, cost=None, report_hashes={},
                            candidate_source='docs/ROADMAP.md')
                       for m in ('textual_model', 'multimodal_candidate')])


def projection(report):
    """The public comparison contains aggregates and observed failures, no keys."""
    keys = ('schema_version', 'comparison', 'evaluation_fingerprint', 'battery', 'input_hashes',
            'scope', 'limitation', 'rights', 'human_review', 'runs')
    return copy.deepcopy({k: report[k] for k in keys})


def build(root=ROOT):
    retrieval = read(RETRIEVAL_REPORT, root)
    validation = validate_retrieval(retrieval, root=root)
    if not validation['valid']:
        raise ValueError('Recuperación inválida: ' + ', '.join(validation['errors']))
    return contract(retrieval, root)


def validate_report(report, root=ROOT, retrieval=None, retrieval_validation=None):
    """Verify complete contract, fresh measured inputs and an independent replay.

    A caller that already replayed retrieval in the same run may pass its validation;
    the default always replays. No booleans in the Lab artifact are trusted.
    """
    errors = []
    try:
        current = read(RETRIEVAL_REPORT, root)
        if retrieval is not None and retrieval != current:
            errors.append('retrieval_not_current')
        checked = retrieval_validation if retrieval_validation is not None else validate_retrieval(current, root=root)
        if not checked['valid']:
            errors.append('retrieval_invalid')
        expected = contract(current, root)
        if digest(projection(report)) != digest(expected):
            errors.append('comparison_contract_or_metrics')
        if set(report) != set(expected):
            errors.append('unexpected_or_missing_fields')
    except (ValueError, KeyError, OSError, TypeError) as error:
        errors.append('invalid_report:' + type(error).__name__)
    return dict(valid=not errors, errors=errors)


def _public_summary_uncached(root=ROOT):
    try:
        report = read(REPORT, root)
        checked = validate_report(report, root=root)
        if not checked['valid']:
            return dict(available=False, ready=False, validation_errors=checked['errors'])
        return dict(projection(report), available=True, ready=True, validation_errors=[],
                    public_summary_fingerprint=digest(projection(report)),
                    downloads=[dict(id='documentary-comparison', path=REPORT, url='/api/laboratory/reports/documentary-comparison'),
                               dict(id='documentary-retrieval', path=RETRIEVAL_REPORT, url='/api/laboratory/reports/documentary-retrieval')])
    except (OSError, ValueError, KeyError, TypeError) as error:
        return dict(available=False, ready=False, validation_errors=['unavailable:' + type(error).__name__])


def _summary_hashes(paths, root):
    # Re-open every dependency through the public path guard on EVERY request.
    # Content hashes, never mtime/size/TTL, determine whether replay is reusable.
    return {path: sha(path, root) for path in sorted(paths)}


def public_summary(root=ROOT):
    """Reuse a replay only while all validated public input bytes stay current.

    CLI/completion validation remains uncached. No report rows, reference keys,
    database, model state or private profile enters this bounded process cache.
    """
    with _SUMMARY_LOCK:
        try:
            project = Path(root).absolute()
            if '..' in project.parts:
                raise ValueError('La raíz pública no puede contener ..')
            public_path(project, REPORT)  # Reject an aliased root before reading.
            key = str(project)
            entry = _SUMMARY_CACHE.get(key)
            if entry is not None:
                try:
                    current = _summary_hashes(entry['hashes'], project)
                    if current == entry['hashes']:
                        _SUMMARY_CACHE.move_to_end(key)
                        return copy.deepcopy(entry['summary'])
                except (OSError, ValueError):
                    pass
                del _SUMMARY_CACHE[key]

            # Battery reconstruction also reads the learning source, which is
            # not part of the retrieval ranker's input manifest.
            initial_hashes = _summary_hashes(set(EVALUATION_INPUTS) | set(SOURCES)
                                             | {REPORT, RETRIEVAL_REPORT}, project)
            summary = _public_summary_uncached(project)
            if summary.get('ready'):
                paths = set(summary['input_hashes']) | set(initial_hashes)
                hashes = _summary_hashes(paths, project)
                # Do not cache or expose a result if files changed during replay.
                if (any(hashes[p] != h for p, h in initial_hashes.items())
                        or any(hashes[p] != h for p, h in summary['input_hashes'].items())):
                    return dict(available=False, ready=False,
                                validation_errors=['inputs_changed_during_validation'])
                _SUMMARY_CACHE[key] = dict(hashes=hashes, summary=copy.deepcopy(summary))
                while len(_SUMMARY_CACHE) > _SUMMARY_CACHE_LIMIT:
                    _SUMMARY_CACHE.popitem(last=False)
            return copy.deepcopy(summary)
        except (OSError, ValueError, KeyError, TypeError) as error:
            return dict(available=False, ready=False,
                        validation_errors=['unavailable:' + type(error).__name__])


def public_download(kind, root=ROOT):
    if kind not in ('documentary-comparison', 'documentary-retrieval'):
        raise ValueError('Informe documental no disponible.')
    summary = public_summary(root)
    if not summary['available']:
        raise ValueError('La comparación documental no está vigente.')
    if kind == 'documentary-comparison':
        return projection(summary)
    if kind == 'documentary-retrieval':
        r = summary['runs'][0]
        return dict(schema_version=1, method='public_documentary_retrieval', battery=summary['battery'],
                    evaluation_fingerprint=summary['evaluation_fingerprint'], report_hashes=r['report_hashes'],
                    input_hashes=summary['input_hashes'], metrics=r['metrics'], cost=r['cost'],
                    failures=r['failures'], scope=summary['scope'], limitation=summary['limitation'],
                    rights=summary['rights'], human_review=summary['human_review'],
                    note='Proyección pública del informe medido; excluye respuestas esperadas, claves y reserva.')
    raise ValueError('Informe documental no disponible.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    path = public_path(ROOT, REPORT, writing=True)
    report = read(REPORT) if args.check else build()
    validation = validate_report(report)
    if not validation['valid']:
        raise ValueError(', '.join(validation['errors']))
    if not args.check:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(validation=validation,
                         methods=[dict(method=r['method'], status=r['status']) for r in report['runs']]), indent=2))


if __name__ == '__main__':
    main()
