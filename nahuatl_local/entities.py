"""Dioses y calendario: entidades con procedencia por dato, lecturas de mitología y una unidad del calendario.

Modelo
------
``corpus/entities-seed-v1.json`` es lo que redacta el proyecto: nombres, atributos breves,
relaciones, numerales, signos y veintenas, y **cada dato cita su fuente** (``sources``):

* ``passage`` + ``quote``: pasaje del archivo (Axolotl); la cita debe estar literalmente en el náhuatl;
* ``sense``: acepción del catálogo léxico (Wiktionary CC BY-SA o curada), con su licencia;
* ``wiktionary``: revisión fijada de una página de Wiktionary (``wiktionary_revisions`` de la semilla);
* ``tlachia_reading`` / ``element``: lectura o elemento del catálogo de Tlachia (UNAM, con atribución).

``generate`` completa la semilla, sin modelo ni red, con lo que ya existe:

* **grafías** de cada nombre desde el índice de términos (``TermIndex.search``: solo las grafías con la
  misma clave laxa, nunca las formas flexionadas ni las inciertas) y frases del archivo (``text.loose_key``);
* **pasajes** del archivo que las nombran (los de documentos restringidos se cuentan, no se muestran);
* **Tlachia**: Señores de la Noche (``yohualteuctli : X``), figuras de lámina (``inacayo : X``) y atavíos;
* **calendario**: los glifos de días del Telleriano-Remensis fijan la trecena de cada lámina y comprueban
  el orden de los 20 signos; los nombres calendáricos del archivo (numeral + signo) dan los pasajes de cada día;
* **lecturas** de mitología (receta de ``lesson_builder``, propuesta sin aplicar) y una **unidad** de los
  nombres del calendario, validada contra las tablas y los pasajes.

Nada del Códice Florentino (``restricted_documents``/``restricted_passages``) ni imágenes generadas: las
imágenes son las de Tlachia, cargadas desde su sitio. Las lecturas, la unidad y la semilla entran en la
cola editorial (``editorial/lesson-decisions.json``): nada se presenta como revisado sin revisor.

Uso::

    python3 -m nahuatl_local.entities            # regenera entidades, receta, propuesta, cola e informe
    python3 -m nahuatl_local.entities --check    # falla si algún archivo generado no está al día
"""
import argparse
import copy
import hashlib
import json
import re
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from threading import Lock

from . import passages as passage_store
from .lesson_audit import fingerprint, merge_decisions
from .morphology import WORD
from .passages import LABELS
from .stems import ROOT
from .text import fold, loose_key
from .units import DECISIONS, RECIPE as UNITS_RECIPE, LEARNING, encode, passage_hash, review_state, sha, stable, whole

SEED = ROOT / 'corpus' / 'entities-seed-v1.json'
ENTITIES = ROOT / 'corpus' / 'entities-v1.json'
READINGS_ID = 'lecturas-mitologia-001'
RECIPE = ROOT / 'configs' / (READINGS_ID + '.json')
PROPOSAL = ROOT / 'editorial' / (READINGS_ID + '.json')
QUEUE = ROOT / 'reports' / 'entities-review-queue.json'
COVERAGE = ROOT / 'reports' / 'entities-coverage.json'
GENERATOR_VERSION = 'entities-gen-1'
SAMPLE = 8            # pasajes de muestra por ficha
DRAFT = ('Fichas generadas desde la semilla del proyecto, el índice de términos, el archivo y Tlachia. '
         'Atributos redactados por el proyecto con su fuente; pendientes de revisión especializada.')
TLACHIA = dict(label='Tlachia, UNAM', url='https://tlachia.iib.unam.mx/',
               license='Consulta con atribución; imágenes desde su sitio, sin redistribuir ni relicenciar')
AXOLOTL = dict(label='Axolotl (Elotl)', license='MPL-2.0 declarada por el distribuidor; auditar cada obra antes de redistribuir')
KIND_LABELS = dict(deity='Deidad', figure='Figura de lámina', epithet='Epíteto', place='Lugar')
CALENDAR_CUES = ('veintena', 'fiesta', 'mes ', 'mes,', 'mes.')


def phrase_key(text):
    """Clave de una frase: claves laxas de sus palabras (``loose_key``), separadas por espacio."""
    return ' '.join(k for k in (loose_key(w) for w in WORD.findall(text)) if k)


def tokens(text):
    return [(m.group(0), loose_key(m.group(0))) for m in WORD.finditer(text)]


def find_phrase(keys, toks):
    """Posiciones donde la frase (lista de claves) aparece en ``toks``."""
    n = len(keys)
    return [i for i in range(len(toks) - n + 1) if [k for _, k in toks[i:i + n]] == keys]


def bounded(needle, haystack):
    return re.search(r'(?<![\w])' + re.escape(fold(needle)) + r'(?![\w])', fold(haystack)) is not None


def folio(locator):
    return locator.split('_', 1)[-1] if locator else ''


class Context:
    """Fuentes ya cargadas: archivo, catálogo léxico, Tlachia y semilla."""

    def __init__(self, records, terms=None, seed=None):
        from .pictography import public_catalog
        self.seed = seed or json.loads(SEED.read_text())
        self.records = records
        self.rows = {r['id']: r for r in passage_store.load()}
        self.terms = terms
        cat = public_catalog(records)
        self.pages = {p['id']: p for p in cat['pages']}
        self.documents = {d['id']: d for d in cat['documents']}
        self.elements = {e['id']: e for e in cat['elements']}
        self.occurrences = cat['occurrences']
        self.tlachia_rights = cat.get('rights', {}).get('note', '')
        self.restricted_docs = self.seed['restricted_documents']
        self.restricted_ids = self.seed['restricted_passages']
        self.nci = [r for r in self.rows.values() if r['iso'] == 'nci']
        self._tokens = {}

    def toks(self, rid):
        if rid not in self._tokens:
            self._tokens[rid] = tokens(self.rows[rid]['nah'])
        return self._tokens[rid]

    def restricted(self, rid):
        row = self.rows[rid]
        return rid in self.restricted_ids or row['document'] in self.restricted_docs

    # -- fuentes ------------------------------------------------------------
    def source(self, src, where):
        """Ficha de una fuente citada, comprobada; ValueError si no respalda el dato."""
        if 'passage' in src:
            row = self.rows.get(src['passage'])
            if not row:
                raise ValueError(f'{where}: pasaje inexistente {src["passage"]}')
            if self.restricted(row['id']):
                raise ValueError(f'{where}: {row["id"]} es de un documento restringido')
            if src['quote'] not in row['nah']:
                raise ValueError(f'{where}: la cita «{src["quote"]}» no está en {row["id"]}')
            return dict(kind='passage', id=row['id'], quote=src['quote'], document=row['document'], locator=row['locator'],
                        url=row['source_url'], license=AXOLOTL['license'], label=f'{row["document"] or "Archivo"} · {row["id"]}',
                        source_hash=passage_hash(row))
        if 'sense' in src:
            r = self.records.get(src['sense'])
            if not r or r['kind'] != 'sense':
                raise ValueError(f'{where}: acepción inexistente {src["sense"]}')
            rights = r.get('rights') or {}
            wikt = r.get('import_source') == 'wiktionary'
            return dict(kind='sense', id=r['id'], gloss=r.get('definition') or r.get('label'),
                        label=('Wiktionary' if wikt else 'Diccionario del proyecto') + ' · ' + (r.get('label') or '')[:60],
                        url=r.get('url'), license=rights.get('license') or rights.get('basis') or rights.get('note'),
                        attribution=rights.get('attribution'), automatic=r.get('import_status') == 'automatic_transcription')
        if 'wiktionary' in src:
            rev = self.seed['wiktionary_revisions'].get(src['wiktionary'])
            if not rev:
                raise ValueError(f'{where}: revisión de Wiktionary sin fijar {src["wiktionary"]}')
            lang, title = src['wiktionary'].split(':', 1)
            url = f'https://{lang}.wiktionary.org/w/index.php?' + 'title=' + title.replace(' ', '_') + f'&oldid={rev["revid"]}'
            return dict(kind='wiktionary', id=src['wiktionary'], gloss=rev['gloss'], url=url, revid=rev['revid'], timestamp=rev['timestamp'],
                        label=f'Wiktionary ({lang}) · {title}', license='CC BY-SA 4.0',
                        attribution=f'Colaboradores de Wiktionary, «{title}», revisión {rev["revid"]}', consulted='2026-10-16')
        if 'tlachia_reading' in src:
            # La lectura completa; si no, las lecturas que la contienen como frase (matlactli oce cohuatl).
            hits = [o for o in self.occurrences if fold(o['reading']) == fold(src['tlachia_reading'])] or \
                [o for o in self.occurrences if find_phrase(phrase_key(src['tlachia_reading']).split(), tokens(o['reading']))]
            if not hits:
                raise ValueError(f'{where}: Tlachia no tiene la lectura «{src["tlachia_reading"]}»')
            pages = sorted({self.pages[o['page_id']]['locator'] for o in hits})
            return dict(kind='tlachia', id=hits[0]['id'], ids=[o['id'] for o in hits], reading=hits[0]['reading'],
                        label=f'Tlachia · {self.documents[self.pages[hits[0]["page_id"]]["document_id"]]["title"]} · '
                              + ', '.join('f. ' + folio(p) for p in pages),
                        url=hits[0]['url'], license=TLACHIA['license'])
        if 'element' in src:
            e = self.elements.get(src['element'])
            if not e:
                raise ValueError(f'{where}: elemento de Tlachia inexistente {src["element"]}')
            return dict(kind='tlachia_element', id=e['id'], designation=e['designation'], gloss=', '.join(e.get('meanings', [])),
                        label=f'Tlachia · elemento {e["designation"]} ({self.documents[e["document_id"]]["title"]})',
                        url=e['url'], image=e.get('image'), license=TLACHIA['license'])
        raise ValueError(f'{where}: fuente desconocida {src}')

    def sources(self, items, where):
        if not items:
            raise ValueError(f'{where}: dato sin fuente')
        return [self.source(s, where) for s in items]

    # -- grafías y pasajes --------------------------------------------------
    def term_group(self, name):
        """Grupo del índice de términos cuya grafía coincide (misma clave laxa) con el nombre, o None."""
        if self.terms is None or len(WORD.findall(name)) != 1:
            return None
        lk = loose_key(name)
        try:
            result = self.terms.search(name, limit=3, full=3)
        except ValueError:
            return None
        for g in result['groups']:
            if 'spellings' in g and any(loose_key(v['form']) == lk for v in g['spellings']['attested']):
                return g
        return None

    def phrase_passages(self, names):
        """Pasajes clásicos y del archivo con alguna de las frases (claves laxas) → {rid: forma}."""
        found = {}
        keys = [phrase_key(n).split() for n in names]
        for rid, row in self.rows.items():
            toks = self.toks(rid)
            for k in keys:
                for i in find_phrase(k, toks):
                    found.setdefault(rid, ' '.join(w for w, _ in toks[i:i + len(k)]))
        return found

    def passage_summary(self, ids, forms=None):
        ids = sorted(set(ids))
        visible = [rid for rid in ids if not self.restricted(rid)]
        nci = [rid for rid in visible if self.rows[rid]['iso'] == 'nci']
        # Muestra: pasajes clásicos, alternando obras para no repetir la misma crónica.
        by_doc = defaultdict(list)
        for rid in nci:
            by_doc[self.rows[rid]['document']].append(rid)
        sample, docs = [], sorted(by_doc, key=lambda d: (-len(by_doc[d]), d))
        while len(sample) < SAMPLE and any(by_doc[d] for d in docs):
            for d in docs:
                if by_doc[d] and len(sample) < SAMPLE:
                    sample.append(by_doc[d].pop(0))
        return dict(total=len(ids), restricted=len(ids) - len(visible),
                    by_variety=dict(Counter(LABELS.get(self.rows[r]['iso'], self.rows[r]['iso']) for r in ids).most_common()),
                    sample=[dict(id=r, form=(forms or {}).get(r)) for r in sample])


# ---------------------------------------------------------------------------
# Tlachia: Señores de la Noche, figuras de lámina, atavíos y glifos de días
# ---------------------------------------------------------------------------
def tlachia_roles(ctx, names):
    """Registros de Tlachia cuya lectura nombra a la entidad tras « : »."""
    wanted = {fold(n) for n in names}
    out = []
    for o in ctx.occurrences:
        if ' : ' not in o['reading']:
            continue
        left, right = (s.strip() for s in o['reading'].split(' : ', 1))
        if fold(right) not in wanted:
            continue
        role = 'night_lord' if fold(left) == 'yohualteuctli' else 'figure' if fold(left).startswith('inacayo') else 'attire'
        page = ctx.pages[o['page_id']]
        out.append(dict(id=o['id'], role=role, reading=o['reading'], item=left, code=o['code'], page_id=o['page_id'],
                        locator=page['locator'], folio=folio(page['locator']),
                        document=ctx.documents[page['document_id']]['title'], url=o['url'], image=o.get('image')))
    return out


def parse_calendar_name(toks, i, numerals, signs):
    """(n, signo, fin) si en la posición ``i`` hay numeral + signo; si no, None."""
    for width in (3, 2, 1):
        key = ' '.join(k for _, k in toks[i:i + width])
        if len(toks[i:i + width]) == width and key in numerals and i + width < len(toks):
            sign = signs.get(toks[i + width][1])
            if sign is not None:
                return numerals[key], sign, i + width + 1
    return None


def calendar_tables(seed):
    numerals = {phrase_key(s): n['n'] for n in seed['numerals'] for s in n['spellings']}
    signs = {phrase_key(s): i for i, sg in enumerate(seed['signs']) for s in sg['spellings']}
    return numerals, signs


def tlachia_days(ctx):
    numerals, signs = calendar_tables(ctx.seed)
    days = []
    for o in ctx.occurrences:
        toks = tokens(o['reading'])
        if ':' in o['reading'] or not toks:
            continue
        hit = parse_calendar_name(toks, 0, numerals, signs)
        if hit and hit[2] == len(toks):
            page = ctx.pages[o['page_id']]
            days.append(dict(id=o['id'], n=hit[0], sign=hit[1], reading=o['reading'], code=o['code'], page_id=o['page_id'],
                             locator=page['locator'], folio=folio(page['locator']), url=o['url'], image=o.get('image')))
    return days


def trecena_of(n, sign):
    """Trecena (1..20) de un día: la que empieza en el signo ``sign - (n - 1)``."""
    start = (sign - (n - 1)) % 20
    return next(k for k in range(1, 21) if (13 * (k - 1)) % 20 == start)


def day_index(n, sign):
    """Posición (0..259) en el tonalpohualli de ``n`` (1..13) y signo (0..19)."""
    return next(d for d in range(260) if d % 13 == n - 1 and d % 20 == sign)


# ---------------------------------------------------------------------------
# Construcción
# ---------------------------------------------------------------------------
def build_entities(ctx):
    seed = ctx.seed
    out, index = [], {}

    def claim(key, eid, kind):
        if not key:
            return
        if key in index and index[key]['id'] != eid:
            raise ValueError(f'La grafía «{key}» lleva a dos fichas: {index[key]["id"]} y {eid}')
        index[key] = dict(id=eid, kind=kind)

    for e in seed['entities']:
        where = e['id']
        spellings, groups, ids, forms = Counter(), [], set(), {}
        names = list(e['names'])
        if e.get('search', True):
            # El índice de términos da el grupo (y sus grafías: misma clave laxa); los pasajes se cuentan por esas
            # grafías, sin formas flexionadas, para no depender de los cambios del analizador.
            phrases = list(names)
            for name in names:
                g = ctx.term_group(name)
                if g and g['id'] not in {x['id'] for x in groups}:
                    groups.append(dict(id=g['id'], lemma=g['lemma'], source=g['source']))
                    phrases += [v['form'] for v in g['spellings']['attested']]
            for rid, form in ctx.phrase_passages(phrases).items():
                ids.add(rid)
                forms[rid] = form
                spellings[form.casefold()] += 1
        tl = tlachia_roles(ctx, e.get('tlachia', []) + [n.casefold() for n in names])
        attrs = [dict(text=a['text'], written_by='project', sources=ctx.sources(a['sources'], where)) for a in e.get('attributes', [])]
        # Atributos de plantilla desde Tlachia (marcados como generados).
        lords = sorted({t['folio'] for t in tl if t['role'] == 'night_lord'})
        if lords:
            attrs.append(dict(text=f'Tlachia lo identifica como Señor de la Noche (yohualteuctli) en {len(lords)} '
                                   f'{"lámina" if len(lords) == 1 else "láminas"} del Telleriano-Remensis.',
                              written_by='template', sources=[dict(kind='tlachia', id=t['id'], label=f'Tlachia · f. {t["folio"]}', url=t['url'],
                                                                   reading=t['reading'], license=TLACHIA['license'])
                                                              for t in tl if t['role'] == 'night_lord'][:3]))
        figure_pages = sorted({t['folio'] for t in tl if t['role'] in ('figure', 'attire')})
        if figure_pages:
            attire = [t for t in tl if t['role'] == 'attire']
            attrs.append(dict(text=f'Figura de {"la lámina" if len(figure_pages) == 1 else "las láminas"} '
                                   + ', '.join('f. ' + p for p in figure_pages)
                                   + f' del Telleriano-Remensis; Tlachia registra {len(attire)} atavíos o elementos con su lectura.',
                              written_by='template', sources=[dict(kind='tlachia', id=t['id'], label=f'Tlachia · f. {t["folio"]}', url=t['url'],
                                                                   reading=t['reading'], license=TLACHIA['license'])
                                                              for t in tl if t['role'] == 'figure'][:3] or
                                                             [dict(kind='tlachia', id=tl[0]['id'], label=f'Tlachia · f. {tl[0]["folio"]}', url=tl[0]['url'],
                                                                   reading=tl[0]['reading'], license=TLACHIA['license'])]))
        epithets = [dict(name=x['name'], sources=ctx.sources(x['sources'], where + ':' + x['name'])) for x in e.get('epithets', [])]
        relations = [dict(type=r['type'], target=r['target'], text=r['text'], sources=ctx.sources(r['sources'], where + ':relación'))
                     for r in e.get('relations', [])]
        senses = [ctx.source(dict(sense=s), where) for s in e.get('senses', [])]
        if not attrs and not senses:
            raise ValueError(f'{where}: ficha sin ningún dato con fuente')
        for name in names + [x['name'] for x in epithets] + list(spellings):
            if e.get('search', True):
                claim(phrase_key(name), e['id'], e['kind'])
        out.append(dict(id=e['id'], kind=e['kind'], kind_label=KIND_LABELS[e['kind']], name=e['name'], names=names,
                        spellings=[dict(form=f, total=n) for f, n in sorted(spellings.items(), key=lambda x: (-x[1], x[0]))],
                        epithets=epithets, senses=senses, attributes=attrs, relations=relations, note=e.get('note'),
                        term_groups=groups, passages=ctx.passage_summary(ids, forms), tlachia=tl,
                        searchable=e.get('search', True)))
    known = {e['id'] for e in out}
    for e in out:
        for r in e['relations']:
            if r['target'] not in known:
                raise ValueError(f'{e["id"]}: relación con una ficha inexistente {r["target"]}')
    return out, index


def build_calendar(ctx, entities, index):
    seed = ctx.seed
    numerals, signs = calendar_tables(seed)
    days = tlachia_days(ctx)
    # Cada lámina con glifos de días pertenece a una sola trecena; si no, el orden de los signos es otro.
    page_trecena = {}
    for d in days:
        k = trecena_of(d['n'], d['sign'])
        if page_trecena.setdefault(d['page_id'], k) != k:
            raise ValueError(f'Los glifos de días de {d["locator"]} no forman una sola trecena con el orden de signos de la semilla')
    if len(page_trecena) < 10:
        raise ValueError('Muy pocas láminas con días para comprobar el orden de los signos')
    # Nombres calendáricos del archivo (numeral + signo): seguros si la traducción da el número.
    archive_days = defaultdict(list)
    for row in ctx.nci:
        if ctx.restricted(row['id']):
            continue
        toks = ctx.toks(row['id'])
        i = 0
        while i < len(toks):
            hit = parse_calendar_name(toks, i, numerals, signs)
            if not hit:
                i += 1
                continue
            n, s, end = hit
            text = ' '.join(w for w, _ in toks[i:end])
            year = end < len(toks) and toks[end][1] in {phrase_key(x) for x in ('xihuitl', 'xiuitl', 'xiuhtonalli')}
            certain = re.search(r'(?<!\d)' + str(n) + r'(?!\d)', row['es']) is not None
            archive_days[(n, s)].append(dict(id=row['id'], text=text, year=year, certain=certain))
            i = end
    entity_by_id = {e['id']: e for e in entities}
    figures_by_page = defaultdict(set)
    lords_by_page = defaultdict(set)
    for e in entities:
        for t in e['tlachia']:
            (lords_by_page if t['role'] == 'night_lord' else figures_by_page)[t['page_id']].add(e['id'])
    num_out = []
    for n in seed['numerals']:
        count = sum(len(v) for (k, _), v in archive_days.items() if k == n['n'])
        num_out.append(dict(id=f'numeral-{n["n"]}', n=n['n'], name=n['name'], spellings=n['spellings'],
                            sources=ctx.sources(n['sources'], f'numeral {n["n"]}'), archive_names=count))
        for s in n['spellings']:
            index.setdefault(phrase_key(s), dict(id=f'numeral-{n["n"]}', kind='numeral'))
    sign_out = []
    for i, sg in enumerate(seed['signs']):
        where = 'signo ' + sg['name']
        gloss = []
        if sg.get('element'):
            gloss.append(ctx.source(dict(element=sg['element']), where))
        if sg.get('sense'):
            gloss.append(ctx.source(dict(sense=sg['sense']), where))
        if not any(bounded(sg['es'], g.get('gloss') or '') for g in gloss):
            raise ValueError(f'{where}: la glosa «{sg["es"]}» no sale de sus fuentes')
        glyphs = [d for d in days if d['sign'] == i]
        hits = [h for (n, s), v in archive_days.items() if s == i for h in v]
        sign_out.append(dict(id='signo-' + sg['name'], n=sg['n'], name=sg['name'], es=sg['es'], spellings=sg['spellings'],
                             gloss_sources=gloss, glyphs=glyphs, element=gloss[0] if gloss and gloss[0]['kind'] == 'tlachia_element' else None,
                             archive_names=dict(total=len(hits), certain=sum(h['certain'] for h in hits))))
        for s in sg['spellings']:
            index.setdefault(phrase_key(s), dict(id='signo-' + sg['name'], kind='sign'))
    trecenas = []
    for k in range(1, 21):
        start = (13 * (k - 1)) % 20
        pages = sorted(p for p, t in page_trecena.items() if t == k)
        trecenas.append(dict(id=f'trecena-{k}', n=k, start_sign=start, name='ce ' + seed['signs'][start]['name'],
                             pages=[dict(page_id=p, folio=folio(ctx.pages[p]['locator']), url=ctx.pages[p]['url']) for p in pages],
                             figures=sorted({f for p in pages for f in figures_by_page[p]}),
                             night_lords=sorted({f for p in pages for f in lords_by_page[p]}),
                             glyphs=[d['id'] for d in days if d['page_id'] in pages]))
    veintenas = []
    for v in seed['veintenas']:
        where = 'veintena ' + v['name']
        found = ctx.phrase_passages(v['spellings'])
        certain, uncertain = [], []
        for rid, form in sorted(found.items()):
            row = ctx.rows[rid]
            if ctx.restricted(rid) or row['iso'] != 'nci':
                continue
            es = fold(row['es'])
            (certain if any(c in es for c in CALENDAR_CUES) or bounded(form, row['es']) or bounded(v['name'], row['es']) else uncertain).append(dict(id=rid, form=form))
        ded = v.get('dedication')
        if ded and ded['target'] and ded['target'] not in entity_by_id:
            raise ValueError(f'{where}: dedicada a una ficha inexistente {ded["target"]}')
        veintenas.append(dict(id='veintena-' + v['name'].replace(' ', '-'), n=v['n'], name=v['name'], kind=v.get('kind', 'veintena'),
                              spellings=v['spellings'],
                              position=dict(basis=v['position']['basis'], text=v['position'].get('text'),
                                            sources=ctx.sources(v['position']['sources'], where + ':posición')),
                              name_sources=[ctx.source(s, where) for s in v['name_sources']], name_pending=not v['name_sources'],
                              dedication=dict(target=ded['target'], label=ded['label'], sources=ctx.sources(ded['sources'], where + ':dedicación')) if ded else None,
                              note=v.get('note'), passages=dict(certain=certain[:SAMPLE], uncertain=uncertain[:SAMPLE],
                                                                certain_total=len(certain), uncertain_total=len(uncertain)),
                              tlachia=[dict(id=o['id'], reading=o['reading'], folio=folio(ctx.pages[o['page_id']]['locator']), url=o['url'], image=o.get('image'))
                                       for o in ctx.occurrences if any(bounded(s, o['reading']) for s in v['spellings'])]))
        for s in v['spellings']:
            index.setdefault(phrase_key(s), dict(id=veintenas[-1]['id'], kind='veintena'))
    if [v['n'] for v in veintenas] != list(range(1, 20)):
        raise ValueError('Las veintenas deben ir numeradas del 1 al 18 más nemontemi')
    # Días con datos: glifo de Tlachia o nombre en el archivo.
    day_data = {}
    for (n, s), hits in archive_days.items():
        day_data.setdefault(f'{n}-{s}', dict(n=n, sign=s, passages=[], glyphs=[]))['passages'] = sorted(hits, key=lambda h: (not h['certain'], h['id']))[:SAMPLE]
        day_data[f'{n}-{s}']['passages_total'] = len(hits)
    for d in days:
        day_data.setdefault(f'{d["n"]}-{d["sign"]}', dict(n=d['n'], sign=d['sign'], passages=[], glyphs=[]))['glyphs'].append(d['id'])
    for key, d in day_data.items():
        d.setdefault('passages_total', 0)
        d['trecena'] = trecena_of(d['n'], d['sign'])
        d['index'] = day_index(d['n'], d['sign'])
    structure = [dict(text=s['text'], sources=ctx.sources(s['sources'], 'estructura')) for s in seed['structure_sources']]
    return dict(numerals=num_out, signs=sign_out, trecenas=trecenas, veintenas=veintenas, structure=structure,
                days=dict(sorted(day_data.items(), key=lambda x: x[1]['index'])), tlachia_days=days,
                check=dict(pages_with_days=len(page_trecena), day_glyphs=len(days),
                           note='El orden de los 20 signos se comprobó con las secuencias de días de cada lámina: todas forman una sola trecena.'))


# ---------------------------------------------------------------------------
# Lecturas de mitología (receta de lesson_builder) y unidad del calendario
# ---------------------------------------------------------------------------
def used_passages():
    used = {e['archive_id'] for l in json.loads(LEARNING.read_text())['lessons'] for e in l['examples']}
    if UNITS_RECIPE.exists():
        used |= {e['archive_id'] for l in json.loads(UNITS_RECIPE.read_text())['lessons'] for e in l['examples']}
    return used


def build_readings(ctx, entities):
    records = ctx.records
    forms = defaultdict(list)
    for r in records.values():
        if r['kind'] == 'form' and r.get('sense_id') in records:
            forms[fold(r['written'])].append(r)
    used, taken, lessons = used_passages(), set(), []
    name_keys = {phrase_key(n): e for e in entities if e['searchable'] for n in e['names']}
    for spec in ctx.seed['readings']['lessons']:
        where = spec['id']
        glyphs = sorted((r for r in records.values() if r['kind'] == 'glyph' and r.get('sense_id') == spec['cover_sense']),
                        key=lambda g: (not g.get('image'), g['id']))
        if not glyphs or spec['cover_sense'] not in spec['sense_ids']:
            raise ValueError(f'{where}: la portada necesita un glifo de una acepción de la lectura')
        examples = []
        for x in spec['examples']:
            rid = x['archive_id']
            row = ctx.rows.get(rid)
            if not row or row['iso'] != 'nci' or ctx.restricted(rid) or rid in used or rid in taken:
                raise ValueError(f'{where}: {rid} no es un pasaje clásico libre (ya usado, restringido o inexistente)')
            taken.add(rid)
            if whole(x['blank'], row['nah']) < 0:
                raise ValueError(f'{where}: «{x["blank"]}» no está como palabra en {rid}')

            def sense_of(word):
                cands = [f for f in forms.get(fold(word), []) if f['written'].casefold() == word.casefold()]
                cands.sort(key=lambda f: (f['sense_id'] not in spec['sense_ids'], f['sense_id'].startswith('sense-gdn'), f['id']))
                return cands[0]['sense_id'] if cands else None
            blank_sense = sense_of(x['blank'])
            if not blank_sense or any(not forms.get(fold(d)) for d in x['distractors']):
                raise ValueError(f'{where}: el hueco y sus distractores necesitan formas del diccionario')
            if any(bounded(d, row['nah']) for d in x['distractors']):
                raise ValueError(f'{where}: un distractor aparece en {rid}')
            label = records[blank_sense].get('label', '').split(' / ')[0].rstrip('.')
            annotations = [dict(quote=x['blank'], relation='full_word', sense_id=blank_sense,
                                note=f'Palabra completa registrada en el diccionario: {x["blank"]} «{label}». Ayuda generada; pendiente de revisión.')]
            named = []
            for w, k in ctx.toks(rid):
                e = name_keys.get(k)
                if e and e['name'] not in named:
                    named.append(e['name'])
                    s = sense_of(w)
                    if s and w != x['blank'] and not any(a['quote'] == w for a in annotations):
                        annotations.append(dict(quote=w, relation='full_word', sense_id=s,
                                                note=f'{e["kind_label"]}: {e["name"]}. Ficha en Dioses y calendario. Ayuda generada; pendiente de revisión.'))
            annotations.sort(key=lambda a: whole(a['quote'], row['nah']))  # Learning las lee en el orden del texto
            if not bounded(x['answer'], row['es']) or any(bounded(w, row['es']) for w in x['wrong']):
                raise ValueError(f'{where}: la respuesta de comprensión de {rid} no sale de la traducción')
            options = stable([x['answer']] + x['wrong'], rid + ':myth')
            examples.append(dict(archive_id=rid,
                                 context=f'Pasaje de {row["document"]}' + (f' que nombra a {", ".join(named)}' if named else '')
                                         + '. Selección del proyecto para esta lectura; contexto pendiente de revisión.',
                                 annotations=annotations, cloze=dict(blank=x['blank'], distractors=x['distractors']),
                                 comprehension=dict(kind='meaning', question=x['question'], options=options, answer=options.index(x['answer']),
                                                    explanation=f'La traducción del archivo dice «{x["answer"]}». Comprobación automática; la interpretación está pendiente de revisión.'),
                                 explore_words=[x['blank']]))
        lessons.append(dict(id=spec['id'], title=spec['title'], objective=spec['objective'], minutes=spec['minutes'],
                            sense_ids=spec['sense_ids'], cover_glyph=glyphs[0]['id'], reading_tips=spec['reading_tips'], examples=examples))
    return dict(schema_version=1, release_id=READINGS_ID, review_status='editorial_draft',
                generated_by=dict(module='nahuatl_local.entities', version=GENERATOR_VERSION, llm_calls=0, network_requests=0),
                note='Receta de lecturas de mitología: pasajes elegidos por el proyecto, ayudas por plantilla. Solo se publica tras revisión.',
                lessons=lessons, lesson_updates=[])


def build_unit(ctx, calendar):
    """Unidad «Los nombres del calendario»: numerales 1-13 y signos, con evidencia de Tlachia y del archivo."""
    seed = ctx.seed
    numerals, signs = calendar_tables(seed)
    names = {n['n']: n['name'] for n in seed['numerals']}
    sign_names = [s['name'] for s in seed['signs']]
    glosses = [s['es'] for s in seed['signs']]
    days = calendar['tlachia_days']

    def tl(n, s):
        d = next(d for d in days if d['n'] == n and d['sign'] == s)
        return dict(source='tlachia', id=d['id'], form=d['reading'], segmentation=f'{names[n]} + {sign_names[s]}',
                    support=f'{n} + {glosses[s]}', folio=d['folio'], url=d['url'])

    def ev_passage(rid, form, n, s):
        row = ctx.rows[rid]
        return dict(source='passage', archive_id=rid, form=form, segmentation=f'{names[n]} + {sign_names[s]}', support=str(n),
                    source_hash=passage_hash(row))
    sign_ix = {s: i for i, s in enumerate(sign_names)}
    ex = []

    def add(kind, **f):
        ex.append(dict(id=f'calendario-{len(ex) + 1}', kind=kind, **f))
    add('match', prompt='Une cada numeral con su número.', pairs=[dict(form=names[n], gloss=str(n)) for n in (1, 2, 3, 4)],
        evidence=[tl(1, sign_ix['tochtli']), tl(2, sign_ix['atl']), tl(3, sign_ix['itzcuintli']), tl(4, sign_ix['ozomatli'])],
        explanation='En las láminas del Telleriano-Remensis cada día lleva su numeral: ce tochtli, ome atl, yei itzcuintli, nahui ozomatli (lecturas de Tlachia).')
    add('match', prompt='Une cada signo con lo que nombra.', pairs=[dict(form=sign_names[i], gloss=glosses[i]) for i in range(4)],
        evidence=[tl(7, 0), tl(8, 1), tl(9, 2), tl(10, 3)],
        explanation='Glosas de los elementos de Tlachia y de Wiktionary; los cuatro primeros signos del tonalpohualli.')
    add('identify', prompt='En «chicuace xochitl», ¿qué número dice chicuace?', form='chicuace xochitl',
        options=stable(['6', '7', '5'], 'cal-6'), answer=None, evidence=[tl(6, 19)],
        explanation='chicuace es 6: el día 6 Flor de la lámina f. 26r.')
    add('identify', prompt='En «matlactli omome miquiztli», ¿qué signo es miquiztli?', form='matlactli omome miquiztli',
        options=stable(['muerte', 'venado', 'lluvia'], 'cal-miq'), answer=None, evidence=[tl(12, 5)],
        explanation='miquiztli es «muerte» (Wiktionary); matlactli omome es 12.')
    tiles = stable(['matlactli', 'omei', 'mazatl', 'omome'], 'cal-build')
    add('build', prompt='Arma el nombre del día 13 Venado.', gloss='13 + venado', tiles=tiles,
        answer=[tiles.index('matlactli'), tiles.index('omei'), tiles.index('mazatl')], form='matlactli omei mazatl',
        evidence=[tl(13, 6)], explanation='Trece es matlactli omei («diez y tres»); el signo va al final: matlactli omei mazatl (f. 26r).')
    add('cloze', prompt='Completa el nombre del día. La traducción del archivo te orienta.', archive_id='axolotl-16027', blank='Ce',
        options=stable(['Ce', 'Ome', 'Nahui'], 'cal-cloze'), answer=None,
        evidence=[ev_passage('axolotl-16027', 'Ce Coatl', 1, 4)],
        explanation='La traducción dice «1-Serpiente»: ce coatl. Ome sería 2 y nahui, 4.')
    add('translate', prompt='¿Qué dice este pasaje?', archive_id='axolotl-10620',
        option_ids=stable(['axolotl-10620', 'axolotl-12752', 'axolotl-01039'], 'cal-tr'), answer=None,
        evidence=[ev_passage('axolotl-10620', 'Chicuey Ecatl', 8, 1)],
        explanation='Chicuey Ecatl es el día 8 Viento; quecholli es la veintena en que llegaron.')
    add('identify', prompt='¿Qué día sigue a ce cipactli?', form='ce cipactli',
        options=stable(['ome ehecatl', 'ome calli', 'ce ehecatl'], 'cal-next'), answer=None,
        evidence=[tl(7, 0), tl(8, 1)],
        explanation='Número y signo avanzan juntos: tras 1 Caimán viene 2 Viento, como en la lámina (7 cipactli, 8 ehecatl).')
    # Claves derivadas de las tablas, no escritas a mano.
    for e in ex:
        if e['kind'] == 'identify':
            if e['id'].endswith('-8'):
                right = 'ome ehecatl'
            else:
                n, s, _ = parse_calendar_name(tokens(e['form']), 0, numerals, signs)
                right = str(n) if 'número' in e['prompt'] else glosses[s]
            e['answer'] = e['options'].index(right)
        elif e['kind'] == 'cloze':
            e['answer'] = e['options'].index(e['blank'])
        elif e['kind'] == 'translate':
            e['answer'] = e['option_ids'].index(e['archive_id'])
    closing_id = 'axolotl-01039'
    unit = dict(id='calendario', edition_id='calendario-v1', version=1, practice_version=1, title='Los nombres del calendario: numerales y signos',
                objective='Leer un nombre del tonalpohualli: un numeral del 1 al 13 y uno de los 20 signos.',
                minutes=10, review_status='automatic_draft',
                rule=dict(summary='Cada día del tonalpohualli tiene un nombre de dos partes: un numeral del 1 al 13 y un signo de los 20. '
                                  'Ambos avanzan juntos: 1 Caimán, 2 Viento, 3 Casa… Después de 13 el numeral vuelve a 1 y empieza otra trecena.',
                          points=['Del 11 al 13 se suma al diez: matlactli once (u oce), matlactli omome, matlactli omei.',
                                  'Los años también llevan nombre calendárico: Ce Acatl xihuitl, «el año 1 Caña».',
                                  'Las grafías cambian: chicuei / chicuey, chiucnahui / chicnahui, cohuatl / coatl.'],
                          morphemes=[dict(surfaces=n['spellings'][:3], gloss=str(n['n'])) for n in seed['numerals']]),
                sense_ids=[], words=[], exercises=ex,
                closing=dict(archive_id=closing_id, forms=[dict(form='Ce Hecatl', segmentation='ce + ehecatl', gloss='1 + viento'),
                                                           dict(form='quecholli', segmentation='veintena', gloss='nombre de la veintena')],
                             evidence=[ev_passage(closing_id, 'Ce Hecatl', 1, 1)]))
    problems = check_unit(ctx, unit)
    if problems:
        raise ValueError('Unidad del calendario sin respaldo: ' + '; '.join(problems))
    return unit


def check_unit(ctx, unit):
    """Problemas de la unidad del calendario: cada clave sale de las tablas, de Tlachia o del pasaje."""
    numerals, signs = calendar_tables(ctx.seed)
    values = {n['name']: n['n'] for n in ctx.seed['numerals']}
    glosses = {s['name']: s['es'] for s in ctx.seed['signs']}
    occ = {o['id']: o for o in ctx.occurrences}
    problems = []
    for e in unit['exercises']:
        for ev in e['evidence']:
            if ev['source'] == 'tlachia':
                if ev['id'] not in occ or fold(occ[ev['id']]['reading']) != fold(ev['form']):
                    problems.append(f'{e["id"]}: lectura de Tlachia {ev["id"]} cambió')
            else:
                row = ctx.rows.get(ev['archive_id'])
                if not row or passage_hash(row) != ev['source_hash'] or ev['form'] not in row['nah'] or ctx.restricted(row['id']):
                    problems.append(f'{e["id"]}: pasaje {ev["archive_id"]} cambió o no respalda «{ev["form"]}»')
                elif re.search(r'(?<!\d)' + ev['support'] + r'(?!\d)', row['es']) is None:
                    problems.append(f'{e["id"]}: la traducción de {ev["archive_id"]} no da el número {ev["support"]}')
        if e['kind'] == 'match':
            for p in e['pairs']:
                if p['gloss'] != (str(values[p['form']]) if p['form'] in values else glosses.get(p['form'])):
                    problems.append(f'{e["id"]}: la pareja {p["form"]} no sale de las tablas')
        elif e['kind'] == 'build':
            pieces = [e['tiles'][i] for i in e['answer']]
            hit = parse_calendar_name(tokens(' '.join(pieces)), 0, numerals, signs)
            if ' '.join(pieces) != e['form'] or not hit or e['gloss'] != f'{hit[0]} + {ctx.seed["signs"][hit[1]]["es"]}':
                problems.append(f'{e["id"]}: las fichas no arman el día pedido')
        elif e['kind'] == 'cloze':
            row = ctx.rows[e['archive_id']]
            if len(re.findall(r'(?<![\w])' + re.escape(e['blank']) + r'(?![\w])', row['nah'])) != 1 or e['options'][e['answer']] != e['blank'] \
                    or len({fold(o) for o in e['options']}) != len(e['options']) or not all(phrase_key(o) in numerals for o in e['options']):
                problems.append(f'{e["id"]}: el hueco debe ser un numeral único del pasaje')
        elif e['kind'] == 'translate':
            rows = [ctx.rows.get(i) for i in e['option_ids']]
            if any(r is None or r['iso'] != 'nci' for r in rows) or e['option_ids'][e['answer']] != e['archive_id'] or len({r['es'] for r in rows}) != 3:
                problems.append(f'{e["id"]}: la respuesta debe ser la traducción del pasaje')
        elif e['kind'] == 'identify' and len(set(e['options'])) != len(e['options']):
            problems.append(f'{e["id"]}: opciones repetidas')
    if {e['kind'] for e in unit['exercises']} != {'match', 'identify', 'build', 'cloze', 'translate'}:
        problems.append('faltan tipos de ejercicio')
    return problems


# ---------------------------------------------------------------------------
# Cola, informe y generación
# ---------------------------------------------------------------------------
def findings(data, recipe):
    out = []

    def issue(fid, lesson_id, title, evidence, acceptance):
        f = dict(id=fid, priority='P1', lesson_id=lesson_id, title=title, evidence=evidence, acceptance=acceptance)
        f['fingerprint'] = fingerprint(f)
        out.append(f)
    seed = json.loads(SEED.read_text())
    issue('entities-seed-review', 'entidades', 'Revisar las fichas de dioses y calendario',
          dict(entities=seed['entities'], veintenas=seed['veintenas'], signs=seed['signs'], numerals=seed['numerals']),
          'Cotejar cada atributo, relación, glosa y posición con su fuente citada; confirmar las grafías reunidas y las '
          'figuras de Tlachia; resolver las veintenas sin fuente para el nombre (teotleco, nemontemi). Registrar revisor, '
          'fecha, evidencia y resolución con esta huella.')
    issue('unit-calendario-review', 'calendario', f'Revisar la unidad generada «{data["unit"]["title"]}»', data['unit'],
          'Cotejar las lecturas de Tlachia y los pasajes, la regla, las claves y los distractores. Registrar revisor, fecha, '
          'evidencia y resolución con esta huella. La validación automática no sustituye esta revisión.')
    for lesson in recipe['lessons']:
        issue(f'myth-reading-{lesson["id"]}-review', lesson['id'], f'Revisar la lectura de mitología «{lesson["title"]}»', lesson,
              'Cotejar los cuatro pasajes con su edición, las ayudas, el hueco, sus distractores y la comprensión. Si se acepta, '
              'publicarla con lesson_builder --apply sobre la propuesta; no editar el archivo generado a mano.')
    return out


def coverage(data, recipe):
    ents = data['entities']
    cal = data['calendar']
    return dict(schema_version=1, generator=GENERATOR_VERSION, llm_calls=0, network_requests=0,
                entities={k: sum(e['kind'] == k for e in ents) for k in KIND_LABELS},
                with_passages=sum(e['passages']['total'] > 0 for e in ents), with_tlachia=sum(bool(e['tlachia']) for e in ents),
                spellings={e['id']: [s['form'] for s in e['spellings']] for e in ents if len(e['spellings']) > 1},
                calendar=dict(signs=len(cal['signs']), numerals=len(cal['numerals']), trecenas=len(cal['trecenas']),
                              trecenas_with_tlachia=sum(bool(t['pages']) for t in cal['trecenas']),
                              veintenas=sum(v['kind'] == 'veintena' for v in cal['veintenas']),
                              veintenas_name_pending=[v['name'] for v in cal['veintenas'] if v['name_pending']],
                              days_with_data=len(cal['days']), day_glyphs=len(cal['tlachia_days'])),
                search_keys=len(data['search']), readings=[l['id'] for l in recipe['lessons']],
                unit=dict(id=data['unit']['id'], exercises=len(data['unit']['exercises'])))


def generate(terms=None, write=True):
    from .lesson_builder import build as build_proposal
    from .lexicon import load_records
    from .terms import TermIndex
    records = load_records()
    ctx = Context(records, terms or TermIndex())
    entities, index = build_entities(ctx)
    calendar = build_calendar(ctx, entities, index)
    unit = build_unit(ctx, calendar)
    recipe = build_readings(ctx, entities)
    data = dict(schema_version=1, id='entidades-v1', review_status='automatic_draft', note=DRAFT,
                generated_by=dict(module='nahuatl_local.entities', version=GENERATOR_VERSION, seed=str(SEED.relative_to(ROOT)),
                                  seed_sha256=sha(SEED.read_bytes()), llm_calls=0, network_requests=0),
                attribution=dict(tlachia=TLACHIA, axolotl=AXOLOTL, tlachia_rights=ctx.tlachia_rights,
                                 restricted=ctx.restricted_docs, wiktionary='Wiktionary, CC BY-SA 4.0: atribución y misma licencia por dato.'),
                entities=entities, calendar=calendar, unit=unit,
                search=dict(sorted(index.items())))
    queue = dict(schema_version=1, decisions=str(DECISIONS.relative_to(ROOT)),
                 tasks=merge_decisions(findings(data, recipe), json.loads(DECISIONS.read_text())['decisions'] if DECISIONS.exists() else {}))
    files = {ENTITIES: encode(data), RECIPE: encode(recipe), QUEUE: encode(queue), COVERAGE: encode(coverage(data, recipe))}
    with tempfile.TemporaryDirectory() as directory:
        tmp = Path(directory) / 'recipe.json'
        tmp.write_bytes(files[RECIPE])
        staging = ROOT / 'editorial' / f'.{READINGS_ID}-{sha(files[RECIPE])[:12]}.json'
        try:
            build_proposal(tmp, staging)
            proof = json.loads(staging.read_text())
        finally:
            staging.unlink(missing_ok=True)
    proof['config_sha256'] = sha(files[RECIPE])
    files[PROPOSAL] = encode(proof)
    if write:
        for path, raw in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
    return files, json.loads(files[COVERAGE])


# ---------------------------------------------------------------------------
# Servicio
# ---------------------------------------------------------------------------
class Entities:
    """Fichas servidas: catálogo ligero, ficha completa con pasajes, búsqueda por grafía y unidad."""

    def __init__(self, path=ENTITIES, recipe=RECIPE, decisions=DECISIONS):
        self.path, self.recipe, self.decisions = Path(path), Path(recipe), Path(decisions)
        self._lock = Lock()
        self._data = None
        self._rows = None

    def data(self):
        with self._lock:
            if self._data is None:
                data = json.loads(self.path.read_text())
                if data.get('schema_version') != 1:
                    raise ValueError('Fichas de entidades inválidas.')
                self._data = data
                self._by_id = {e['id']: e for e in data['entities']}
                cal = data['calendar']
                for group in ('numerals', 'signs', 'trecenas', 'veintenas'):
                    self._by_id.update({x['id']: dict(x, kind=x.get('kind', group[:-1])) for x in cal[group]})
            return self._data

    def rows(self):
        if self._rows is None:
            self._rows = {r['id']: r for r in passage_store.load()}
        return self._rows

    def review(self):
        data = self.data()
        recipe = json.loads(self.recipe.read_text())
        return review_state(findings(data, recipe), self.decisions), recipe

    def catalog(self):
        data = self.data()
        state, recipe = self.review()
        light = lambda e: dict(id=e['id'], kind=e['kind'], kind_label=e['kind_label'], name=e['name'],
                               spellings=[s['form'] for s in e['spellings'][:6]], passages=e['passages']['total'],
                               tlachia=len(e['tlachia']), image=next((t['image'] for t in e['tlachia'] if t['role'] == 'figure' and t.get('image')), None),
                               summary=(e['attributes'][0]['text'] if e['attributes'] else (e['senses'][0]['gloss'] if e['senses'] else '')))
        cal = data['calendar']
        rows = self.rows()
        readings = [dict(id=l['id'], title=l['title'], objective=l['objective'], review=state[l['id']],
                         passages=[rows[x['archive_id']] for x in l['examples']]) for l in recipe['lessons']]
        return dict(id=data['id'], note=data['note'], generated_by=data['generated_by'], attribution=data['attribution'],
                    review=state['entidades'], entities=[light(e) for e in data['entities']],
                    calendar=dict(numerals=cal['numerals'], signs=[{k: v for k, v in s.items() if k != 'glyphs'} | dict(glyph=(s['glyphs'] or [None])[0])
                                                                   for s in cal['signs']],
                                  trecenas=cal['trecenas'], veintenas=[{k: v for k, v in x.items() if k != 'passages'} | dict(passages=x['passages']['certain_total'])
                                                                       for x in cal['veintenas']],
                                  structure=cal['structure'], days=cal['days'], check=cal['check']),
                    readings=readings, unit=dict(id=data['unit']['id'], title=data['unit']['title'], objective=data['unit']['objective'],
                                                 review=state['calendario']))

    def get(self, eid):
        self.data()
        item = self._by_id.get(eid)
        if not item:
            raise KeyError(eid)
        out = copy.deepcopy(item)
        rows = self.rows()
        hydrate = lambda ids: [dict(rows[x['id']], form=x.get('form')) for x in ids if x['id'] in rows]
        if 'passages' in out and isinstance(out['passages'], dict) and 'sample' in out['passages']:
            out['passages']['rows'] = hydrate(out['passages']['sample'])
        if out.get('kind') in ('veintena', 'nemontemi'):
            out['passages']['certain_rows'] = hydrate(out['passages']['certain'])
            out['passages']['uncertain_rows'] = hydrate(out['passages']['uncertain'])
        if out.get('id', '').startswith('signo-'):
            sign = out['n'] - 1
            days = self._data['calendar']['days']
            out['days'] = [d for d in days.values() if d['sign'] == sign]
            for d in out['days']:
                d['rows'] = hydrate(d['passages'][:2])
        state, _ = self.review()
        out['review'] = state['entidades']
        return out

    def day(self, n, sign):
        if not (1 <= n <= 13 and 0 <= sign <= 19):
            raise KeyError(f'{n}-{sign}')
        data = self.data()
        d = copy.deepcopy(data['calendar']['days'].get(f'{n}-{sign}') or dict(n=n, sign=sign, passages=[], glyphs=[], passages_total=0))
        d.update(trecena=trecena_of(n, sign), index=day_index(n, sign))
        rows = self.rows()
        d['rows'] = [dict(rows[x['id']], text=x['text'], year=x['year'], certain=x['certain']) for x in d['passages'] if x['id'] in rows]
        tl = {t['id']: t for t in data['calendar']['tlachia_days']}
        d['glyph_rows'] = [tl[g] for g in d['glyphs'] if g in tl]
        return d

    def search(self, query):
        if not isinstance(query, str) or not query.strip() or len(query) > 120:
            raise ValueError('Escribe un nombre o una fecha breve (hasta 120 caracteres).')
        data = self.data()
        key = phrase_key(query)
        matches = []
        hit = data['search'].get(key)
        if hit:
            e = self._by_id[hit['id']]
            matches.append(dict(id=hit['id'], kind=hit['kind'], name=e['name'], why='misma grafía o grafía variante'))
        numerals, signs = calendar_tables(dict(numerals=data['calendar']['numerals'], signs=data['calendar']['signs']))
        toks = tokens(query)
        day = parse_calendar_name(toks, 0, numerals, signs) if toks else None
        if day and day[2] == len(toks):
            matches.append(dict(id=f'dia/{day[0]}-{day[1]}', kind='day', name=f'{day[0]} {data["calendar"]["signs"][day[1]]["name"]}',
                                why='nombre calendárico: numeral + signo'))
        return dict(query=query.strip(), key=key, matches=matches)

    def unit(self):
        data = self.data()
        state, _ = self.review()
        unit = copy.deepcopy(data['unit'])
        unit['review'] = state['calendario']
        rows = self.rows()
        ids = {unit['closing']['archive_id']} | {i for e in unit['exercises'] for i in [e.get('archive_id')] + e.get('option_ids', []) if i}
        unit['passages'] = {i: rows[i] for i in sorted(ids)}
        return dict(id=unit['edition_id'], units=[unit])


def routes(router, service=None):
    """Rutas de la sección: catálogo, ficha, búsqueda por grafía, día del tonalpohualli y unidad."""
    from .community import Problem
    service = service or Entities()

    def card(request):
        try:
            return request.reply(service.get(request.tail))
        except KeyError:
            raise Problem('Ficha no encontrada.', 404) from None

    def search(request):
        try:
            return request.reply(service.search(request.arg('q')))
        except ValueError as error:
            raise Problem(str(error)) from None

    def day(request):
        try:
            return request.reply(service.day(int(request.arg('n')), int(request.arg('sign'))))
        except (KeyError, ValueError):
            raise Problem('Día inválido: n va de 1 a 13 y sign de 0 a 19.') from None
    router.add('GET', '/api/entities', lambda r: r.reply(service.catalog()))
    router.add('GET', '/api/entities/', card, prefix=True)
    router.add('GET', '/api/entity-search', search)
    router.add('GET', '/api/calendar/day', day)
    router.add('GET', '/api/calendar/unit', lambda r: r.reply(service.unit()))
    return service


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--check', action='store_true', help='Falla si algún archivo generado no coincide con una generación nueva.')
    args = parser.parse_args(argv)
    files, cov = generate(write=not args.check)
    if args.check:
        stale = [str(p.relative_to(ROOT)) for p, raw in files.items() if not p.exists() or p.read_bytes() != raw]
        if stale:
            print('Generación desactualizada: ' + ', '.join(stale) + '. Ejecuta python3 -m nahuatl_local.entities', file=sys.stderr)
            return 1
    print(json.dumps(dict(entities=cov['entities'], calendar=cov['calendar'], readings=cov['readings']), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
