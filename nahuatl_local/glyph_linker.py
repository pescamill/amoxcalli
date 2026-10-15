"""Enlaces glíficos reproducibles: referencias locales, sin red, modelo ni OCR.

Una referencia de la definición o de un ejemplo NO es la escritura de la palabra.
Las coincidencias de letras no se usan para inferir componentes o fonogramas.
"""
import argparse
from collections import Counter, defaultdict
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import time

from .community import ROOT
from .corpus import CorpusStore
from .text import fold, tokens as text_tokens
from .research import Archive


def tokens(value):
    """Conjunto de palabras plegadas (solo letras); ver ``text.tokens``."""
    return set(text_tokens(value, letters_only=True))


def build_bundle(records, rules, passages):
    records = copy.deepcopy(records)
    additions = copy.deepcopy(rules['records'])
    records.update({r['id']: r for r in additions})
    forms = defaultdict(list)
    linked = set()
    for r in records.values():
        if r['kind'] == 'form':
            forms[r['sense_id']].append(r)
        elif r['kind'] == 'glyph' and r.get('image'):
            linked.add(r['sense_id'])
    anchors = [(records[a['glyph_id']], set(map(fold, a['spanish_terms'])))
               for a in rules['anchors']]
    # Índice de tokens exactos, una sola pasada. No BM25, embeddings ni generación.
    examples = defaultdict(list)
    for row in sorted(passages, key=lambda r: (len(r['nah']) + len(r['es']), r['id'])):
        if row['iso'] != 'nci' or len(row['nah']) + len(row['es']) > 1200:
            continue
        nah, es = tokens(row['nah']), tokens(row['es'])
        candidates = [(g, next(iter(sorted(terms & es)))) for g, terms in anchors
                      if terms & es and fold(g['reading']) in nah]
        if candidates:
            for word in nah:
                examples[word].append((row, candidates))
    unresolved = []
    for sense in sorted((r for r in records.values() if r['kind'] == 'sense'), key=lambda r: r['id']):
        if sense['id'] in linked:
            continue
        fs = sorted(forms[sense['id']], key=lambda f: (not f['id'].startswith('lex-'), f['id']))
        if not fs:
            unresolved.append(dict(sense_id=sense['id'], reason='no_form'))
            continue
        form = fs[0]
        word = form['written']
        chosen = None
        # La definición de Molina menciona un referente: se relaciona ese concepto,
        # sin afirmar que sea un componente morfológico de la palabra.
        gloss = tokens(sense['definition'])
        for g, terms in anchors:
            matches = sorted(terms & gloss)
            if matches:
                term = matches[0]
                chosen = (g, dict(type='definition_reference', matched_term=term,
                    note=f'La definición histórica menciona «{term}». La imagen permite consultar ese referente; no escribe la palabra {word} completa ni demuestra su segmentación.',
                    evidence_url=form['url'], definition_quote=sense['definition']))
                break
        # Si falta un referente en la definición, busca un ejemplo de la misma
        # variedad donde aparezcan literalmente la palabra y un referente conocido.
        if chosen is None:
            for f in fs:
                keys = [fold(f['written'])]
                options = [entry for key in keys for entry in examples.get(key, [])]
                if not options:
                    continue
                row, candidates = min(options, key=lambda e: (len(e[0]['nah']) + len(e[0]['es']), e[0]['id']))
                g, term = candidates[0]
                form = f
                chosen = (g, dict(type='passage_reference', matched_term=term,
                    note=f'Referencia visual de «{g["reading"]}» en un ejemplo que contiene esta forma. No representa {word} ni es un componente suyo. El glifo y el pasaje proceden de documentos distintos.',
                    evidence_url=row['source_url'] + '#L' + str(row['line']),
                    passage=dict(id=row['id'], nah=row['nah'], es=row['es'], document=row['document'],
                                 iso=row['iso'], line=row['line'], sha256=hashlib.sha256((row['nah']+'\n'+row['es']).encode()).hexdigest())))
                break
        if chosen is None:
            unresolved.append(dict(sense_id=sense['id'], written=word, definition=sense['definition'],
                                   reason='no_documented_reference', form_url=form.get('url', '')))
            continue
        g, association = chosen
        association['reference_form_id'] = form['id']
        association['reference_glyph_id'] = g['id']
        record = {k: copy.deepcopy(v) for k, v in g.items()
                  if k not in ('id', 'version', 'association', 'expected_version')}
        record.update(id='glyph-link-v7-'+sense['id'], sense_id=sense['id'],
                      label='Referencia relacionada: '+g['reading'], association=association,
                      verification='inherited', glyph_status='proposed',
                      notes='Enlace contextual por script determinista. No es una atribución de lectura completa ni una revisión lingüística.')
        record['rights']['training'] = False
        record['evidence'].extend(copy.deepcopy(form['evidence']))
        if association['type'] == 'passage_reference':
            record['evidence'].append(dict(source_id='src-axolotl', locator='Axolotl, registro CSV '+str(association['passage']['line']), status='inherited'))
        additions.append(record)
        linked.add(sense['id'])
    report = dict(schema_version=1, senses=sum(r['kind']=='sense' for r in records.values()),
                  with_image=len(linked), pending=len(unresolved), unresolved=unresolved,
                  added_records=len(additions), association_types=dict(Counter(r['association']['type'] for r in additions if 'association' in r)),
                  llm_calls=0, network_requests=0, policy=rules['policy'])
    return dict(schema_version=1, records=additions), report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rules', type=Path, default=ROOT/'corpus/glyph-link-rules-v7.json')
    p.add_argument('--output', type=Path, default=ROOT/'corpus/glyph-associations-v7.json')
    p.add_argument('--report', type=Path, default=ROOT/'reports/glyph-coverage-v7.json')
    a = p.parse_args()
    started = time.monotonic()
    rules = json.loads(a.rules.read_text(encoding='utf-8'))
    # No abre ni modifica la base de usuarios. El lote anterior se excluye del
    # inventario para que repetir el script produzca el mismo JSON.
    installed = ROOT/'corpus/glyph-associations-v7.json'
    excluded = {r['id'] for r in json.loads(installed.read_text())['records']} if installed.exists() else set()
    with tempfile.TemporaryDirectory() as directory:
        store = CorpusStore(Path(directory)/'validation.sqlite3')
        base = {k: v for k, v in store.records().items() if k not in excluded}
        bundle, report = build_bundle(base, rules, Archive().rows)
        merged = {**base, **{r['id']:r for r in bundle['records']}}
        for r in bundle['records']:
            store.validate(r, merged)
    a.output.write_text(json.dumps(bundle, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    report['elapsed_seconds'] = round(time.monotonic()-started, 3)
    report['bundle_sha256'] = hashlib.sha256(a.output.read_bytes()).hexdigest()
    a.report.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='unresolved'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
