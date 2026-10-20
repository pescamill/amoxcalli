"""Preguntar por tema: lecturas, fichas, unidades, notas y obras relacionadas con una frase.

Preguntar respondía una sola palabra. Este módulo acepta frases y preguntas («¿qué dice sobre
el calendario?», «dioses de la lluvia», «¿quién fue Quetzalcóatl?») y busca en todo el contenido
del proyecto, no solo en el diccionario:

* lecturas publicadas y propuestas en revisión (título, objetivo, claves, contexto, pasajes);
* unidades de gramática y notas de Carochi (1645);
* fichas de dioses, figuras y lugares; signos, veintenas y la estructura del calendario;
* obras del archivo («libros») y sus pasajes, y el diccionario.

Cómo ordena (sin modelo): BM25 sobre el español plegado (``text.fold`` + ``text.es_key``) y sobre
las palabras nahuas por clave laxa (``text.loose_key``), de modo que *Quetzalcóatl* encuentra
*Quetzalcohuatl*. La consulta se amplía con las raíces que el corpus paralelo asocia a cada palabra
española (pistas IBM‑1 del índice de términos): *lluvia* suma los pasajes con su raíz. Palabras de
intención (*dioses*, *calendario*, *lecturas*, *gramática*, *libro*) dan prioridad a ese tipo de
contenido. Un resultado debe contener la mayor parte de la consulta; si nada lo hace, se abstiene.
Cada resultado dice por qué aparece y enlaza a su lugar en la aplicación.
"""
import functools
import json
import math
import re
from collections import Counter, defaultdict
from threading import Lock

from . import passages
from .passages import LABELS
from .stems import ES_STOP, ROOT, es_tokens
from .text import es_key, fold, loose_key

TOPIC_VERSION = 'topics-v1'
MAX_QUERY = 300
WORD = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*", re.U)

# Palabras que solo expresan la pregunta: no se buscan, pero algunas indican el tipo de contenido.
QUESTION = {es_key(w) for w in '''que quien quienes como cual cuales donde cuando cuanto sobre acerca dice dicen decir
habla hablan hablar fue fueron era eran son hay tema temas informacion saber quiero busco buscar busca encuentra encontrar
mostrar muestra muestrame ensename explica explicame significa significado relacionado relacionada relacionados algo algun
alguna puedo puede lectura lecturas leer libro libros obra obras texto textos fuente fuentes ficha fichas pasaje pasajes'''.split()}
INTENTS = {
    'entity': {es_key(w) for w in 'dios dioses diosa diosas deidad deidades divinidad numen mitologia mito mitos'.split()},
    'calendar': {es_key(w) for w in 'calendario calendarios dia dias signo signos trecena trecenas veintena veintenas tonalpohualli xiuhpohualli fiesta fiestas mes meses ano anos'.split()},
    'lesson': {es_key(w) for w in 'lectura lecturas leer relato relatos'.split()},
    'grammar': {es_key(w) for w in 'gramatica prefijo prefijos sufijo sufijos plural plurales sustantivo sustantivos verbo verbos'.split()},
    'work': {es_key(w) for w in 'libro libros obra obras codice codices fuente fuentes anales'.split()},
}
INTENT_KINDS = {'entity': {'entity'}, 'calendar': {'calendar', 'calendar-unit', 'sign', 'veintena'},
                'lesson': {'lesson', 'lesson-draft'}, 'grammar': {'unit', 'note'}, 'work': {'work'}}
# Contenido curado y redactado con fuentes primero; pasajes y diccionario después (son muchos).
PRIOR = {'lesson': 1.6, 'lesson-draft': 1.35, 'entity': 1.6, 'calendar': 1.6, 'calendar-unit': 1.4, 'sign': 1.25,
         'veintena': 1.25, 'unit': 1.45, 'note': 1.45, 'work': 1.3, 'sense': 0.85, 'passage': 0.75}
KIND_LABEL = {'lesson': 'Lectura', 'lesson-draft': 'Lectura propuesta (en revisión)', 'entity': 'Ficha',
              'calendar': 'Calendario', 'calendar-unit': 'Unidad del calendario (borrador)', 'sign': 'Signo del calendario',
              'veintena': 'Veintena', 'unit': 'Unidad de gramática (borrador)', 'note': 'Nota de gramática (Carochi, 1645)',
              'work': 'Obra del archivo', 'sense': 'Entrada del diccionario', 'passage': 'Pasaje'}
GROUPS = (('lessons', 'Lecturas', ('lesson', 'lesson-draft')),
          ('entities', 'Dioses, lugares y calendario', ('entity', 'calendar', 'calendar-unit', 'sign', 'veintena')),
          ('grammar', 'Gramática', ('unit', 'note')),
          ('works', 'Obras del archivo', ('work',)),
          ('passages', 'Pasajes', ('passage',)),
          ('senses', 'Diccionario', ('sense',)))
KIND_WORDS = {'deity': 'dios diosa deidad', 'place': 'lugar', 'figure': 'figura', 'epithet': 'nombre epíteto'}
TITLE_BONUS = 1.5
K1, B = 1.2, 0.75
EXPANSION_WEIGHT = 0.6


def _strings(value):
    """Textos de un objeto anidado (para reunir campos redactados)."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from _strings(v)
    elif isinstance(value, (list, tuple)):
        for v in value:
            yield from _strings(v)


def _read(path):
    return json.loads(path.read_text(encoding='utf-8')) if path.is_file() else None


@functools.lru_cache(maxsize=200_000)
def _loose(word):
    return loose_key(word)


def _clip(text, terms, limit=220):
    """La frase del texto que contiene más términos de la consulta, recortada."""
    text = re.sub(r'\s+', ' ', text or '').strip()
    if not text:
        return ''
    sentences = re.split(r'(?<=[.;:!?])\s+', text)
    def hits(s):
        keys = {k for k, _ in es_tokens(s)} | {'n:' + _loose(w) for w in WORD.findall(s)}
        return len(keys & terms)
    best = max(sentences, key=hits)
    return best if len(best) <= limit else best[:limit].rsplit(' ', 1)[0] + '…'


class Doc:
    __slots__ = ('id', 'kind', 'title', 'href', 'body', 'review', 'cites', 'tf', 'length', 'meta', 'title_keys')

    def __init__(self, id, kind, title, body, href=None, review=None, cites=(), nah=(), title_nah=(), meta=None):
        self.id, self.kind, self.title, self.href, self.review = id, kind, title, href, review
        self.body, self.cites, self.meta = body, list(cites), meta or {}
        tf = Counter()
        for k, _ in es_tokens(title):
            tf[k] += 3
        for w in title_nah:
            tf['n:' + loose_key(w)] += 3
        for k, _ in es_tokens(body):
            tf[k] += 1
        for w in nah:
            tf['n:' + loose_key(w)] += 1
        self.tf, self.length = tf, sum(tf.values()) or 1
        self.title_keys = {k for k, _ in es_tokens(title)} | {'n:' + loose_key(w) for w in title_nah}


class TopicIndex:
    """Índice de temas sobre el contenido del proyecto, construido una vez."""

    def __init__(self, terms=None, root=ROOT):
        self.terms, self.root = terms, root
        self._lock, self._ready = Lock(), False

    # -- construcción -------------------------------------------------------------
    def _build(self):
        with self._lock:
            if self._ready:
                return
            docs = []
            rows = {r['id']: r for r in passages.load(self.root)}
            self.rows = rows
            docs += self._lessons(rows)
            docs += self._entities(rows)
            docs += self._grammar()
            docs += self._works(rows)
            docs += self._senses()
            for rid, r in rows.items():
                docs.append(Doc(rid, 'passage', '', r['es'], href='#preguntar/' + rid, cites=[rid],
                                nah=WORD.findall(r['nah']), meta=dict(document=r['document'], iso=r['iso'], nah=r['nah'])))
            self.docs = docs
            self.by_id = {d.id: d for d in docs}
            self.pos = {d.id: i for i, d in enumerate(docs)}
            self.df = Counter()
            for d in docs:
                self.df.update(d.tf.keys())
            self.avg = sum(d.length for d in docs) / len(docs)
            self.postings = defaultdict(list)
            for i, d in enumerate(docs):
                for k, n in d.tf.items():
                    self.postings[k].append((i, n))
            self.vocab_es = {k for k in self.df if not k.startswith('n:')}
            self._ready = True

    def _lessons(self, rows):
        out = []
        learning = _read(self.root / 'corpus/learning-v1.json') or {'lessons': []}
        published = {l['id'] for l in learning['lessons']}
        sources = [(l, 'lesson', 'Publicada', f"#aprender/{l['id']}") for l in learning['lessons']]
        for name in ('lecturas-mitologia-001.json', 'lecturas-generadas-001.json'):
            proposal = _read(self.root / 'editorial' / name)
            if not proposal:
                continue
            for l in proposal['learning']['lessons']:
                if l['id'] not in published:
                    href = '#dioses/lecturas' if l['id'].startswith('mito-') else None
                    sources.append((l, 'lesson-draft', 'Propuesta en revisión, sin publicar', href))
        for l, kind, review, href in sources:
            ids = [e['archive_id'] for e in l['examples'] if e['archive_id'] in rows]
            body = ' '.join([l.get('objective', '')] + list(l.get('reading_tips') or [])
                            + [e.get('context', '') for e in l['examples']]
                            + [a.get('note', '') for e in l['examples'] for a in e.get('annotations', [])]
                            + [rows[i]['es'] for i in ids])
            nah = [w for i in ids for w in WORD.findall(rows[i]['nah'])]
            out.append(Doc(f"{kind}:{l['id']}", kind, l['title'], body, href=href or (f'#preguntar/{ids[0]}' if ids else None),
                           review=review, cites=ids[:3], nah=nah))
        return out

    def _entities(self, rows=None):
        rows = rows or {}
        data = _read(self.root / 'corpus/entities-v1.json')
        if not data:
            return []
        out = []
        for e in data['entities']:
            body = ' '.join([e.get('kind_label') or ''] + [a.get('text', '') for a in e.get('attributes', [])]
                            + [r.get('text', '') for r in e.get('relations', []) if r.get('text')]
                            + [s.get('gloss', '') for s in e.get('senses', [])] + [e.get('note') or ''])
            names = list(e.get('names', [])) + [x['name'] for x in e.get('epithets', [])]
            spellings = [s['form'] for s in e.get('spellings', [])]
            sample = [p['id'] for p in (e.get('passages') or {}).get('sample', []) if p['id'] in rows]
            cites = sample[:3]
            # Tipo de ficha en palabras («dios», «lugar») y el español de sus pasajes de ejemplo, con su fuente.
            context = ' '.join([KIND_WORDS.get(e['kind'], '')] + [rows[i]['es'] for i in sample[:8]])
            out.append(Doc(f"entity:{e['id']}", 'entity', e['name'], body + ' ' + ' '.join(names) + ' ' + context, href=f"#dioses/{e['id']}",
                           review='Borrador con fuentes, sin revisar', cites=cites,
                           nah=spellings + [w for n in names for w in WORD.findall(n)],
                           title_nah=WORD.findall(e['name']), meta=dict(kind_label=e.get('kind_label'))))
        cal = data['calendar']
        signs = cal['signs']
        sign_text = ', '.join(f"{s['name']} ({s.get('es') or ''})" for s in signs)
        out.append(Doc('calendar:tonalpohualli', 'calendar', 'Tonalpohualli: la cuenta de los días',
                       'Calendario adivinatorio de 260 días: veinte signos de los días combinados con trece numerales, '
                       'en veinte trecenas. Signos del día: ' + sign_text + '.', href='#dioses/calendario',
                       nah=['tonalpohualli'] + [s['name'] for s in signs], title_nah=['tonalpohualli']))
        veintenas = cal['veintenas']
        out.append(Doc('calendar:xiuhpohualli', 'calendar', 'Xiuhpohualli: las veintenas del año',
                       'Calendario del año solar: dieciocho veintenas de veinte días y cinco días nemontemi; cada veintena con su fiesta. '
                       'Veintenas: ' + ', '.join(v['name'] for v in veintenas) + '.', href='#dioses/veintenas',
                       nah=['xiuhpohualli'] + [v['name'] for v in veintenas], title_nah=['xiuhpohualli']))
        unit = data.get('unit') or {}
        if unit:
            out.append(Doc(f"calendar-unit:{unit['id']}", 'calendar-unit', unit['title'],
                           (unit.get('objective') or '') + ' calendario tonalpohualli numerales signos días', href='#dioses/unidad',
                           review='Borrador automático, sin revisar'))
        for s in signs:
            ids = [p['id'] for p in (s.get('passages') or {}).get('certain', [])][:3] if isinstance(s.get('passages'), dict) else []
            out.append(Doc(f"sign:{s['id']}", 'sign', f"{s['name']} · {s.get('es') or ''}",
                           f"Signo del día del tonalpohualli: {s.get('es') or ''}.", href=f"#dioses/{s['id']}", cites=ids,
                           nah=s.get('spellings', []), title_nah=[s['name']]))
        for v in veintenas:
            dedication = v.get('dedication') or {}
            text = ' '.join(_strings({k: dedication.get(k) for k in ('text', 'gloss', 'target_name')})) if isinstance(dedication, dict) else ''
            ids = [p['id'] for p in (v.get('passages') or {}).get('certain', [])][:3]
            out.append(Doc(f"veintena:{v['id']}", 'veintena', v['name'],
                           f"Veintena del xiuhpohualli. {v.get('note') or ''} {text}", href=f"#dioses/{v['id']}", cites=ids,
                           nah=v.get('spellings', []), title_nah=[v['name']]))
        return out

    def _grammar(self):
        out = []
        units = _read(self.root / 'corpus/units-v1.json') or {'units': []}
        for u in units['units']:
            body = ' '.join([u.get('objective', '')] + list(_strings((u.get('rule') or {}).get('points', []))))
            out.append(Doc(f"unit:{u['id']}", 'unit', u['title'], body, href=f"#unidades/{u['id']}",
                           review='Borrador automático, sin revisar', nah=list(_strings(u.get('words', [])))[:40]))
        notes = _read(self.root / 'corpus/grammar-notes-carochi-v1.json') or {'notes': []}
        for n in notes['notes']:
            units_of = n.get('units') or []
            out.append(Doc(f"note:{n['id']}", 'note', n['topic'], f"{n.get('summary', '')} {n.get('citation', '')}",
                           href=f"#unidades/{units_of[0]}" if units_of else None, review='Nota redactada por el proyecto con cita de folio',
                           nah=list(_strings(n.get('examples', [])))))
        return out

    def _works(self, rows):
        by_work = defaultdict(list)
        for rid, r in rows.items():
            by_work[r['document'] or ''].append(rid)
        out = []
        for work, ids in by_work.items():
            if not work:
                continue
            variety = Counter(rows[i]['iso'] for i in ids).most_common(1)[0][0]
            out.append(Doc(f"work:{work}", 'work', work, '', href='#investigar/' + work, cites=ids[:1],
                           meta=dict(passages=len(ids), variety=LABELS.get(variety, variety))))
        return out

    def _senses(self):
        if not self.terms:
            return []
        self.terms._build()
        out = []
        for sid, h in self.terms.entries.items():
            out.append(Doc(f"sense:{sid}", 'sense', h['written'] or '', h['label'] or '', href=f'#lexico/{sid}',
                           review='Extracción automática' if h.get('automatic') else None, title_nah=[h['written'] or '']))
        return out

    # -- consulta ---------------------------------------------------------------------
    def parse(self, query):
        if not isinstance(query, str) or not query.strip():
            raise ValueError('Escribe una palabra, una frase o una pregunta.')
        if len(query) > MAX_QUERY:
            raise ValueError(f'Escribe una consulta de hasta {MAX_QUERY} caracteres.')
        words = WORD.findall(query)
        es = []
        for w in words:
            n = fold(w)
            if len(n) < 3 or n in ES_STOP:
                continue
            es.append((es_key(w), w))
        intents = {name for name, keys in INTENTS.items() if any(k in keys for k, _ in es)}
        content = [(k, w) for k, w in es if k not in QUESTION]
        return words, content, intents

    def search(self, query, limit=12):
        self._build()
        words, content, intents = self.parse(query)
        # Cada término de la consulta es un grupo de claves: la española y, si existe, la náhuatl.
        groups = []
        for key, surface in content:
            keys = {key} if key in self.vocab_es else set()
            nk = 'n:' + loose_key(surface)
            if nk in self.df:
                keys.add(nk)
            groups.append((surface, keys))
        if not content and intents:
            # «dioses», «calendario» solos: la intención es el tema.
            groups = [(k, {k}) for name in intents for k in INTENTS[name] if k in self.vocab_es][:1]
        if not groups:
            return self._empty(query, words, intents, 'La consulta no tiene palabras que buscar.')
        scores = defaultdict(float)
        matched = defaultdict(set)
        n = len(self.docs)
        for surface, keys in groups:
            for k in keys:
                idf = math.log(1 + (n - self.df[k] + 0.5) / (self.df[k] + 0.5))
                for i, tf in self.postings.get(k, ()):
                    d = self.docs[i]
                    scores[i] += idf * tf * (K1 + 1) / (tf + K1 * (1 - B + B * d.length / self.avg))
                    if k in d.title_keys:
                        scores[i] += TITLE_BONUS * idf
                    matched[i].add(surface)
        # Ampliación: pasajes con la raíz que el corpus paralelo asocia a una palabra española.
        expansions = []
        if self.terms is not None and getattr(self.terms, '_ready', False):
            for surface, keys in groups:
                for cand in self.terms.es_to_stem.get(es_key(surface), [])[:1]:
                    expansions.append(dict(word=surface, stem=cand['stem_key'], support=cand['support']))
            for ex in expansions:
                for rid, _ in self.terms.concordance.index.get(ex['stem'], [])[:400]:
                    i = self.pos.get(rid)
                    if i is not None:
                        scores[i] += EXPANSION_WEIGHT * 2.0
                        matched[i].add(ex['word'])
        need = len(groups)
        boost = set().union(*(INTENT_KINDS[name] for name in intents)) if intents else set()
        # Una palabra de intención («gramática», «calendario») describe el tipo: el contenido de ese tipo la cubre.
        intent_groups = {surface: set().union(*(INTENT_KINDS[name] for name, keys in INTENTS.items() if es_key(surface) in keys))
                         for surface, _ in groups if any(es_key(surface) in keys for keys in INTENTS.values())}
        if intent_groups and need > 1:
            for i, d in enumerate(self.docs):
                for surface, kinds in intent_groups.items():
                    if d.kind in kinds and i in scores:
                        matched[i].add(surface)
        ranked = []
        for i, s in scores.items():
            d = self.docs[i]
            coverage = len(matched[i]) / need
            if need > 1 and coverage < 0.6:
                continue
            final = s * PRIOR[d.kind] * (1.6 if d.kind in boost else 1.0) * (0.5 + 0.5 * coverage)
            ranked.append((final, i))
        # Obras: además de su título, suman la evidencia de sus pasajes mejor puntuados.
        rank_of = {self.docs[i].id: k for k, (_, i) in enumerate(ranked)}
        work_bonus = defaultdict(list)
        for final, i in ranked:
            d = self.docs[i]
            if d.kind == 'passage':
                work_bonus[d.meta['document']].append(final)
        extra = []
        for work, vals in work_bonus.items():
            d = self.by_id.get('work:' + work)
            if d is None or ('work' not in intents and rank_of.get(d.id) is None):
                continue
            bonus = 0.15 * sum(sorted(vals, reverse=True)[:5])
            idx = rank_of.get(d.id)
            if idx is None:
                extra.append((bonus * PRIOR['work'] * (1.6 if 'work' in boost else 1.0), self.pos[d.id]))
            else:
                ranked[idx] = (ranked[idx][0] + bonus, ranked[idx][1])
        ranked += extra
        ranked.sort(key=lambda x: (-x[0], self.docs[x[1]].id))
        if not ranked:
            return self._empty(query, words, intents, 'Ningún contenido reúne la mayor parte de la consulta.')
        terms = {k for _, keys in groups for k in keys}
        # Solo se arman (con su fragmento) los resultados que se muestran: los primeros y los de cada grupo.
        shown, per_kind = [], Counter()
        caps = {gid: (6 if gid in ('passages', 'senses') else 5) for gid, _, _ in GROUPS}
        group_of = {k: gid for gid, _, kinds in GROUPS for k in kinds}
        for k, (score, i) in enumerate(ranked):
            gid = group_of[self.docs[i].kind]
            if k < limit or per_kind[gid] < caps[gid]:
                shown.append((k, score, i))
                per_kind[gid] += 1
        built = {k: self._item(self.docs[i], score, matched[i], terms) for k, score, i in shown}
        top = [built[k] for k in sorted(built) if k < limit]
        grouped = []
        rank = {it['id']: k for k, it in built.items()}
        for gid, label, kinds in GROUPS:
            rows = [built[k] for k in sorted(built) if built[k]['kind'] in kinds][:caps[gid]]
            if rows:
                grouped.append(dict(id=gid, label=label, items=rows))
        # El grupo con el resultado más pertinente va primero (una ficha antes que las lecturas, si es lo mejor).
        grouped.sort(key=lambda g: rank[g['items'][0]['id']])
        return dict(query=query.strip(), mode='topic', abstained=False, version=TOPIC_VERSION,
                    interpreted=dict(terms=[s for s, _ in groups], intents=sorted(intents), expansions=expansions),
                    top=top, groups=grouped, method=dict(version=TOPIC_VERSION, model_calls=0, network_requests=0),
                    note='Búsqueda por tema sin modelo: coincidencias en lecturas, fichas, notas y pasajes, con la razón de cada una. '
                         'Las lecturas propuestas, las unidades y las fichas son borradores pendientes de revisión.')

    def _item(self, d, score, matched, terms):
        snippet = _clip(d.body or d.title, terms) if d.kind != 'work' else ''
        item = dict(id=d.id, kind=d.kind, label=KIND_LABEL[d.kind], title=d.title or (d.meta.get('nah', '')[:80]),
                    href=d.href, snippet=snippet, why='coincide: ' + ', '.join(sorted(matched)), review=d.review,
                    cites=d.cites, score=round(score, 3))
        if d.kind == 'passage':
            item.update(nah=d.meta['nah'], document=d.meta['document'], variety=LABELS.get(d.meta['iso'], d.meta['iso']),
                        title=d.meta['document'] or 'Pasaje')
        if d.kind == 'work':
            item.update(passages=d.meta['passages'], variety=d.meta['variety'])
        if d.kind == 'entity' and d.meta.get('kind_label'):
            item['label'] = d.meta['kind_label']
        return item

    def _empty(self, query, words, intents, reason):
        return dict(query=query.strip(), mode='topic', abstained=True, reason=reason, version=TOPIC_VERSION,
                    interpreted=dict(terms=[], intents=sorted(intents), expansions=[]), top=[], groups=[],
                    method=dict(version=TOPIC_VERSION, model_calls=0, network_requests=0))
