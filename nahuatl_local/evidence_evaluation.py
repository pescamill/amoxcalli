"""Evaluación reproducible de la consulta con evidencia frente a la búsqueda exacta.

Uso::

    python3 -m nahuatl_local.evidence_evaluation             # informe completo
    python3 -m nahuatl_local.evidence_evaluation --split dev  # solo para ajustar

Escribe ``reports/evidence-evaluation.json`` y ``reports/EVIDENCIA_EVALUACION.md``.
La pertinencia de un pasaje se decide automáticamente (raíz esperada en alguna
palabra náhuatl del pasaje, por clave laxa). Mide recuperación, no corrección
lingüística.
"""
import argparse
import json
import re
import time
from collections import defaultdict

from .evidence import EVIDENCE_VERSION, Evidence, loose_key
from .morphology import WORD
from .stems import ROOT, es_norm

QUESTIONS = ROOT / 'evaluation' / 'evidence-questions-v1.json'
SYSTEMS = ('exact_search', 'evidence')


class ExactSearch:
    """Línea base: lo que hacía la aplicación antes (coincidencia literal).

    Entradas cuya forma escrita es la palabra o cuya definición la contiene;
    pasajes del archivo con la palabra completa en náhuatl o en español."""

    def __init__(self, evidence):
        self.e = evidence

    def ask(self, query):
        e = self.e
        e._build()
        word, _ = e.parse(query)
        low, norm = word.casefold(), es_norm(word)
        pattern = re.compile(r'(?<![^\W\d_])' + re.escape(norm) + r'(?![^\W\d_])')
        entries = [h for h in e.entries.values()
                   if (h['written'] or '').casefold() == low or pattern.search(es_norm(h['label'] or ''))]
        entries.sort(key=lambda h: ((h['written'] or '').casefold() != low, h['automatic'], len(h['label'] or '')))
        passages = []
        for rid, r in e.rows.items():
            if len(passages) >= 6:
                break
            if low in {w.casefold() for w in WORD.findall(r['nah'])} or pattern.search(es_norm(r['es'])):
                passages.append(dict(id=rid, nah=r['nah']))
        return dict(entries=[dict(written=h['written']) for h in entries[:5]], passages=passages, other_varieties=[],
                    abstained=not (entries or passages))


def relevant(passage, roots):
    keys = [loose_key(r) for r in roots]
    return any(k in loose_key(w) for w in WORD.findall(passage['nah']) for k in keys)


def score(result, q):
    if q.get('abstain'):
        return dict(abstain_item=True, correct=bool(result['abstained']))
    expected = {loose_key(w) for w in q.get('entry_any', [])}
    written = [loose_key(x['written'] or '') for x in result['entries']]
    passages = result['passages'] + result.get('other_varieties', [])
    rel = sum(relevant(p, q['root']) for p in passages)
    return dict(abstain_item=False, answered=not result['abstained'],
                has_entry_expectation=bool(expected),
                entry_at1=bool(expected) and bool(written) and written[0] in expected,
                entry_at3=bool(expected) and any(w in expected for w in written[:3]),
                passages=len(passages), relevant=rel, hit=rel > 0)


def aggregate(rows):
    answer = [r for r in rows if not r['abstain_item']]
    entry = [r for r in answer if r['has_entry_expectation']]
    abst = [r for r in rows if r['abstain_item']]
    returned = sum(r['passages'] for r in answer)

    def pct(n, d):
        return round(100 * n / d, 1) if d else None
    return dict(n=len(rows), answerable=len(answer), with_entry=len(entry), abstain_items=len(abst),
                entry_at1=pct(sum(r['entry_at1'] for r in entry), len(entry)),
                entry_at3=pct(sum(r['entry_at3'] for r in entry), len(entry)),
                passage_hit=pct(sum(r['hit'] for r in answer), len(answer)),
                passage_precision=pct(sum(r['relevant'] for r in answer), returned),
                false_abstention=pct(sum(not r['answered'] for r in answer), len(answer)),
                abstention_correct=pct(sum(r['correct'] for r in abst), len(abst)))


def run(split='all', write=True):
    data = json.loads(QUESTIONS.read_text(encoding='utf-8'))
    questions = [q for q in data['questions'] if split in ('all', q['split'])]
    evidence = Evidence()
    t0 = time.perf_counter()
    evidence._build()
    build_seconds = time.perf_counter() - t0
    systems = dict(exact_search=ExactSearch(evidence), evidence=evidence)
    per_item, timing = [], {}
    for name, system in systems.items():
        t = time.perf_counter()
        for q in questions:
            result = system.ask(q['query'])
            per_item.append(dict(system=name, id=q['id'], split=q['split'], kind=q['kind'], query=q['query'], note=q.get('note'),
                                 **score(result, q),
                                 top_entry=result['entries'][0]['written'] if result['entries'] else None,
                                 interpreted_as=result.get('interpreted_as'), language=result.get('language')))
        timing[name] = round((time.perf_counter() - t) / max(1, len(questions)) * 1000, 2)
    summary = defaultdict(dict)
    for name in systems:
        mine = [r for r in per_item if r['system'] == name]
        summary[name]['all'] = aggregate(mine)
        for s in ('dev', 'test'):
            if any(r['split'] == s for r in mine):
                summary[name][s] = aggregate([r for r in mine if r['split'] == s])
        for kind in sorted({r['kind'] for r in mine}):
            summary[name]['kind:' + kind] = aggregate([r for r in mine if r['kind'] == kind])
    report = dict(version=EVIDENCE_VERSION, questions=data['id'], split=split, relevance=data['relevance'],
                  build_seconds=round(build_seconds, 2), mean_ms_per_query=timing, model_calls=0,
                  summary=summary, items=per_item)
    if write:
        (ROOT / 'reports' / 'evidence-evaluation.json').write_text(
            json.dumps(report, ensure_ascii=False, indent=1, sort_keys=True) + '\n', encoding='utf-8')
        (ROOT / 'reports' / 'EVIDENCIA_EVALUACION.md').write_text(markdown(report), encoding='utf-8')
    return report


def _cell(v):
    return '—' if v is None else f'{v:g}%'


def markdown(r):
    s = r['summary']
    lines = ['# Evaluación de la consulta con evidencia', '',
             f"Sistema `{r['version']}` · conjunto `{r['questions']}` · partición `{r['split']}`. "
             'Generado por `python3 -m nahuatl_local.evidence_evaluation`. Cero llamadas a modelos.', '',
             '## 1. Resultado por partición', '',
             '| Sistema | Partición | n | Entrada top‑1 | Entrada top‑3 | Con pasaje pertinente | Precisión de pasajes | Abstención falsa | Abstención correcta |',
             '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for name in SYSTEMS:
        for part in ('dev', 'test', 'all'):
            if part in s[name]:
                a = s[name][part]
                lines.append(f"| {name} | {part} | {a['n']} | {_cell(a['entry_at1'])} | {_cell(a['entry_at3'])} | "
                             f"{_cell(a['passage_hit'])} | {_cell(a['passage_precision'])} | {_cell(a['false_abstention'])} | "
                             f"{_cell(a['abstention_correct'])} |")
    lines += ['', '## 2. Por tipo de consulta (todas las particiones)', '',
              '| Tipo | n | Entrada top‑1 (base → evidencia) | Con pasaje pertinente (base → evidencia) |', '|---|---:|---|---|']
    for key in sorted(k for k in s['evidence'] if k.startswith('kind:')):
        b, e = s['exact_search'][key], s['evidence'][key]
        lines.append(f"| {key[5:]} | {e['n']} | {_cell(b['entry_at1'])} → {_cell(e['entry_at1'])} | "
                     f"{_cell(b['passage_hit'])} → {_cell(e['passage_hit'])} |")
    misses = [i for i in r['items'] if i['system'] == 'evidence' and
              ((i['abstain_item'] and not i['correct']) or
               (not i['abstain_item'] and (not i['hit'] or (i['has_entry_expectation'] and not i['entry_at1']))))]
    lines += ['', '## 3. Fallos del sistema con evidencia', '']
    for i in misses:
        what = ('no se abstuvo' if i['abstain_item'] else
                ', '.join(x for x in (('sin pasaje pertinente' if not i['hit'] else ''),
                                      (f"entrada top‑1: {i['top_entry'] or 'ninguna'}" if i['has_entry_expectation'] and not i['entry_at1'] else '')) if x))
        lines.append(f"- `{i['query']}` ({i['split']}, {i['kind']}): {what}" + (f" — {i['note']}" if i.get('note') else ''))
    if not misses:
        lines.append('- Ninguno.')
    lines += ['', '## Límites', '',
              f"- {r['relevance']}",
              '- El conjunto es pequeño y lo escribió el equipo técnico; las particiones separan desarrollo de prueba, no sustituyen la revisión de una persona experta.',
              f"- Construcción de índices: {r['build_seconds']} s (sobre cachés derivados ya presentes). Tiempo medio por consulta: "
              + ', '.join(f'{k} {v} ms' for k, v in r['mean_ms_per_query'].items()) + '.', '']
    return '\n'.join(lines)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--split', choices=['dev', 'test', 'all'], default='all')
    p.add_argument('--no-write', action='store_true')
    a = p.parse_args()
    print(markdown(run(a.split, not a.no_write)))


if __name__ == '__main__':
    main()
