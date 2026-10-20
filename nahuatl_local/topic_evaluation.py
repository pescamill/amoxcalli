"""Evaluación de la búsqueda por tema (``topics.TopicIndex``).

Uso::

    python -m nahuatl_local.topic_evaluation             # dev y test
    python -m nahuatl_local.topic_evaluation --split dev  # solo para ajustar

Conjunto: ``evaluation/topic-questions-v1.json``, escrito antes de construir la búsqueda. Acierto: algún
elemento esperado entre los 5 primeros; también se informa el primer lugar y la abstención.
"""
import argparse
import json
import time

from .stems import ROOT, WordStudy
from .terms import TermIndex
from .topics import TOPIC_VERSION, TopicIndex

QUESTIONS = ROOT / 'evaluation' / 'topic-questions-v1.json'


def run(split='all', index=None):
    data = json.loads(QUESTIONS.read_text(encoding='utf-8'))
    if index is None:
        index = TopicIndex(TermIndex(WordStudy()))
    t0 = time.perf_counter()
    index._build()
    build = time.perf_counter() - t0
    items, times = [], []
    for q in data['questions']:
        if split not in ('all', q['split']):
            continue
        t = time.perf_counter()
        r = index.search(q['query'])
        times.append(time.perf_counter() - t)
        ids = [it['id'] for it in r['top']]
        if q.get('abstain'):
            items.append(dict(id=q['id'], split=q['split'], query=q['query'], abstain_item=True, correct=r['abstained'], top=ids[:3]))
            continue
        expected = set(q['expect_any'])
        items.append(dict(id=q['id'], split=q['split'], query=q['query'], abstain_item=False,
                          at1=bool(ids) and ids[0] in expected, at5=bool(expected & set(ids[:5])), top=ids[:5]))
    summary = {}
    for part in ('dev', 'test'):
        rows = [i for i in items if i['split'] == part]
        if not rows:
            continue
        answer = [i for i in rows if not i['abstain_item']]
        abst = [i for i in rows if i['abstain_item']]
        pct = lambda n, d: round(100 * n / d, 1) if d else None
        summary[part] = dict(n=len(rows), at1=pct(sum(i['at1'] for i in answer), len(answer)),
                             at5=pct(sum(i['at5'] for i in answer), len(answer)),
                             abstention=pct(sum(i['correct'] for i in abst), len(abst)))
    return dict(version=TOPIC_VERSION, questions=data['id'], summary=summary, items=items,
                build_seconds=round(build, 2), mean_ms=round(1000 * sum(times) / max(1, len(times)), 1))


def markdown(r):
    lines = ['## Búsqueda por tema', '',
             f"`{r['version']}` · conjunto `{r['questions']}` (escrito antes de construir la búsqueda). Acierto: un elemento esperado entre los 5 primeros.", '',
             '| Partición | n | Primer lugar | Entre los 5 primeros | Abstención correcta |', '|---|---:|---:|---:|---:|']
    for part, s in r['summary'].items():
        lines.append(f"| {part} | {s['n']} | {s['at1']} % | {s['at5']} % | {s['abstention']} % |")
    misses = [i for i in r['items'] if (i['abstain_item'] and not i['correct']) or (not i['abstain_item'] and not i['at5'])]
    lines += ['', 'Fallos:', ''] + ([f"- `{i['query']}` ({i['split']}): {', '.join(i['top']) or 'sin resultados'}" for i in misses] or ['- Ninguno.'])
    if 'build_seconds' in r:
        lines += ['', f"Índice: {r['build_seconds']} s (tras el índice de términos); {r['mean_ms']} ms por consulta."]
    lines.append('')
    return '\n'.join(lines)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--split', choices=['dev', 'test', 'all'], default='all')
    print(markdown(run(p.parse_args().split)))


if __name__ == '__main__':
    main()
