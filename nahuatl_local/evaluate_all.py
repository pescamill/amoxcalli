"""Arnés único de evaluación: morfología, índice de términos, Preguntar y fichas documentales.

Uso::

    make eval                                   # = python -m nahuatl_local.evaluate_all
    make check                                  # = python -m nahuatl_local.evaluate_all --check
    python -m nahuatl_local.evaluate_all --only terms --split dev   # ajustar: imprime, no escribe

Escribe ``reports/evaluation.json`` (detalle por componente) y ``reports/EVALUACION.md`` (una
tabla de resultados y el detalle regenerable). Cada componente conserva su conjunto y sus
particiones: ``dev`` sirve para ajustar y ``test`` solo para medir; la batería documental tiene
``development`` y una reserva que no se usa.

Compuerta (``--check``): vuelve a medir y falla si una cifra difiere del informe guardado o si la
batería documental ya no se reconstruye desde los datos. Solo miden las entradas medidas (datos,
conjuntos, analizador, índices, Preguntar, fichas): un cambio de interfaz o de documentación no
mueve ninguna cifra. Tiempos y memoria se guardan aparte y no cuentan. Sin modelos ni red.
"""
import argparse
from collections import Counter
import json
import sys
import time

from . import lexicon
from . import evidence_evaluation, morphology_evaluation, term_evaluation
from .cards import CONFIG as CARDS_CONFIG, Cards, PublicSources
from .community import ROOT
from .documentary_evaluation import public_path as battery_path, validate as validate_battery
from .terms import TermIndex

REPORT = ROOT / 'reports' / 'evaluation.json'
MARKDOWN = ROOT / 'reports' / 'EVALUACION.md'
BATTERY = 'configs/documentary-evaluation-v1.json'
COMPONENTS = ('morphology', 'terms', 'evidence', 'documentary')
# Claves que dependen del equipo o de la corrida: se guardan, pero no forman parte de la compuerta.
VOLATILE = {'seconds', 'build_seconds', 'mean_ms_per_query', 'timing'}


# ---------------------------------------------------------------------------
# Fichas documentales (antes Consultar fichas): la batería de 123 consultas textuales
# ---------------------------------------------------------------------------
def field_key(field):
    return tuple(field[k] for k in ('path', 'table', 'record_id', 'field'))


def audit(query, response, sources):
    """Compara la respuesta con la referencia literal; las referencias nunca entran en la consulta."""
    expected = query['reference']
    fields = [f for hit in response['results'] for f in hit['fields']]
    returned = {field_key(f): f for f in fields}
    required = {field_key(f): f for f in expected['fields']}
    matched = [k for k, f in required.items() if k in returned and returned[k]['value'] == f['value']
               and returned[k]['row_sha256'] == f['row_sha256'] and returned[k]['file_sha256'] == f['file_sha256']]
    unsupported = [field_key(f) for f in fields if not sources.citation_valid(f)]
    urls = {u for hit in response['results'] for u in hit['urls']}
    sources_ok = set(expected['source_ids']).issubset(set(response['source_ids']))
    urls_ok = set(expected['urls']).issubset(urls)
    correct = len(matched) == len(required) and sources_ok and urls_ok
    supported = bool(fields) and not unsupported
    errors = ([] if len(matched) == len(required) else ['missing_required_fields']) + \
             ([] if not unsupported else ['unsupported_citations']) + \
             ([] if sources_ok else ['missing_required_sources']) + ([] if urls_ok else ['missing_required_urls']) + \
             (['abstained'] if response['abstained'] else [])
    return dict(correct_source=correct, supported_citations=supported, abstained=response['abstained'],
                exact_fields=dict(matched=len(matched), required=len(required)), errors=errors,
                category='complete' if correct and supported else 'abstention' if response['abstained'] else 'incomplete_or_unsupported')


def documentary_metrics(rows):
    return dict(queries=len(rows), complete=sum(r['category'] == 'complete' for r in rows),
                covered=sum(not r['abstained'] for r in rows), abstained=sum(r['abstained'] for r in rows),
                supported_citations=sum(r['supported_citations'] for r in rows),
                exact_fields_matched=sum(r['exact_fields']['matched'] for r in rows),
                exact_fields_required=sum(r['exact_fields']['required'] for r in rows),
                categories=dict(sorted(Counter(r['category'] for r in rows).items())))


def documentary(terms=None, root=ROOT):
    """Las consultas textuales de desarrollo de la batería v1, respondidas por las fichas de Preguntar."""
    battery = json.loads(battery_path(root, BATTERY).read_text(encoding='utf-8'))
    validation = validate_battery(battery, root)
    if not validation['valid']:
        raise ValueError('Batería documental obsoleta (' + ', '.join(validation['errors']) +
                         '): reconstrúyela con python -m nahuatl_local.documentary_evaluation')
    queries = [q for q in battery['queries'] if q['split'] == 'development' and q['modality'] == 'textual']
    t0 = time.perf_counter()
    sources = PublicSources(root)
    records = lexicon.load_records(root)
    cards = Cards(records, sources)
    terms = terms or TermIndex(records_fn=lambda: records)
    terms._build()
    build = time.perf_counter() - t0
    rows = []
    t0 = time.perf_counter()
    for q in queries:
        response = cards.lookup(q['question'], terms)
        rows.append(dict(query_id=q['id'], query=q['question'], task=q['task'],
                         returned=[h['kind'] + ':' + h['id'] for h in response['results']], **audit(q, response, sources)))
    seconds = time.perf_counter() - t0
    return dict(method=CARDS_CONFIG['version'], battery=dict(path=BATTERY, evaluation_sha256=validation['evaluation_sha256'],
                                                             counts=validation['counts']),
                evaluated='development · textual', reserve_used=False, model_calls=0, network_requests=0,
                summary=dict(all=documentary_metrics(rows),
                             **{'task:' + t: documentary_metrics([r for r in rows if r['task'] == t])
                                for t in sorted({r['task'] for r in rows})}),
                timing=dict(build_seconds=round(build, 2), mean_ms_per_query=round(1000 * seconds / max(1, len(rows)), 2)),
                results=rows)


def documentary_markdown(r):
    a = r['summary']['all']
    c = r['battery']['counts']
    lines = ['# Fichas documentales (Preguntar)', '',
             f"Fichas `{r['method']}` · batería `{r['battery']['path']}` (SHA256 estructurado `{r['battery']['evaluation_sha256'][:16]}…`). "
             f"Se miden las {c['development']['textual']} consultas textuales de desarrollo; la reserva "
             f"({c['reserve']['textual']} textuales y {c['reserve']['visual']} visuales) no se usa, y las "
             f"{c['development']['visual']} observaciones visuales esperan derechos de imagen y un modelo con imágenes.", '',
             'Una consulta está completa si las fichas devueltas contienen todos los campos de referencia (mismo valor, fila y '
             'archivo), sus fuentes y URLs, y todas las citas son válidas. Las referencias nunca entran en la consulta.', '',
             '| Tarea | Consultas | Completas | Con fichas | Citas válidas | Campos exactos |', '|---|---:|---:|---:|---:|---:|']
    for key, m in r['summary'].items():
        lines.append(f"| {'todas' if key == 'all' else key[5:]} | {m['queries']} | {m['complete']} | {m['covered']} | "
                     f"{m['supported_citations']}/{m['covered']} | {m['exact_fields_matched']}/{m['exact_fields_required']} |")
    lines += ['', 'Consultas incompletas:', '']
    lines += [f"- `{x['query_id']}` ({x['category']}, {x['exact_fields']['matched']}/{x['exact_fields']['required']} campos): {x['query']}"
              for x in r['results'] if x['category'] != 'complete'] or ['- Ninguna.']
    lines += ['', 'Límites: consultas parametrizadas sobre fichas conocidas; no miden comprensión, traducción ni '
              'reconocimiento de imágenes. Las referencias son documentales, sin revisión humana nueva.', '']
    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Tabla única
# ---------------------------------------------------------------------------
def _pct(v):
    return '—' if v is None else f'{v:g} %'


def _frac(v):
    return '—' if v is None else f'{100 * v:.0f} %'


def table(report):
    """Filas (componente, conjunto, medida, dev, test, total)."""
    rows = []
    m = report['morphology']
    full = list(m['gold'].values())[-1]
    sp = full.get('by_split', {})
    gold = '`evaluation/morphology-gold-v1.json`'
    rows.append(('Morfología', gold, 'Segmentación exacta (top‑1)', _frac(sp.get('dev', {}).get('top1')),
                 _frac(sp.get('test', {}).get('top1')), _frac(full['top1'])))
    rows.append(('Morfología', gold, 'Segmentación en top‑3', _frac(sp.get('dev', {}).get('top3')),
                 _frac(sp.get('test', {}).get('top3')), _frac(full['top3'])))
    rows.append(('Morfología', gold, 'Raíz correcta (top‑1)', '', '', _frac(full['stem_top1'])))
    if 'coverage' in m:
        rows.append(('Morfología', 'Pasajes `nci` de Axolotl', 'Palabras con raíz enlazada', '', '',
                     f"{100 * m['coverage']['analyzer_linked_tokens']:.1f} %"))
        ibm = m['gloss_hints']['evaluation']['results']['ibm1']
        rows.append(('Morfología', 'Molina (entradas evaluables)', 'Pistas de glosa, precisión@1 (IBM‑1)', '', '',
                     _frac(ibm['precision_at_1'])))
    t = report['terms']['summary']
    gold = '`evaluation/term-groups-v1.json`'
    for key, label in (('query_top1', 'Consulta → grupo (top‑1)'), ('spelling_coverage_certain', 'Grafías seguras'),
                       ('glyph_coverage', 'Glifos'), ('spelling_precision_labeled', 'Precisión de grafías (etiquetadas)'),
                       ('glyph_precision_labeled', 'Precisión de glifos (etiquetados)')):
        rows.append(('Índice de términos', gold, label, *(_pct(t[s][key]) if s in t else '—' for s in ('dev', 'test', 'all'))))
    e = report['evidence']['summary']['evidence']
    gold = '`evaluation/evidence-questions-v1.json`'
    for key, label in (('entry_at1', 'Entrada top‑1'), ('entry_at3', 'Entrada top‑3'), ('passage_hit', 'Con pasaje pertinente'),
                       ('passage_precision', 'Precisión de pasajes'), ('false_abstention', 'Abstención falsa'),
                       ('abstention_correct', 'Abstención correcta')):
        rows.append(('Preguntar', gold, label, *(_pct(e[s][key]) if s in e else '—' for s in ('dev', 'test', 'all'))))
    x = report['evidence']['explanation']
    rows.append(('Preguntar', gold, 'Explicaciones con citas válidas', '', '', f"{x['valid']}/{x['items']}"))
    d = report['documentary']['summary']['all']
    gold = f'`{BATTERY}`'
    rows.append(('Fichas documentales', gold, 'Consultas completas', f"{d['complete']}/{d['queries']}", 'reserva sin usar', ''))
    rows.append(('Fichas documentales', gold, 'Citas válidas', f"{d['supported_citations']}/{d['covered']}", 'reserva sin usar', ''))
    rows.append(('Fichas documentales', gold, 'Campos de referencia exactos',
                 f"{d['exact_fields_matched']}/{d['exact_fields_required']}", 'reserva sin usar', ''))
    return rows


def demote(markdown):
    """Baja un nivel los títulos de un informe de componente para incluirlo como sección."""
    return '\n'.join('#' + line if line.startswith('#') else line for line in markdown.splitlines()).strip() + '\n'


def markdown(report):
    lines = ['# Evaluación de Amoxcalli', '',
             'Una sola tabla, regenerable con `make eval` (`python -m nahuatl_local.evaluate_all`); `make check` vuelve a medir '
             'y falla si alguna cifra cambió sin regenerar este informe. Sin modelos ni red. Los conjuntos son pequeños y '
             'los escribió el equipo técnico: miden comportamiento técnico, no sustituyen la revisión de una persona experta.', '',
             '`dev` se usa para ajustar; `test` solo para medir (la primera medición de cada conjunto de prueba, antes de '
             'corregir fallos, se conserva en `reports/*-first-test-run.*`). La batería documental se mide en desarrollo; su reserva no se usa.', '',
             '| Componente | Conjunto | Medida | dev | test | total |', '|---|---|---|---:|---:|---:|']
    lines += [f"| {c} | {g} | {m} | {d} | {t} | {a} |" for c, g, m, d, t, a in table(report)]
    lines += ['', 'Detalle por componente: ' + ', '.join(f'[{n}](#{a})' for n, a in (
        ('morfología', 'evaluación-del-analizador-morfológico'), ('términos', 'evaluación-de-grupos-de-término'),
        ('Preguntar', 'evaluación-de-la-consulta-con-evidencia'), ('fichas documentales', 'fichas-documentales-preguntar'))) + '.', '']
    lines += [demote(morphology_evaluation.markdown(report['morphology'])),
              demote(term_evaluation.markdown(report['terms'])),
              demote(evidence_evaluation.markdown(report['evidence'])),
              demote(documentary_markdown(report['documentary']))]
    return '\n'.join(lines)


# ---------------------------------------------------------------------------
def stable(value):
    """El informe sin tiempos: lo que la compuerta compara."""
    if isinstance(value, dict):
        return {k: stable(v) for k, v in value.items() if k not in VOLATILE}
    if isinstance(value, list):
        return [stable(v) for v in value]
    return value


def run(only=None, split='all', write_sample=False):
    """Mide los componentes pedidos (todos por omisión) y devuelve {componente: informe}."""
    out = {}
    wanted = only or COMPONENTS
    timing = {}
    terms = TermIndex() if {'terms', 'documentary'} & set(wanted) else None
    for name in COMPONENTS:
        if name not in wanted:
            continue
        t0 = time.perf_counter()
        if name == 'morphology':
            out[name] = morphology_evaluation.run(split, write_sample=write_sample)
        elif name == 'terms':
            out[name] = term_evaluation.run(terms, split)
        elif name == 'evidence':
            out[name] = evidence_evaluation.run(split)
        elif split != 'test':
            out[name] = documentary(terms)
        timing[name] = round(time.perf_counter() - t0, 1)
        print(f'{name}: {timing[name]} s', file=sys.stderr, flush=True)
    out['timing'] = dict(seconds_per_component=timing)
    return out


def encode(report):
    # Sin ordenar claves: el orden de los sistemas y particiones es parte del informe (y de la tabla).
    return json.dumps(report, ensure_ascii=False, indent=1) + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--check', action='store_true', help='Vuelve a medir y falla si el informe guardado no coincide (no escribe).')
    parser.add_argument('--only', choices=COMPONENTS, action='append', help='Solo estos componentes: imprime, no escribe.')
    parser.add_argument('--split', choices=['dev', 'test', 'all'], default='all', help='Con --only: dev para ajustar.')
    args = parser.parse_args(argv)
    if args.only or args.split != 'all':
        report = run(args.only, args.split)
        for name in COMPONENTS:
            if name in report:
                print({'morphology': morphology_evaluation.markdown, 'terms': term_evaluation.markdown,
                       'evidence': evidence_evaluation.markdown, 'documentary': documentary_markdown}[name](report[name]))
        return
    report = run(write_sample=not args.check)
    report = dict(schema_version=1, generated_by='python -m nahuatl_local.evaluate_all', **report)
    if args.check:
        saved = json.loads(REPORT.read_text(encoding='utf-8')) if REPORT.is_file() else {}
        differences = [name for name in COMPONENTS if stable(saved.get(name)) != stable(report[name])]
        if differences:
            sys.exit('La evaluación cambió en: ' + ', '.join(differences) +
                     '. Revisa la diferencia y regenera con make eval (reports/evaluation.json, reports/EVALUACION.md).')
        if not MARKDOWN.is_file() or MARKDOWN.read_text(encoding='utf-8') != markdown(stable(saved)):
            sys.exit('reports/EVALUACION.md no corresponde a reports/evaluation.json: ejecuta make eval.')
        print('Evaluación vigente: ' + ', '.join(COMPONENTS) + '.')
        return
    REPORT.write_text(encode(report), encoding='utf-8')
    # Sin tiempos: el Markdown solo cambia cuando cambia una cifra. Se genera desde el JSON guardado,
    # igual que lo comprueba --check.
    MARKDOWN.write_text(markdown(stable(json.loads(encode(report)))), encoding='utf-8')
    print(f'{REPORT.relative_to(ROOT)} y {MARKDOWN.relative_to(ROOT)} escritos.')


if __name__ == '__main__':
    main()
