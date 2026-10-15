"""Consulta con evidencia: una palabra o pregunta → análisis, entradas y pasajes citados.

Recuperación sin LLM sobre tres fuentes ya existentes:

* el analizador morfológico y la concordancia por raíz (``stems``), para encontrar
  pasajes clásicos de la misma raíz aunque cambien prefijos y sufijos;
* una **clave laxa** de grafía (``loose_key``), solo para recuperar: une la ortografía
  moderna (SEP/INALI: k, kw, ts, w, j) con la colonial (c/qu, cu/qu, tz, hu, h) y
  reduce consonantes dobles. No sustituye a la clave fonémica evaluada del analizador;
* el modelo IBM-1 de pistas de glosa invertido, para preguntas en español
  («¿cómo se dice mujer?»): raíces cuyos pasajes alineados traducen esa palabra.

Cada resultado lleva su motivo («misma raíz», «otra grafía», «la traducción dice…»)
y los IDs de los pasajes. Sin evidencia suficiente, la respuesta se abstiene.
"""
import re
from collections import Counter, defaultdict
from threading import Lock

from .morphology import WORD, key_of, readable
from .research import LABELS
from .stems import ROOT, WordStudy, es_key, es_norm, es_tokens, load_rows

EVIDENCE_VERSION = 'evidence-root-v1'
# Pistas invertidas español → raíz: solo asociaciones con apoyo amplio.
ES_MIN_SUPPORT = 8
ES_MIN_P = 0.3
NAH_HINT_SUPPORT = 5

ASK_NAH = re.compile(r'^\s*¿?\s*(?:qu[eé]\s+(?:significa|quiere\s+decir)|significado\s+de)\s+(.+?)\s*\??\s*$', re.I)
ASK_ES = re.compile(r'^\s*¿?\s*c[oó]mo\s+se\s+dice\s+(.+?)(?:\s+en\s+n[aá]huatl)?\s*\??\s*$', re.I)
SHORT = 260  # pasajes breves primero: se leen mejor como ejemplo
ARTICLE = re.compile(r'^(?:el|la|los|las|un|una)\s+', re.I)


def loose_key(word):
    """Clave de recuperación tolerante a la ortografía.

    >>> loose_key('kuali') == loose_key('cualli') == loose_key('qualli')
    True
    >>> loose_key('tsontli') == loose_key('tzontli')
    True
    """
    k = key_of(word)
    k = k.replace('q', 'kw').replace('ts', 'ʦ').replace('j', '')
    k = re.sub(r'([^aeio])\1+', r'\1', k)
    if len(k) > 2 and k.endswith('w') and k[-2] in 'aeio':
        k = k[:-1] + 'o'  # tonatiuh / tonatiu
    return k


def _snippet_label(label, limit=120):
    label = re.sub(r'\s+', ' ', label or '').strip()
    return label if len(label) <= limit else label[:limit].rsplit(' ', 1)[0] + '…'


class Evidence:
    """Índices de recuperación construidos una vez sobre ``WordStudy``."""

    def __init__(self, word_study=None, root=ROOT):
        self.word_study = word_study or WordStudy(root)
        self.root = root
        self._lock = Lock()
        self._ready = False

    # -- construcción ---------------------------------------------------------
    def _build(self):
        with self._lock:
            if self._ready:
                return
            self.analyzer, self.concordance, self.hints = self.word_study._build()
            self.rows = {r['id']: r for r in load_rows(self.root)}
            self.postings = defaultdict(list)       # clave laxa → [(id, forma)]
            self.nah_vocab = Counter()
            self.es_vocab = Counter()
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
            # Diccionario por clave laxa de la forma escrita
            self.lex_loose = defaultdict(list)
            self.entries = {}
            lexicon = self.analyzer.lexicon
            for bucket in (lexicon.stems, lexicon.whole):
                for hits in bucket.values():
                    for h in hits:
                        if h['sense_id'] in self.entries:
                            continue
                        self.entries[h['sense_id']] = h
                        self.lex_loose[loose_key(h['written'] or '')].append(h)
            # Pistas invertidas: palabra española → [(raíz, p, apoyo)]
            self.es_to_stem = defaultdict(list)
            for stem, rows in self.hints.table.items():
                for h in rows:
                    if h['support'] >= ES_MIN_SUPPORT and h['p'] >= ES_MIN_P:
                        self.es_to_stem[h['es']].append(dict(stem_key=stem, p=h['p'], support=h['support']))
            for rows in self.es_to_stem.values():
                rows.sort(key=lambda h: (-h['p'] * min(1, h['support'] / 20), h['stem_key']))
            self._ready = True

    # -- utilidades -----------------------------------------------------------
    def _entry(self, h, how):
        return dict(sense_id=h['sense_id'], form_id=h['form_id'], written=h['written'], label=_snippet_label(h['label']),
                    url=h['url'], automatic=h['automatic'], how=how)

    def _passage(self, rid, form, why):
        r = self.rows[rid]
        return dict(id=rid, nah=r['nah'], es=r['es'], document=r['document'], iso=r['iso'],
                    variety=LABELS.get(r['iso'], r['iso']), form=form, why=why)

    def parse(self, query):
        """Devuelve (palabra, idioma pedido o None). Una palabra por consulta."""
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

    def detect(self, word):
        lk = loose_key(word)
        if lk in self.lex_loose:
            return 'nah'
        nah_n, es_n = self.nah_vocab[lk], self.es_vocab[es_key(word)]
        if es_norm(word) != word.casefold() and nah_n == 0:
            return 'es'  # acento español sin testimonio náhuatl
        return 'es' if es_n > max(3, 2 * nah_n) else 'nah'

    # -- consulta ---------------------------------------------------------------
    def ask(self, query):
        self._build()
        word, language = self.parse(query)
        language = language or self.detect(word)
        result = self._ask_es(word) if language == 'es' else self._ask_nah(word)
        result.update(query=query.strip(), word=word, language=language,
                      method=dict(version=EVIDENCE_VERSION, analyzer=self.analyzer.fingerprint[:12] if getattr(self.analyzer, 'fingerprint', None) else None,
                                  model_calls=0, network_requests=0))
        result['abstained'] = not (result['entries'] or result['passages'] or result['other_varieties'])
        if result['abstained']:
            result['reason'] = ('No hay entrada del diccionario ni pasajes que sostengan una respuesta. '
                                'No se propone una traducción sin evidencia.')
        return result

    def _variants(self, word):
        """Grafías del archivo con la misma clave laxa, por variedad."""
        lk = loose_key(word)
        counts = defaultdict(Counter)
        for rid, w in self.postings.get(lk, []):
            counts[w.casefold()][self.rows[rid]['iso']] += 1
        out = [dict(form=f, total=sum(c.values()), by_variety={LABELS.get(k, k): n for k, n in c.most_common()})
               for f, c in counts.items()]
        out.sort(key=lambda v: (-v['total'], v['form']))
        return out

    def _ask_nah(self, word):
        analyses = self.analyzer.analyze(word, limit=3)
        best = analyses[0] if analyses else None
        strong = best and best['basis'] in ('dictionary', 'particle_table')
        interpreted_as, chosen = None, best
        variants = self._variants(word)
        if not strong:
            # Otra grafía del mismo vocablo con análisis apoyado (kuali → cualli, nimann → niman)
            classical = [v for v in variants if v['form'] != word.casefold()
                         and v['by_variety'].get(LABELS['nci'])]
            classical.sort(key=lambda v: -v['by_variety'][LABELS['nci']])
            for v in classical[:3]:
                a = self.analyzer.analyze(v['form'], limit=1)
                if a and (a[0]['basis'] in ('dictionary', 'particle_table') or not chosen
                          or chosen['basis'] in ('rules', 'loan_or_name')):
                    interpreted_as, chosen = v['form'], a[0]
                    if a[0]['basis'] in ('dictionary', 'particle_table'):
                        break
        entries, seen = [], set()
        for h in self.lex_loose.get(loose_key(word), []):
            if h['sense_id'] not in seen:
                seen.add(h['sense_id'])
                entries.append(self._entry(h, 'misma palabra (otra grafía)' if (h['written'] or '').casefold() != word.casefold()
                                           else 'misma palabra'))
        if chosen:
            for d in chosen['dictionary']:
                if d['sense_id'] not in seen:
                    seen.add(d['sense_id'])
                    entries.append(dict(self._entry(self.entries.get(d['sense_id'], dict(d, form_id=d['form_id'])), 'misma raíz'),
                                        derivation=d['derivation']))
        if not chosen and entries:
            a = self.analyzer.analyze(entries[0]['written'], limit=1)
            chosen = a[0] if a else None
        passages, total, forms = [], 0, []
        stem_key = None
        if chosen and chosen['class_'] != 'foreign':
            stem_key = chosen['stem_key']
            conc = self.concordance.lookup(chosen['word'], limit=24, stem_key=stem_key)
            total, forms = conc['total_passages'], conc['forms']
            ranked = sorted(conc['passages'], key=lambda p: len(p['nah']) > SHORT)  # estable: conserva la diversidad
            passages = [self._passage(p['id'], p['form'], 'misma raíz' if p['form'].casefold() != word.casefold() else 'misma forma')
                        for p in ranked[:6]]
            if interpreted_as and not any(p['form'].casefold() == interpreted_as for p in passages):
                # Un ejemplo de la grafía con la que se leyó la palabra, primero.
                same = sorted((rid for rid, w in self.postings.get(loose_key(interpreted_as), [])
                               if w.casefold() == interpreted_as and self.rows[rid]['iso'] == 'nci'),
                              key=lambda rid: len(self.rows[rid]['nah']) > SHORT)
                if same:
                    form = next(w for rid, w in self.postings[loose_key(interpreted_as)] if rid == same[0] and w.casefold() == interpreted_as)
                    passages = [self._passage(same[0], form, 'grafía con la que se leyó')] + [p for p in passages if p['id'] != same[0]][:5]
        # Otras variedades: misma palabra por clave laxa (el analizador es solo clásico)
        other, docs = [], set()
        for form in dict.fromkeys([word] + ([interpreted_as] if interpreted_as else [])):
            for rid, w in self.postings.get(loose_key(form), []):
                r = self.rows[rid]
                if r['iso'] == 'nci' or len(other) >= 4 or (r['iso'], r['document']) in docs:
                    continue
                docs.add((r['iso'], r['document']))
                other.append(self._passage(rid, w, 'misma palabra' if w.casefold() == word.casefold() else 'otra grafía'))
        hints = []
        if stem_key and chosen['class_'] not in ('particle', 'foreign'):
            hints = [dict(word=h['word'], support=h['support'], p=h['p'], passages=h['passages'])
                     for h in self.hints.hints(stem_key, limit=3, min_support=NAH_HINT_SUPPORT)]
        return dict(analysis=chosen, alternatives=analyses[1:] if chosen is best else analyses[:2],
                    interpreted_as=interpreted_as, entries=entries[:5], variants=variants[:8],
                    root=dict(stem=readable(stem_key), stem_key=stem_key, total_passages=total, forms=forms[:8]) if stem_key else None,
                    passages=passages, other_varieties=other, gloss_hints=hints,
                    note='Análisis automático y pasajes de la misma raíz; las traducciones son las del archivo. '
                         'Pendiente de revisión lingüística.')

    def _ask_es(self, word):
        key = es_key(word)
        pattern = re.compile(r'(?<![^\W\d_])' + re.escape(es_norm(word)) + r'(?:e?s)?(?![^\W\d_])')
        entries = []
        for h in self.entries.values():
            label = es_norm(h['label'] or '')
            m = pattern.search(label)
            if m:
                rank = (0 if m.start() == 0 else 1, h['automatic'], len(label), h['written'] or '')
                entries.append((rank, h))
        entries.sort(key=lambda x: x[0])
        entries = [self._entry(h, 'la definición dice «%s»' % word) for _, h in entries[:5]]
        entry_stems = {self.analyzer.best_stem(e['written']) for e in entries if e['written']}
        candidates, passages = [], []
        for c in self.es_to_stem.get(key, [])[:3]:
            stem = c['stem_key']
            hits = [(rid, w) for rid, w in self.concordance.index.get(stem, [])
                    if key in {k for k, _ in es_tokens(self.rows[rid]['es'])}]
            if not hits:
                continue
            forms = Counter(w.casefold() for _, w in hits)
            hits.sort(key=lambda h: len(self.rows[h[0]]['nah']) > SHORT)
            sample, seen = [], set()
            for rid, w in hits:
                if rid in seen or len(sample) >= 3:
                    continue
                if any(p['form'].casefold() == w.casefold() for p in sample) and len(forms) > len(sample):
                    continue
                seen.add(rid)
                sample.append(self._passage(rid, w, 'la traducción dice «%s»' % word))
            candidates.append(dict(stem=readable(stem), stem_key=stem, p=c['p'], support=c['support'],
                                   in_dictionary=stem in entry_stems, forms=[dict(form=f, count=n) for f, n in forms.most_common(6)],
                                   passages=sample))
            passages.extend(sample)
        if not candidates:
            # Sin raíz con apoyo suficiente: pasajes cuya traducción contiene la palabra,
            # sin proponer un equivalente náhuatl (primero el clásico).
            ordered = sorted(self.rows.values(), key=lambda r: (r['iso'] != 'nci', len(r['nah']) > SHORT, r['id']))
            for r in ordered:
                if len(passages) >= 6:
                    break
                if key in {k for k, _ in es_tokens(r['es'])}:
                    passages.append(self._passage(r['id'], None, 'la traducción dice «%s»; no se propone equivalente' % word))
        return dict(analysis=None, interpreted_as=None, entries=entries, candidates=candidates,
                    passages=passages, other_varieties=[], variants=[], root=None, gloss_hints=[],
                    note='Entradas cuya definición contiene la palabra y raíces que el corpus paralelo traduce así '
                         '(asociación estadística con pasajes de apoyo, no una definición). Pendiente de revisión lingüística.')
