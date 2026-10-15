"""Concordancia por raíz y pistas de glosa a partir del corpus paralelo.

Tres piezas, todas deterministas y reproducibles (solo stdlib):

* ``load_default``: construye el analizador morfológico con el catálogo léxico
  canónico (``lexicon``) y estima frecuencias de raíz sobre los pasajes de náhuatl clásico.
  El resultado se guarda en ``data/derived/`` con el hash de sus entradas; si
  las entradas cambian, se reconstruye.
* ``StemConcordance``: índice raíz → pasajes. Responde «¿dónde más aparece esta
  raíz?» aunque la palabra tenga otros prefijos o sufijos (nocal, calco, calli).
* ``GlossHints``: modelo de traducción léxica IBM-1 (Brown et al., 1993) entre
  raíces nahuas y palabras españolas de los mismos pasajes alineados. Cada
  pista conserva los pasajes que la sustentan: es una asociación estadística
  con evidencia, no una definición.
"""
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from threading import Lock

from .morphology import Analyzer, WORD, PARTICLES, ANALYZER_VERSION, corpus_words, key_of, readable
from . import lexicon, passages
from .text import LETTERS, es_key, fold, squash

ROOT = Path(__file__).resolve().parents[1]
DERIVED = ROOT / 'data' / 'derived'
HINTS_VERSION = 'gloss-hints-ibm1-v1'


# ---------------------------------------------------------------------------
# Entradas
# ---------------------------------------------------------------------------
def load_records(root=ROOT):
    """Registros públicos del catálogo léxico canónico (``lexicon``), sin base de datos."""
    return lexicon.load_records(root)


def _fingerprint(records, rows):
    h = hashlib.sha256()
    h.update(ANALYZER_VERSION.encode())
    for name in ('morphology.py', 'text.py'):
        h.update(Path(__file__).with_name(name).read_bytes())
    for rid in sorted(records):
        r = records[rid]
        if r.get('kind') in ('form', 'sense'):
            h.update(json.dumps([rid, r.get('written'), r.get('catalog_normalized'), r.get('label'),
                                 r.get('definition'), r.get('pos'), r.get('sense_id')], ensure_ascii=False).encode())
    for r in rows:
        if r['iso'] == 'nci':
            h.update(r['id'].encode()); h.update(r['nah'].encode()); h.update(r['es'].encode())
    return h.hexdigest()


_DEFAULT = {}
_LOCK = Lock()


def load_default(fit=True, root=ROOT, records=None, rows=None, cache=True):
    """Analizador listo para usar; reutiliza ``data/derived/stem-counts.json``."""
    records = load_records(root) if records is None else records
    rows = passages.load(root) if rows is None else rows
    fp = _fingerprint(records, rows)
    memo = (fp, fit)
    with _LOCK:
        if memo in _DEFAULT:
            return _DEFAULT[memo]
        analyzer = Analyzer(records)
        path = Path(root) / 'data' / 'derived' / 'stem-counts.json'
        if fit:
            loaded = False
            if cache and path.is_file():
                data = json.loads(path.read_text(encoding='utf-8'))
                if data.get('fingerprint') == fp:
                    analyzer.stem_counts = Counter(data['stem_counts'])
                    analyzer.stem_class = {k: tuple(v) for k, v in data.get('stem_class', {}).items()}
                    loaded = True
            if not loaded:
                history = analyzer.fit(list(corpus_words(rows)))
                if cache:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(json.dumps(dict(version=ANALYZER_VERSION, fingerprint=fp, em_history=history,
                                                    note='Frecuencias de raíz por tipo (EM duro). Derivado; se regenera si cambian diccionario, corpus o analizador.',
                                                    stem_counts=dict(analyzer.stem_counts.most_common()),
                                                    stem_class={k: list(v) for k, v in analyzer.stem_class.items()}),
                                               ensure_ascii=False), encoding='utf-8')
        analyzer.fingerprint = fp
        _DEFAULT[memo] = analyzer
        return analyzer


# ---------------------------------------------------------------------------
# Concordancia por raíz
# ---------------------------------------------------------------------------
class StemConcordance:
    """Índice raíz → [(pasaje, palabra)] sobre los pasajes ``nci``."""

    def __init__(self, analyzer, rows):
        self.analyzer = analyzer
        self.rows = {r['id']: r for r in rows if r.get('iso') == 'nci'}
        self.index = defaultdict(list)
        self.type_stem = {}
        for rid, r in self.rows.items():
            seen = set()
            for m in WORD.finditer(r['nah']):
                w = m.group(0)
                stem = self._stem(w)
                if stem and (stem, w.casefold()) not in seen:
                    seen.add((stem, w.casefold()))
                    self.index[stem].append((rid, w))

    def _stem(self, word):
        k = key_of(word)
        if k not in self.type_stem:
            self.type_stem[k] = self.analyzer.best_stem(word)
        return self.type_stem[k]

    def lookup(self, word, limit=10, exclude=None, stem_key=None):
        stem = stem_key or self._stem(word)
        hits = [h for h in self.index.get(stem, []) if h[0] != exclude]
        forms = Counter(w.casefold() for _, w in hits)
        passages, seen = [], set()
        # Diversidad: primero un pasaje por forma distinta, después el resto
        for pass_ in (0, 1):
            for rid, w in hits:
                if rid in seen or len(passages) >= limit:
                    continue
                if pass_ == 0 and any(p['form'].casefold() == w.casefold() for p in passages):
                    continue
                seen.add(rid)
                r = self.rows[rid]
                passages.append(dict(id=rid, form=w, nah=r['nah'], es=r['es'], document=r['document']))
        return dict(stem=readable(stem), stem_key=stem, total_passages=len({h[0] for h in hits}), distinct_forms=len(forms),
                    forms=[dict(form=f, count=c) for f, c in forms.most_common(12)], passages=passages)


# ---------------------------------------------------------------------------
# Pistas de glosa: IBM Model 1 raíz náhuatl → palabra española
# ---------------------------------------------------------------------------
ES_STOP = set('''a al algo algun alguna algunas alguno algunos ante antes aquel aquella aquellas aquello aquellos aqui asi
aun aunque cada como con contra cual cuales cuando de del desde donde dos e el ella ellas ello ellos en entonces entre era
eran es esa esas ese eso esos esta estaba estaban estas este esto estos fue fueron ha habia han hasta hay he la las le les
lo los mas me mi mis mucho muy nada ni no nos nosotros o os otra otras otro otros para pero poco por porque pues que quien
quienes se sea sean ser si sin sino sobre son su sus tal tambien tan tanto te ti tiene todo todos tu tus un una unas uno
unos y ya yo vosotros usted ustedes asimismo tambien dicho dicha cosa cosas'''.split())


def es_tokens(text):
    """Palabras de contenido españolas: (``text.es_key``, superficie), sin palabras vacías."""
    out = []
    for m in LETTERS.finditer(text):
        n = fold(m.group(0))
        if len(n) < 3 or n in ES_STOP:
            continue
        out.append((es_key(m.group(0)), m.group(0)))
    return out


class GlossHints:
    """Tabla t(es | raíz) estimada con EM (IBM-1) sobre pares ``nci``."""

    def __init__(self, table, evidence, surfaces, meta):
        self.table, self.evidence, self.surfaces, self.meta = table, evidence, surfaces, meta

    @classmethod
    def train(cls, analyzer, rows, iterations=8, min_count=2, split_ids=None):
        pairs = []
        surface_counts = defaultdict(Counter)
        for r in rows:
            if r.get('iso') != 'nci' or (split_ids is not None and r['id'] not in split_ids):
                continue
            nah = []
            for m in WORD.finditer(r['nah']):
                k = key_of(m.group(0))
                if not k:
                    continue
                nah.append(k if k in PARTICLES else analyzer.best_stem(m.group(0)))
            nah_keys = {key_of(m.group(0)) for m in WORD.finditer(r['nah'])}
            # Las palabras nahuas copiadas sin traducir (nombres, fechas) no son glosas.
            es = [(k, surf) for k, surf in es_tokens(r['es']) if key_of(surf) not in nah_keys]
            for k, surf in es:
                surface_counts[k][surf.casefold()] += 1
            if nah and es:
                pairs.append((r['id'], nah, [k for k, _ in es]))
        stem_df = Counter(s for _, nah, _ in pairs for s in set(nah))
        es_df = Counter(e for _, _, es in pairs for e in set(es))
        # Inicialización uniforme
        t = defaultdict(lambda: 1.0)
        NULL = '∅'
        for it in range(iterations):
            count = defaultdict(float)
            total = defaultdict(float)
            for _, nah, es in pairs:
                src = nah + [NULL]
                for e in es:
                    z = sum(t[(e, f)] for f in src)
                    if z <= 0:
                        continue
                    for f in src:
                        c = t[(e, f)] / z
                        count[(e, f)] += c
                        total[f] += c
            t = defaultdict(float, {(e, f): c / total[f] for (e, f), c in count.items()})
        # Tabla compacta: top-5 por raíz con al menos min_count pasajes compartidos
        cooc = defaultdict(list)
        for rid, nah, es in pairs:
            es_set = set(es)
            for f in set(nah):
                if stem_df[f] >= min_count:
                    cooc[f].append((rid, es_set))
        table, evidence = {}, {}
        by_f = defaultdict(list)
        for (e, f), p in t.items():
            if f != NULL and stem_df.get(f, 0) >= min_count and p >= 0.02:
                by_f[f].append((p, e))
        for f, cands in by_f.items():
            cands.sort(reverse=True)
            best = []
            for p, e in cands[:8]:
                support = [rid for rid, es_set in cooc[f] if e in es_set]
                if len(support) < min_count:
                    continue
                dice = 2 * len(support) / (stem_df[f] + es_df[e])
                best.append(dict(es=e, p=round(p, 4), support=len(support), dice=round(dice, 4)))
                evidence[(f, e)] = support[:5]
                if len(best) >= 5:
                    break
            if best:
                table[f] = best
        surfaces = {k: c.most_common(1)[0][0] for k, c in surface_counts.items()}
        meta = dict(version=HINTS_VERSION, method='IBM Model 1 (EM), raíz náhuatl → palabra española, con palabra nula',
                    iterations=iterations, pairs=len(pairs), stems=len(table), min_support=min_count,
                    analyzer=ANALYZER_VERSION)
        return cls(table, evidence, surfaces, meta)

    def hints(self, stem_key, limit=3, min_support=3):
        """Pistas para mostrar: al menos ``min_support`` pasajes compartidos."""
        out = []
        for h in [h for h in self.table.get(stem_key, []) if h['support'] >= min_support][:limit]:
            out.append(dict(h, word=self.surfaces.get(h['es'], h['es']),
                            passages=self.evidence.get((stem_key, h['es']), [])[:3]))
        return out

    def to_json(self):
        return dict(meta=self.meta, table=self.table, surfaces=self.surfaces,
                    evidence={f'{f}\t{e}': v for (f, e), v in self.evidence.items()})

    @classmethod
    def from_json(cls, data):
        ev = {tuple(k.split('\t', 1)): v for k, v in data['evidence'].items()}
        return cls(data['table'], ev, data['surfaces'], data['meta'])


def load_hints(analyzer, rows, root=ROOT, cache=True):
    path = Path(root) / 'data' / 'derived' / 'gloss-hints.json'
    fp = getattr(analyzer, 'fingerprint', None)
    if cache and path.is_file() and fp:
        data = json.loads(path.read_text(encoding='utf-8'))
        if data.get('fingerprint') == fp and data.get('meta', {}).get('version') == HINTS_VERSION:
            return GlossHints.from_json(data)
    hints = GlossHints.train(analyzer, rows)
    if cache and fp:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(dict(hints.to_json(), fingerprint=fp), ensure_ascii=False), encoding='utf-8')
    return hints


# ---------------------------------------------------------------------------
# Servicio combinado para la aplicación
# ---------------------------------------------------------------------------
def _short(text, limit=42):
    text = squash(text or '')
    return text if len(text) <= limit else text[:limit].rsplit(' ', 1)[0].rstrip(',;:') + '…'


class WordStudy:
    """Fachada perezosa: análisis + concordancia + pistas, construida una vez."""

    def __init__(self, root=ROOT, records_fn=None):
        self.root = root
        self.records_fn = records_fn
        self._lock = Lock()
        self._ready = None

    def _build(self):
        with self._lock:
            if self._ready is None:
                rows = passages.load(self.root)
                records = self.records_fn() if self.records_fn else load_records(self.root)
                analyzer = load_default(True, self.root, records, rows)
                self._ready = (analyzer, StemConcordance(analyzer, rows), load_hints(analyzer, rows, self.root))
        return self._ready

    def warm(self):
        try:
            self._build()
        except Exception:  # el arranque no debe fallar por el análisis opcional
            pass

    def word(self, word, exclude=None):
        if not isinstance(word, str) or not word.strip() or len(word) > 60 or not WORD.fullmatch(word.strip()):
            raise ValueError('Escribe una sola palabra (hasta 60 letras).')
        analyzer, concordance, hints = self._build()
        analyses = analyzer.analyze(word.strip(), limit=4)
        best = analyses[0] if analyses else None
        stem_key = best['stem_key'] if best else None
        attest = concordance.lookup(word.strip(), limit=6, exclude=exclude, stem_key=stem_key) if best else None
        return dict(word=word.strip(), analyses=analyses, attestations=attest,
                    gloss_hints=hints.hints(stem_key) if stem_key and best['class_'] not in ('particle', 'foreign') else [],
                    method=dict(analyzer=ANALYZER_VERSION, hints=hints.meta, model_calls=0),
                    note='Análisis automático por reglas, diccionario y corpus. Es una hipótesis de lectura pendiente de revisión; '
                         'las pistas de glosa son asociaciones estadísticas con sus pasajes de apoyo, no definiciones.')

    def gloss(self, text):
        if not isinstance(text, str) or not text.strip() or len(text) > 1200:
            raise ValueError('Glosa textos de hasta 1200 caracteres.')
        analyzer, _, hints = self._build()
        out = []
        for item in analyzer.gloss_text(text):
            b = item['best']
            hint = hints.hints(b['stem_key'], 1) if b and b['class_'] not in ('particle', 'foreign') else []
            out.append(dict(token=item['token'], start=item['start'], end=item['end'],
                            segmentation=b['segmentation'] if b else item['token'],
                            tags=[m['tag'] for m in b['morphemes']] if b else [],
                            morphemes=b['morphemes'] if b else [],
                            basis=b['basis'] if b else None,
                            lemma=(b['dictionary'][0]['written'] if b and b['dictionary'] else None),
                            gloss=_short((b['morphemes'][[m['role'] for m in b['morphemes']].index('stem')]['gloss'] if b else '')
                                         or (('≈ ' + hint[0]['word']) if hint else '')),
                            gloss_source='particle_table' if b and b['basis'] == 'particle_table' else 'dictionary' if b and b['dictionary']
                                         else 'corpus_hint' if hint else None,
                            confidence=b.get('relative_confidence') if b else None))
        return dict(text=text, tokens=out, method=ANALYZER_VERSION,
                    note='Glosa interlineal automática. «≈» indica una pista estadística del corpus paralelo, no una acepción del diccionario.')
