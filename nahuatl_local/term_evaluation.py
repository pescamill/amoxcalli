"""Evaluación de los grupos de término: grafías, glifos y precisión por término.

Uso::

    make eval                                            # informe único (reports/EVALUACION.md)
    python3 -m nahuatl_local.term_evaluation --split dev  # solo para ajustar; no escribe

Lee ``evaluation/term-groups-v1.json`` (escrito antes de construir el índice) y mide,
por término y por partición (dev / test):

* **consulta**: cada consulta lleva como primer grupo a uno de los lemas esperados, y
  todas las consultas del término llevan al mismo grupo;
* **cobertura de grafías**: grafías y formas flexionadas esperadas presentes en el
  grupo (en cualquier nivel; también se cuenta cuántas quedan entre las seguras);
* **cobertura de glifos**: referencias esperadas presentes con su alcance;
* **precisión sobre lo etiquetado**: aciertos seguros / (aciertos seguros + formas o
  glifos que el conjunto marca como no seguros y el índice presenta como seguros).
  Solo cuenta lo etiquetado; las demás grafías del grupo no se juzgan aquí.

Deterministas: el informe solo cambia si cambian el conjunto, el índice o sus datos.
"""
import argparse
import json
from collections import defaultdict

from .stems import ROOT
from .terms import TERMS_VERSION, TermIndex
from .text import fold, loose_key

GOLD = ROOT / 'evaluation' / 'term-groups-v1.json'


def tiers(group):
    """Formas del grupo por nivel: {forma plegada: 'certain' | 'uncertain'}."""
    out = {}
    for v in group['spellings']['uncertain']:
        for f in v['forms']:
            out[fold(f)] = 'uncertain'
    for v in group['spellings']['attested']:
        out[fold(v['form'])] = 'certain'
    for v in group['spellings']['inflected']:
        for f in v['forms']:
            out[fold(f)] = 'certain'
    return out


def glyph_name(g):
    return fold((g.get('reading') or g.get('designation') or '').split('_')[0])


def glyph_found(expected, glyphs):
    name = fold(expected.get('reading') or expected.get('designation'))
    return [g for g in glyphs if g['source'] == expected['source'] and glyph_name(g) == name
            and (not expected.get('scope') or g['scope'] == expected['scope'])]


def score_term(index, term):
    resolved = []
    for q in term['queries']:
        r = index.search(q, limit=3)
        top = r['groups'][0] if r['groups'] else None
        resolved.append(dict(query=q, group=top['id'] if top else None, lemma=top['lemma'] if top else None,
                             why=top['match']['why'] if top else None))
    lemmas = {loose_key(x) for x in term['lemma_any']}
    ok = [x for x in resolved if x['lemma'] and loose_key(x['lemma']) in lemmas]
    ids = [x['group'] for x in resolved if x['group']]
    gid = max(set(ids), key=ids.count) if ids else None
    group = index.summary(gid) if gid else None
    forms = tiers(group) if group else {}
    expected = term['spellings'] + term['inflected']
    found = {f: forms.get(fold(f)) for f in expected}
    negatives = {f: forms.get(fold(f)) for f in term['not_certain']}
    glyphs = group['glyphs'] if group else []
    uncertain_glyphs = group['glyphs_uncertain'] if group else []
    glyph_hits = [bool(glyph_found(g, glyphs)) for g in term['glyphs']]
    glyph_any = [bool(glyph_found(g, glyphs + uncertain_glyphs)) for g in term['glyphs']]
    glyph_negatives = [bool(glyph_found(dict(g, scope=None), glyphs)) for g in term['glyphs_not_certain']]
    return dict(
        id=term['id'], split=term['split'], group=gid, lemma=group['lemma'] if group else None,
        source=group['source'] if group else None,
        queries=resolved, queries_ok=len(ok), queries_total=len(resolved), same_group=len(set(ids)) == 1 and len(ids) == len(resolved),
        spellings_expected=len(expected), spellings_found=sum(v is not None for v in found.values()),
        spellings_found_certain=sum(v == 'certain' for v in found.values()),
        missing_spellings=sorted(f for f, v in found.items() if v is None),
        negatives=len(negatives), negatives_in_certain=sorted(f for f, v in negatives.items() if v == 'certain'),
        negatives_marked_uncertain=sum(v == 'uncertain' for v in negatives.values()),
        glyphs_expected=len(term['glyphs']), glyphs_found=sum(glyph_hits), glyphs_found_any_tier=sum(glyph_any),
        missing_glyphs=[g for g, hit in zip(term['glyphs'], glyph_hits) if not hit],
        glyph_negatives=len(term['glyphs_not_certain']), glyph_negatives_in_certain=sum(glyph_negatives),
        glyph_negatives_listed=[g for g, hit in zip(term['glyphs_not_certain'], glyph_negatives) if hit],
        group_size=dict(attested=len(group['spellings']['attested']) if group else 0,
                        inflected=len(group['spellings']['inflected']) if group else 0,
                        uncertain=len(group['spellings']['uncertain']) if group else 0,
                        glyphs=len(glyphs), glyphs_uncertain=len(uncertain_glyphs),
                        passages=group['passages']['total'] if group else 0))


def aggregate(rows):
    def pct(n, d):
        return round(100 * n / d, 1) if d else None
    s = lambda k: sum(r[k] for r in rows)
    fp_sp = sum(len(r['negatives_in_certain']) for r in rows)
    fp_gl = s('glyph_negatives_in_certain')
    return dict(terms=len(rows), queries=s('queries_total'),
                query_top1=pct(s('queries_ok'), s('queries_total')),
                same_group=pct(sum(r['same_group'] for r in rows), len(rows)),
                spelling_coverage=pct(s('spellings_found'), s('spellings_expected')),
                spelling_coverage_certain=pct(s('spellings_found_certain'), s('spellings_expected')),
                glyph_coverage=pct(s('glyphs_found'), s('glyphs_expected')),
                spelling_precision_labeled=pct(s('spellings_found_certain'), s('spellings_found_certain') + fp_sp),
                glyph_precision_labeled=pct(s('glyphs_found'), s('glyphs_found') + fp_gl),
                homographs_separated=pct(s('negatives') - fp_sp, s('negatives')),
                glyph_negatives_separated=pct(s('glyph_negatives') - fp_gl, s('glyph_negatives')),
                counts=dict(spellings_expected=s('spellings_expected'), spellings_found=s('spellings_found'),
                            spellings_found_certain=s('spellings_found_certain'), negatives=s('negatives'),
                            negatives_in_certain=fp_sp, glyphs_expected=s('glyphs_expected'), glyphs_found=s('glyphs_found'),
                            glyph_negatives=s('glyph_negatives'), glyph_negatives_in_certain=fp_gl))


def run(index=None, split='all'):
    gold = json.loads(GOLD.read_text(encoding='utf-8'))
    index = index or TermIndex()
    rows = [score_term(index, t) for t in gold['terms'] if split in ('all', t['split'])]
    summary = dict(all=aggregate(rows), **{s: aggregate([r for r in rows if r['split'] == s]) for s in ('dev', 'test')
                                           if any(r['split'] == s for r in rows)})
    return dict(version=TERMS_VERSION, gold=gold['id'], protocol=gold['protocol'], model_calls=0,
                generated_by='python -m nahuatl_local.evaluate_all', summary=summary, terms=rows)


def markdown(report):
    lines = ['# Evaluación de grupos de término', '',
             f"Índice `{report['version']}` · conjunto `{report['gold']}` · sin modelos. "
             'Regenerar: `make eval` (`python -m nahuatl_local.evaluate_all`).', '',
             report['protocol'], '',
             '| Partición | Términos | Consulta → grupo (top-1) | Mismo grupo | Grafías (cualquier nivel) | Grafías seguras | Glifos | Precisión grafías* | Precisión glifos* | Homógrafos separados |',
             '|---|---|---|---|---|---|---|---|---|---|']
    for split in [s for s in ('dev', 'test', 'all') if s in report['summary']]:
        a = report['summary'][split]
        lines.append(f"| {split} | {a['terms']} | {a['query_top1']}% de {a['queries']} | {a['same_group']}% | {a['spelling_coverage']}% | "
                     f"{a['spelling_coverage_certain']}% | {a['glyph_coverage']}% | {a['spelling_precision_labeled']}% | "
                     f"{a['glyph_precision_labeled']}% | {a['homographs_separated']}% |")
    lines += ['', '\\* Precisión sobre lo etiquetado: aciertos seguros frente a formas o glifos que el conjunto marca como no seguros y el índice presenta como seguros.', '',
              '## Por término', '', '| Término | Partición | Grupo | Consultas | Grafías | Glifos | Faltan | Presentadas como seguras sin serlo |', '|---|---|---|---|---|---|---|---|']
    for r in report['terms']:
        missing = ', '.join(r['missing_spellings'] + [(g.get('reading') or g.get('designation')) + f" ({g.get('scope') or 'alcance'})" for g in r['missing_glyphs']])
        wrong = ', '.join(r['negatives_in_certain'] + [(g.get('reading') or g.get('designation')) for g in r['glyph_negatives_listed']])
        lines.append(f"| {r['id']} | {r['split']} | {r['lemma']} ({r['source']}) | {r['queries_ok']}/{r['queries_total']} | "
                     f"{r['spellings_found']}/{r['spellings_expected']} | {r['glyphs_found']}/{r['glyphs_expected']} | {missing or '—'} | {wrong or '—'} |")
    lines += ['', 'Consultas que no llevan al grupo esperado:', '']
    misses = [(r['id'], q) for r in report['terms'] for q in r['queries'] if not q['lemma'] or q['group'] != r['group'] or
              loose_key(q['lemma']) not in {loose_key(x) for x in next(t for t in json.loads(GOLD.read_text(encoding='utf-8'))['terms'] if t['id'] == r['id'])['lemma_any']}]
    lines += [f"- {tid}: «{q['query']}» → {q['lemma'] or 'sin grupo'} ({q['why'] or '—'})" for tid, q in misses] or ['- ninguna']
    return '\n'.join(lines) + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--split', choices=['all', 'dev'], default='dev', help='dev: solo para ajustar.')
    args = parser.parse_args(argv)
    print(markdown(run(split=args.split)))


if __name__ == '__main__':
    main()
