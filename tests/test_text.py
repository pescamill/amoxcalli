import doctest
import hashlib
import json
import re
import unittest
from pathlib import Path

from nahuatl_local import passages, text
from nahuatl_local.morphology import WORD
from nahuatl_local.text import es_key, fold, key_of, loose_key, phonemic_key, squash, strip_marks, tokens

ROOT = Path(__file__).resolve().parents[1]
# Huellas medidas antes de unificar la normalización (commit 86c217f): la clave fonémica
# es entrada evaluada del analizador y no debe cambiar sin volver a medir.
PHONEMIC_SHA256 = '2612061e11dc05eb5cbeb6489b0065027005faa42fe8ced39d6d069e5cb18b01'
LOOSE_SHA256 = '89b43116a6bcd18dfb4e6608f316a69b8d469d055ca1c398bcb5123029ae35ea'


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False).encode()).hexdigest()


class TextTests(unittest.TestCase):
    def test_doctests(self):
        self.assertEqual(doctest.testmod(text).failed, 0)

    def test_spanish_fold(self):
        self.assertEqual(fold('Árbol ÇAN Tōnatiuh'), 'arbol can tonatiuh')
        self.assertEqual(fold(12), '12')
        self.assertEqual(strip_marks('Ñandú'), 'Nandu')
        self.assertEqual(squash('  a \n\t b  '), 'a b')
        self.assertEqual(es_key('Mujeres'), es_key('mujer'))
        self.assertEqual(es_key('casas'), 'casa')

    def test_tokens_variants(self):
        self.assertEqual(tokens('Año 1521 de_x'), ['ano', '1521', 'de_x'])
        self.assertEqual(tokens('Año 1521 de_x', letters_only=True), ['ano', 'de', 'x'])
        self.assertEqual(tokens('Árbol', keep_accents=True), ['árbol'])

    def test_phonemic_and_loose_keys_are_frozen_over_the_archive(self):
        words = sorted({w for _, f in passages.records() for col in f[:2] for w in WORD.findall(col)})
        self.assertEqual(len(words), 76698)
        self.assertEqual(digest([(w, phonemic_key(w)) for w in words]), PHONEMIC_SHA256)
        self.assertEqual(digest([loose_key(w) for w in words]), LOOSE_SHA256)

    def test_three_keys_have_distinct_reach(self):
        # Fonémica: ortografía colonial; laxa: además la moderna; plegado: solo acentos y mayúsculas.
        self.assertEqual(key_of('quauitl'), key_of('cuahuitl'))
        self.assertNotEqual(key_of('kuawitl'), key_of('cuahuitl'))
        self.assertEqual(loose_key('kuawitl'), loose_key('cuahuitl'))
        self.assertNotEqual(fold('quauitl'), fold('cuahuitl'))

    def test_no_duplicate_normalizers_or_csv_readers(self):
        """El paradigma único se mantiene: nadie más quita acentos ni lee el CSV de Axolotl."""
        offenders = []
        for path in sorted((ROOT / 'nahuatl_local').glob('*.py')) + sorted((ROOT / 'scripts').glob('*.py')):
            source = path.read_text(encoding='utf-8')
            name = path.relative_to(ROOT).as_posix()
            if name != 'nahuatl_local/text.py' and re.search(r"category\([^)]*\)\s*!=\s*'Mn'", source):
                offenders.append(name + ': quita marcas por su cuenta (usa text.fold / text.strip_marks)')
            if name != 'nahuatl_local/text.py' and re.search(r'^def (phonemic_key|loose_key|es_key|es_norm|normalized|_norm)\b', source, re.M):
                offenders.append(name + ': define otra clave de normalización')
            if name != 'nahuatl_local/passages.py' and re.search(r'csv\.reader\(', source):
                offenders.append(name + ': analiza un CSV por su cuenta (usa passages)')
            if name != 'nahuatl_local/passages.py' and "'corpus/axolotl/axolotl.csv'" in source:
                offenders.append(name + ': repite la ruta del archivo (usa passages.AXOLOTL)')
        self.assertEqual(offenders, [])

    def test_browser_has_one_shared_fold(self):
        web = ROOT / 'nahuatl_local/platform_web'
        definitions = [p.name for p in web.glob('*.js') if re.search(r'\bconst norm\s*=|function norm\s*\(', p.read_text(encoding='utf-8'))]
        self.assertEqual(definitions, ['app.js'])
        self.assertNotRegex((web / 'app.js').read_text(encoding='utf-8'), r'\\u0300-\\u036f')


if __name__ == '__main__':
    unittest.main()
