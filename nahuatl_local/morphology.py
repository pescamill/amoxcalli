"""Analizador morfológico transparente para náhuatl clásico (solo stdlib).

Por qué existe
--------------
El náhuatl es polisintético: «nocal» (mi casa), «calco» (en la casa) y «calli»
(casa) comparten la raíz *cal*, pero una búsqueda por palabra completa nunca los
relaciona. Este módulo propone segmentaciones (prefijos + raíz + sufijos),
las vincula con entradas del diccionario del proyecto y explica cada morfema.

Diseño
------
1. **Clave fonémica** (``phonemic_key``): neutraliza variación ortográfica
   colonial (qu/c/k, hu/uh/u/v, z/ç/c, h saltillo, y/i, vocales dobles) y
   conserva, para cada fonema, el tramo de la grafía original. Así la
   segmentación se muestra en la escritura de la fuente.
2. **Generación de candidatos**: gramática de posiciones (prefijos de poseedor,
   sujeto, objeto, reflexivo, direccional, antecesivo; sufijos nominales,
   relacionales y verbales) con restricciones de alomorfía.
3. **Puntuación**: coincidencia con raíces del diccionario > frecuencia de la
   raíz en el corpus (estimada por EM duro sobre los tipos del archivo) >
   parsimonia (cada afijo cuesta). Cada análisis declara su ``basis``.

Límites declarados
------------------
Las tablas de afijos y partículas fueron compiladas a partir de gramáticas de
referencia (p. ej. Andrews, *Introduction to Classical Nahuatl*, 2003; Launey,
*Introducción a la lengua y a la literatura náhuatl*, 1992) por el equipo del
proyecto y siguen **pendientes de revisión especializada**. No modela
reduplicación, compuestos de más de dos raíces, longitud vocálica ni todos los
pretéritos irregulares. Un análisis es una hipótesis de lectura, no una
traducción: la interfaz siempre lo presenta así.
"""
import json
import math
import re
import unicodedata
from collections import Counter, defaultdict
from functools import lru_cache

ANALYZER_VERSION = 'nah-morph-1'
VOWELS = set('aeio')

# --------------------------------------------------------------------------
# 1. Clave fonémica con alineación a la grafía original
# --------------------------------------------------------------------------
# Símbolos de un carácter: č=ch, ʦ=tz, λ=tl, q=kw. El resto son letras latinas.
DISPLAY = {'č': 'ch', 'ʦ': 'tz', 'λ': 'tl', 'q': 'kw'}


def _base(text):
    """Minúsculas, sin marcas diacríticas; ç→s, v→u (ortografía colonial).

    «j» se conserva: en el corpus clásico de Axolotl aparece casi solo en
    préstamos y nombres (Juan, justicia, juez), que se marcan como tales."""
    out = []
    for ch in unicodedata.normalize('NFC', text):
        low = ch.casefold()
        if low == 'ç':
            out.append('s')
            continue
        decomposed = unicodedata.normalize('NFD', low)
        base = ''.join(c for c in decomposed if unicodedata.category(c) != 'Mn') or low
        base = {'v': 'u'}.get(base, base)
        out.append(base[:1])  # un carácter de salida por carácter de entrada
    return ''.join(out)


def phonemic_key(word):
    """Devuelve (clave, tramos). ``tramos[i]`` es (inicio, fin) en ``word``.

    >>> phonemic_key('niquitta')[0]
    'nikitta'
    >>> phonemic_key('yhuan')[0] == phonemic_key('ihuan')[0] == phonemic_key('iuan')[0]
    True
    """
    s = _base(word)
    n = len(s)
    key, spans = [], []

    lead = None  # «h» inicial: se une al primer símbolo

    def emit(sym, start, end):
        nonlocal lead
        if lead is not None and not spans:
            start, lead = 0, None
        key.append(sym)
        spans.append([start, end])

    def is_v(i):
        return 0 <= i < n and s[i] in 'aeiou'

    i = 0
    while i < n:
        c = s[i]
        nxt = s[i + 1] if i + 1 < n else ''
        if c == 'c' and nxt == 'h':
            emit('č', i, i + 2); i += 2; continue
        if c == 't' and nxt == 'z':
            emit('ʦ', i, i + 2); i += 2; continue
        if c == 't' and nxt == 'l':
            emit('λ', i, i + 2); i += 2; continue
        if c == 'q' and nxt == 'u':
            after = s[i + 2] if i + 2 < n else ''
            if after in ('e', 'i'):
                emit('k', i, i + 2); i += 2; continue
            emit('q', i, i + 2); i += 2; continue          # qua/quo = kw
        if c == 'c' and nxt == 'u' and is_v(i + 2):
            emit('q', i, i + 2); i += 2; continue          # cua/cui = kw
        if c == 'u' and nxt == 'c' and i > 0 and is_v(i - 1) and not is_v(i + 2) and s[i + 2:i + 3] != 'h':
            emit('q', i, i + 2); i += 2; continue          # teuctli = tekw-tli
        if c == 'h' and nxt == 'u' and is_v(i + 2):
            emit('w', i, i + 2); i += 2; continue          # hua = wa
        if c == 'u' and nxt == 'h' and i > 0 and is_v(i - 1):
            emit('w', i, i + 2); i += 2; continue          # -uh = w
        if c == 'u' and is_v(i + 1) and (i == 0 or is_v(i - 1) or s[i - 1] not in 'qg'):
            emit('w', i, i + 1); i += 1; continue          # uel = wel, xiuitl = xiwitl
        if c == 'c':
            emit('s' if nxt in ('e', 'i') else 'k', i, i + 1); i += 1; continue
        if c == 'z':
            emit('s', i, i + 1); i += 1; continue
        if c == 'h':
            # Saltillo u «h» ortográfica: se omite; su tramo se une al símbolo vecino.
            if spans:
                spans[-1][1] = i + 1
            else:
                lead = i + 1 if lead is None else lead
            i += 1; continue
        if c == 'y':
            emit('y' if is_v(i + 1) else 'i', i, i + 1); i += 1; continue
        if c == 'u':
            emit('o', i, i + 1); i += 1; continue          # u vocálica = o
        if c == 'k':
            emit('k', i, i + 1); i += 1; continue
        emit(c, i, i + 1); i += 1

    # vocales dobles (longitud) → una sola, uniendo tramos
    out_k, out_s = [], []
    for sym, sp in zip(key, spans):
        if out_k and sym in VOWELS and out_k[-1] == sym:
            out_s[-1][1] = sp[1]
            continue
        out_k.append(sym); out_s.append(sp)
    # w deslizante entre o y vocal: tlahtohua = tlahtoa, itohua = itoa
    k2, s2 = [], []
    j = 0
    while j < len(out_k):
        if out_k[j] == 'w' and k2 and k2[-1] == 'o' and j + 1 < len(out_k) and out_k[j + 1] in VOWELS:
            s2[-1][1] = out_s[j][1]
            j += 1
            continue
        k2.append(out_k[j]); s2.append(out_s[j]); j += 1
    return ''.join(k2), [tuple(x) for x in s2]


def key_of(word):
    return phonemic_key(word)[0]


def readable(key):
    """Clave fonémica legible (ch, tz, tl, kw)."""
    return ''.join(DISPLAY.get(c, c) for c in key)


# --------------------------------------------------------------------------
# 2. Inventario de morfemas (claves fonémicas)
# --------------------------------------------------------------------------
# (id, clave, etiqueta Leipzig, glosa española, clase)
PREFIXES = {
    'ANT': [('o', 'ANT', 'pasado (antecesivo)')],
    'NEG': [('a', 'NEG', 'no (negación)')],
    'SUBJ': [('ni', '1SG.S', 'yo (sujeto)'), ('ti', '2SG/1PL.S', 'tú / nosotros (sujeto)'),
             ('an', '2PL.S', 'ustedes (sujeto)'), ('am', '2PL.S', 'ustedes (sujeto)'),
             ('n', '1SG.S', 'yo (sujeto, ante vocal)'), ('t', '2SG/1PL.S', 'tú / nosotros (sujeto, ante vocal)')],
    'DIR': [('on', 'DIR.ALLÁ', 'hacia allá'), ('wal', 'DIR.ACÁ', 'hacia acá')],
    'OBJ': [('neč', '1SG.O', 'a mí'), ('miʦ', '2SG.O', 'a ti'), ('ki', '3SG.O', 'lo / la'),
            ('k', '3SG.O', 'lo / la'), ('kin', '3PL.O', 'los / las'), ('kim', '3PL.O', 'los / las'),
            ('teč', '1PL.O', 'a nosotros'), ('ameč', '2PL.O', 'a ustedes'),
            ('te', 'INDF.HUM.O', 'a alguien'), ('λa', 'INDF.O', 'algo')],
    'REFL': [('no', '1SG.REFL', 'me (reflexivo)'), ('mo', '2/3.REFL', 'se / te (reflexivo)'),
             ('to', '1PL.REFL', 'nos (reflexivo)'), ('ne', 'IMPERS.REFL', 'se (reflexivo impersonal)'),
             ('m', '2/3.REFL', 'se (reflexivo, ante vocal)')],
    'POSS': [('no', '1SG.POS', 'mi'), ('mo', '2SG.POS', 'tu'), ('i', '3SG.POS', 'su (de él / ella)'),
             ('to', '1PL.POS', 'nuestro'), ('amo', '2PL.POS', 'de ustedes'), ('in', '3PL.POS', 'su (de ellos)'),
             ('im', '3PL.POS', 'su (de ellos)'), ('te', 'INDF.POS', 'de alguien'),
             ('n', '1SG.POS', 'mi (ante vocal)'), ('m', '2SG.POS', 'tu (ante vocal)'),
             ('t', '1PL.POS', 'nuestro (ante vocal)'), ('am', '2PL.POS', 'de ustedes (ante vocal)')],
}
BEFORE_VOWEL_ONLY = {('SUBJ', 'n'), ('SUBJ', 't'), ('REFL', 'm'), ('POSS', 'n'), ('POSS', 'm'),
                     ('POSS', 't'), ('POSS', 'am')}

# Sufijos nominales
N_DERIV = [('ʦin', 'REV/DIM', 'reverencial o diminutivo'), ('ton', 'DIM', 'diminutivo'),
           ('yo', 'ABST', 'cualidad, lo propio de'), ('kayo', 'ABST', 'cualidad, lo propio de'),
           ('lis', 'NMLZ.ACC', 'acción de (nominalizador)'), ('l', 'NMLZ.PAT', 'lo que es objeto de la acción'),
           ('ni', 'AGT', 'el que (agentivo)'), ('ka', 'GENT', 'gentilicio / de'),
           ('teka', 'GENT', 'gentilicio / de'), ('w', 'POSSR', 'dueño de'), ('e', 'POSSR', 'que tiene')]
N_ABS = [('λ', 'ABS', 'absolutivo (sin poseedor)'), ('λi', 'ABS', 'absolutivo (sin poseedor)'),
         ('li', 'ABS', 'absolutivo (sin poseedor)'), ('in', 'ABS', 'absolutivo (sin poseedor)'),
         ('', 'ABS', '')]
N_ABS_PL = [('me', 'PL', 'plural'), ('tin', 'PL', 'plural'), ('tke', 'PL', 'plural'), ('ke', 'PL', 'plural')]
N_POSS_SG = [('w', 'POSD', 'poseído'), ('wi', 'POSD', 'poseído'), ('yo', 'POSD.INAL', 'poseído (inalienable)'),
             ('', 'POSD', '')]
N_POSS_PL = [('wan', 'POSD.PL', 'poseído plural')]
RELATIONAL = [('ko', 'LOC', 'en (lugar)'), ('k', 'LOC', 'en (lugar)'), ('pan', 'LOC.SUPER', 'en, sobre'),
              ('λan', 'LOC.JUNTO', 'junto a, entre'), ('nawak', 'LOC.CERCA', 'cerca de'),
              ('teč', 'REL.CONTACTO', 'en, junto a, acerca de'), ('λok', 'REL.CERCA', 'junto a'),
              ('kpak', 'REL.ENCIMA', 'encima de'), ('ikpak', 'REL.ENCIMA', 'encima de'),
              ('itik', 'REL.DENTRO', 'dentro de'), ('pampa', 'REL.CAUSA', 'por, a causa de'),
              ('ka', 'REL.INSTR', 'con, por medio de'), ('pal', 'REL.MEDIO', 'por medio de'),
              ('wik', 'REL.HACIA', 'hacia'), ('ʦalan', 'REL.ENTRE', 'entre'), ('tiλan', 'REL.HACIA', 'hacia, junto a'),
              ('kan', 'LOC.LUGAR', 'lugar donde'), ('yan', 'LOC.LUGAR', 'lugar donde'),
              ('teč-kopa', 'REL', 'acerca de')]
# Sufijos verbales
V_DERIV = [('lia', 'APPL', 'a / para (aplicativo)'), ('tia', 'CAUS', 'hacer que (causativo)'),
           ('lo', 'PASS', 'pasiva'), ('wa', 'IMPERS', 'impersonal / pasiva')]
V_TENSE = [('', 'PRS', ''), ('s', 'FUT', 'futuro'), ('ske', 'FUT.PL', 'futuro plural'),
           ('ya', 'IMPF', 'imperfecto'), ('ka', 'PLUPERF', 'pluscuamperfecto'),
           ('k', 'PRET', 'pretérito'), ('ke', 'PRET.PL', 'pretérito plural'),
           ('ki', 'PRET', 'pretérito'), ('ni', 'CUST', 'habitual'), ('skia', 'COND', 'condicional'),
           ('kiw', 'PURP', 'viene a / va a (propósito)'), ('to', 'PURP', 'va a (propósito)'),
           ('tiw', 'PURP', 'va a (propósito)'), ('tok', 'PROG', 'está (progresivo)')]
# Costes extra de afijos raros o ambiguos (clave: (posición, forma)).
RARE = {('ABS', 'in'): 1.2, ('ABS', ''): 0.6, ('POSD', ''): 0.2, ('V', 'wa'): 0.9, ('T', 'ki'): 0.8,
        ('T', 'to'): 0.8, ('T', 'tiw'): 0.6, ('T', 'tok'): 0.6, ('T', 'kiw'): 0.6, ('T', 'ka'): 1.0,
        ('N', 'w'): 1.0, ('N', 'e'): 1.2, ('N', 'ka'): 0.8, ('N', 'teka'): 0.6, ('PRE', 'a'): 1.5,
        ('REL', 'ka'): 0.6, ('REL', 'k'): 0.6, ('PL', 'ke'): 0.8, ('PL', 'tke'): 0.4}

# Partículas y pronombres frecuentes (forma entera, sin segmentar).
# Glosas resumidas de gramáticas de referencia; pendientes de revisión.
_PARTICLE_LIST = [
    ('in', 'DET/SUB', 'el, la, lo; que (artículo / subordinante)'),
    ('auh', 'CONJ', 'y, pero (conjunción)'),
    ('ye', 'ADV', 'ya'),
    ('ca', 'PTCL', 'pues, en verdad (afirmativo)'),
    ('inic', 'SUB', 'con lo cual; para que; ordinal'),
    ('ihuan', 'CONJ', 'y, con'),
    ('yoan', 'CONJ', 'y, con (grafía antigua de ihuan)'),
    ('oncan', 'ADV', 'allí'),
    ('niman', 'ADV', 'luego, enseguida'),
    ('nima', 'ADV', 'luego (grafía abreviada de niman)'),
    ('ic', 'ADV', 'entonces; con ello'),
    ('ma', 'OPT', 'que, ojalá (exhortativo)'),
    ('nican', 'ADV', 'aquí'),
    ('zan', 'ADV', 'solamente; pero'),
    ('za', 'ADV', 'solamente (grafía abreviada)'),
    ('huel', 'ADV', 'bien, muy; poder'),
    ('no', 'ADV', 'también'),
    ('ompa', 'ADV', 'allá'),
    ('oc', 'ADV', 'todavía, aún; más'),
    ('axcan', 'ADV', 'ahora'),
    ('iuh', 'ADV', 'así'),
    ('iuhqui', 'ADV', 'así, como'),
    ('cenca', 'ADV', 'mucho, muy'),
    ('ixquich', 'QNT', 'todo, tanto'),
    ('ayac', 'PRO', 'nadie'),
    ('iquac', 'SUB', 'cuando'),
    ('azo', 'ADV', 'quizá'),
    ('cuix', 'Q', '¿acaso? (interrogativo)'),
    ('intla', 'SUB', 'si (condicional)'),
    ('nel', 'ADV', 'en verdad; pero'),
    ('tle', 'Q', '¿qué?'),
    ('tlein', 'Q', '¿qué?; lo que'),
    ('aquin', 'Q', '¿quién?'),
    ('amo', 'NEG', 'no'),
    ('ayamo', 'NEG', 'todavía no'),
    ('quemaca', 'ADV', 'sí'),
    ('quenin', 'Q', '¿cómo?'),
    ('can', 'Q', '¿dónde?; lugar'),
    ('canin', 'Q', '¿dónde?'),
    ('ihcon', 'ADV', 'así'),
    ('yehuatl', 'PRO', 'él, ella; ése'),
    ('yehua', 'PRO', 'él, ella; ése'),
    ('yehuantin', 'PRO', 'ellos, ellas'),
    ('nehuatl', 'PRO', 'yo'),
    ('tehuatl', 'PRO', 'tú'),
    ('tehuantin', 'PRO', 'nosotros'),
    ('amehuantin', 'PRO', 'ustedes'),
    ('mochi', 'QNT', 'todo'),
    ('ce', 'NUM', 'uno'),
    ('ome', 'NUM', 'dos'),
    ('yei', 'NUM', 'tres'),
    ('nahui', 'NUM', 'cuatro'),
    ('catca', 'V.IRR', 'estaba, era (pretérito de cah)'),
    ('cah', 'V.IRR', 'está, es'),
    ('tel', 'CONJ', 'pero'),
    ('inin', 'DEM', 'este, esta'),
    ('inon', 'DEM', 'ese, esa'),
    ('o', 'PTCL', '¡oh! / ya (antecesivo suelto)'),
    ('tla', 'SUB', 'si (condicional)'),
    ('ipampa', 'REL', 'por eso, a causa de ello'),
]
PARTICLES = {}
for _surface, _tag, _gloss in _PARTICLE_LIST:
    PARTICLES.setdefault(key_of(_surface), (_surface, _tag, _gloss))
# Préstamos y nombres: letras ajenas a la ortografía náhuatl colonial.
FOREIGN = re.compile(r'[bdfgjrñ]|s[^a-z]?$|^s|ss')


# --------------------------------------------------------------------------
# 3. Léxico de raíces a partir de los registros del diccionario
# --------------------------------------------------------------------------
def _lemma_stems(key, noun_hint):
    """Raíces candidatas de una entrada de diccionario (clave fonémica)."""
    stems = []
    if key.endswith('λi') and len(key) > 3 and key[-3] not in VOWELS:
        stems.append((key[:-2], 'sin absolutivo -tli'))
    elif key.endswith('lli') and len(key) > 3:
        stems.append((key[:-2], 'sin absolutivo -li'))
    elif key.endswith('λ') and len(key) >= 2 and key[-2] in VOWELS:
        stems.append((key[:-1], 'sin absolutivo -tl'))
    elif key.endswith('in') and noun_hint and len(key) > 3:
        stems.append((key[:-2], 'sin absolutivo -in'))
    # Sin sufijo absolutivo reconocible (verbos, adjetivos): la entrada completa es la raíz.
    return stems or [(key, 'entrada completa')]


PRETERIT = re.compile(r'pret(?:erit)?[a-z]*\s*[:.]?\s*(o[a-zçñ]+)', re.I)


class Lexicon:
    """Índice clave fonémica → entradas (forma + acepción) del diccionario público."""

    def __init__(self, records):
        records = records.values() if isinstance(records, dict) else records
        by_id = {r['id']: r for r in records}
        self.stems = defaultdict(list)
        self.whole = defaultdict(list)
        self.entries = 0
        for form in by_id.values():
            if form.get('kind') != 'form' or not form.get('sense_id'):
                continue
            sense = by_id.get(form['sense_id'])
            if not sense or sense.get('kind') != 'sense':
                continue
            written = form.get('catalog_normalized') or form.get('written') or ''
            if not re.search(r'[a-zA-Z]', written) or ' ' in written.strip():
                continue
            label = sense.get('label') or sense.get('definition') or ''
            noun_hint = sense.get('pos') == 'noun' or bool(re.search(r'(tl|tli|li|in)$', written.casefold()))
            verb_hint = sense.get('pos') == 'verb' or bool(re.match(r'\s*[a-záéíóú]+(ar|er|ir)\b', label.casefold()))
            function_word = bool(re.search(r'\b(conjunc|coniunc|preposic|aduerb|adverb|interjec|partic)', label.casefold()))
            entry = dict(form_id=form['id'], sense_id=sense['id'], written=form.get('written'),
                         label=label[:160], url=form.get('url') or sense.get('url') or '',
                         pos='verb' if verb_hint and not noun_hint else 'noun' if noun_hint else sense.get('pos', 'other'),
                         automatic=sense.get('import_status') == 'automatic_transcription')
            self.entries += 1
            key = key_of(written)
            if len(key) < 1:
                continue
            if function_word:
                self.whole[key].append(dict(entry, stem=key, derivation='palabra funcional (solo forma completa)'))
                continue
            for stem, how in _lemma_stems(key, noun_hint):
                self.stems[stem].append(dict(entry, stem=stem, derivation=how))
            # Molina registra muchos sustantivos inalienables ya poseídos: «Noma: mi mano»
            if key.startswith('no') and len(key) > 3 and re.match(r'\s*(mi|mis)\b', label.casefold()):
                for stem, how in _lemma_stems(key[2:], noun_hint):
                    self.stems[stem].append(dict(entry, stem=stem, derivation='sin poseedor no- (entrada poseída en Molina)'))
            # Molina suele dar el pretérito: «pret: onacaxuac» → raíz nacaxua(c)
            for m in PRETERIT.finditer(sense.get('definition') or sense.get('label') or ''):
                pk = key_of(m.group(1))
                if pk.startswith('o') and len(pk) > 3:
                    pk = pk[1:]
                    if pk.endswith('k'):
                        pk = pk[:-1]
                    if pk != key:
                        self.stems[pk].append(dict(entry, stem=pk, derivation='raíz de pretérito registrada'))

    def lookup(self, stem):
        return self.stems.get(stem, [])


# --------------------------------------------------------------------------
# 4. Generación y puntuación de análisis
# --------------------------------------------------------------------------
def _consonant_final(s):
    return bool(s) and s[-1] not in VOWELS


def _prefix_paths(key):
    """Cadenas de prefijos posibles: lista de (clase, [(slot, forma, tag, glosa)], resto)."""
    results = [('none', [], key)]
    # Nominal: poseedor
    for form, tag, gloss in PREFIXES['POSS']:
        if key.startswith(form) and len(key) > len(form) + 1:
            rest = key[len(form):]
            if ('POSS', form) in BEFORE_VOWEL_ONLY and rest[0] not in VOWELS and not (form == 'am' and rest[0] in 'mp'):
                continue
            if form == 'im' and rest[0] not in 'mp':
                continue
            results.append(('noun', [('POSS', form, tag, gloss)], rest))
    # Verbal: [ANT][SUBJ][DIR][OBJ][REFL] — al menos uno
    verbal = []

    def walk(slots, rest, chain):
        if not slots:
            if chain:
                verbal.append((chain, rest))
            return
        slot = slots[0]
        walk(slots[1:], rest, chain)  # vacío
        for form, tag, gloss in PREFIXES[slot]:
            if not rest.startswith(form) or len(rest) <= len(form):
                continue
            nxt = rest[len(form):]
            if (slot, form) in BEFORE_VOWEL_ONLY and nxt[0] not in VOWELS:
                continue
            if slot == 'OBJ' and form == 'k':
                prev = chain[-1][1] if chain else ''
                if not ((prev and prev[-1] in VOWELS) or nxt[0] in VOWELS):
                    continue
            if slot == 'OBJ' and form == 'ki' and nxt[0] in VOWELS:
                continue
            if form in ('kim', 'am') and nxt[0] not in 'mp' + ('aeio' if form == 'am' else ''):
                continue  # quim-/am- solo ante m, p (am- también ante vocal)
            if form == 'kin' and nxt[0] in 'mp':
                continue
            walk(slots[1:], nxt, chain + [(slot, form, tag, gloss)])

    walk(['ANT', 'SUBJ', 'DIR', 'OBJ', 'REFL'], key, [])
    for chain, rest in verbal:
        slots = [c[0] for c in chain]
        forms = dict((c[0], c[1]) for c in chain)
        # Concordancia sujeto/reflexivo y combinaciones imposibles
        subj, refl, obj = forms.get('SUBJ'), forms.get('REFL'), forms.get('OBJ')
        if refl and subj:
            if subj in ('ni', 'n') and refl != 'no':
                continue
            if subj in ('ti', 't') and refl not in ('mo', 'to', 'm'):
                continue
            if subj in ('an', 'am') and refl not in ('mo', 'm'):
                continue
        if refl == 'no' and subj not in ('ni', 'n'):
            continue
        if refl == 'to' and subj not in ('ti', 't'):
            continue
        if subj in ('ni', 'n') and obj == 'neč':
            continue
        if subj in ('ti', 't') and obj == 'miʦ':
            continue
        nominalizer_only = slots == ['OBJ'] and obj in ('λa', 'te')
        results.append(('nominalized' if nominalizer_only else 'verb', chain, rest))
    return results


def _suffix_paths(rest, klass):
    """(cadena de sufijos [(slot, forma, tag, glosa)], raíz) para una clase."""
    out = []

    def strip(s, form):
        return s[:-len(form)] if form and s.endswith(form) and len(s) > len(form) else (s if not form else None)

    if klass in ('none', 'noun', 'nominalized'):
        possessed = klass == 'noun'
        inflections = []
        if possessed:
            inflections += [('POSD', *x) for x in N_POSS_SG] + [('POSD.PL', *x) for x in N_POSS_PL]
        else:
            inflections += [('ABS', *x) for x in N_ABS] + [('PL', *x) for x in N_ABS_PL]
        for slot, form, tag, gloss in inflections:
            base = strip(rest, form)
            if base is None:
                continue
            # alomorfía del absolutivo y del poseído
            if slot == 'ABS':
                if form == 'λ' and _consonant_final(base):
                    continue
                if form == 'λi' and (not _consonant_final(base) or base.endswith('l')):
                    continue
                if form == 'li' and not base.endswith('l'):
                    continue
            if slot == 'POSD':
                if form == 'w' and _consonant_final(base):
                    continue
                if form == 'wi' and not _consonant_final(base):
                    continue
            chain = [(slot, form, tag, gloss)] if form else []
            out.append((chain, base))
            # derivación nominal antes de la flexión
            for dform, dtag, dgloss in N_DERIV:
                if base.endswith(dform) and len(base) > len(dform) + 1:
                    if dform == 'l' and form != 'li':
                        continue
                    if dform == 'ni' and form:
                        continue
                    out.append(([('N', dform, dtag, dgloss)] + chain, base[:-len(dform)]))
        # relacionales (sin absolutivo; poseídos o topónimos)
        for form, tag, gloss in RELATIONAL:
            form = form.replace('-', '')
            if rest.endswith(form) and len(rest) > len(form) + 1:
                base = rest[:-len(form)]
                out.append(([('REL', form, tag, gloss)], base))
                for dform, dtag, dgloss in (('ʦin', 'REV/DIM', 'reverencial o diminutivo'),):
                    if base.endswith(dform) and len(base) > len(dform) + 1:
                        out.append(([('N', dform, dtag, dgloss), ('REL', form, tag, gloss)], base[:-len(dform)]))
                # poseído + relacional con ligadura -ti- (tlal-ti-cpac)
                if base.endswith('ti') and len(base) > 3:
                    out.append(([('LIG', 'ti', 'LIG', 'ligadura'), ('REL', form, tag, gloss)], base[:-2]))
    if klass in ('none', 'verb', 'nominalized'):
        for tform, ttag, tgloss in V_TENSE:
            base = strip(rest, tform)
            if base is None:
                continue
            if tform == 'k' and _consonant_final(base):
                continue
            chain = [('T', tform, ttag, tgloss)] if tform else []
            out.append((chain, base))
            for dform, dtag, dgloss in V_DERIV:
                if base.endswith(dform) and len(base) > len(dform) + 1:
                    out.append(([('V', dform, dtag, dgloss)] + chain, base[:-len(dform)]))
    return out


NOUN_MARK = {'ABS', 'PL', 'POSD', 'POSD.PL', 'REL', 'POSS', 'LIG'}
VERB_MARK = {'SUBJ', 'OBJ', 'T', 'ANT', 'DIR', 'V'}


def _class_of(prefix_chain, suffix_chain):
    slots = {c[0] for c in prefix_chain} | {c[0] for c in suffix_chain if c[1]}
    noun, verb = bool(slots & NOUN_MARK), bool(slots & (VERB_MARK - {'OBJ'}) or
                                               any(c[0] == 'OBJ' and c[1] not in ('λa', 'te') for c in prefix_chain))
    if noun and not verb:
        return 'N'
    if verb and not noun:
        return 'V'
    return None


def _compatible(hits, cls):
    """Concordancia de categoría: un análisis verbal no se apoya en un sustantivo, y viceversa.
    Las entradas sin categoría inferible solo apoyan análisis sin marcas de clase."""
    if not hits or cls is None:
        return hits
    want = 'noun' if cls == 'N' else 'verb'
    return [h for h in hits if h['pos'] == want]


def _dict_bonus(stem, full):
    """Las entradas muy breves (ca, ic, a) coinciden por azar: valen menos."""
    if len(stem) >= 4:
        return full
    if len(stem) == 3:
        return full - 3.5
    return None


class Analyzer:
    """Analiza palabras; ``stem_counts`` se estima con ``fit`` sobre un corpus."""

    def __init__(self, records=(), stem_counts=None):
        self.lexicon = Lexicon(records)
        self.stem_counts = Counter(stem_counts or {})
        self.stem_class = {}
        self.total_types = max(sum(self.stem_counts.values()), 1)
        self._cache = {}

    # -- puntuación ------------------------------------------------------
    def _stem_evidence(self, stem, klass, has_tense_or_poss, cls=None):
        hits = _compatible(self.lexicon.lookup(stem), cls)
        if hits and _dict_bonus(stem, 6.0) is not None:
            return _dict_bonus(stem, 6.0), 'dictionary', hits
        # pretérito / poseído con pérdida de vocal final: chiuh ← chihua, cuic ← cuica
        if has_tense_or_poss and len(stem) >= 2:
            for v in 'aeio':
                hits = _compatible(self.lexicon.lookup(stem + v), cls)
                if hits and len(stem) >= 3:
                    return _dict_bonus(stem, 4.5), 'dictionary_truncated', hits
            if stem.endswith('w'):
                hits = _compatible(self.lexicon.lookup(stem + 'a'), cls)
                if hits and len(stem) >= 3:
                    return _dict_bonus(stem, 4.5), 'dictionary_truncated', hits
        # compuesto de dos raíces del diccionario: xochi+cuahui-tl
        for cut in range(3, len(stem) - 2):
            left, right = stem[:cut], stem[cut:]
            lh, rh = _compatible(self.lexicon.lookup(left), 'N'), _compatible(self.lexicon.lookup(right), cls)
            if lh and rh:
                return 4.0, 'dictionary_compound', lh[:2] + rh[:2]
        return 0.0, None, []

    def _affix_cost(self, form):
        # Un afijo largo (mitz, nech, tzin) rara vez coincide por azar: cuesta menos.
        return max(0.15, 1.0 - 0.25 * len(form))

    def _corpus_freq(self, stem, has_tense_or_poss):
        f = self.stem_counts.get(stem, 0)
        if has_tense_or_poss:
            for v in ('a', 'i', 'e', 'o'):
                f = max(f, 0.7 * self.stem_counts.get(stem + v, 0))
        return f

    def _score(self, word_key, prefix_chain, suffix_chain, stem, klass):
        cost = 0.0
        for c in prefix_chain:
            cost += self._affix_cost(c[1]) + RARE.get(('PRE', c[1]), 0)
        for c in suffix_chain:
            cost += self._affix_cost(c[1]) + RARE.get((c[0], c[1]), 0)
        if not prefix_chain and not [c for c in suffix_chain if c[1]] and len(word_key) >= 6:
            cost += 1.0  # casi toda palabra náhuatl larga lleva algún afijo
        has_tense_or_poss = any(c[0] in ('T', 'POSD', 'POSD.PL') for c in suffix_chain) or klass == 'noun'
        cls = _class_of(prefix_chain, suffix_chain)
        bonus, basis, hits = self._stem_evidence(stem, klass, has_tense_or_poss, cls)
        freq = self._corpus_freq(stem, has_tense_or_poss)
        corpus = 1.1 * math.log1p(freq)
        if len(stem) <= 1:
            cost += 5
        elif len(stem) == 2:
            cost += 1.0
        if stem and all(ch not in VOWELS for ch in stem):
            cost += 4  # raíz sin vocal
        # Preferencia nominal/verbal aprendida del corpus (marcadores inequívocos)
        if cls and self.stem_class:
            n, v = self.stem_class.get(stem, (0, 0))
            cost -= 0.5 * math.log((1 + (n if cls == 'N' else v)) / (1 + (v if cls == 'N' else n)))
        score = bonus + corpus - cost
        return score, basis or ('corpus' if freq >= 2 else 'rules'), hits

    # -- API -------------------------------------------------------------
    def candidates(self, key):
        seen = set()
        for klass, pchain, rest in _prefix_paths(key):
            for schain, stem in _suffix_paths(rest, klass):
                if not stem:
                    continue
                sig = (tuple(c[:2] for c in pchain), stem, tuple(c[:2] for c in schain))
                if sig in seen:
                    continue
                seen.add(sig)
                yield klass, pchain, stem, schain

    def analyze(self, word, limit=5):
        """Lista ordenada de análisis de ``word`` (texto de la fuente)."""
        word = word.strip()
        cache_key = (word, limit)
        if cache_key in self._cache:
            return self._cache[cache_key]
        key, spans = phonemic_key(word)
        results = []
        if not key:
            return []
        base = _base(word)
        if FOREIGN.search(base) or re.fullmatch(r'\d+', base):
            results.append(self._package(word, key, spans, 'foreign', [], key, [], 0.0,
                                         'loan_or_name', [], note='Posible préstamo del español, nombre propio o cifra.'))
        if key in PARTICLES:
            lemma, tag, gloss = PARTICLES[key]
            hits = self.lexicon.whole.get(key, []) + self.lexicon.lookup(key)
            results.append(self._package(word, key, spans, 'particle', [], key, [], 8.0, 'particle_table', hits,
                                         particle=dict(lemma=lemma, tag=tag, gloss=gloss)))
        if key not in PARTICLES and self.lexicon.whole.get(key):
            h = self.lexicon.whole[key]
            results.append(self._package(word, key, spans, 'particle', [], key, [], 7.0, 'dictionary', h,
                                         particle=dict(lemma=h[0]['written'], tag='PTCL', gloss=h[0]['label'][:80])))
        scored = []
        for klass, pchain, stem, schain in self.candidates(key):
            score, basis, hits = self._score(key, pchain, schain, stem, klass)
            if not pchain and len(stem) < 3 and schain and schain[0][0] == 'ABS':
                # Sustantivos breves registrados completos (atl, tetl, metl): la forma
                # entera coincide con la entrada; la raíz breve no se busca sola.
                whole = [h for h in self.lexicon.lookup(stem) if key_of(h['written'] or '') == key]
                if whole:
                    score, basis, hits = score + 6.0 + (5 if len(stem) <= 1 else 1), 'dictionary', whole
            scored.append((score, klass, pchain, stem, schain, basis, hits))
        scored.sort(key=lambda x: (-x[0], len(x[2]) + len(x[4]), x[3]))
        for score, klass, pchain, stem, schain, basis, hits in scored[:limit * 3]:
            results.append(self._package(word, key, spans, klass, pchain, stem, schain, score, basis, hits))
        # deduplicar por segmentación visible
        unique, seen = [], set()
        for r in sorted(results, key=lambda r: -r['score']):
            sig = (r['segmentation'], tuple(m['tag'] for m in r['morphemes']))
            if sig in seen:
                continue
            seen.add(sig)
            unique.append(r)
        out = unique[:limit]
        # confianza relativa (softmax sobre los candidatos mostrados)
        if out:
            m = max(r['score'] for r in out)
            z = sum(math.exp(r['score'] - m) for r in out)
            for r in out:
                r['relative_confidence'] = round(math.exp(r['score'] - m) / z, 3)
        self._cache[cache_key] = out
        return out

    def best_stem(self, word):
        a = self.analyze(word, limit=1)
        return a[0]['stem_key'] if a else key_of(word)

    def _package(self, word, key, spans, klass, pchain, stem, schain, score, basis, hits, particle=None, note=None):
        morphemes = []
        pos = 0

        def surface(a, b):
            if a >= b or not spans:
                return ''
            return word[spans[a][0]:spans[b - 1][1]]

        for slot, form, tag, gloss in pchain:
            morphemes.append(dict(role='prefix', slot=slot, key=form, tag=tag, gloss=gloss,
                                  surface=surface(pos, pos + len(form))))
            pos += len(form)
        stem_start = pos
        stem_len = len(stem) if klass not in ('particle', 'foreign') else len(key)
        morphemes.append(dict(role='stem', slot='STEM', key=stem, tag='RAÍZ', gloss='',
                              surface=surface(stem_start, stem_start + stem_len)))
        pos += stem_len
        for slot, form, tag, gloss in schain:
            if not form:
                continue
            morphemes.append(dict(role='suffix', slot=slot, key=form, tag=tag, gloss=gloss,
                                  surface=surface(pos, pos + len(form))))
            pos += len(form)
        dictionary = [dict(form_id=h['form_id'], sense_id=h['sense_id'], written=h['written'], label=h['label'],
                           url=h['url'], derivation=h['derivation'], automatic=h['automatic']) for h in hits[:4]]
        if particle:
            morphemes[0].update(tag=particle['tag'], gloss=particle['gloss'])
        elif dictionary:
            morphemes[[m['role'] for m in morphemes].index('stem')]['gloss'] = dictionary[0]['label'][:80]
        seg = '-'.join(m['surface'] or m['key'] for m in morphemes)
        return dict(word=word, key=readable(key), class_=klass, morphemes=morphemes,
                    segmentation=seg, stem_key=stem, stem=readable(stem), score=round(score, 3), basis=basis,
                    dictionary=dictionary, note=note or NOTES.get(basis, ''))

    # -- Estimación de frecuencias de raíz (EM duro, tipo Morfessor sin MDL completo)
    def fit(self, words, iterations=3):
        """Estima ``stem_counts`` a partir de una colección de palabras del corpus.

        Iteración 0: cada tipo reparte un voto uniforme entre las raíces de sus
        candidatos. Iteraciones siguientes: cada tipo vota solo por la raíz de
        su mejor análisis con los conteos actuales (EM duro).
        """
        types = Counter(key_of(w) for w in words if w)
        types.pop('', None)
        cands = {}
        for key in types:
            stems = {stem for _, _, stem, _ in self.candidates(key) if len(stem) >= 2}
            cands[key] = stems or {key}
        counts = Counter()
        for key, stems in cands.items():
            for s in stems:
                counts[s] += 1 / len(stems)
        history = []
        for _ in range(iterations):
            self.stem_counts = counts
            self._cache = {}
            new = Counter()
            klass = defaultdict(lambda: [0, 0])
            for key in types:
                if key in PARTICLES:
                    new[key] += 1
                    continue
                best, cls = self._best_key(key)
                new[best] += 1
                if cls:
                    klass[best][0 if cls == 'N' else 1] += 1
            self.stem_class = {k: tuple(v) for k, v in klass.items()}
            changed = sum(1 for s in set(new) | set(counts) if round(new.get(s, 0)) != round(counts.get(s, 0)))
            history.append(dict(stems=len(new), changed=changed))
            counts = new
        self.stem_counts = counts
        self._cache = {}
        return history

    def _best_key(self, key):
        best, best_score, best_cls = key, -1e9, None
        for klass, pchain, stem, schain in self.candidates(key):
            score, _, _ = self._score(key, pchain, schain, stem, klass)
            if score > best_score or (score == best_score and len(stem) > len(best)):
                best, best_score, best_cls = stem, score, _class_of(pchain, schain)
        return best, best_cls

    def gloss_text(self, text):
        """Glosa interlineal: una entrada por palabra con su mejor análisis y alternativas."""
        out = []
        for m in WORD.finditer(text):
            analyses = self.analyze(m.group(0), limit=3)
            out.append(dict(token=m.group(0), start=m.start(), end=m.end(),
                            best=analyses[0] if analyses else None, alternatives=analyses[1:]))
        return out

    def to_json(self):
        return dict(version=ANALYZER_VERSION, stem_counts=dict(self.stem_counts.most_common()),
                    stem_class={k: list(v) for k, v in self.stem_class.items()})


WORD = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*", re.U)
NOTES = {
    'dictionary': 'La raíz coincide con una entrada del diccionario del proyecto.',
    'dictionary_truncated': 'La raíz coincide con una entrada si se restituye la vocal final (pretérito o forma poseída).',
    'dictionary_compound': 'La raíz parece un compuesto de dos entradas del diccionario.',
    'corpus': 'La raíz no está en el diccionario; se repite en otras palabras del archivo.',
    'rules': 'Segmentación solo por reglas; la raíz no tiene apoyo en el diccionario ni en el archivo.',
    'particle_table': 'Partícula o pronombre frecuente (tabla gramatical del analizador).',
    'loan_or_name': 'Posible préstamo, nombre propio o cifra.',
}


def corpus_words(rows, iso='nci'):
    for r in rows:
        if iso and r.get('iso') != iso:
            continue
        for m in WORD.finditer(r['nah']):
            yield m.group(0)


def build(records, rows, iterations=3):
    analyzer = Analyzer(records)
    analyzer.fit(list(corpus_words(rows)), iterations)
    return analyzer


def main():
    import argparse
    p = argparse.ArgumentParser(description='Analiza palabras de náhuatl clásico (reglas + diccionario + corpus).')
    p.add_argument('words', nargs='+')
    p.add_argument('--no-corpus', action='store_true', help='No estimar frecuencias con el archivo (más rápido).')
    a = p.parse_args()
    from .stems import load_default
    analyzer = load_default(fit=not a.no_corpus)
    for w in a.words:
        print(w)
        for r in analyzer.analyze(w):
            print(f"  {r['segmentation']:<28} {r['score']:>7.2f}  {r['basis']:<20} "
                  + ' '.join(m['tag'] for m in r['morphemes'])
                  + (f"  ← {r['dictionary'][0]['written']}: {r['dictionary'][0]['label'][:50]}" if r['dictionary'] else ''))


if __name__ == '__main__':
    main()
