import csv
import unittest
from pathlib import Path

from nahuatl_local import passages
from nahuatl_local.documentary_retrieval import PublicSources
from nahuatl_local.research import Archive

ROOT = Path(__file__).resolve().parents[1]


class PassageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = passages.load()

    def test_single_reader_matches_the_csv_module_over_the_file(self):
        with (ROOT / passages.AXOLOTL).open(encoding='utf-8', newline='') as file:
            expected = list(enumerate(csv.reader(file), 1))
        self.assertEqual(passages.records(), expected)
        self.assertEqual(len(expected), 16111)

    def test_passage_model(self):
        self.assertEqual(len(self.rows), 16111)
        first = self.rows[0]
        self.assertEqual(set(first), {'id', 'line', 'es', 'nah', 'variant', 'iso', 'variant_label', 'period', 'document',
                                      'locator', 'source_url', 'rights_note', 'verification'})
        self.assertEqual(first['id'], 'axolotl-00001')
        self.assertTrue(first['source_url'].startswith('https://github.com/'))
        self.assertTrue(first['rights_note'])
        unknown = [r for r in self.rows if r['iso'] == 'unknown']
        self.assertTrue(unknown and all(r['period'] == 'unknown' for r in unknown))
        self.assertEqual({r['period'] for r in self.rows if r['iso'] == 'nci'}, {'historical'})

    def test_unusable_records_are_not_passages(self):
        self.assertIsNone(passages.passage(1, ['es', 'nah', 'v', 'doc']))
        self.assertIsNone(passages.passage(1, ['  ', 'nah', 'v', 'doc', 'nci']))
        self.assertEqual(passages.passage(7, ['es', 'nah', 'v', 'doc', ''])['iso'], 'unknown')
        self.assertEqual(passages.original(['a', 'b', 'c', 'd', 'e']),
                         dict(es='a', nah='b', variant='c', document='d', iso='e'))

    def test_cached_records_are_defensive_copies(self):
        first = passages.records()
        first[0][1][0] = 'cambiado'
        self.assertNotEqual(passages.records()[0][1][0], 'cambiado')

    def test_application_and_documentary_lookup_share_the_model(self):
        self.assertEqual(Archive().rows, self.rows)
        sources = PublicSources()
        self.assertEqual(list(sources.archive.values()), self.rows)
        # Las citas documentales conservan los campos originales, incluida la variedad vacía.
        empty = next(r for r in self.rows if r['iso'] == 'unknown')
        self.assertEqual(passages.original(sources.csv_rows[empty['id']])['iso'], '')


if __name__ == '__main__':
    unittest.main()
