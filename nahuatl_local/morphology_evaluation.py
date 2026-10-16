"""Evaluación reproducible del analizador, la concordancia por raíz y las pistas de glosa.

Uso::

    python3 -m nahuatl_local.morphology_evaluation            # informe completo
    python3 -m nahuatl_local.morphology_evaluation --split dev  # solo para ajustar reglas

Escribe ``reports/morphology-evaluation.json`` y ``reports/MORFOLOGIA_EVALUACION.md``.
Las cifras miden comportamiento técnico frente a un conjunto pequeño y a un
diccionario histórico; no sustituyen la revisión lingüística.
"""
import argparse
import csv
import json
import random
import re
import statistics
import time
from collections import Counter, defaultdict
from pathlib import Path

from .morphology import Analyzer, WORD, PARTICLES, key_of, corpus_words, ANALYZER_VERSION
from .nahuatl_orthography import comparison
from . import passages
from .stems import (ROOT, load_records, load_default, StemConcordance, GlossHints, es_tokens, ES_STOP)
from .text import es_key, fold

GOLD = ROOT / 'evaluation' / 'morphology-gold-v1.json'


def _seg(a):
    return a['segmentation'].casefold() if a else ''


# ---------------------------------------------------------------------------
# 1. Conjunto de referencia (segmentación)
# ---------------------------------------------------------------------------
def gold_eval(analyzers, split):
    items = [i for i in json.loads(GOLD.read_text(encoding='utf-8'))['items'] if split in ('all', i['split'])]
    out = {}
    for name, analyzer in analyzers.items():
        top1 = top3 = stem1 = 0
        rows = []
        for item in items:
            exp = item['segmentation'].casefold()
            if analyzer is None:  # línea base: palabra sin segmentar
                got = [dict(segmentation=item['word'], stem_key=key_of(item['word']))]
            else:
                got = analyzer.analyze(item['word'], limit=3)
            segs = [_seg(a) for a in got]
            exp_stem = key_of(max(exp.split('-'), key=len))
            ok1 = bool(segs) and segs[0] == exp
            top1 += ok1
            top3 += exp in segs
            # raíz: el morfema más largo esperado coincide con la raíz propuesta
            stem_ok = bool(got) and got[0].get('stem_key') == exp_stem
            stem1 += stem_ok
            rows.append(dict(word=item['word'], expected=item['segmentation'], got=segs[0] if segs else '',
                             correct=ok1, in_top3=exp in segs, split=item['split']))
        n = len(items)
        by_split = {}
        for sp in ('dev', 'test'):
            rs = [r for r in rows if r['split'] == sp]
            if rs:
                by_split[sp] = dict(n=len(rs), top1=round(sum(r['correct'] for r in rs) / len(rs), 3),
                                    top3=round(sum(r['in_top3'] for r in rs) / len(rs), 3))
        out[name] = dict(n=n, top1=round(top1 / n, 3), top3=round(top3 / n, 3), stem_top1=round(stem1 / n, 3),
                         by_split=by_split, errors=[r for r in rows if not r['correct']])
    return out


# ---------------------------------------------------------------------------
# 2. Cobertura del diccionario en el corpus clásico
# ---------------------------------------------------------------------------
def coverage(analyzer, rows, records):
    forms = {comparison(r.get('catalog_normalized') or r.get('written') or '') for r in records.values()
             if r.get('kind') == 'form'}
    forms.discard('')
    tokens = Counter(w for w in corpus_words(rows))
    total = sum(tokens.values())
    exact = linked = explained = 0
    exact_types = linked_types = 0
    for w, n in tokens.items():
        e = comparison(w) in forms
        best = analyzer.analyze(w, limit=1)
        b = best[0] if best else None
        l = bool(b and (b['dictionary'] or b['basis'] == 'particle_table'))
        x = bool(b and (l or any(m['role'] != 'stem' for m in b['morphemes'])))
        exact += n * e; linked += n * l; explained += n * x
        exact_types += e; linked_types += l
    return dict(tokens=total, types=len(tokens),
                exact_dictionary_tokens=round(exact / total, 4),
                analyzer_linked_tokens=round(linked / total, 4),
                analyzer_explained_tokens=round(explained / total, 4),
                exact_dictionary_types=round(exact_types / len(tokens), 4),
                analyzer_linked_types=round(linked_types / len(tokens), 4),
                definitions=dict(exact='la palabra completa, normalizada, coincide con una forma del diccionario',
                                 linked='el mejor análisis enlaza la raíz con una entrada o con la tabla de partículas',
                                 explained='enlazada, o con al menos un afijo identificado'))


# ---------------------------------------------------------------------------
# 3. Concordancia: pasajes recuperables para cada entrada del diccionario
# ---------------------------------------------------------------------------
def concordance_recall(analyzer, rows, records, sample_path, seed=2026):
    conc = StemConcordance(analyzer, rows)
    nci = [r for r in rows if r['iso'] == 'nci']
    word_index = defaultdict(set)
    for r in nci:
        for m in WORD.finditer(r['nah']):
            word_index[comparison(m.group(0))].add(r['id'])
    per_entry, sample = [], []
    for stem, entries in analyzer.lexicon.stems.items():
        if len(stem) < 4:
            continue
        written = sorted({e['written'] or '' for e in entries})
        exact = set().union(*(word_index.get(comparison(w), set()) for w in written))
        stem_hits = {rid for rid, _ in conc.index.get(stem, [])}
        if not exact and not stem_hits:
            continue
        per_entry.append(dict(stem=stem, written=written, exact=len(exact), stem_index=len(stem_hits),
                              only_stem=len(stem_hits - exact), only_exact=len(exact - stem_hits)))
        for rid, w in conc.index.get(stem, []):
            if rid not in exact:
                sample.append(dict(stem=stem, entry=written[0], form=w, passage=rid))
    random.Random(seed).shuffle(sample)
    sample = sample[:60]
    if sample_path:
        Path(sample_path).parent.mkdir(parents=True, exist_ok=True)
        with open(sample_path, 'w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=['stem', 'entry', 'form', 'passage', 'nah', 'es', 'same_lexeme(y/n/?)'])
            w.writeheader()
            rows_by_id = {r['id']: r for r in nci}
            for s in sample:
                r = rows_by_id[s['passage']]
                w.writerow(dict(s, nah=r['nah'][:300], es=r['es'][:300]))
    found = [e for e in per_entry]
    return dict(entries_with_hits=len(found),
                passages_exact=sum(e['exact'] for e in found),
                passages_stem=sum(e['stem_index'] for e in found),
                entries_gaining=sum(e['only_stem'] > 0 for e in found),
                entries_losing=sum(e['only_exact'] > 0 for e in found),
                passages_only_exact=sum(e['only_exact'] for e in found),
                median_gain=statistics.median([e['stem_index'] - e['exact'] for e in found]) if found else 0,
                top_gains=sorted(found, key=lambda e: -(e['only_stem']))[:12],
                review_sample=str(sample_path.relative_to(ROOT)) if sample_path else None,
                caveat='Más pasajes no implica más aciertos: la muestra de revisión estima la precisión de los nuevos hallazgos.')


# ---------------------------------------------------------------------------
# 4. Pistas de glosa frente a las definiciones de Molina
# ---------------------------------------------------------------------------
def _molina_keys(label):
    """Claves de palabras españolas de una definición del s. XVI, con ortografía relajada."""
    out = set()
    for m in re.finditer(r'[^\W\d_]+', label):
        n = fold(m.group(0))
        if len(n) < 3 or n in ES_STOP:
            continue
        out.add(_relax(es_key(m.group(0))))
    return out


def _relax(k):
    # dezir/decir, dixo/dijo, vasallo/basallo, yerua/hierba
    k = k.replace('v', 'b').replace('z', 'c').replace('ç', 'c').replace('x', 'j').replace('y', 'i').replace('h', '')
    k = re.sub(r'(?<=[aeiou])u(?=[aeiou])', 'b', k)
    return k[:5]


def hint_eval(analyzer, rows, hints):
    # Modelos de comparación con los mismos pares: frecuencia de coocurrencia y Dice.
    pairs = []
    for r in rows:
        if r['iso'] != 'nci':
            continue
        nah = {k if k in PARTICLES else analyzer.best_stem(m.group(0)) for m in WORD.finditer(r['nah'])
               for k in [key_of(m.group(0))] if k}
        nah_keys = {key_of(m.group(0)) for m in WORD.finditer(r['nah'])}
        es = {k for k, surf in es_tokens(r['es']) if key_of(surf) not in nah_keys}
        if nah and es:
            pairs.append((nah, es))
    cooc = defaultdict(Counter)
    df_n, df_e = Counter(), Counter()
    for nah, es in pairs:
        df_e.update(es)
        for f in nah:
            df_n[f] += 1
            cooc[f].update(es)

    def baseline(f, kind):
        c = cooc.get(f)
        if not c:
            return []
        if kind == 'cooc':
            return [e for e, _ in sorted(c.items(), key=lambda x: (-x[1], x[0]))[:3]]  # empates por orden alfabético: determinista
        scored = sorted(((2 * n / (df_n[f] + df_e[e]), e) for e, n in c.items() if n >= 2), reverse=True)
        return [e for _, e in scored[:3]]

    results = {k: dict(p1=0, p3=0) for k in ('cooccurrence', 'dice', 'ibm1')}
    examples, n = [], 0
    for stem, entries in analyzer.lexicon.stems.items():
        if len(stem) < 3 or df_n.get(stem, 0) < 2:
            continue
        # Solo definiciones de Molina o del índice editorial: las glosas de Wiktionary (a veces en
        # inglés) no son la referencia que describe esta medida.
        entries = [e for e in entries if not e.get('secondary')]
        gold = set().union(*(_molina_keys(e['label']) for e in entries))
        if not gold:
            continue
        n += 1
        preds = dict(cooccurrence=baseline(stem, 'cooc'), dice=baseline(stem, 'dice'),
                     ibm1=[h['es'] for h in hints.hints(stem, 3, min_support=2)])
        for k, p in preds.items():
            rel = [_relax(x) for x in p]
            results[k]['p1'] += bool(rel[:1] and rel[0] in gold)
            results[k]['p3'] += any(x in gold for x in rel)
        if len(examples) < 15:
            examples.append(dict(stem=stem, entry=entries[0]['written'], molina=entries[0]['label'][:80],
                                 ibm1=preds['ibm1'], dice=preds['dice'], cooccurrence=preds['cooccurrence']))
    for k in results:
        results[k] = dict(precision_at_1=round(results[k]['p1'] / n, 3) if n else None,
                          hit_at_3=round(results[k]['p3'] / n, 3) if n else None)
    return dict(evaluable_entries=n, results=results, examples=examples,
                definition='Acierto si una palabra propuesta (normalizada) aparece en la definición de Molina de esa entrada. '
                           'Molina es independiente del corpus paralelo; la coincidencia ortográfica del s. XVI es aproximada.')


# ---------------------------------------------------------------------------
def run(split='all', write=True):
    t0 = time.time()
    records, rows = load_records(), passages.load()
    full = load_default(True, ROOT, records, rows)
    rules_dict = Analyzer(records)                       # diccionario sin frecuencias del corpus
    rules_only = Analyzer({})                            # solo reglas
    corpus_only = Analyzer({}); corpus_only.stem_counts = full.stem_counts; corpus_only.stem_class = full.stem_class
    gold = gold_eval({'unsegmented_baseline': None, 'rules_only': rules_only, 'rules+dictionary': rules_dict,
                      'rules+corpus_em': corpus_only, 'full (rules+dictionary+corpus_em)': full}, split)
    report = dict(analyzer=ANALYZER_VERSION, split=split, gold=gold)
    if split != 'dev':
        report['coverage'] = coverage(full, rows, records)
        report['concordance'] = concordance_recall(full, rows, records,
                                                   ROOT / 'reports' / 'morphology-review' / 'stem-hits-sample.csv' if write else None)
        hints = GlossHints.train(full, rows)
        report['gloss_hints'] = dict(meta=hints.meta, evaluation=hint_eval(full, rows, hints))
    report['seconds'] = round(time.time() - t0, 1)
    if write:
        (ROOT / 'reports').mkdir(exist_ok=True)
        (ROOT / 'reports' / 'morphology-evaluation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        (ROOT / 'reports' / 'MORFOLOGIA_EVALUACION.md').write_text(markdown(report), encoding='utf-8')
    return report


def markdown(r):
    g = r['gold']
    lines = ['# Evaluación del analizador morfológico', '',
             f"Analizador `{r['analyzer']}` · conjunto `{GOLD.name}` · partición `{r['split']}`. "
             'Generado por `python3 -m nahuatl_local.morphology_evaluation`.', '',
             '## 1. Segmentación frente al conjunto de referencia', '',
             '| Sistema | n | Segmentación exacta (top‑1) | top‑1 dev / test | En top‑3 | Raíz correcta (top‑1) |', '|---|---:|---:|---:|---:|---:|']
    for name, v in g.items():
        sp = v.get('by_split', {})
        split_cell = ' / '.join(f"{sp[k]['top1']:.0%}" for k in ('dev', 'test') if k in sp) or '—'
        lines.append(f"| {name} | {v['n']} | {v['top1']:.0%} | {split_cell} | {v['top3']:.0%} | {v['stem_top1']:.0%} |")
    full = list(g.values())[-1]
    if full['errors']:
        lines += ['', 'Errores del sistema completo:', '']
        lines += [f"- `{e['word']}` → `{e['got']}` (esperado `{e['expected']}`, {e['split']})" for e in full['errors']]
    if 'coverage' in r:
        c = r['coverage']
        lines += ['', '## 2. Cobertura del diccionario en el corpus clásico', '',
                  f"{c['tokens']:,} palabras ({c['types']:,} formas distintas) de los pasajes `nci` de Axolotl.", '',
                  '| Medida | Palabras | Formas distintas |', '|---|---:|---:|',
                  f"| Coincidencia exacta con una forma del diccionario | {c['exact_dictionary_tokens']:.1%} | {c['exact_dictionary_types']:.1%} |",
                  f"| Raíz enlazada por el analizador (diccionario o partícula) | {c['analyzer_linked_tokens']:.1%} | {c['analyzer_linked_types']:.1%} |",
                  f"| Con al menos un afijo o enlace explicado | {c['analyzer_explained_tokens']:.1%} | — |"]
        k = r['concordance']
        lines += ['', '## 3. Concordancia por raíz', '',
                  f"Para {k['entries_with_hits']} raíces del diccionario (≥4 fonemas) presentes en el corpus: "
                  f"la búsqueda por palabra exacta encuentra {k['passages_exact']} pasajes; el índice por raíz, {k['passages_stem']}. "
                  f"{k['entries_gaining']} entradas ganan pasajes; {k['entries_losing']} pierden alguno ({k['passages_only_exact']} pasajes solo por búsqueda exacta).", '',
                  f"Muestra para revisión humana de precisión: `{k['review_sample']}`. {k['caveat']}", '',
                  '| Entrada | Exacta | Por raíz |', '|---|---:|---:|']
        lines += [f"| {', '.join(e['written'])} | {e['exact']} | {e['stem_index']} |" for e in k['top_gains'][:8]]
        h = r['gloss_hints']['evaluation']
        lines += ['', '## 4. Pistas de glosa del corpus paralelo frente a Molina', '',
                  f"{h['evaluable_entries']} entradas con raíz presente en ≥2 pasajes. {h['definition']}", '',
                  '| Método | Precisión@1 | Acierto en top‑3 |', '|---|---:|---:|']
        for name, v in h['results'].items():
            lines.append(f"| {name} | {v['precision_at_1']:.0%} | {v['hit_at_3']:.0%} |")
        lines += ['', 'Ejemplos (IBM‑1):', '']
        lines += [f"- `{e['entry']}` — Molina: «{e['molina']}» → {', '.join(e['ibm1']) or '—'}" for e in h['examples'][:10]]
    lines += ['', '## Límites', '',
              '- El conjunto de referencia es pequeño y lo redactó el equipo a partir de paradigmas de gramáticas; requiere revisión especializada.',
              '- La partición `dev` se usó para ajustar costes. Tras la primera medición de `test` se corrigieron dos fallos generales '
              '(concordancia de categoría entre análisis y entrada; sustantivos breves registrados completos, como *atl*); '
              'la primera medición se conserva en `reports/morphology-evaluation-first-test-run.json`. Con 27 casos, un caso equivale a ~4 puntos.',
              '- Molina (1571) no es un diccionario completo ni moderno: una pista correcta puede no aparecer en su definición.',
              '- Ninguna cifra mide comprensión lectora ni calidad de traducción.',
              f"\nTiempo de ejecución: {r['seconds']} s."]
    return '\n'.join(lines) + '\n'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--split', choices=['dev', 'test', 'all'], default='all')
    p.add_argument('--no-write', action='store_true')
    a = p.parse_args()
    r = run(a.split, not a.no_write)
    print(markdown(r))


if __name__ == '__main__':
    main()
