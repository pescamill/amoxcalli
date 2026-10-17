"""Consulta con evidencia: una palabra o pregunta → análisis, entradas y pasajes citados.

La resolución de la palabra es la búsqueda única del índice de términos
(``terms.TermIndex``: normalizar → clave laxa / raíz → orden), la misma que usan
Diccionario, Archivo y Consultar fichas. Sobre ella, Preguntar presenta:

* el análisis morfológico y la concordancia por raíz (``stems``), para mostrar
  pasajes clásicos de la misma raíz aunque cambien prefijos y sufijos;
* las grafías del archivo con la misma **clave laxa** (``text.loose_key``), que une la
  ortografía moderna (SEP/INALI) con la colonial; no sustituye a la clave del analizador;
* para preguntas en español («¿cómo se dice mujer?»), las raíces cuyos pasajes
  alineados traducen esa palabra (pistas IBM-1 invertidas del índice de términos).

Cada resultado lleva su motivo («misma raíz», «otra grafía», «la traducción dice…»)
y los IDs de los pasajes; ``terms`` trae los grupos de término de la consulta.
Sin evidencia suficiente, la respuesta se abstiene.
"""
from collections import Counter

from .passages import LABELS
from .stems import ROOT, WordStudy, es_tokens
from .terms import TermIndex, parse
from .text import es_key, loose_key, readable, squash

EVIDENCE_VERSION = 'evidence-root-v1'
NAH_HINT_SUPPORT = 5
SHORT = 260  # pasajes breves primero: se leen mejor como ejemplo


def _snippet_label(label, limit=120):
    label = squash(label or '')
    return label if len(label) <= limit else label[:limit].rsplit(' ', 1)[0] + '…'


class Evidence:
    """Consulta con evidencia sobre el índice de términos (``terms.TermIndex``): la misma búsqueda que las demás vistas."""

    def __init__(self, word_study=None, root=ROOT, terms=None):
        self.terms = terms or TermIndex(word_study or WordStudy(root), root)
        self.word_study = self.terms.word_study
        self.root = root
        self._ready = False

    # -- construcción ---------------------------------------------------------
    def _build(self):
        if self._ready:
            return
        t = self.terms
        t._build()
        self.analyzer, self.concordance = t.analyzer, t.concordance
        self.rows, self.postings, self.entries, self.lex_loose = t.rows, t.postings, t.entries, t.lex_loose
        self._ready = True

    @property
    def hints(self):
        return self.terms.hints

    # -- utilidades -----------------------------------------------------------
    def _entry(self, h, how):
        return dict(sense_id=h['sense_id'], form_id=h['form_id'], written=h['written'], label=_snippet_label(h['label']),
                    url=h['url'], automatic=h['automatic'], how=how)

    def _passage(self, rid, form, why):
        r = self.rows[rid]
        return dict(id=rid, nah=r['nah'], es=r['es'], document=r['document'], iso=r['iso'],
                    variety=LABELS.get(r['iso'], r['iso']), form=form, why=why)

    def parse(self, query):
        """Devuelve (palabra, idioma pedido o None): la normalización de ``terms.parse``."""
        return parse(query)

    def detect(self, word):
        return self.terms.detect(word)

    # -- consulta ---------------------------------------------------------------
    def ask(self, query):
        self._build()
        word, language = self.parse(query)
        language = language or self.detect(word)
        result = self._ask_es(word) if language == 'es' else self._ask_nah(word)
        result.update(query=query.strip(), word=word, language=language,
                      method=dict(version=EVIDENCE_VERSION, analyzer=self.analyzer.fingerprint[:12] if getattr(self.analyzer, 'fingerprint', None) else None,
                                  model_calls=0, network_requests=0))
        result['terms'] = self.terms.search(query, limit=3)['groups']
        result['abstained'] = not (result['entries'] or result['passages'] or result['other_varieties'])
        if result['abstained']:
            result['reason'] = ('No hay entrada del diccionario ni pasajes que sostengan una respuesta. '
                                'No se propone una traducción sin evidencia.')
        return result

    def _variants(self, word):
        """Grafías del archivo con la misma clave laxa, por variedad."""
        return self.terms.variants(word)

    def _ask_nah(self, word):
        analyses = self.analyzer.analyze(word, limit=3)
        best = analyses[0] if analyses else None
        strong = best and best['basis'] in ('dictionary', 'particle_table', 'name_list')
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
            conc = self.concordance.lookup(chosen['word'], limit=24, stem_key=self.concordance.index_key(chosen))
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
        if stem_key and chosen['class_'] not in ('particle', 'foreign', 'name'):
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
        entries = [self._entry(h, 'la definición dice «%s»' % word) for h in self.terms.spanish_entries(word)]
        entry_stems = {self.analyzer.best_stem(e['written']) for e in entries if e['written']}
        candidates, passages = [], []
        for c in self.terms.spanish_stems(word):
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
