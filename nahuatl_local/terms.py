"""Índice de términos: cada término reúne todas sus grafías, pasajes y glifos, y una sola búsqueda.

Grupo de término
----------------
Un **grupo** parte de una entrada del catálogo léxico (``lexicon.entries``: acepciones
y formas con la misma clave fonémica) o, si el diccionario no tiene la palabra, de
una grafía del archivo (``term-…``: *cualli*, *cihuatl*). Reúne::

    id, lemma, source               entrada del diccionario o grafía del archivo
    senses                          acepciones (vacío en un grupo del archivo)
    spellings.attested              grafías con la misma clave laxa (colonial, SEP/INALI), por variedad
    spellings.inflected             formas de la misma raíz que el analizador apoya en el diccionario
    spellings.uncertain             misma raíz escrita o palabra que contiene el término, con su motivo:
                                    raíces homógrafas (cualli / tlacualli, coatl / cohua «comprar»),
                                    compuestos y nombres (mixcoatl), raíz sin entrada, raíz breve
    passages                        pasajes por variedad (seguros e inciertos por separado)
    glyphs                          glifos del diccionario y elementos/lecturas de Tlachia, cada
                                    uno con su alcance (``SCOPES``); los inciertos, aparte

Ninguna grafía incierta se cuenta como segura ni lleva al grupo como coincidencia
principal. No se generan imágenes: solo se citan las fichas existentes.

Una sola búsqueda
-----------------
``TermIndex.search`` es la cadena que usan Diccionario, Archivo, Preguntar y Consultar
fichas: normalizar (``parse``: pregunta → palabra; ``text.fold``) → clave laxa
(``text.loose_key``) y raíz del analizador → orden (``SCORES``). Las vistas solo
cambian la presentación.
"""
import re
from collections import Counter, defaultdict
from threading import Lock

from . import lexicon, passages
from .morphology import WORD
from .passages import LABELS
from .pictography import public_catalog
from .stems import ROOT, WordStudy, es_tokens
from .text import es_key, fold, loose_key, readable, squash

TERMS_VERSION = 'terms-v1'
SCOPES = dict(word='Palabra completa', component='Componente', meaning='Relación de significado',
              thematic='Referencia temática')
# Orden de la búsqueda. El idioma detectado va primero (+LANGUAGE); dentro de él, estas puntuaciones.
SCORES = dict(spelling=100, archive=95, label=90, designation=85, inflected=80, hint=70, label_start=60,
              label_word=50, possible=40, root_only=30, definition=20)
LANGUAGE = 200
STRONG = 80          # a partir de aquí el grupo es la respuesta (Archivo filtra por sus grafías)
MIN_STEM = 3         # raíces más breves (atl → a) no reúnen formas flexionadas seguras
MIN_CONTAINED = 5    # clave mínima para buscar el término dentro de otras palabras
UNCERTAIN = dict(other_entry='otra entrada del diccionario tiene esta grafía',
                 verb='forma verbal con la misma raíz escrita (posible homógrafo)',
                 nominalized='derivado con tla-/te-: puede ser otra raíz homógrafa',
                 corpus_root='raíz sin entrada en el diccionario: asociación del corpus',
                 short_root='raíz breve: puede coincidir con otras palabras',
                 bare_root='raíz sin afijos: puede ser otra palabra (cohua «comprar», cal)',
                 contains='contiene el término (compuesto o nombre)')

ES_MIN_SUPPORT = 8   # pistas invertidas español → raíz: solo asociaciones con apoyo amplio
ES_MIN_P = 0.3
ASK_NAH = re.compile(r'^\s*¿?\s*(?:qu[eé]\s+(?:significa|quiere\s+decir)|significado\s+de)\s+(.+?)\s*\??\s*$', re.I)
ASK_ES = re.compile(r'^\s*¿?\s*c[oó]mo\s+se\s+dice\s+(.+?)(?:\s+en\s+n[aá]huatl)?\s*\??\s*$', re.I)
ARTICLE = re.compile(r'^(?:el|la|los|las|un|una)\s+', re.I)
MODERN = re.compile(r'k|w|ts|j')


def parse(query):
    """Normaliza una consulta: (palabra, idioma pedido o None). Una palabra por consulta."""
    if not isinstance(query, str) or not query.strip() or len(query) > 120:
        raise ValueError('Escribe una palabra o una pregunta breve (hasta 120 caracteres).')
    language, text = None, query.strip()
    for pattern, lang in ((ASK_NAH, 'nah'), (ASK_ES, 'es')):
        m = pattern.match(text)
        if m:
            language, text = lang, m.group(1)
            break
    text = ARTICLE.sub('', text.strip(' ¿?¡!.,;:«»"\'')).strip()
    words = WORD.findall(text)
    if len(words) != 1:
        raise ValueError('Consulta una sola palabra, por ejemplo «nocal», «kuali» o «¿cómo se dice mujer?».')
    return words[0], language


def orthography(form):
    """Convención aparente de una grafía: moderna (SEP/INALI: k, w, ts, j) o colonial."""
    return 'moderna' if MODERN.search(fold(form)) else 'colonial'


def glyph_scope(glyph):
    """Alcance de un glifo del diccionario, tal como lo distingue la interfaz.

    Una asociación declarada (``association.type``) manda: relación de significado o
    referencia de la definición o del pasaje (temática). Sin asociación, un elemento
    de compuesto es un componente; la iconografía, temática; lo demás, la palabra."""
    kind = (glyph.get('association') or {}).get('type')
    if kind == 'related_meaning':
        return 'meaning'
    if kind:
        return 'thematic'
    return {'element': 'component', 'iconography': 'thematic'}.get(glyph.get('glyph_type'), 'word')


def _snippet(label, limit=120):
    label = squash(label or '')
    return label if len(label) <= limit else label[:limit].rsplit(' ', 1)[0] + '…'


class TermIndex:
    """Grupos de término y la búsqueda única. Se construye una vez (perezoso)."""

    def __init__(self, word_study=None, root=ROOT, records_fn=None):
        self.word_study = word_study or WordStudy(root, records_fn=records_fn)
        self.root = root
        self.records_fn = records_fn or self.word_study.records_fn
        self._lock = Lock()
        self._ready = False
        self._groups = {}

    # -- construcción ---------------------------------------------------------
    def _build(self):
        with self._lock:
            if self._ready:
                return
            self.analyzer, self.concordance, self.hints = self.word_study._build()
            self.rows = {r['id']: r for r in passages.load(self.root)}
            records = self.records_fn() if self.records_fn else lexicon.load_records(self.root)
            # Archivo: clave laxa → [(pasaje, forma)], una vez por pasaje.
            self.postings = defaultdict(list)
            self.nah_vocab, self.es_vocab = Counter(), Counter()
            cache = {}
            for rid, r in self.rows.items():
                seen = set()
                for m in WORD.finditer(r['nah']):
                    w = m.group(0)
                    lk = cache.get(w.casefold())
                    if lk is None:
                        lk = cache[w.casefold()] = loose_key(w)
                    self.nah_vocab[lk] += 1
                    if lk and lk not in seen:
                        seen.add(lk)
                        self.postings[lk].append((rid, w))
                for key, _ in es_tokens(r['es']):
                    self.es_vocab[key] += 1
            # Diccionario visto por el analizador: una acepción → su forma de consulta.
            self.entries, self.lex_loose = {}, defaultdict(list)
            for bucket in (self.analyzer.lexicon.stems, self.analyzer.lexicon.whole):
                for hits in bucket.values():
                    for h in hits:
                        if h['sense_id'] not in self.entries:
                            self.entries[h['sense_id']] = h
                            self.lex_loose[loose_key(h['written'] or '')].append(h)
            # Pistas invertidas: palabra española → [(raíz, p, apoyo)].
            self.es_to_stem = defaultdict(list)
            for stem, hints in self.hints.table.items():
                for h in hints:
                    if h['support'] >= ES_MIN_SUPPORT and h['p'] >= ES_MIN_P:
                        self.es_to_stem[h['es']].append(dict(stem_key=stem, p=h['p'], support=h['support']))
            for hints in self.es_to_stem.values():
                hints.sort(key=lambda h: (-h['p'] * min(1, h['support'] / 20), h['stem_key']))
            # Grupos del diccionario: entradas del catálogo léxico, con su clave laxa y su raíz.
            self.lexicon = {}
            self.spelling_owner, self.stem_owner = defaultdict(list), defaultdict(list)
            self.label_index, self.label_tokens = defaultdict(set), defaultdict(set)
            sense_group = {}
            for e in lexicon.entries(records):
                keys = sorted({loose_key(s) for s in e['spellings']} - {''})
                if not keys:
                    continue
                stem = None
                for s in e['spellings']:
                    a = self.analyzer.analyze(s, limit=1)
                    if a and a[0]['basis'] == 'dictionary' and any(d['sense_id'] in {x['id'] for x in e['senses']} for d in a[0]['dictionary']):
                        stem = a[0]['stem_key']
                        break
                self.lexicon[e['id']] = dict(entry=e, keys=keys, stem=stem)
                for k in keys:
                    self.spelling_owner[k].append(e['id'])
                if stem:
                    self.stem_owner[stem].append(e['id'])
                for s in e['senses']:
                    sense_group[s['id']] = e['id']
                    for label in [s.get('label', '')] + list(s.get('aliases', [])):
                        if label:
                            self.label_index[es_key(label)].add(e['id'])
                            for i, t in enumerate(re.findall(r'[^\W\d_]+', fold(label))):
                                self.label_tokens[es_key(t)].add((e['id'], i == 0))
            self.sense_group = sense_group
            # Tlachia: elementos (designación) y apariciones (lectura), sin imágenes nuevas.
            catalog = public_catalog(records)
            self.pictography = catalog
            self.elements = {e['id']: dict(e, key=loose_key(e['designation'].split('_')[0])) for e in catalog['elements']}
            self.meaning_index = defaultdict(set)
            for e in self.elements.values():
                for m in e.get('meanings', []):
                    self.meaning_index[es_key(m)].add(e['id'])
            self.pages = {p['id']: p for p in catalog['pages']}
            self.documents = {d['id']: d for d in catalog['documents']}
            self.archive_ids = {}  # grupo del archivo → clave laxa
            self._ready = True

    # -- detección e índice ---------------------------------------------------
    def detect(self, word):
        """Idioma probable de una palabra suelta: 'nah' o 'es'."""
        self._build()
        lk = loose_key(word)
        if lk in self.lex_loose:
            return 'nah'
        if es_key(word) in self.label_index or es_key(word) in self.meaning_index:
            return 'es'  # etiqueta de una acepción o significado de Tlachia: el diccionario manda sobre la frecuencia
        nah_n, es_n = self.nah_vocab[lk], self.es_vocab[es_key(word)]
        if fold(word) != word.casefold() and nah_n == 0:
            return 'es'  # acento español sin testimonio náhuatl
        return 'es' if es_n > max(3, 2 * nah_n) else 'nah'

    def variants(self, word):
        """Grafías del archivo con la misma clave laxa, por variedad."""
        self._build()
        return self._surfaces(loose_key(word))

    def _surfaces(self, lk):
        counts = defaultdict(Counter)
        for rid, w in self.postings.get(lk, []):
            counts[w.casefold()][self.rows[rid]['iso']] += 1
        out = [dict(form=f, total=sum(c.values()), by_variety={LABELS.get(k, k): n for k, n in c.most_common()})
               for f, c in counts.items()]
        out.sort(key=lambda v: (-v['total'], v['form']))
        return out

    def spanish_entries(self, word, limit=5):
        """Acepciones cuya etiqueta dice la palabra española (inicio de etiqueta primero)."""
        self._build()
        pattern = re.compile(r'(?<![^\W\d_])' + re.escape(fold(word)) + r'(?:e?s)?(?![^\W\d_])')
        found = []
        for h in self.entries.values():
            label = fold(h['label'] or '')
            m = pattern.search(label)
            if m:
                found.append(((0 if m.start() == 0 else 1, h['automatic'], len(label), h['written'] or ''), h))
        found.sort(key=lambda x: x[0])
        return [h for _, h in found[:limit]]

    def spanish_stems(self, word, limit=3):
        """Raíces que el corpus paralelo traduce con la palabra española (IBM-1 invertido)."""
        self._build()
        return self.es_to_stem.get(es_key(word), [])[:limit]

    def entry(self, sense_id):
        """Forma de consulta de una acepción tal como la usa el analizador, o None."""
        self._build()
        return self.entries.get(sense_id)

    # -- grupos ---------------------------------------------------------------
    def _archive_id(self, lk):
        gid = 'term-' + readable(lk)
        self.archive_ids.setdefault(gid, lk)
        return gid

    def _stem_group(self, stem):
        """Grupo de una raíz: la entrada que la apoya o la grafía más frecuente de la raíz."""
        if self.stem_owner.get(stem):
            return self.stem_owner[stem][0]
        keys = Counter()
        for _, w in self.concordance.index.get(stem, []):
            keys[loose_key(w)] += 1
        if not keys:
            return None
        lk = sorted(keys, key=lambda k: (-sum(1 for _ in self.postings.get(k, [])), k))[0]
        return self._key_group(lk)

    def _certainty(self, analysis, gid, stem, senses):
        """None si la forma pertenece con seguridad al grupo; si no, el motivo."""
        if analysis['basis'] != 'dictionary' or not any(d['sense_id'] in senses for d in analysis['dictionary']):
            return 'corpus_root'
        if len(stem or '') < MIN_STEM:
            return 'short_root'
        if analysis['class_'] in ('verb', 'nominalized'):
            return analysis['class_']
        if all(m['role'] == 'stem' for m in analysis['morphemes']):
            return 'bare_root'
        return None

    def group(self, gid):
        """Detalle completo de un grupo (en caché)."""
        self._build()
        if gid in self._groups:
            return self._groups[gid]
        if gid in self.lexicon:
            info = self.lexicon[gid]
            entry, keys, stem = info['entry'], set(info['keys']), info['stem']
            senses = {s['id'] for s in entry['senses']}
            source = 'dictionary'
        elif gid in self.archive_ids:
            lk = self.archive_ids[gid]
            entry, keys, senses, source = None, {lk}, set(), 'archive'
            top = self._surfaces(lk)
            stem = self.analyzer.best_stem(top[0]['form']) if top else None
        else:
            raise KeyError(gid)
        dictionary_spellings = set(entry['spellings']) if entry else set()
        attested = []
        for k in sorted(keys):
            for v in self._surfaces(k):
                attested.append(dict(v, orthography=orthography(v['form']), dictionary=v['form'] in {s.casefold() for s in dictionary_spellings}))
        attested.sort(key=lambda v: (-v['total'], v['form']))
        for s in sorted(dictionary_spellings, key=fold):
            if not any(v['form'] == s.casefold() for v in attested):
                attested.append(dict(form=s.casefold(), total=0, by_variety={}, orthography=orthography(s), dictionary=True))
        inflected, uncertain, seen_keys = [], [], set(keys)
        if stem:
            forms = Counter(w.casefold() for _, w in self.concordance.index.get(stem, []))
            by_key = defaultdict(list)
            for f in forms:
                by_key[loose_key(f)].append(f)
            for k, fs in sorted(by_key.items()):
                if k in seen_keys:
                    continue
                seen_keys.add(k)
                owners = [o for o in self.spelling_owner.get(k, []) if o != gid]
                analysis = self.analyzer.analyze(fs[0], limit=3)
                reason = 'other_entry' if owners else self._certainty(analysis[0], gid, stem, senses) if analysis else 'corpus_root'
                if reason is None:
                    # Empate exacto con otra lectura de la misma segmentación (te-coua-ni: «mordedor» o
                    # «comprador»): si la otra es verbal, la forma es ambigua y no se presenta como segura.
                    tied = [x['class_'] for x in analysis[1:] if x['segmentation'] == analysis[0]['segmentation']
                            and abs(x['score'] - analysis[0]['score']) < 1e-9 and x['class_'] in ('verb', 'nominalized')]
                    reason = tied[0] if tied else None
                surfaces = self._surfaces(k)
                item = dict(forms=[v['form'] for v in surfaces] or fs, total=sum(v['total'] for v in surfaces),
                            by_variety=_merge(v['by_variety'] for v in surfaces),
                            segmentation=analysis[0]['segmentation'] if analysis else None, key=k)
                if reason:
                    uncertain.append(dict(item, reason=reason, why=UNCERTAIN[reason], other_group=owners[0] if owners else None))
                else:
                    inflected.append(item)
        lemma_key = loose_key(entry['lemma']) if entry else next(iter(keys))
        if len(lemma_key) >= MIN_CONTAINED:
            for k in sorted(self.nah_vocab):
                if k not in seen_keys and k != lemma_key and lemma_key in k:
                    seen_keys.add(k)
                    surfaces = self._surfaces(k)
                    uncertain.append(dict(forms=[v['form'] for v in surfaces], total=sum(v['total'] for v in surfaces),
                                          by_variety=_merge(v['by_variety'] for v in surfaces), segmentation=None, key=k,
                                          reason='contains', why=UNCERTAIN['contains'], other_group=None))
        inflected.sort(key=lambda v: (-v['total'], v['forms'][0]))
        uncertain.sort(key=lambda v: (list(UNCERTAIN).index(v['reason']), -v['total'], v['forms'][0]))
        certain_keys = keys | {v['key'] for v in inflected}
        certain_ids = sorted({rid for k in certain_keys for rid, _ in self.postings.get(k, [])})
        uncertain_ids = sorted({rid for v in uncertain for rid, _ in self.postings.get(v['key'], [])} - set(certain_ids))
        glyphs, glyphs_uncertain = self._glyphs(entry, senses, certain_keys, lemma_key, stem)
        g = dict(id=gid, source=source, lemma=entry['lemma'] if entry else (attested[0]['form'] if attested else readable(lemma_key)),
                 key=lemma_key, stem=readable(stem) if stem else None, stem_key=stem,
                 forms=[dict(id=f['id'], sense_id=f.get('sense_id'), written=f.get('written'), catalog_normalized=f.get('catalog_normalized'),
                             variant_label=f.get('variant_label'), period=f.get('period')) for f in (entry['forms'] if entry else [])],
                 senses=[dict(id=s['id'], label=s.get('label'), definition=_snippet(s.get('definition'), 240), pos=s.get('pos'),
                              automatic=s.get('import_status') == 'automatic_transcription') for s in (entry['senses'] if entry else [])],
                 gloss_hints=[dict(word=h['word'], support=h['support']) for h in self.hints.hints(stem, limit=3, min_support=5)]
                 if stem and not entry else [],
                 spellings=dict(attested=attested, inflected=inflected, uncertain=uncertain),
                 passages=dict(total=len(certain_ids), by_variety=_count(self.rows[r]['iso'] for r in certain_ids),
                               uncertain_total=len(uncertain_ids)),
                 glyphs=glyphs, glyphs_uncertain=glyphs_uncertain,
                 review=entry['review'] if entry else dict(status='archive_only', automatic=True, primary_checked=False))
        g['_certain_keys'] = sorted(certain_keys)
        self._groups[gid] = g
        return g

    def _contains(self, key, lemma_key, stem_key):
        return key != lemma_key and ((len(lemma_key) >= MIN_CONTAINED - 1 and lemma_key in key)
                                     or (len(stem_key) >= MIN_STEM and key.startswith(stem_key)))

    def _glyphs(self, entry, senses, certain_keys, lemma_key, stem):
        certain, uncertain = [], []
        for gl in (entry['glyphs'] if entry else []):
            certain.append(dict(source='dictionary', id=gl['id'], reading=gl.get('reading'), scope=glyph_scope(gl),
                                basis='sense', url=gl.get('url'), image=gl.get('image'), sense_id=gl.get('sense_id')))
        stem_key = loose_key(readable(stem)) if stem and len(stem) >= MIN_STEM else ''
        matched = set()
        for e in self.elements.values():
            linked = any(l['sense_id'] in senses for l in e.get('lexical_links', []))
            item = dict(source='tlachia_element', id=e['id'], designation=e['designation'], meanings=e.get('meanings', []),
                        document=self.documents.get(e['document_id'], {}).get('title'), url=e['url'], image=e.get('image'))
            if linked or e['key'] in certain_keys:
                matched.add(e['id'])
                certain.append(dict(item, scope='component', basis='lexical_link' if linked else 'designation'))
            elif self._contains(e['key'], lemma_key, stem_key):
                uncertain.append(dict(item, scope='component', basis='contains', why=UNCERTAIN['contains']))
        for o in self.pictography['occurrences']:
            words = [loose_key(w) for w in WORD.findall(o['reading'])]
            page = self.pages.get(o['page_id'], {})
            item = dict(source='tlachia_occurrence', id=o['id'], reading=o['reading'], kind=o['kind'], code=o['code'],
                        document=self.documents.get(page.get('document_id'), {}).get('title'), locator=page.get('locator'),
                        url=o['url'], image=o.get('image'))
            component = any(c['element_id'] in matched for c in o['components'])
            if any(w in certain_keys for w in words):
                certain.append(dict(item, scope='word', basis='reading'))
            elif any(self._contains(w, lemma_key, stem_key) for w in words):
                # La lectura es otra palabra que contiene el término (mixcohuatl, cihuapilli): aparte.
                uncertain.append(dict(item, scope='component' if component else 'word', basis='contains', why=UNCERTAIN['contains']))
            elif component:
                certain.append(dict(item, scope='component', basis='component',
                                    values=[v for c in o['components'] if c['element_id'] in matched for v in c['values']]))
        order = list(SCOPES)
        certain.sort(key=lambda g: (g['source'] != 'dictionary', order.index(g['scope']), g['id']))
        return certain, uncertain

    def summary(self, gid):
        """Grupo sin campos internos, para las respuestas de la API."""
        return {k: v for k, v in self.group(gid).items() if not k.startswith('_')}

    def passage_ids(self, gid, first=None):
        """Pasajes del grupo (grafías seguras): primero la grafía consultada, luego las demás y las flexionadas."""
        g = self.group(gid)
        tiers = [loose_key(first)] if first else []
        tiers += [v for v in sorted({loose_key(a['form']) for a in g['spellings']['attested']}) if v not in tiers]
        tiers += [v['key'] for v in g['spellings']['inflected'] if v['key'] not in tiers]
        out, seen = [], set()
        for k in tiers:
            hits = self.postings.get(k, [])
            exact = [rid for rid, w in hits if first and w.casefold() == first.casefold()]
            for rid in exact + [rid for rid, _ in hits]:
                if rid not in seen:
                    seen.add(rid)
                    out.append(rid)
        return out

    # -- la búsqueda única ------------------------------------------------------
    def light(self, gid):
        """Identidad del grupo sin grafías ni glifos: para listas largas (Diccionario)."""
        if gid in self.lexicon:
            e = self.lexicon[gid]['entry']
            return dict(id=gid, source='dictionary', lemma=e['lemma'], senses=[dict(id=s['id'], label=s.get('label')) for s in e['senses']])
        return dict(id=gid, source='archive', lemma=self._surfaces(self.archive_ids[gid])[0]['form'], senses=[])

    def search(self, query, limit=5, full=3):
        """normalizar → clave laxa / raíz → orden. Devuelve los grupos con su motivo
        (los ``full`` primeros completos; el resto, solo su identidad)."""
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ValueError('limit debe ser un entero entre 1 y 100.')
        self._build()
        word, asked = parse(query)
        language = asked or self.detect(word)
        found = {}

        def add(gid, side, score, why):
            if not gid:
                return
            total = score + (LANGUAGE if side == language else 0)
            if gid not in found or total > found[gid][0]:
                found[gid] = (total, side, why, score)

        # Náhuatl: misma clave laxa; si no, la raíz del analizador.
        lk = loose_key(word)
        for gid in self.spelling_owner.get(lk, []):
            add(gid, 'nah', SCORES['spelling'], 'misma palabra' if word.casefold() in {s.casefold() for s in self.lexicon[gid]['entry']['spellings']}
                else 'otra grafía')
        if not self.spelling_owner.get(lk):
            analysis = self.analyzer.analyze(word, limit=1)
            a = analysis[0] if analysis else None
            certain = False
            if a and a['class_'] != 'foreign':
                for gid in self.stem_owner.get(a['stem_key'], []):
                    info = self.lexicon[gid]
                    reason = self._certainty(a, gid, info['stem'], {s['id'] for s in info['entry']['senses']})
                    certain = certain or reason is None
                    add(gid, 'nah', SCORES['inflected'] if reason is None else SCORES['possible'],
                        'forma flexionada (misma raíz)' if reason is None else 'posible: ' + UNCERTAIN[reason])
            if self.postings.get(lk) and not certain:
                add(self._archive_id(lk), 'nah', SCORES['archive'], 'grafía del archivo (sin entrada en el diccionario)')
                if a and a['class_'] != 'foreign' and not self.stem_owner.get(a['stem_key']):
                    other = self._stem_group(a['stem_key'])
                    if other and other != self._archive_id(lk):
                        add(other, 'nah', SCORES['possible'], 'posible: ' + UNCERTAIN['corpus_root'])
            elif not certain and a and a['class_'] != 'foreign' and len(a['stem_key']) >= MIN_STEM:
                add(self._stem_group(a['stem_key']), 'nah', SCORES['root_only'], 'misma raíz (sin esta grafía en el archivo)')
        # Español: etiqueta de la acepción, designación de Tlachia, traducciones del corpus.
        key = es_key(word)
        for gid in self.label_index.get(key, ()):
            add(gid, 'es', SCORES['label'], 'la acepción dice «%s»' % word)
        for eid in self.meaning_index.get(key, ()):
            add(self._key_group(self.elements[eid]['key']), 'es', SCORES['designation'], 'Tlachia: «%s» designa este elemento' % word)
        for i, c in enumerate(self.spanish_stems(word)):
            add(self._stem_group(c['stem_key']), 'es', SCORES['hint'] - i, 'las traducciones del archivo dicen «%s»' % word)
        for gid, first in self.label_tokens.get(key, ()):
            add(gid, 'es', SCORES['label_start'] if first else SCORES['label_word'], 'la acepción dice «%s»' % word)
        ranked = sorted(found, key=lambda g: (-found[g][0], -self._weight(g), g))
        groups = [dict(self.summary(g) if i < full else self.light(g),
                       match=dict(score=found[g][0], language=found[g][1], why=found[g][2],
                                  strong=found[g][3] >= STRONG and found[g][1] == language))
                  for i, g in enumerate(ranked[:limit])]
        return dict(query=query.strip(), word=word, language=language, groups=groups, total=len(ranked),
                    method=dict(version=TERMS_VERSION, pipeline='normalizar → clave laxa / raíz → orden', model_calls=0))

    def _weight(self, gid):
        keys = self.lexicon[gid]['keys'] if gid in self.lexicon else [self.archive_ids[gid]]
        return sum(len(self.postings.get(k, [])) for k in keys)

    def _key_group(self, key):
        if self.spelling_owner.get(key):
            return self.spelling_owner[key][0]
        return self._archive_id(key) if self.postings.get(key) else None

    def resolve(self, query):
        """Grupo principal de una consulta (o None): lo que Archivo y Consultar fichas presentan."""
        try:
            result = self.search(query, limit=1)
        except ValueError:
            return None
        top = result['groups'][0] if result['groups'] else None
        return (top, result['word']) if top and top['match']['strong'] else None


def _merge(dicts):
    out = Counter()
    for d in dicts:
        out.update(d)
    return dict(out.most_common())


def _count(values):
    return {LABELS.get(k, k): n for k, n in Counter(values).most_common()}
