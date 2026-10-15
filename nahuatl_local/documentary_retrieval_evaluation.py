"""Measure all textual DEVELOPMENT queries; references never enter the ranker."""
import argparse
from collections import Counter
import copy
import hashlib
import json
import math
from time import perf_counter
import tracemalloc

from .community import ROOT
from . import lexicon
from .documentary_evaluation import FIXED as EVALUATION_INPUTS, load_development
from .documentary_retrieval import CONFIG, DocumentaryIndex, PublicSources, digest, public_path

REPORT = 'reports/documentary-retrieval-v1.json'
# Dependencies of measured responses/citations and their reference audit only.
# Presentation/QA belongs to documentary_laboratory; process guides to iteration.
# The measured records are the canonical lexicon catalog (identical to a fresh CorpusStore,
# checked by tests), so the store and server code are no longer measured inputs.
IMPLEMENTATION = ('nahuatl_local/documentary_retrieval.py', 'nahuatl_local/documentary_retrieval_evaluation.py',
                  'nahuatl_local/lexicon.py', 'nahuatl_local/passages.py', 'nahuatl_local/text.py',
                  lexicon.CATALOG, 'nahuatl_local/pictography.py', 'nahuatl_local/documentary_evaluation.py',
                  'configs/documentary-evaluation-v1.json')


def manifest(sources):
    return dict(sorted(dict(sources.hashes, **{p: hashlib.sha256(public_path(sources.root, p).read_bytes()).hexdigest()
                                             for p in set(IMPLEMENTATION) | set(EVALUATION_INPUTS)}).items()))


def evaluation_fingerprint(root):
    # Opaque fingerprint only; reserve reference fields are never returned/used.
    value = json.loads(public_path(root, 'configs/documentary-evaluation-v1.json').read_text())
    # Same historical fingerprint bytes, without importing diagnostic code.
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def field_key(field):
    return tuple(field[k] for k in ('path', 'table', 'record_id', 'field'))


def audit(query, response, sources):
    expected = query['reference']
    fields = [f for hit in response['results'] for f in hit['fields']]
    returned = {field_key(f): f for f in fields}
    required = {field_key(f): f for f in expected['fields']}
    matched = [k for k, f in required.items() if k in returned and returned[k]['value'] == f['value']
               and returned[k]['row_sha256'] == f['row_sha256'] and returned[k]['file_sha256'] == f['file_sha256']]
    missing = sorted(set(required) - set(matched))
    unsupported = [field_key(f) for f in fields if not sources.citation_valid(f)]
    urls = {u for hit in response['results'] for u in hit['urls']}
    actual_sources = set(response['source_ids'])
    correct = not missing and set(expected['source_ids']).issubset(actual_sources) and set(expected['urls']).issubset(urls)
    supported = bool(fields) and not unsupported
    errors = ([] if not missing else ['missing_required_fields']) + ([] if not unsupported else ['unsupported_citations'])
    if not set(expected['source_ids']).issubset(actual_sources): errors.append('missing_required_sources')
    if not set(expected['urls']).issubset(urls): errors.append('missing_required_urls')
    if response['abstained']: errors.append('abstained')
    return dict(source_ids=response['source_ids'], correct_source=correct, supported_citations=supported,
                abstained=response['abstained'], reference_checked=True,
                relevant_results=bool(matched), exact_fields=dict(matched=len(matched), required=len(required)),
                expected_target_ids=sorted({f['record_id'] for f in required.values()}),
                expected_fields=[list(k) for k in sorted(required)], missing_fields=[list(k) for k in missing],
                unsupported_fields=[list(k) for k in unsupported], errors=errors,
                category='complete' if correct and supported else 'abstention' if response['abstained'] else 'incomplete_or_unsupported')


def measure(root=ROOT):
    start = perf_counter()
    queries = load_development(modality='textual', root=root)
    sources = PublicSources(root)
    hashes = manifest(sources)
    tracemalloc.start()
    build_start = perf_counter()
    records = lexicon.load_records(root)
    index = DocumentaryIndex(records, sources)
    build_seconds = perf_counter() - build_start
    rows = []
    query_seconds = 0
    for q in queries:
        query_start = perf_counter()
        response = index.search(q['question'])
        seconds = perf_counter() - query_start
        query_seconds += seconds
        checked = audit(q, response, sources)
        rows.append(dict(query_id=q['id'], query=q['question'], task=q['task'], seconds=seconds,
                         response=response, **checked))
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    if manifest(sources) != hashes:
        raise ValueError('Una fuente cambió durante la medición.')
    return dict(schema_version=1, method='public_documentary_retrieval',
                evaluation_fingerprint=evaluation_fingerprint(root), input_hashes=hashes,
                configuration=copy.deepcopy(CONFIG), elapsed_seconds=perf_counter()-start,
                timing=dict(index_build_seconds=build_seconds, query_total_seconds=query_seconds,
                            query_mean_seconds=query_seconds / len(rows), query_max_seconds=max(r['seconds'] for r in rows)),
                memory=dict(python_current_bytes=current, python_peak_bytes=peak, measurement='tracemalloc; excludes native/process memory'),
                index=dict(public_records=len(records), passages=len(sources.archive), entries=len(index.entries),
                           pictography={t: len(r) for t, r in sources.tables.items()}),
                metrics=dict(queries=len(rows), complete=sum(r['correct_source'] and r['supported_citations'] for r in rows),
                             correct_source=sum(r['correct_source'] for r in rows), supported_citations=sum(r['supported_citations'] for r in rows),
                             covered=sum(not r['abstained'] for r in rows), abstained=sum(r['abstained'] for r in rows),
                             relevant_results=sum(r['relevant_results'] for r in rows),
                             exact_fields_matched=sum(r['exact_fields']['matched'] for r in rows),
                             exact_fields_required=sum(r['exact_fields']['required'] for r in rows),
                             categories=dict(Counter(r['category'] for r in rows))),
                scope='local_documentary_fields_only', reserve_used=False, model_calls=0, network_requests=0,
                private_database_opened=False, image_downloads=0, results=rows)


def validate_report(report, queries=None, root=ROOT, replay=True):
    """Completion gate: verify actual deterministic retrieval, not claimed booleans."""
    errors = []
    try:
        queries = queries if queries is not None else load_development(modality='textual', root=root)
        sources = PublicSources(root)
        if report.get('schema_version') != 1 or report.get('method') != 'public_documentary_retrieval': errors.append('contract')
        if report.get('configuration') != CONFIG or report.get('evaluation_fingerprint') != evaluation_fingerprint(root): errors.append('method_or_battery')
        if report.get('input_hashes') != manifest(sources): errors.append('stale_inputs')
        seconds = report.get('elapsed_seconds')
        if type(seconds) not in (int, float) or not math.isfinite(seconds) or seconds <= 0: errors.append('timing')
        if report.get('scope') != 'local_documentary_fields_only' or report.get('reserve_used') is not False: errors.append('scope')
        for key in ('model_calls', 'network_requests', 'image_downloads'):
            if report.get(key) != 0: errors.append(key)
        if report.get('private_database_opened') is not False: errors.append('privacy')
        rows = report.get('results', [])
        by_id = {q['id']: q for q in queries}
        if not isinstance(rows, list) or len(rows) != len(queries) or {r['query_id'] for r in rows} != set(by_id):
            return dict(valid=False, errors=errors + ['query_coverage'])
        if replay:
            index = DocumentaryIndex(lexicon.load_records(root), sources)
        for row in rows:
            query = by_id[row['query_id']]
            if row.get('query') != query['question'] or row.get('task') != query['task']:
                errors.append('query_identity'); continue
            response = row['response']
            if replay and response != index.search(query['question']): errors.append('response_replay:' + row['query_id'])
            expected = audit(query, response, sources)
            if any(row.get(k) != v or type(row.get(k)) != type(v) for k, v in expected.items()): errors.append('reference_audit:' + row['query_id'])
            if type(row.get('seconds')) not in (int, float) or not math.isfinite(row['seconds']) or row['seconds'] < 0: errors.append('query_timing')
        expected_metrics = dict(queries=len(rows), complete=sum(r['correct_source'] and r['supported_citations'] for r in rows),
                             correct_source=sum(r['correct_source'] for r in rows), supported_citations=sum(r['supported_citations'] for r in rows),
                             covered=sum(not r['abstained'] for r in rows), abstained=sum(r['abstained'] for r in rows),
                             relevant_results=sum(r['relevant_results'] for r in rows),
                             exact_fields_matched=sum(r['exact_fields']['matched'] for r in rows),
                             exact_fields_required=sum(r['exact_fields']['required'] for r in rows),
                             categories=dict(Counter(r['category'] for r in rows)))
        if report.get('metrics') != expected_metrics: errors.append('metrics')
    except (KeyError, TypeError, ValueError, OSError) as error:
        errors.append('invalid_report:' + type(error).__name__)
    return dict(valid=not errors, errors=errors)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    path = public_path(ROOT, REPORT, writing=True)
    if args.check:
        report = json.loads(path.read_text())
    else:
        report = measure()
    validation = validate_report(report)
    if not validation['valid']:
        raise ValueError(', '.join(validation['errors']))
    if not args.check:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            raw = path.read_bytes()
            import hashlib
            backup = public_path(ROOT, 'reports/documentary-retrieval-backups/' + hashlib.sha256(raw).hexdigest() + '.json', writing=True)
            backup.parent.mkdir(parents=True, exist_ok=True)
            backup.write_bytes(raw)
        path.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + '\n')
    print(json.dumps(dict(validation=validation, metrics=report['metrics'], timing=report['timing'], memory=report['memory']), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
