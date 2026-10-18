"""Normalización única de texto: tres claves, cada una con un solo uso.

Toda comparación de texto del proyecto pasa por este módulo. Ninguna clave
modifica lo almacenado: las transcripciones, definiciones y traducciones se
conservan con su grafía original y la clave se calcula solo para comparar.

=====================  ===========================================  =================================
Función                Qué neutraliza                               Para qué se usa
=====================  ===========================================  =================================
``fold``               mayúsculas y marcas diacríticas              buscar en español, títulos, catálogos
``phonemic_key``       ortografía colonial (qu/c/k, hu/uh/u, z/ç,   analizador morfológico (evaluado;
                       saltillo h, y/i, vocales dobles)             su salida está congelada)
``loose_key``          además la ortografía moderna (k, kw, ts, w)  recuperación tolerante en Preguntar
                       y consonantes dobles
=====================  ===========================================  =================================

Funciones auxiliares construidas sobre ellas: ``strip_marks`` (la primitiva de
``fold``), ``squash`` (espacios), ``tokens`` (palabras plegadas), ``es_key``
(plural regular español), ``key_of`` y ``readable``.

La normalización ortográfica ``nah-ortho-1`` (``nahuatl_orthography``) no es una
cuarta clave de consulta: limpia texto para persistirlo (``storage``) y fija la
clave de deduplicación de las particiones de entrenamiento y del índice BM25
(``comparison``). Está versionada en los manifiestos de ``data/prepared`` y del
banco de pruebas, por eso se conserva congelada en su propio módulo; usa
``strip_marks`` de aquí. Ver ``docs/ARCHITECTURE.md`` §2.
"""
import re
import unicodedata

# --------------------------------------------------------------------------
# 1. Plegado español
# --------------------------------------------------------------------------
WORDS = re.compile(r'\w+')               # letras, cifras y «_»
LETTERS = re.compile(r'[^\W\d_]+')       # solo letras


def strip_marks(text):
    """Descompone en NFD y elimina las marcas no espaciadas (tildes, diéresis, macrones).

    >>> strip_marks('Tōnatiuh, corazón')
    'Tonatiuh, corazon'
    """
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')


def fold(text):
    """Plegado español: sin mayúsculas (casefold) ni marcas diacríticas.

    Acepta cualquier valor (se convierte con ``str``). Es la única forma de
    comparar texto español o etiquetas de catálogo sin distinguir acentos.

    >>> fold('Árbol') == fold('arbol')
    True
    """
    return strip_marks(str(text).casefold())


def squash(text):
    """Colapsa espacios en blanco a uno solo y recorta los extremos."""
    return ' '.join(str(text).split())


def tokens(text, *, letters_only=False, keep_accents=False):
    """Palabras plegadas de ``text``.

    ``letters_only`` descarta cifras y «_»; ``keep_accents`` pliega solo
    mayúsculas (lo usa el BM25 del archivo, cuya tokenización está medida).

    >>> tokens('Año 1521: Tenochtitlan')
    ['ano', '1521', 'tenochtitlan']
    """
    value = str(text).casefold() if keep_accents else fold(text)
    return (LETTERS if letters_only else WORDS).findall(value)


def es_key(word):
    """Clave española ligera: plegado y sin plural regular (-es tras consonante, -s).

    >>> es_key('Flores') == es_key('flor')
    True
    """
    w = fold(word)
    if len(w) > 4 and w.endswith('es') and w[-3] not in 'aeiou':
        w = w[:-2]
    elif len(w) > 3 and w.endswith('s'):
        w = w[:-1]
    return w


# --------------------------------------------------------------------------
# 2. Clave fonémica estricta (analizador, nah-morph-1)
# --------------------------------------------------------------------------
VOWELS = set('aeio')
# Símbolos de un carácter: č=ch, ʦ=tz, λ=tl, q=kw. El resto son letras latinas.
DISPLAY = {'č': 'ch', 'ʦ': 'tz', 'λ': 'tl', 'q': 'kw'}


def spelling_base(text):
    """Minúsculas, sin marcas diacríticas; ç→s, v→u (ortografía colonial).

    Devuelve un carácter por carácter de entrada, de modo que los índices
    coinciden con ``text`` (en NFC). «j» se conserva: en el corpus clásico de
    Axolotl aparece casi solo en préstamos y nombres (Juan, justicia, juez),
    que se marcan como tales."""
    out = []
    for ch in unicodedata.normalize('NFC', text):
        low = ch.casefold()
        if low == 'ç':
            out.append('s')
            continue
        base = strip_marks(low) or low
        base = {'v': 'u'}.get(base, base)
        out.append(base[:1])  # un carácter de salida por carácter de entrada
    return ''.join(out)


def phonemic_key(word):
    """Clave ortográficamente neutra de una palabra náhuatl y su alineación.

    Devuelve (clave, tramos); ``tramos[i]`` es (inicio, fin) en ``word``, para
    mostrar segmentaciones en la grafía de la fuente. Su salida es la que mide
    ``morphology_evaluation``: cualquier cambio exige volver a medir.

    >>> phonemic_key('niquitta')[0]
    'nikitta'
    >>> phonemic_key('yhuan')[0] == phonemic_key('ihuan')[0] == phonemic_key('iuan')[0]
    True
    """
    s = spelling_base(word)
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
    """Solo la clave de ``phonemic_key``."""
    return phonemic_key(word)[0]


def readable(key):
    """Clave fonémica legible (ch, tz, tl, kw)."""
    return ''.join(DISPLAY.get(c, c) for c in key)


# --------------------------------------------------------------------------
# 3. Clave laxa de grafía (recuperación)
# --------------------------------------------------------------------------
def loose_key(word):
    """Clave de recuperación tolerante a la ortografía colonial y moderna.

    Parte de la clave fonémica y además une la grafía moderna (SEP/INALI: k, kw,
    ts, w, j) con la colonial y reduce consonantes dobles. Solo recupera; no
    sustituye a la clave fonémica evaluada del analizador.

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
