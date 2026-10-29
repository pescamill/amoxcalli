"""Aclaraciones: validación, almacén local, lectura desde un issue y clasificación para quien revisa."""
import json
import tempfile
import unittest
from pathlib import Path

from nahuatl_local.aclaraciones import MARK, Store, clean, extract, lookup, triage
from nahuatl_local.community import Problem


def item(**kw):
    return dict(dict(target='axolotl-00602', category='traduccion', basis='fuente', note='Falta «una mujer»',
                     proposal='y otra vez una mujer le puso pleito', citation='Reyes 1996, p. 4',
                     context=dict(nah='Auh on ceppan', es='Y demas desto', route='#preguntar/mujer')), **kw)


class AclaracionesTests(unittest.TestCase):
    def test_clean_keeps_only_known_fields_and_requires_a_category(self):
        out = clean(dict(item(), name='Ana', email='ana@example.org', variant='huasteca'))
        self.assertNotIn('name', out)
        self.assertNotIn('email', out)
        self.assertEqual(out['variant'], '')  # la variante solo cuenta si habla una variante actual
        self.assertEqual(clean(item(basis='hablante', variant='huasteca'))['variant'], 'huasteca')
        for bad in (item(category=''), item(category='x'), item(target='<script>'), item(basis='otro'),
                    item(note='x' * 1001)):
            with self.subTest(bad=bad), self.assertRaises(Problem):
                clean(bad)

    def test_store_add_list_remove(self):
        with tempfile.TemporaryDirectory() as d:
            store = Store(Path(d) / 'a.jsonl')
            a = store.add(item())
            self.assertTrue(a['id'].startswith('ac-'))
            self.assertEqual([x['id'] for x in store.all()], [a['id']])
            store.remove(a['id'])
            self.assertEqual(store.all(), [])
            with self.assertRaises(Problem):
                store.remove(a['id'])

    def test_extract_from_issue_body_and_from_downloaded_file(self):
        body = f'**La traducción no corresponde**\n\n{MARK}\n```json\n{json.dumps(item(), ensure_ascii=False)}\n```'
        self.assertEqual(extract(body)[0]['target'], 'axolotl-00602')
        self.assertEqual(len(extract(json.dumps(dict(items=[item(), item(category='duda')])))), 2)
        self.assertEqual(extract('Texto libre sin bloque'), [])

    def test_triage_labels_and_compares_with_current_record(self):
        current = lookup('axolotl-00602')
        self.assertIn('mujer', current['es'])
        out = triage(clean(item()), current)
        self.assertEqual(out['labels'], ['aclaración', 'traducción'])
        self.assertIn('Registro actual', out['comment'])
        self.assertIn('Reyes 1996', out['comment'])
        speaker = triage(clean(item(category='uso', basis='hablante', variant='huasteca')), current)
        self.assertIn('variante-actual', speaker['labels'])
        self.assertIn('id-no-encontrado', triage(clean(item(target='axolotl-99999')), lookup('axolotl-99999'))['labels'])


if __name__ == '__main__':
    unittest.main()
