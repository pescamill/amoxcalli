"""Minería de reglas y pares de grafías, con compuerta medida y cola de revisión humana.

Uso::

    python3 -m nahuatl_local.spelling_mining            # escribe configs/spelling-rules-v1.json
    python3 -m nahuatl_local.spelling_mining --dry-run  # solo imprime

1. **Propone** reglas nuevas desde pares de grafías atestiguadas cercanas (distancia ponderada ≤ 1)
   cuyas traducciones alineadas coinciden en el corpus paralelo (comparten una palabra española
   distintiva): la diferencia de símbolos de cada par (``a → o``, ``λ → t`` al final…) se agrega por
   variedad; una diferencia con apoyo suficiente es una regla candidata.
2. **Compuerta**: una regla (de perfil o minada), o la política «las traducciones confirman una regla»
   (``aligned``), solo se activa si en la partición dev del conjunto congelado mejora el top-1 o la
   cobertura del grafo sin bajar la precisión ni añadir uniones erróneas, y si sus aristas no
   contradicen las traducciones del archivo (tasa de desacuerdo ≤ ``MAX_DISAGREE``). La partición test
   no se mira aquí.
3. Lo que no pasa la compuerta, y los pares fuertes que ninguna regla activa cubre, quedan en
   ``review``: aparecen como asociaciones inciertas y en la cola de revisión de editores
   (``editorial/spelling-review.json`` guarda las decisiones; la última por par manda y se puede deshacer).
"""
import argparse
import difflib
import json
import sys
from collections import Counter, defaultdict

from . import spelling_evaluation as E
from .spelling import RULES, RULES_PATH, ROOT, Graph, Search, deletes, distance, load_rules, symbols, unsymbols
from .stems import es_tokens
from .terms import TermIndex

MAX_DISAGREE = 0.25
REJECT_DISAGREE = 0.5   # más de la mitad de sus aristas contradicen las traducciones: se descarta, no se revisa
MIN_SUPPORT = 4
MIN_COUNT = 3
MAX_PAIR_COST = 1.0
MINED_COST = 0.5


def signature(a, b):
    """Diferencia de símbolos de un par (una sola operación), o None."""
    ops = [op for op in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes() if op[0] != 'equal']
    if len(ops) != 1:
        return None
    tag, i1, i2, j1, j2 = ops[0]
    x, y = a[i1:i2], b[j1:j2]
    if not x or not y or len(x) > 2 or len(y) > 2:
        return None
    ctx = 'end' if i2 == len(a) and j2 == len(b) else 'any'
    return (x, y, ctx) if (x, y) <= (y, x) else (y, x, ctx)


def candidate_pairs(graph):
    """Pares cercanos con traducciones que coinciden, sin arista de regla: [(a, b, costo, palabras)]."""
    keys = [k for k, s in graph.sym.items() if graph.total[k] >= MIN_COUNT and len(s) >= 4]
    index = defaultdict(set)
    for k in keys:
        s = graph.sym[k]
        index[s].add(k)
        for d in deletes(s):
            index[d].add(k)
    out = []
    for k in keys:
        s = graph.sym[k]
        pool = set(index.get(s, ()))
        for d in deletes(s):
            pool |= index.get(d, set())
        for o in pool:
            if o <= k or (min(k, o), max(k, o)) in graph.edges:
                continue
            d = distance(s, graph.sym[o], MAX_PAIR_COST)
            if d > MAX_PAIR_COST:
                continue
            verdict, shared = graph.aligned(k, o)
            if verdict == 'agree':
                out.append((k, o, round(d, 2), shared))
    return sorted(out)


def dominant(graph, k):
    c = Counter()
    for f, by in graph.forms.get(k, {}).items():
        c.update(by)
    return c.most_common(1)[0][0] if c else 'unknown'


def mine(graph):
    """Reglas candidatas desde los pares fuertes: [{id, a, b, context, support, varieties, examples}]."""
    pairs = candidate_pairs(graph)
    groups = defaultdict(list)
    for a, b, cost, shared in pairs:
        sig = signature(graph.sym[a], graph.sym[b])
        if sig:
            groups[sig].append((a, b, cost, shared))
    rules = []
    for (x, y, ctx), items in sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        if len(items) < MIN_SUPPORT or any((x, y) in ((r[0], r[1]), (r[1], r[0])) for r in RULES.values()):
            continue
        varieties = Counter(dominant(graph, k) for a, b, _, _ in items for k in (a, b))
        examples = [dict(a=graph.surfaces(a)[0]['form'], b=graph.surfaces(b)[0]['form'], shared=shared)
                    for a, b, _, shared in items[:5]]
        rid = 'mined_%s_%s%s' % (unsymbols(x), unsymbols(y), '_end' if ctx == 'end' else '')
        rules.append(dict(id=rid, a=x, b=y, context=ctx, cost=MINED_COST, support=len(items),
                          varieties=dict(varieties.most_common(4)), examples=examples,
                          label='%s = %s%s (minada: %s)' % (unsymbols(x), unsymbols(y), ' al final' if ctx == 'end' else '',
                                                          ', '.join('%s/%s' % (e['a'], e['b']) for e in examples[:2]))))
    return rules, pairs


def disagree_rate(graph, rid):
    edges = [e for e in graph.edges.values() if rid in e['rules'] and (e.get('translations') or {}).get('verdict')]
    bad = sum(e['translations']['verdict'] == 'disagree' for e in edges)
    return (round(bad / len(edges), 3) if edges else None), len(edges)


def measure(ti, gold, cfg):
    dev = dict(gold, queries=[q for q in gold['queries'] if q['split'] == 'dev'],
               pairs=[p for p in gold['pairs'] if p['split'] == 'dev'])
    search = Search(ti, cfg=cfg)
    report = E.evaluate(search, dev)
    return report['summary']['dev'], search.graph


def better(new, old):
    no_worse = (new['top1'] >= old['top1'] and (new['pair_recall'] or 0) >= (old['pair_recall'] or 0)
                and (new['pair_precision'] or 0) >= (old['pair_precision'] or 0) and new['false_merges'] <= old['false_merges'])
    gain = new['top1'] > old['top1'] or (new['pair_recall'] or 0) > (old['pair_recall'] or 0) or new['top3'] > old['top3']
    return no_worse and gain


def run(ti=None, gold=None, log=print):
    ti = ti or TermIndex()
    ti._build()
    gold = gold or json.loads(E.GOLD.read_text(encoding='utf-8'))
    decisions = load_rules()['decisions']
    base_cfg = dict(active=set(), mined=[], pairs=[], decisions=decisions)
    graph = Graph(ti.postings, ti.rows, ti.spelling_owner.keys(), cfg=base_cfg, es_tokens=es_tokens)
    mined, pairs = mine(graph)
    log('reglas minadas: %d · pares fuertes: %d' % (len(mined), len(pairs)))
    candidates = list(RULES) + [r['id'] for r in mined] + ['aligned']
    mined_by_id = {r['id']: dict(r, status='review') for r in mined}

    def cfg_with(active):
        return dict(active=set(active), decisions=decisions,
                    mined=[dict(r, status='active' if r['id'] in active else r['status']) for r in mined_by_id.values()])
    active, current = [], measure(ti, gold, cfg_with([]))[0]
    log('base dev: %s' % current)
    trail = []
    for rid in candidates:
        trial, g = measure(ti, gold, cfg_with(active + [rid]))
        rate, n = disagree_rate(g, rid) if rid != 'aligned' else (None, 0)
        ok = better(trial, current) and (rate is None or rate <= MAX_DISAGREE)
        decision = 'active' if ok else 'rejected' if rate is not None and rate > REJECT_DISAGREE else 'review'
        trail.append(dict(rule=rid, before=current, after=trial, disagree_rate=rate, edges_with_translations=n,
                          decision=decision))
        if rid in mined_by_id:
            mined_by_id[rid]['status'] = decision
        log('%-22s %s  top1 %s→%s  rec %s→%s  prec %s→%s  desacuerdo %s' % (
            rid, decision, current['top1'], trial['top1'], current['pair_recall'],
            trial['pair_recall'], current['pair_precision'], trial['pair_precision'], rate))
        if ok:
            active.append(rid)
            current = trial
    final_graph = Graph(ti.postings, ti.rows, ti.spelling_owner.keys(), cfg=cfg_with(active), es_tokens=es_tokens)
    queue = []
    for a, b, cost, shared in pairs:
        if (min(a, b), max(a, b)) in final_graph.edges or b in final_graph.cluster(a):
            continue
        queue.append(dict(a=final_graph.surfaces(a)[0]['form'], b=final_graph.surfaces(b)[0]['form'], cost=cost,
                          shared=shared, status='review'))
    return dict(version='spelling-rules-v1', gate=dict(split='dev', gold=gold['version'], max_disagree=MAX_DISAGREE,
                                                       min_support=MIN_SUPPORT),
                active=active,
                rules=[dict(id=r, label=RULES[r][4] if r in RULES else mined_by_id[r]['label'] if r in mined_by_id
                            else 'las traducciones alineadas confirman una regla de perfil') for r in candidates],
                mined_rules=[dict(r, status='active' if r['id'] in active else r['status']) for r in mined_by_id.values()],
                pairs=queue, trail=trail)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--dry-run', action='store_true')
    a = p.parse_args(argv)
    out = run()
    if not a.dry_run:
        (ROOT / RULES_PATH).write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print('activas:', out['active'], '· en revisión: %d reglas, %d pares' % (
        sum(r['status'] == 'review' for r in out['mined_rules']), len(out['pairs'])))
    return 0


if __name__ == '__main__':
    sys.exit(main())
