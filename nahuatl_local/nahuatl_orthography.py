"""Normalización ortográfica del náhuatl: almacenamiento y comparación.

Sin dependencias (solo stdlib). Distingue dos modos:

- ``storage``: forma canónica persistida en el corpus. Preserva
  diacríticos, ç, ñ y mayúsculas; compone NFC, repara mojibake cp1252 C1 y
  colapsa espacios. Es idempotente; la reparación y limpieza no son reversibles.
  La transcripción exacta se conserva en el CSV original separado.
- ``comparison``: forma para comparar/dedupar. Colapsa variantes ortográficas
  atestiguadas (ç→tz, v→u, marcas diacríticas, mayúsculas, puntuación). No es
  reversible; NO debe usarse como forma de almacenamiento.

Las reglas se declaran una sola vez en ``RULES``; ``STORAGE_RULE_IDS`` y
``COMPARISON_RULE_IDS`` fijan el orden de aplicación por modo.

Lugar en el proyecto: ``nah-ortho-1`` está congelada. Su versión y sus reglas se
registran en ``data/prepared/manifest.json`` y en los informes del banco de
pruebas; cambiarla invalidaría particiones y cifras ya publicadas. Sirve para
limpiar texto que se persiste (``storage``) y como clave de deduplicación y del
BM25 del archivo (``comparison``). No es una clave de consulta léxica: para eso
están ``text.fold``, ``text.phonemic_key`` y ``text.loose_key``. Nota: aquí
``ç→tz``; el analizador (``text.phonemic_key``) usa ``ç→s`` como GDN. La
discrepancia está documentada en ``docs/ARCHITECTURE.md`` y se resolverá con una
``nah-ortho-2`` revisada, no modificando esta versión.
"""
import argparse
import collections
import re
import unicodedata

from .text import strip_marks

ORTHOGRAPHY_VERSION = 'nah-ortho-1'

# kind ∈ {'unicode','regex','map'}; mode ∈ {'storage','comparison','both'}.
# Para kind='regex', pattern es el patrón y replacement la sustitución.
# Para kind='unicode', pattern es la operación ('NFC','casefold','strip_marks').
# Para kind='map', pattern es el diccionario carácter→sustituto y replacement
# puede ser 'drop_controls' para, además, eliminar bytes de control huérfanos.
Rule = collections.namedtuple('Rule', 'id mode kind pattern replacement description')

# Mojibake cp1252: los bytes C1 U+0091–U+0097 proceden de comillas/dash
# decodificados como controles. Se reasignan a su glifo real.
_C1_MAP = {
    '\x91': '\u2018',  # ‘
    '\x92': '\u2019',  # ’
    '\x93': '\u201c',  # “
    '\x94': '\u201d',  # ”
    '\x95': '\u2022',  # •
    '\x96': '\u2013',  # –
    '\x97': '\u2014',  # —
}

RULES = (
    Rule('nfc', 'both', 'unicode', 'NFC', None,
         'Composición a NFC (equivalencia canónica; no conserva la secuencia original de puntos de código).'),
    Rule('repair_c1', 'both', 'map', _C1_MAP, 'drop_controls',
         'Repara mojibake cp1252 C1 (\\x91–\\x97) y elimina bytes de control huérfanos.'),
    Rule('strip_invisible', 'both', 'regex', '[\u200b-\u200f\ufeff]', '',
         'Elimina separadores de ancho cero y BOM.'),
    Rule('collapse_space', 'both', 'regex', r'\s+', ' ',
         'Colapsa espacios en blanco a un único espacio.'),
    Rule('casefold', 'comparison', 'unicode', 'casefold', None,
         'Pliegue de mayúsculas/minúsculas (Ç→ç, Ñ→ñ).'),
    Rule('c_cedilla', 'comparison', 'regex', 'ç', 'tz',
         'ç colonial (= /ts/) → tz.'),
    Rule('v_to_u', 'comparison', 'regex', 'v', 'u',
         'v colonial (= /w/) → u.'),
    Rule('strip_marks', 'comparison', 'unicode', 'strip_marks', None,
         'Descomposición NFD y eliminación de marcas (tildes, macrones, diéresis).'),
    Rule('strip_punct', 'comparison', 'regex', r'[^\w\s]', ' ',
         'Sustituye puntuación por espacio (replica el canonical anterior).'),
    # Reglas agresivas PENDIENTES de aprobación filológica. Definidas aquí pero
    # EXCLUIDAS de COMPARISON_RULE_IDS; no se aplican hasta nueva revisión.
    Rule('glottal_h', 'comparison', 'regex', 'h', '',
         'PENDIENTE: elimina la h glotal/saltillo.'),
    Rule('qu_to_cu', 'comparison', 'regex', 'qu', 'cu',
         'PENDIENTE: qu → cu (alternancia /kʷ/).'),
    Rule('initial_y', 'comparison', 'regex', r'\by', 'i',
         'PENDIENTE: y inicial → i (yn→in).'),
)

STORAGE_RULE_IDS = ('nfc', 'repair_c1', 'strip_invisible', 'collapse_space')
COMPARISON_RULE_IDS = ('nfc', 'repair_c1', 'strip_invisible', 'casefold',
                       'c_cedilla', 'v_to_u', 'strip_marks', 'strip_punct',
                       'collapse_space')

_RULE_BY_ID = {rule.id: rule for rule in RULES}


def _ids_for_mode(mode):
    if mode == 'storage':
        return STORAGE_RULE_IDS
    if mode == 'comparison':
        return COMPARISON_RULE_IDS
    raise ValueError('modo desconocido: %r (usa "storage" o "comparison")' % (mode,))


def _apply(rule, text):
    """Aplica una única regla. Devuelve (nuevo_texto, nº de cambios)."""
    kind = rule.kind
    if kind == 'unicode':
        op = rule.pattern
        if op == 'NFC':
            out = unicodedata.normalize('NFC', text)
            return out, 1 if out != text else 0
        if op == 'casefold':
            out = text.casefold()
            return out, 1 if out != text else 0
        if op == 'strip_marks':
            out = strip_marks(text)
            return out, len(unicodedata.normalize('NFD', text)) - len(out)
        raise ValueError('operación unicode desconocida: %r' % (op,))
    if kind == 'regex':
        out, count = re.subn(rule.pattern, rule.replacement, text)
        return out, count
    if kind == 'map':
        table = rule.pattern
        drop_controls = rule.replacement == 'drop_controls'
        out = []
        count = 0
        for ch in text:
            if ch in table:
                rep = table[ch]
                if rep is None:
                    count += 1
                else:
                    out.append(rep)
                    if rep != ch:
                        count += 1
            elif drop_controls and unicodedata.category(ch) == 'Cc' and ch not in '\t\n\r\x0b\x0c':
                count += 1
            else:
                out.append(ch)
        return ''.join(out), count
    raise ValueError('tipo de regla desconocido: %r' % (kind,))


def normalize(text, mode='storage'):
    ids = _ids_for_mode(mode)
    out = text
    for rule_id in ids:
        out, _ = _apply(_RULE_BY_ID[rule_id], out)
    return out.strip()


def storage(text):
    return normalize(text, 'storage')


def comparison(text):
    return normalize(text, 'comparison')


def explain(text, mode='storage'):
    """Aplica las reglas por pasos y registra qué cambió cada una."""
    ids = _ids_for_mode(mode)
    out = text
    rules = []
    edits = []
    for rule_id in ids:
        rule = _RULE_BY_ID[rule_id]
        before = out
        out, count = _apply(rule, out)
        rules.append({'id': rule_id, 'count': count})
        if count:
            edits.append({'id': rule_id, 'count': count, 'before': before, 'after': out})
    out = out.strip()
    return {'input': text, 'output': out, 'mode': mode,
            'changed': out != text, 'rules': rules, 'edits': edits}


def audit(texts, mode='storage'):
    """Agrega los cambios de normalización sobre una colección de textos."""
    reports = [explain(text, mode) for text in texts]
    totals = collections.Counter()
    changed = 0
    for report in reports:
        if report['changed']:
            changed += 1
        for rule in report['rules']:
            totals[rule['id']] += rule['count']
    total = len(reports)
    return {
        'mode': mode,
        'total': total,
        'changed': changed,
        'changed_fraction': round(changed / total, 4) if total else 0.0,
        'rule_totals': [{'id': rule_id, 'count': totals[rule_id]} for rule_id in totals],
        'examples': [{'input': r['input'], 'output': r['output']}
                     for r in reports if r['changed']][:5],
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('text')
    p.add_argument('--mode', choices=['storage', 'comparison'], default='storage')
    a = p.parse_args()
    print(explain(a.text, a.mode))


if __name__ == '__main__':
    main()
