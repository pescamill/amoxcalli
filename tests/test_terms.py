import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from nahuatl_local import term_evaluation
from nahuatl_local.terms import TermIndex, glyph_scope, parse

ROOT = Path(__file__).resolve().parents[1]
# Las consultas de la tarea: cada una debe llevar al mismo grupo en cualquier vista.
SAME = {'kuali': 'term-kwali', 'cualli': 'term-kwali', 'qualli': 'term-kwali', 'nocal': 'lemma-kalli',
        'calli': 'lemma-kalli', 'tonatiu': 'lemma-tonatiw', 'mujer': 'term-siwatl'}


class TermIndexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.terms = TermIndex()

    def top(self, query):
        return self.terms.search(query)['groups'][0]

    def test_every_spelling_reaches_the_same_group(self):
        for query, gid in SAME.items():
            self.assertEqual(self.top(query)['id'], gid, query)
        for gid in set(SAME.values()):
            self.assertEqual({self.top(q)['id'] for q, g in SAME.items() if g == gid}, {gid})

    def test_group_gathers_colonial_modern_and_inflected_spellings(self):
        g = self.terms.summary('term-kwali')
        attested = {v['form'] for v in g['spellings']['attested']}
        self.assertTrue({'cualli', 'qualli', 'kuali', 'kwali'} <= attested)
        self.assertEqual({v['orthography'] for v in g['spellings']['attested'] if v['form'] in ('kuali', 'kwali')}, {'moderna'})
        calli = self.terms.summary('lemma-kalli')
        inflected = {f for v in calli['spellings']['inflected'] for f in v['forms']}
        self.assertTrue({'nocal', 'ical', 'tocal'} <= inflected)
        self.assertEqual(calli['passages']['total'], sum(calli['passages']['by_variety'].values()))

    def test_homographs_and_contained_words_stay_apart(self):
        cualli = self.terms.summary('term-kwali')
        certain = {v['form'] for v in cualli['spellings']['attested']} | {f for v in cualli['spellings']['inflected'] for f in v['forms']}
        uncertain = {f for v in cualli['spellings']['uncertain'] for f in v['forms']}
        self.assertIn('tlacualli', uncertain)
        self.assertNotIn('tlacualli', certain)
        coatl = self.terms.summary('lemma-koatl')
        certain = {v['form'] for v in coatl['spellings']['attested']} | {f for v in coatl['spellings']['inflected'] for f in v['forms']}
        for form in ('quicohua', 'tecouani', 'mixcoatl', 'quetzalcoatl'):
            self.assertNotIn(form, certain, form)
        self.assertTrue(all(v['why'] for v in coatl['spellings']['uncertain']))
        self.assertFalse({g['id'] for g in coatl['glyphs']} & {g['id'] for g in coatl['glyphs_uncertain']})

    def test_glyphs_carry_their_scope(self):
        calli = self.terms.summary('lemma-kalli')
        scopes = {(g['source'], g['scope']) for g in calli['glyphs']}
        self.assertIn(('dictionary', 'word'), scopes)
        self.assertIn(('tlachia_element', 'component'), scopes)
        self.assertIn(('tlachia_occurrence', 'word'), scopes)
        self.assertEqual(glyph_scope({'glyph_type': 'element'}), 'component')
        self.assertEqual(glyph_scope({'glyph_type': 'simplex', 'association': {'type': 'related_meaning'}}), 'meaning')
        self.assertEqual(glyph_scope({'glyph_type': 'element', 'association': {'type': 'passage_reference'}}), 'thematic')
        self.assertEqual(glyph_scope({}), 'word')

    def test_spanish_and_abstention(self):
        self.assertEqual(self.terms.search('casa')['language'], 'es')
        self.assertEqual(self.top('casa')['id'], 'lemma-kalli')
        self.assertEqual(self.terms.search('xyzq')['groups'], [])
        self.assertIsNone(self.terms.resolve('dos palabras'))
        with self.assertRaises(ValueError):
            parse('dos palabras')
        with self.assertRaises(ValueError):
            self.terms.search('calli', limit=0)

    def test_evaluation_report_is_current(self):
        report = term_evaluation.run(self.terms)
        self.assertEqual(term_evaluation.REPORT.read_text(encoding='utf-8'), term_evaluation.encode(report),
                         'Regenera con python -m nahuatl_local.term_evaluation')
        self.assertEqual(report['summary']['all']['spelling_precision_labeled'], 100.0)


class OneSearchAcrossViewsTests(unittest.TestCase):
    def test_four_views_answer_with_the_same_group(self):
        from nahuatl_local import platform
        from nahuatl_local.corpus import CorpusStore
        with tempfile.TemporaryDirectory() as d:
            httpd = platform.make_server(CorpusStore(Path(d) / 'voces.sqlite3'), port=0)
            threading.Thread(target=httpd.serve_forever, daemon=True).start()
            base = f'http://127.0.0.1:{httpd.server_address[1]}'
            get = lambda path, **q: json.load(urllib.request.urlopen(base + path + '?' + urllib.parse.urlencode(q)))
            try:
                for query, gid in SAME.items():
                    self.assertEqual(get('/api/terms', q=query)['groups'][0]['id'], gid, query)
                    self.assertEqual(get('/api/research', query=query)['term']['id'], gid, query)
                    self.assertEqual(get('/api/ask', q=query)['terms'][0]['id'], gid, query)
                    self.assertEqual(get('/api/documentary', query=query)['term']['id'], gid, query)
                research = get('/api/research', query='kuali', limit=100)
                self.assertEqual(research['method'], 'term_group')
                self.assertEqual(research['total'], get('/api/terms', q='kuali')['groups'][0]['passages']['total'])
                self.assertEqual(get('/api/research', query='agua de la casa')['method'], 'bm25')  # frase: BM25
                cards = get('/api/documentary', query='calli')['results']
                self.assertEqual(cards[0]['match'], ['term_group'])
                self.assertIn('form', {c['kind'] for c in cards})
                with self.assertRaises(urllib.error.HTTPError) as error:
                    urllib.request.urlopen(base + '/api/search?query=calli')
                self.assertEqual(error.exception.code, 404)
                with self.assertRaises(urllib.error.HTTPError) as error:
                    urllib.request.urlopen(base + '/api/terms?q=dos%20palabras')
                self.assertEqual(error.exception.code, 400)
            finally:
                httpd.shutdown()
                httpd.server_close()


if __name__ == '__main__':
    unittest.main()
