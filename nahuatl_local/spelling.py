"""Buscador y asociador de grafías: escribir como uno escribe y encontrar la palabra con sus fuentes.

Ninguna grafía es «la correcta». Para relacionar formas se usa una **forma pivote**
interna (``pivot``: la clave laxa ``text.loose_key``, que parte de la clave fonémica del
analizador), y cada persona ve la grafía original de cada fuente. El pivote nunca se
muestra como palabra: solo sirve para comparar.

Piezas
------
``PROFILES`` / ``convert``   perfiles ortográficos explícitos (colonial, ACK, SEP/INALI y
                              rasgos por variedad medidos en el archivo) y un conversor.
``RULES`` / ``alternates``   alternancias conocidas entre perfiles (u = w en coda, -t = -tl,
                              z = tz ante consonante, s = x, …), con su costo.
``distance``                  distancia de edición sobre el pivote: barata para sustituciones
                              ortográficas conocidas, cara para errores arbitrarios.
``Graph``                     grafo de equivalencias entre grafías atestiguadas; cada arista
                              lleva tipo y evidencia (regla de perfil, traducciones alineadas
                              que coinciden, confirmación humana). Solo las aristas seguras
                              forman grupos; las demás se muestran aparte.
``Search``                    búsqueda tolerante: pivote igual → reglas → distancia → raíz del
                              analizador; ordena por evidencia y dice por qué propone cada
                              candidato y con qué confianza. Una conjetura nunca se presenta
                              como forma atestiguada.

Las reglas activas, los pares minados y las decisiones de revisión viven en
``configs/spelling-rules-v1.json`` y ``editorial/spelling-review.json``
(``spelling_mining``); la medida, en ``spelling_evaluation``.
"""
import json
import math
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from threading import Lock

from .passages import LABELS
from .text import fold, loose_key, phonemic_key, spelling_base

SPELLING_VERSION = 'spelling-v1'
ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = 'configs/spelling-rules-v1.json'
REVIEW_PATH = 'editorial/spelling-review.json'
VOWELS = set('aeio')
LIMIT_NOTE = ('Las fuentes coloniales casi nunca marcan las vocales largas ni el saltillo: una forma colonial '
              'convertida a ACK o SEP no puede recuperarlos. Solo se muestran cuando una fuente los registra.')

# ---------------------------------------------------------------------------
# 1. Pivote y símbolos
# ---------------------------------------------------------------------------
# Alfabeto del pivote: un carácter por fonema. q = kw, ʦ = tz/ts, λ = tl, č = ch.


def pivot(word):
    """Forma pivote interna (clave laxa). Solo compara; no es una grafía."""
    return loose_key(word)


def symbols(key):
    """Pivote como cadena de un símbolo por fonema (kw → q)."""
    return key.replace('kw', 'q')


def unsymbols(sym):
    return sym.replace('q', 'kw')


# ---------------------------------------------------------------------------
# 2. Perfiles ortográficos y conversor
# ---------------------------------------------------------------------------
PROFILES = {
    'colonial': dict(label='Colonial (Molina, Carochi)', sources='Molina 1571, Carochi 1645, Códice Florentino',
                     traits='c/qu, cu/qu + vocal, uc en coda, hu/uh (también u, v), z/ç/c, tz, tl, ch, x; '
                            'sin saltillo ni vocales largas (Carochi los marca con acentos en parte de su obra)'),
    'ack': dict(label='ACK (Andrews, Campbell, Karttunen)', sources='Andrews 2003, Karttunen 1983, Wiktionary',
                traits='c/qu, cu/uc, hu/uh, z/c, tz; saltillo h; vocales largas con macrón solo si un diccionario las registra'),
    'sep': dict(label='SEP / INALI (moderna)', sources='materiales SEP, INALI, autores contemporáneos',
                traits='k, kw, w, s, ts, ch, tl, x; saltillo h (o j en muchos textos)'),
}
VARIETY_PROFILES = ('azz', 'nhm', 'nhn', 'nhw', 'nhe')


def segments(word):
    """Fonemas de una grafía con saltillo (ʔ) y longitud cuando la grafía los marca.

    Devuelve [(símbolo, largo)], con símbolos del pivote (q, ʦ, λ, č…) y ʔ. Se apoya en
    los tramos de ``text.phonemic_key``: una «h» o «j» que el pivote omite tras vocal y
    ante consonante o final es saltillo; una vocal con macrón o doble es larga."""
    w = unicodedata.normalize('NFC', word)
    key, spans = phonemic_key(w)
    base = spelling_base(w)
    out = []
    for i, (sym, (a, b)) in enumerate(zip(key, spans)):
        if sym == 'j':
            if out and out[-1][0] in VOWELS:
                out.append(('ʔ', False))
            continue
        piece = w[a:b]
        long_ = False
        if sym in VOWELS:
            long_ = any(unicodedata.normalize('NFD', c)[1:2] in ('̄', '̂') for c in piece) or \
                    sum(1 for c in base[a:b] if c in 'aeiou') > 1
        out.append(({'q': 'q', 'ʦ': 'ʦ'}.get(sym, sym), long_))
        tail = base[a:b]
        # «h» final del tramo tras vocal (tlahtolli, ohtli): saltillo, salvo hu/uh/ch.
        if sym in VOWELS and tail.endswith('h') and len(tail) > 1:
            out.append(('ʔ', False))
    # t + s del pivote estricto = ts (moderna)
    merged = []
    for s, l in out:
        if merged and s == 's' and merged[-1][0] == 't':
            merged[-1] = ('ʦ', False)
            continue
        if merged and s == 'w' and merged[-1][0] == 'k':
            merged[-1] = ('q', False)
            continue
        merged.append((s, l))
    return merged


MACRON = dict(a='ā', e='ē', i='ī', o='ō')


def _render(segs, profile, variety=None):
    out = []
    n = len(segs)
    for i, (s, long_) in enumerate(segs):
        nxt = segs[i + 1][0] if i + 1 < n else ''
        prev = segs[i - 1][0] if i else ''
        before_v = nxt in VOWELS
        front = nxt in ('e', 'i')
        if s in VOWELS:
            out.append(MACRON[s] if long_ and profile == 'ack' else s)
        elif s == 'ʔ':
            out.append({'ack': 'h', 'sep': 'h'}.get(profile, variety.get('saltillo', '') if variety else ''))
        elif profile in ('colonial', 'ack'):
            if s == 'k':
                out.append('qu' if front else 'c')
            elif s == 'q':
                out.append(('qu' if profile == 'colonial' else 'cu') if before_v else 'uc')
            elif s == 'w':
                out.append('hu' if before_v else 'uh')
            elif s == 's':
                out.append('c' if front else 'z')
            else:
                out.append(dict(ʦ='tz', λ='tl', č='ch').get(s, s))
        else:  # sep o variedad
            v = variety or {}
            if s == 'k':
                out.append(v.get('k', 'k') if not front else v.get('k_front', 'k'))
            elif s == 'q':
                out.append(v.get('kw', 'kw') if before_v else v.get('kw_coda', 'kw'))
            elif s == 'w':
                out.append(v.get('w', 'w') if before_v or not prev else v.get('w_coda', 'w'))
            elif s == 's':
                out.append(v.get('s', 's'))
            elif s == 'ʦ':
                out.append(v.get('ts', 'ts'))
            elif s == 'λ':
                # Una variedad que escribe -t final escribe t por tl en toda la palabra (metsti, pajti, takuauak).
                out.append(v.get('tl_final', 'tl'))
            elif s == 'č':
                out.append('ch')
            else:
                out.append(s)
    return ''.join(out)


def _degeminate(form):
    return re.sub(r'([^aeiouāēīō])\1', r'\1', form)


def convert(word, profiles=None, varieties=None):
    """Una grafía en cada perfil: [{profile, label, form, note}]. ``varieties``: rasgos medidos (``variety_traits``)."""
    segs = segments(word)
    marked = any(s == 'ʔ' for s, _ in segs) or any(l for _, l in segs)
    out = []
    for pid in profiles or list(PROFILES):
        note = None
        if pid in ('ack', 'sep') and not marked:
            note = 'sin saltillo ni vocales largas registrados en esta grafía'
        out.append(dict(profile=pid, label=PROFILES[pid]['label'], form=_render(segs, pid), note=note))
    for iso, traits in (varieties or {}).items():
        out.append(dict(profile=iso, label='Rasgos del archivo · ' + LABELS.get(iso, iso),
                        form=_degeminate(_render(segs, 'variety', traits)) if traits.get('double') == 'single' else _render(segs, 'variety', traits),
                        note='rasgos medidos en %s apariciones del archivo' % format(traits['_tokens'], ',').replace(',', ' ')))
    return out


def variety_traits(forms_by_iso):
    """Rasgos ortográficos por variedad medidos en el archivo: cómo escribe cada una kw, w, s, ts, saltillo y -tl.

    ``forms_by_iso``: {iso: Counter(grafía → apariciones)}. Devuelve {iso: {rasgo: grafía más frecuente}}."""
    out = {}
    for iso in VARIETY_PROFILES:
        forms = forms_by_iso.get(iso)
        if not forms:
            continue
        c = defaultdict(Counter)
        tokens = 0
        for form, n in forms.items():
            f = fold(form)
            tokens += n
            key, spans = phonemic_key(f)
            for i, (sym, (a, b)) in enumerate(zip(key, spans)):
                piece = f[a:b].replace('h', '') if sym not in ('w', 'q', 'č') else f[a:b]
                nxt = key[i + 1] if i + 1 < len(key) else ''
                if sym == 'q' or (sym == 'k' and nxt == 'w'):
                    c['kw' if (key[i + 2:i + 3] if sym == 'k' else nxt) in VOWELS or sym == 'k' else 'kw_coda'][
                        f[a:spans[i + 1][1]] if sym == 'k' else piece] += n
                elif sym == 'w' and (not i or key[i - 1] != 'k'):
                    c['w' if nxt in VOWELS else 'w_coda'][piece] += n
                elif sym == 'k':
                    c['k_front' if nxt in 'ei' else 'k'][piece] += n
                elif sym == 's':
                    c['s'][piece] += n
                elif sym == 'ʦ':
                    c['ts'][piece] += n
                elif sym == 't' and nxt == 's':
                    c['ts'][f[a:spans[i + 1][1]]] += n
                elif sym == 'j':
                    c['saltillo']['j'] += n
            if re.search(r'[aeiou]h(?=[^aeiou]|$)', f) and not re.search(r'[aeiou]h(?=u[aeiou])', f):
                c['saltillo']['h'] += n
            if re.search(r'([^aeiouh])\1', f):
                c['double']['double'] += n
            elif re.search(r'[aeiou]l[aeiou]', f):
                c['double']['single'] += n
            if f.endswith('tl'):
                c['tl_final']['tl'] += n
            elif f.endswith('t') and not f.endswith('tz') and len(f) > 3:
                c['tl_final']['t'] += n
        traits = {k: v.most_common(1)[0][0] for k, v in c.items() if v}
        # El saltillo solo se escribe si una variedad lo marca con frecuencia.
        sal = c.get('saltillo', Counter())
        traits['saltillo'] = sal.most_common(1)[0][0] if sum(sal.values()) > 0.01 * tokens else ''
        # -t final: solo si es claramente el uso de la variedad (Sierra de Puebla).
        tl = c.get('tl_final', Counter())
        traits['tl_final'] = 't' if tl['t'] > 2 * tl['tl'] else 'tl'
        # Consonantes dobles (ll): una variedad que casi no las escribe las simplifica (kuali).
        dbl = c.get('double', Counter())
        traits['double'] = 'single' if dbl['single'] > 4 * dbl['double'] else 'double'
        traits['_tokens'] = tokens
        traits['_counts'] = {k: dict(v.most_common(4)) for k, v in c.items()}
        out[iso] = traits
    return out


# ---------------------------------------------------------------------------
# 3. Alternancias de perfil y distancia de edición
# ---------------------------------------------------------------------------
# id: (a, b, contexto, costo, etiqueta). Se aplican en ambos sentidos sobre los símbolos.
# Contextos: 'any', 'end' (final de palabra), 'coda' (tras vocal, ante consonante o final),
# 'before_c' (ante consonante), 'between_iv' (entre i y vocal).
RULES = {
    'coda_w': ('o', 'w', 'coda', 0.2, 'u tras vocal = w en coda (kuautli = cuauhtli)'),
    'final_tl': ('t', 'λ', 'end', 0.2, '-t final = -tl (Sierra de Puebla y otras variedades)'),
    'tl_t': ('t', 'λ', 'any', 0.35, 'tl = t también dentro de la palabra (Sierra de Puebla: metsti, pajti)'),
    'tl_typo': ('lt', 'λ', 'end', 0.4, 'lt por tl al final (error de tecleo)'),
    'z_tz': ('s', 'ʦ', 'before_c', 0.25, 'z/s ante consonante = tz (meztli = metztli)'),
    's_x': ('s', 'x', 'any', 0.35, 's o sh = x (sochitl, shochitl = xochitl)'),
    'x_ch': ('x', 'č', 'any', 0.5, 'x = ch (toxtli = tochtli)'),
    'e_i': ('e', 'i', 'any', 0.4, 'e = i (sintli = centli)'),
    'y_glide': ('iy', 'i', 'between_iv', 0.2, 'y entre i y vocal (quiyahuitl = quiahuitl)'),
    'n_m': ('n', 'm', 'before_p', 0.3, 'n = m ante p o m'),
}
MAX_RULE_COST = 0.9
MAX_VARIANTS = 64

# Costos de la distancia: sustituciones ortográficas conocidas son baratas.
SUB = {}
for _a, _b, _ctx, _cost, _ in RULES.values():
    if len(_a) == len(_b) == 1:
        SUB[_a, _b] = SUB[_b, _a] = min(_cost + 0.1, SUB.get((_a, _b), 9))
for _a, _b, _c in (('o', 'a', 0.7), ('a', 'e', 0.8), ('i', 'a', 0.8), ('o', 'e', 0.8), ('o', 'i', 0.8),
                   ('k', 'q', 0.9), ('s', 'č', 0.7), ('ʦ', 'č', 0.6), ('ʦ', 'x', 0.6), ('t', 'ʦ', 0.7),
                   ('w', 'y', 0.7), ('l', 'λ', 0.7)):
    SUB[_a, _b] = SUB[_b, _a] = _c
INDEL = dict(a=0.7, e=0.7, i=0.7, o=0.7, y=0.3, w=0.5, l=0.6, n=0.8)
TRANSPOSE = 0.6


def distance(a, b, cap=9.0):
    """Distancia de edición ponderada entre dos cadenas de símbolos (Damerau restringida)."""
    n, m = len(a), len(b)
    if abs(n - m) > 3:
        return cap
    prev2, prev = None, [0.0] * (m + 1)
    for j in range(1, m + 1):
        prev[j] = prev[j - 1] + INDEL.get(b[j - 1], 1.0)
    for i in range(1, n + 1):
        cur = [prev[0] + INDEL.get(a[i - 1], 1.0)] + [0.0] * m
        ai = a[i - 1]
        best = cur[0]
        for j in range(1, m + 1):
            bj = b[j - 1]
            sub = 0.0 if ai == bj else SUB.get((ai, bj), 1.0)
            v = min(prev[j - 1] + sub, prev[j] + INDEL.get(ai, 1.0), cur[j - 1] + INDEL.get(bj, 1.0))
            if i > 1 and j > 1 and ai == b[j - 2] and a[i - 2] == bj and ai != bj:
                v = min(v, prev2[j - 2] + TRANSPOSE)
            cur[j] = v
            best = min(best, v)
        if best > cap:
            return cap
        prev2, prev = prev, cur
    return prev[m]


def _context_ok(ctx, s, i, j):
    """¿Cabe la alternancia en s[i:j]?"""
    after = s[j:j + 1]
    before = s[i - 1:i]
    if ctx == 'any':
        return True
    if ctx == 'end':
        return j == len(s)
    if ctx == 'coda':
        return before in VOWELS and (not after or after not in VOWELS)
    if ctx == 'before_c':
        return bool(after) and after not in VOWELS
    if ctx == 'between_iv':
        return after in VOWELS
    if ctx == 'before_p':
        return after in ('p', 'm')
    return False


def rule_steps(s, table=None):
    """Variantes de s a un paso de una regla: [(variante, id de regla)]."""
    out = []
    table = table or RULES
    for rid, (a, b, ctx, _, _) in table.items():
        for src, dst in ((a, b), (b, a)):
            start = 0
            while True:
                i = s.find(src, start)
                if i < 0:
                    break
                j = i + len(src)
                probe = s[:i] + dst + s[j:]
                # el contexto se juzga sobre la forma con la alternativa «larga» (a) para que sea simétrico
                long_form, li, lj = (s, i, j) if src == a else (probe, i, i + len(a))
                if _context_ok(ctx, long_form, li, lj):
                    out.append((probe, rid))
                start = i + 1
    return out


def alternates(s, table=None, max_cost=MAX_RULE_COST, limit=MAX_VARIANTS):
    """Lecturas alternativas de s por reglas de perfil: {variante: (costo, [reglas])}, s incluida (costo 0)."""
    table = table or RULES
    best = {s: (0.0, ())}
    frontier = [s]
    while frontier and len(best) < limit:
        nxt = []
        for v in frontier:
            cost, used = best[v]
            for probe, rid in rule_steps(v, table):
                c = cost + table[rid][3]
                if c <= max_cost + 1e-9 and (probe not in best or best[probe][0] > c):
                    best[probe] = (c, used + (rid,))
                    nxt.append(probe)
        frontier = nxt
    return dict(sorted(best.items(), key=lambda x: x[1][0])[:limit])


def deletes(s):
    return {s[:i] + s[i + 1:] for i in range(len(s))}


def load_rules(root=ROOT):
    """Reglas activas, pares minados y decisiones de revisión (archivos versionados)."""
    path = Path(root) / RULES_PATH
    cfg = json.loads(path.read_text(encoding='utf-8')) if path.is_file() else {}
    review = Path(root) / REVIEW_PATH
    rev = json.loads(review.read_text(encoding='utf-8')) if review.is_file() else {}
    return dict(active=set(cfg.get('active', [])), mined=cfg.get('mined_rules', []), pairs=cfg.get('pairs', []),
                decisions=rev.get('decisions', []))


def rule_table(cfg=None):
    """Reglas de perfil más las reglas minadas (``mined_rules`` con estado propuesto o activo)."""
    table = dict(RULES)
    for r in (cfg or {}).get('mined', []):
        if r.get('status') in ('active', 'review') and r['id'] not in table:
            table[r['id']] = (r['a'], r['b'], r.get('context', 'any'), float(r.get('cost', 0.5)), r['label'])
    return table


_ES_WORD = re.compile(r'[^\W\d_]+')


def _es_set(text, es_tokens):
    """Mismas claves que ``stems.es_tokens`` (sin palabras vacías, sin plural regular), plegando el texto una vez."""
    from .stems import ES_STOP
    out = set()
    for n in _ES_WORD.findall(fold(text)):
        if len(n) < 3 or n in ES_STOP:
            continue
        if len(n) > 4 and n.endswith('es') and n[-3] not in 'aeiou':
            n = n[:-2]
        elif len(n) > 3 and n.endswith('s'):
            n = n[:-1]
        out.add(n)
    return out


# ---------------------------------------------------------------------------
# 4. Grafo de equivalencias entre grafías atestiguadas
# ---------------------------------------------------------------------------
EDGE_TYPES = dict(same_key='misma clave (solo cambia la convención ortográfica)',
                  rule='regla de perfil', aligned='las traducciones alineadas coinciden',
                  human='confirmación humana')
ALIGN_TOP = 6
ALIGN_SHARE = 0.3
MIN_GRAPH_SYMBOLS = 3


class Graph:
    """Nodos: claves pivote atestiguadas (cada una con sus grafías originales). Aristas: posibles otras
    grafías de la misma palabra, con tipo y evidencia. Grupos = componentes de las aristas seguras."""

    def __init__(self, postings, rows, dictionary_keys=(), cfg=None, es_tokens=None):
        self.cfg = cfg if cfg is not None else load_rules()
        self.table = rule_table(self.cfg)
        self.active = set(self.cfg.get('active', ()))
        self.postings, self.rows = postings, rows
        self._es_tokens = es_tokens
        # Grafías originales por clave: {clave: {forma: Counter(iso)}}
        self.forms = {}
        self.total = Counter()
        for k, hits in postings.items():
            fc = defaultdict(Counter)
            for rid, w in hits:
                fc[w.casefold()][rows[rid]['iso']] += 1
            self.forms[k] = fc
            self.total[k] = len(hits)
        for k in dictionary_keys:
            self.forms.setdefault(k, {})
        self.sym = {k: symbols(k) for k in self.forms}
        self.by_sym = {s: k for k, s in self.sym.items()}
        self._profiles = {}
        self._df = None
        self.edges = {}
        self._build_edges()

    # -- traducciones alineadas -------------------------------------------
    def _es(self, rid):
        """Palabras españolas de contenido de un pasaje (plegadas una vez por pasaje)."""
        got = self._es_cache.get(rid)
        if got is None:
            got = self._es_cache[rid] = _es_set(self.rows[rid]['es'], self._es_tokens)
        return got

    def _doc_freq(self):
        if self._df is None:
            self._es_cache = {}
            df = Counter()
            for rid in self.rows:
                df.update(self._es(rid))
            self._df = df
        return self._df

    def profile(self, k):
        """Palabras españolas distintivas de los pasajes de una clave: [(palabra, apariciones)]."""
        if k in self._profiles:
            return self._profiles[k]
        hits = self.postings.get(k, [])
        if not hits or self._es_tokens is None:
            self._profiles[k] = []
            return []
        df, n = self._doc_freq(), len(self.rows)
        c = Counter()
        for rid, _ in hits:
            c.update(self._es(rid))
        scored = sorted(((cnt / len(hits)) * math.log(n / (1 + df[t])), t, cnt) for t, cnt in c.items() if df[t] < n / 20)
        top = [(t, cnt) for _, t, cnt in sorted(scored, reverse=True)[:ALIGN_TOP * 2]]
        self._profiles[k] = top
        return top

    def aligned(self, a, b):
        """'agree' si comparten una palabra española distintiva en sus pasajes; 'disagree' si, con
        pasajes suficientes, no comparten ninguna; None si no hay datos. Devuelve (veredicto, palabras)."""
        pa, pb = self.profile(a), self.profile(b)
        if not pa or not pb:
            return None, []
        # Coinciden si una palabra española distintiva está entre las primeras de ambas y aparece en
        # buena parte de los pasajes de cada una (no basta con compartir un texto).
        na, nb = self.total[a], self.total[b]
        ta = {t for t, c in pa[:ALIGN_TOP] if c >= max(1, ALIGN_SHARE * na)}
        tb = {t for t, c in pb[:ALIGN_TOP] if c >= max(1, ALIGN_SHARE * nb)}
        shared = sorted(ta & tb)
        if shared:
            return 'agree', shared[:3]
        wide = {t for t, _ in pa} & {t for t, _ in pb}
        if not wide and self.total[a] >= 3 and self.total[b] >= 3:
            return 'disagree', []
        return None, sorted(wide)[:3]

    # -- aristas ------------------------------------------------------------
    def _add(self, a, b, kind, **evidence):
        key = (a, b) if a < b else (b, a)
        e = self.edges.setdefault(key, dict(a=key[0], b=key[1], types=[], rules=[], cost=None))
        if kind not in e['types']:
            e['types'].append(kind)
        for r in evidence.pop('rules', ()):
            if r not in e['rules']:
                e['rules'].append(r)
        cost = evidence.pop('cost', None)
        if cost is not None:
            e['cost'] = cost if e['cost'] is None else min(e['cost'], cost)
        e.update(evidence)
        return e

    def _build_edges(self):
        for k, s in self.sym.items():
            if len(s) < MIN_GRAPH_SYMBOLS:
                continue
            # Un paso de regla por arista: las cadenas de reglas se recorren por transitividad.
            for v, rid in rule_steps(s, self.table):
                other = self.by_sym.get(v)
                if other and other != k:
                    self._add(k, other, 'rule', rules=[rid], cost=self.table[rid][3])
        for p in self.cfg.get('pairs', []):
            a, b = pivot(p['a']), pivot(p['b'])
            if a in self.forms and b in self.forms and a != b and p.get('status') in ('active', 'review'):
                self._add(a, b, 'aligned', cost=p.get('cost'), mined=p.get('status'), shared=p.get('shared', []))
        self.decisions = {}
        for d in self.cfg.get('decisions', []):
            a, b = pivot(d['a']), pivot(d['b'])
            self.decisions[(a, b) if a < b else (b, a)] = d  # la última decisión manda; «clear» la deshace
        for (a, b), d in self.decisions.items():
            if d['decision'] == 'accept' and a in self.forms and b in self.forms and a != b:
                self._add(a, b, 'human', cost=0.0)
        for key, e in self.edges.items():
            e['status'], e['why'] = self._status(key, e)
        self._clusters()

    def _status(self, key, e):
        d = self.decisions.get(key)
        if d and d['decision'] == 'reject':
            return 'rejected', 'rechazada por revisión humana (%s)' % d.get('by', 'editor')
        if d and d['decision'] == 'accept':
            return 'certain', EDGE_TYPES['human']
        verdict, shared = self.aligned(*key)
        e['translations'] = dict(verdict=verdict, shared=shared)
        if verdict == 'disagree':
            return 'uncertain', 'las traducciones de sus pasajes no coinciden'
        if 'aligned' in e['types'] and e.get('mined') == 'active':
            return 'certain', EDGE_TYPES['aligned'] + ' (par minado y validado)'
        on = [r for r in e['rules'] if r in self.active]
        if 'rule' in e['types'] and on:
            return 'certain', 'regla de perfil activa: ' + '; '.join(self.table[r][4] for r in on)
        if 'rule' in e['types'] and verdict == 'agree' and 'aligned' in self.active:
            return 'certain', 'regla de perfil confirmada por traducciones alineadas («%s»)' % '», «'.join(shared)
        return 'uncertain', 'posible: ' + '; '.join(self.table[r][4] for r in e['rules'] if r in self.table) if e['rules'] \
            else 'posible: par propuesto por la minería (en revisión)'

    def _clusters(self):
        parent = {}

        def find(x):
            while parent.get(x, x) != x:
                parent[x] = parent.get(parent[x], parent[x])
                x = parent[x]
            return x
        for (a, b), e in self.edges.items():
            if e['status'] == 'certain':
                parent.setdefault(a, a)
                parent.setdefault(b, b)
                ra, rb = find(a), find(b)
                if ra != rb:
                    parent[ra] = rb
        groups = defaultdict(list)
        for k in parent:
            groups[find(k)].append(k)
        self.cluster_of = {}
        for members in groups.values():
            members = sorted(members, key=lambda k: (-self.total[k], k))
            for k in members:
                self.cluster_of[k] = members
        self.neighbors = defaultdict(list)
        for key, e in self.edges.items():
            self.neighbors[key[0]].append(e)
            self.neighbors[key[1]].append(e)

    def cluster(self, k):
        """Claves de la misma palabra (aristas seguras), la más atestiguada primero."""
        return self.cluster_of.get(k, [k])

    def uncertain(self, k):
        """Aristas inciertas que salen del grupo de k (otras grafías posibles, aparte)."""
        members = set(self.cluster(k))
        return [e for m in members for e in self.neighbors.get(m, ())
                if e['status'] == 'uncertain' and not ({e['a'], e['b']} <= members)]

    def edge_list(self, k):
        members = set(self.cluster(k))
        return [e for m in sorted(members) for e in self.neighbors.get(m, ())]

    def surfaces(self, k):
        out = [dict(form=f, total=sum(c.values()), by_variety={LABELS.get(i, i): n for i, n in c.most_common()},
                    varieties=[i for i, _ in c.most_common()])
               for f, c in self.forms.get(k, {}).items()]
        out.sort(key=lambda v: (-v['total'], v['form']))
        return out


# ---------------------------------------------------------------------------
# 5. Búsqueda tolerante
# ---------------------------------------------------------------------------
HOW = dict(pivot='misma forma pivote (otra convención ortográfica)', rule='regla de perfil',
           edit='grafía parecida (posible error o variante)', root='misma raíz según el analizador (forma flexionada)')
MAX_EDIT = 2.0
EVIDENCE_WEIGHT = 0.2   # orden: costo − peso · log10(1 + apariciones) − entrada del diccionario


def _confidence(cost):
    value = round(max(0.05, 1 - cost / 2.2), 2)
    return dict(value=value, label='alta' if cost <= 0.3 else 'media' if cost <= 0.8 else 'baja')


def _snippet(text, limit=110):
    text = ' '.join((text or '').split())
    return text if len(text) <= limit else text[:limit].rsplit(' ', 1)[0] + '…'


class Search:
    """Búsqueda de grafías sobre un ``terms.TermIndex`` ya construido (o perezoso)."""

    def __init__(self, terms, cfg=None):
        self.terms = terms
        self.cfg = cfg
        self._lock = Lock()
        self._ready = False

    def _build(self):
        with self._lock:
            if self._ready:
                return
            ti = self.terms
            ti._build()
            from .stems import es_tokens
            # El grafo del índice de términos, salvo que se pida otra configuración (minería, pruebas).
            shared = getattr(ti, 'graph', None)
            self.graph = shared if shared is not None and self.cfg is None else Graph(
                ti.postings, ti.rows, ti.spelling_owner.keys(), cfg=self.cfg, es_tokens=es_tokens)
            g = self.graph
            self.index = defaultdict(set)   # borrado de un símbolo → claves
            for k, s in g.sym.items():
                if len(s) >= 2:
                    self.index[s].add(k)
                    for d in deletes(s):
                        self.index[d].add(k)
            self.glyph_keys = Counter()
            for e in ti.elements.values():
                self.glyph_keys[e['key']] += 1
            from .morphology import WORD
            for o in ti.pictography['occurrences']:
                for w in WORD.findall(o['reading']):
                    self.glyph_keys[loose_key(w)] += 1
            forms_by_iso = defaultdict(Counter)
            for k, fc in g.forms.items():
                for f, c in fc.items():
                    for iso, n in c.items():
                        forms_by_iso[iso][f] += n
            self.traits = variety_traits(forms_by_iso)
            self._words = {}
            self._ready = True

    def reload(self):
        """Rehace el grafo tras una decisión de revisión (las reglas y decisiones se releen del disco)."""
        from .stems import es_tokens
        ti = self.terms
        with self._lock:
            self._ready = False
            if getattr(ti, 'graph', None) is not None:
                with ti._lock:
                    ti.graph = Graph(ti.postings, ti.rows, ti.spelling_owner.keys(), es_tokens=es_tokens)
                    ti._groups.clear()
        self._build()

    # -- de clave a palabra -----------------------------------------------
    def word_of(self, k):
        """Palabra de una clave: (id de grupo, vía). Vía: spelling (entrada con esta grafía), graph (otra
        grafía segura de la entrada), root (forma flexionada de una entrada), archive (solo el archivo)."""
        if k in self._words:
            return self._words[k]
        ti, g = self.terms, self.graph
        out = None
        if ti.spelling_owner.get(k):
            out = (ti.spelling_owner[k][0], 'spelling', None)
        else:
            for m in g.cluster(k):
                if ti.spelling_owner.get(m):
                    out = (ti.spelling_owner[m][0], 'graph', m)
                    break
        if out is None:
            rep = g.cluster(k)[0]
            surf = g.surfaces(rep)
            a = ti.analyzer.analyze(surf[0]['form'], limit=1) if surf else []
            if a and a[0]['class_'] != 'foreign' and a[0]['basis'] == 'dictionary':
                for gid in ti.stem_owner.get(a[0]['stem_key'], []):
                    info = ti.lexicon[gid]
                    if ti._certainty(a[0], gid, info['stem'], {s['id'] for s in info['entry']['senses']}) is None:
                        out = (gid, 'root', a[0]['segmentation'])
                        break
            if out is None:
                out = (ti._archive_id(rep), 'archive', None)
        self._words[k] = out
        return out

    def _word_keys(self, gid):
        ti, g = self.terms, self.graph
        if gid in ti.lexicon:
            keys = []
            for k in ti.lexicon[gid]['keys']:
                for m in g.cluster(k):
                    if m not in keys:
                        keys.append(m)
            return keys
        return list(g.cluster(ti.archive_ids[gid]))

    def word(self, gid):
        """Identidad y evidencia breve de una palabra: lema, grafías atestiguadas, entradas, glifos, ejemplo."""
        ti, g = self.terms, self.graph
        keys = self._word_keys(gid)
        spellings = []
        for k in keys:
            for v in g.surfaces(k):
                spellings.append(dict(v, key=k))
        spellings.sort(key=lambda v: (-v['total'], v['form']))
        total = sum(v['total'] for v in spellings)
        varieties = Counter()
        for v in spellings:
            varieties.update(v['by_variety'])
        entry = ti.lexicon[gid]['entry'] if gid in ti.lexicon else None
        glyphs = (len(entry['glyphs']) if entry else 0) + sum(self.glyph_keys[k] for k in keys)
        return dict(id=gid, source='dictionary' if entry else 'archive',
                    lemma=entry['lemma'] if entry else (spellings[0]['form'] if spellings else readable_key(keys[0])),
                    senses=[dict(id=s['id'], label=s.get('label')) for s in entry['senses'][:3]] if entry else [],
                    dictionary_spellings=sorted(entry['spellings'], key=fold) if entry else [],
                    spellings=spellings[:8], spellings_total=len(spellings), total=total,
                    by_variety=dict(varieties.most_common()), glyphs=glyphs, keys=keys)

    def example(self, k, form=None):
        """Un pasaje de ejemplo de la clave (con la grafía pedida si existe)."""
        hits = self.graph.postings.get(k, [])
        pick = next((rid for rid, w in hits if form and w.casefold() == form), hits[0][0] if hits else None)
        if not pick:
            return None
        r = self.terms.rows[pick]
        return dict(id=pick, nah=_snippet(r['nah']), es=_snippet(r['es']), variety=LABELS.get(r['iso'], r['iso']))

    # -- candidatos -----------------------------------------------------------
    def matches(self, word):
        """Claves candidatas para una palabra escrita: {clave: (costo, vía, reglas)}."""
        g = self.graph
        s = symbols(pivot(word))
        found = {}

        def keep(k, cost, how, rules=()):
            if k not in found or cost < found[k][0] - 1e-9:
                found[k] = (round(cost, 3), how, tuple(rules))
        if not s:
            return found
        variants = alternates(s, g.table)
        for v, (cost, used) in variants.items():
            k = g.by_sym.get(v)
            if k:
                keep(k, cost, 'pivot' if not used else 'rule', used)
        cap = min(MAX_EDIT, 0.35 * len(s) + 0.2)
        pool = set()
        for v, (cost, _) in list(variants.items())[:12]:
            for d in deletes(v) | {v}:
                pool |= self.index.get(d, set())
        for k in pool:
            if k in found and found[k][0] == 0:
                continue
            d = distance(s, g.sym[k], cap)
            if d <= cap:
                keep(k, d, 'edit')
        return found

    def search(self, query, limit=6):
        """Posibilidades para lo que alguien escribió, con fuentes, motivo y confianza."""
        from .terms import parse
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 30:
            raise ValueError('limit debe ser un entero entre 1 y 30.')
        self._build()
        word, _ = parse(query)
        ti, g = self.terms, self.graph
        typed = word.casefold()
        lk = pivot(word)
        attested = any(typed == f for f in g.forms.get(lk, {}))
        in_dictionary = bool(ti.spelling_owner.get(lk)) and any(
            typed == s.casefold() for gid in ti.spelling_owner[lk] for s in ti.lexicon[gid]['entry']['spellings'])
        words = {}

        def offer(gid, cost, how, key, rules=(), via=None, detail=None):
            prev = words.get(gid)
            if prev is None or cost < prev['cost'] - 1e-9:
                words[gid] = dict(cost=cost, how=how, key=key, rules=list(rules), via=via, detail=detail)
        for k, (cost, how, rules) in self.matches(word).items():
            gid, via, detail = self.word_of(k)
            # Pasar de una grafía a su palabra por otra grafía segura o por la raíz cuesta un poco.
            offer(gid, cost + (0.05 if via == 'graph' else 0.25 if via == 'root' else 0), how, k, rules, via, detail)
        a = ti.analyzer.analyze(word, limit=1)
        if a and a[0]['class_'] != 'foreign' and a[0]['basis'] == 'dictionary' and len(a[0]['stem_key']) >= 3:
            for gid in ti.stem_owner.get(a[0]['stem_key'], []):
                info = ti.lexicon[gid]
                reason = ti._certainty(a[0], gid, info['stem'], {s['id'] for s in info['entry']['senses']})
                offer(gid, 0.35 if reason is None else 1.0, 'root', None, (), 'root', a[0]['segmentation'])
        ranked = []
        for gid, m in words.items():
            info = self.word(gid)
            evidence = math.log10(1 + info['total']) * EVIDENCE_WEIGHT + (0.05 if info['source'] == 'dictionary' else 0)
            ranked.append((m['cost'] - evidence, gid, m, info))
        ranked.sort(key=lambda x: (x[0], x[1]))
        out = []
        for _, gid, m, info in ranked[:limit]:
            matched = g.surfaces(m['key'])[0]['form'] if m['key'] and g.surfaces(m['key']) else None
            out.append(dict(info, keys=None, match=dict(
                how=m['how'], label=HOW[m['how']], form=matched, cost=m['cost'],
                confidence=_confidence(m['cost']), via=m['via'], segmentation=m['detail'] if m['via'] == 'root' else None,
                rules=[dict(id=r, label=g.table[r][4], active=r in g.active) for r in m['rules']],
                why=self._why(word, m, matched, info)),
                example=self.example(m['key'], matched) if m['key'] else None))
        return dict(query=query.strip(), word=word, pivot=lk, attested=attested, in_dictionary=in_dictionary,
                    note=None if attested or in_dictionary else
                    '«%s» no aparece tal cual en el archivo ni en el diccionario: se proponen grafías atestiguadas '
                    'cercanas. Ninguna es una corrección; son posibilidades.' % word,
                    profiles=convert(word), candidates=out, total=len(ranked), limit_note=LIMIT_NOTE,
                    method=dict(version=SPELLING_VERSION, pipeline='pivote → reglas de perfil → distancia → raíz', model_calls=0))

    def _why(self, word, m, matched, info):
        parts = []
        if m['how'] == 'pivot':
            parts.append('«%s» y «%s» son la misma forma en otra convención ortográfica' % (word, matched)
                         if matched and matched != word.casefold() else 'grafía atestiguada tal cual')
        elif m['how'] == 'rule':
            parts.append('«%s» → «%s» por %s' % (word, matched, '; '.join(self.graph.table[r][4] for r in m['rules'])))
        elif m['how'] == 'edit':
            parts.append('«%s» se parece a «%s» (distancia %.2f): posible error o variante' % (word, matched, m['cost']))
        else:
            parts.append('el analizador lee «%s» como %s, forma de «%s»' % (word, m['detail'], info['lemma']))
        if m['via'] == 'graph':
            parts.append('«%s» es otra grafía segura de «%s»' % (matched, info['lemma']))
        elif m['via'] == 'root' and m['how'] != 'root':
            parts.append('«%s» es forma flexionada de «%s» (%s)' % (matched, info['lemma'], m['detail']))
        return '; '.join(parts)

    # -- vista «Grafías» --------------------------------------------------------
    def detail(self, gid):
        """Vista de una palabra: conversor de perfiles, grafías por variedad con pasajes, motivo de cada asociación."""
        self._build()
        g = self.graph
        info = self.word(gid)
        keys = info['keys']
        base = info['dictionary_spellings'][0] if info['dictionary_spellings'] else info['lemma']
        varieties = {iso: t for iso, t in self.traits.items()}
        spellings = []
        for k in keys:
            for v in g.surfaces(k):
                spellings.append(dict(v, key=k, example=self.example(k, v['form'])))
        spellings.sort(key=lambda v: (-v['total'], v['form']))
        unique = {(e['a'], e['b']): e for k in keys for e in g.edge_list(k)}
        edges = [self._edge_view(e) for _, e in sorted(unique.items())]
        loose = {(e['a'], e['b']): e for e in (g.uncertain(keys[0]) if keys else [])}
        uncertain = [self._edge_view(e) for _, e in sorted(loose.items())]
        return dict(id=gid, lemma=info['lemma'], source=info['source'], senses=info['senses'],
                    profiles=convert(base, varieties=varieties), limit_note=LIMIT_NOTE,
                    spellings=spellings, edges=[e for e in edges if e['status'] != 'uncertain'],
                    uncertain=[e for e in uncertain], total=info['total'], by_variety=info['by_variety'],
                    glyphs=info['glyphs'], dictionary_spellings=info['dictionary_spellings'])

    def _edge_view(self, e):
        g = self.graph
        fa, fb = g.surfaces(e['a']), g.surfaces(e['b'])
        return dict(a=fa[0]['form'] if fa else unsymbols(e['a']), b=fb[0]['form'] if fb else unsymbols(e['b']),
                    types=[EDGE_TYPES[t] for t in e['types']], kinds=list(e['types']), status=e['status'], why=e['why'],
                    rules=[dict(id=r, label=g.table[r][4], active=r in g.active) for r in e['rules'] if r in g.table],
                    translations=e.get('translations'), cost=e['cost'])


def readable_key(k):
    from .text import readable
    return readable(k)


# ---------------------------------------------------------------------------
# 6. Revisión humana (reversible) y rutas
# ---------------------------------------------------------------------------
DECISIONS = ('accept', 'reject', 'clear')


def record_decision(a, b, decision, by, note='', root=ROOT, when=None):
    """Añade una decisión de editor sobre un par de grafías. La última por par manda; 'clear' la deshace."""
    if decision not in DECISIONS:
        raise ValueError('Decisión desconocida: usa accept, reject o clear.')
    a, b = fold(str(a)).strip(), fold(str(b)).strip()
    if not a or not b or pivot(a) == pivot(b):
        raise ValueError('Indica dos grafías distintas.')
    path = Path(root) / REVIEW_PATH
    data = json.loads(path.read_text(encoding='utf-8')) if path.is_file() else dict(
        version='spelling-review-v1', note='Decisiones de editores sobre pares de grafías. Solo se añaden; '
        'la última decisión de cada par manda y «clear» la deshace.', decisions=[])
    import datetime
    data['decisions'].append(dict(a=a, b=b, decision=decision, by=str(by)[:120], note=str(note)[:500],
                                  at=when or datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')))
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    return data['decisions'][-1]


def queue(cfg=None, limit=50):
    """Cola de revisión: reglas y pares minados que no pasaron la compuerta y siguen sin decisión."""
    cfg = cfg or load_rules()
    decided = {(pivot(d['a']), pivot(d['b'])) for d in cfg['decisions']} | {(pivot(d['b']), pivot(d['a'])) for d in cfg['decisions']}
    pairs = [p for p in cfg['pairs'] if (pivot(p['a']), pivot(p['b'])) not in decided]
    return dict(rules=[r for r in cfg['mined'] if r.get('status') == 'review'][:limit], pairs=pairs[:limit],
                total_pairs=len(pairs), decisions=cfg['decisions'][-limit:])


def routes(router, search, problem, person=None):
    """/api/spellings (sugerencias), /api/spellings/word (vista Grafías), /api/spellings/review (editores)."""
    def suggest(request):
        try:
            return request.reply(search.search(request.arg('q'), limit=int(request.arg('limit', 6))))
        except ValueError as error:
            raise problem(str(error)) from None

    def word(request):
        try:
            return request.reply(search.detail(request.arg('id')))
        except KeyError:
            raise problem('Palabra no encontrada.', 404) from None

    def review_queue(request):
        return request.reply(queue())

    def review(request):
        who = person(request) if person else 'editor'
        body = request.body()
        try:
            d = record_decision(body.get('a'), body.get('b'), body.get('decision'), who, body.get('note', ''))
        except ValueError as error:
            raise problem(str(error)) from None
        search.reload()
        return request.reply(d, 201)
    router.add('GET', '/api/spellings', suggest)
    router.add('GET', '/api/spellings/word', word)
    router.add('GET', '/api/spellings/review', review_queue)
    router.add('POST', '/api/spellings/review', review)
