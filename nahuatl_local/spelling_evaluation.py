"""Evaluación del buscador de grafías: la palabra buscada en el top-1 y top-3, precisión del grafo y latencia.

Uso::

    make eval                                            # informe único (reports/evaluation.json, «spelling»)
    python3 -m nahuatl_local.spelling_evaluation          # ajustar: imprime dev y la latencia, no escribe

Lee ``evaluation/spelling-search-v1.json`` (escrito antes de construir el buscador, con su
SHA-256 al lado) y mide por partición (dev / test) y por tipo de consulta:

* **top-1 / top-3**: el candidato (palabra) contiene alguna grafía esperada entre sus grafías
  atestiguadas seguras y ninguna de las marcadas ``not`` (homógrafos cercanos);
* **grafo**: precisión y cobertura de las asociaciones seguras sobre los pares etiquetados;
* **latencia** por consulta con los índices ya construidos (mediana, p95, máximo). Depende de la máquina:
  se imprime aparte y no entra en el informe que compara ``make check``.
"""
import argparse
import hashlib
import json
import statistics
import time
from collections import defaultdict

from .spelling import SPELLING_VERSION, Search, pivot
from .stems import ROOT
from .terms import TermIndex
from .text import fold

GOLD = ROOT / 'evaluation' / 'spelling-search-v1.json'


def forms_of(search, gid):
    info = search.word(gid)
    out = {fold(f) for k in info['keys'] for f in search.graph.forms.get(k, {})}
    out |= {fold(s) for s in info['dictionary_spellings']} | {fold(info['lemma'])}
    return out


def hit(search, candidate, query):
    forms = forms_of(search, candidate['id'])
    return bool(forms & {fold(x) for x in query['expect']}) and not (forms & {fold(x) for x in query.get('not', [])})


def score_queries(search, queries):
    rows = []
    for q in queries:
        r = search.search(q['q'], limit=3)
        cands = r['candidates']
        ok = [hit(search, c, q) for c in cands]
        rows.append(dict(split=q['split'], kind=q['kind'], q=q['q'], expect=q['expect'],
                         top1=bool(ok[:1] and ok[0]), top3=any(ok[:3]),
                         got=[dict(lemma=c['lemma'], form=c['match']['form'], how=c['match']['how'],
                                   confidence=c['match']['confidence']['label']) for c in cands[:3]],
                         attested=r['attested']))
    return rows


def score_pairs(search, pairs):
    g = search.graph
    rows = []
    for p in pairs:
        a, b = pivot(p['a']), pivot(p['b'])
        predicted = a == b or b in g.cluster(a)
        rows.append(dict(p, predicted=predicted))
    return rows


def aggregate(qrows, prows):
    def pct(n, d):
        return round(100 * n / d, 1) if d else None
    out = dict(queries=len(qrows), top1=pct(sum(r['top1'] for r in qrows), len(qrows)),
               top3=pct(sum(r['top3'] for r in qrows), len(qrows)))
    tp = sum(r['predicted'] and r['same'] for r in prows)
    fp = sum(r['predicted'] and not r['same'] for r in prows)
    pos = sum(r['same'] for r in prows)
    out.update(pairs=len(prows), pair_precision=pct(tp, tp + fp), pair_recall=pct(tp, pos), false_merges=fp)
    return out


def run(terms=None, split='all', search=None):
    """Informe del buscador de grafías sobre el conjunto congelado (``split``: 'dev' para ajustar)."""
    gold = json.loads(GOLD.read_text(encoding='utf-8'))
    if split != 'all':
        gold = dict(gold, queries=[q for q in gold['queries'] if q['split'] == split],
                    pairs=[p for p in gold['pairs'] if p['split'] == split])
    return evaluate(search or Search(terms or TermIndex()), gold)


def evaluate(search=None, gold=None):
    gold = gold or json.loads(GOLD.read_text(encoding='utf-8'))
    search = search or Search(TermIndex())
    search._build()
    qrows = score_queries(search, gold['queries'])
    prows = score_pairs(search, gold['pairs'])
    summary = {}
    for split in ('dev', 'test', 'all'):
        qs = [r for r in qrows if split == 'all' or r['split'] == split]
        if not qs:
            continue
        ps = [r for r in prows if split == 'all' or r['split'] == split]
        summary[split] = aggregate(qs, ps)
    kinds = defaultdict(list)
    for r in qrows:
        kinds[r['kind']].append(r)
    by_kind = {k: aggregate(v, []) for k, v in sorted(kinds.items())}
    for v in by_kind.values():
        for key in ('pairs', 'pair_precision', 'pair_recall', 'false_merges'):
            v.pop(key)
    return dict(version=SPELLING_VERSION, gold=gold['version'],
                gold_sha256=hashlib.sha256(GOLD.read_bytes()).hexdigest() if GOLD.is_file() else None,
                active_rules=sorted(search.graph.active), summary=summary, by_kind=by_kind,
                misses=[r for r in qrows if not r['top1']],
                pair_errors=[r for r in prows if r['predicted'] != r['same']])


def latency(search, gold, repeat=3):
    times = []
    for _ in range(repeat):
        for q in gold['queries']:
            t = time.perf_counter()
            search.search(q['q'])
            times.append((time.perf_counter() - t) * 1000)
    times.sort()
    return dict(median_ms=round(statistics.median(times), 1), p95_ms=round(times[int(0.95 * len(times))], 1),
                max_ms=round(times[-1], 1))


def markdown(report):
    s = report['summary']
    lines = ['# Evaluación del buscador de grafías', '',
             'Buscador `%s` · conjunto `%s` (SHA-256 `%s…`) · sin modelos. Regenerar: `make eval`. '
             'Detalle: [docs/GRAFIAS.md](../docs/GRAFIAS.md).' % (
                 report['version'], report['gold'], (report['gold_sha256'] or '')[:12]), '',
             'El conjunto se escribió y congeló antes de construir el buscador (commit c079a11). '
             'Reglas activas: %s.' % (', '.join(report['active_rules']) or 'ninguna'), '',
             '| Partición | Consultas | Top-1 | Top-3 | Pares | Precisión del grafo | Cobertura del grafo | Uniones erróneas |',
             '|---|---|---|---|---|---|---|---|']
    for split in [x for x in ('dev', 'test', 'all') if x in s]:
        v = s[split]
        lines.append('| %s | %d | %s%% | %s%% | %d | %s%% | %s%% | %d |' % (
            split, v['queries'], v['top1'], v['top3'], v['pairs'], v['pair_precision'], v['pair_recall'], v['false_merges']))
    lines += ['', '## Por tipo de consulta', '', '| Tipo | Consultas | Top-1 | Top-3 |', '|---|---|---|---|']
    for k, v in report['by_kind'].items():
        lines.append('| %s | %d | %s%% | %s%% |' % (k, v['queries'], v['top1'], v['top3']))
    lines += ['', '## Consultas cuyo primer candidato no es la palabra buscada', '']
    for r in report['misses']:
        got = ', '.join('%s (%s)' % (g['lemma'], g['how']) for g in r['got']) or '—'
        lines.append('- %s · «%s» → %s; esperado %s%s' % (r['split'], r['q'], got, '/'.join(r['expect']),
                                                         ' · top-3 sí' if r['top3'] else ''))
    lines += ['', '## Pares mal asociados', '']
    for r in report['pair_errors']:
        lines.append('- %s · %s / %s: %s' % (r['split'], r['a'], r['b'],
                                             'unidas sin ser la misma palabra' if r['predicted'] else 'no unidas (misma palabra)'))
    return '\n'.join(lines) + '\n'


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--split', choices=['all', 'dev'], default='dev', help='dev: solo para ajustar.')
    a = p.parse_args(argv)
    search = Search(TermIndex())
    print(markdown(run(split=a.split, search=search)))
    print('Latencia por consulta (índices construidos):', latency(search, json.loads(GOLD.read_text(encoding='utf-8'))))


if __name__ == '__main__':
    main()
