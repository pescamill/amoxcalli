import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from nahuatl_local.evidence import Evidence, loose_key
from nahuatl_local.morphology import key_of
from nahuatl_local.stems import WordStudy

ROOT = Path(__file__).resolve().parents[1]


class LooseKeyTests(unittest.TestCase):
    def test_modern_and_colonial_spellings_meet(self):
        for group in (['kuali', 'cualli', 'qualli', 'cuali'], ['tsontli', 'tzontli'], ['kali', 'calli'],
                      ['kuawitl', 'cuahuitl', 'quauitl'], ['tlajtoli', 'tlahtolli', 'tlatolli'], ['tonatiu', 'tonatiuh'],
                      ['nimann', 'niman'], ['metstli', 'metztli']):
            self.assertEqual(len({loose_key(w) for w in group}), 1, group)

    def test_loose_key_does_not_change_the_evaluated_phonemic_key(self):
        self.assertNotEqual(key_of('kuali'), key_of('cualli'))
        self.assertEqual(key_of('niquitta'), 'nikitta')

    def test_distinct_words_stay_distinct(self):
        self.assertNotEqual(loose_key('calli'), loose_key('cualli'))
        self.assertNotEqual(loose_key('atl'), loose_key('tletl'))


class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ws = WordStudy(ROOT)
        cls.e = Evidence(cls.ws)

    def test_parse_accepts_one_word_or_a_short_question(self):
        self.assertEqual(self.e.parse('¿Qué significa xochitl?'), ('xochitl', 'nah'))
        self.assertEqual(self.e.parse('¿Cómo se dice el cerro en náhuatl?'), ('cerro', 'es'))
        self.assertEqual(self.e.parse('  nocal '), ('nocal', None))
        for bad in ('', 'dos palabras', 'x' * 121, None):
            with self.assertRaises(ValueError):
                self.e.parse(bad)

    def test_language_detection(self):
        r = self.e.ask('casa')
        self.assertEqual(r['language'], 'es')
        self.assertEqual(self.e.ask('atl')['language'], 'nah')
        self.assertEqual(self.e.ask('in')['language'], 'nah')

    def test_inflected_form_reaches_its_entry_and_root_passages(self):
        r = self.e.ask('nocal')
        self.assertEqual(r['analysis']['segmentation'], 'no-cal')
        self.assertEqual(r['entries'][0]['written'], 'calli')
        self.assertGreaterEqual(len(r['passages']), 3)
        for p in r['passages']:
            self.assertIn(p['form'], p['nah'])
            self.assertTrue(p['why'])
        self.assertEqual(r['method']['model_calls'], 0)

    def test_modern_spelling_is_read_through_an_attested_classical_spelling(self):
        r = self.e.ask('kuali')
        self.assertEqual(r['interpreted_as'], 'cualli')
        self.assertFalse(r['abstained'])
        forms = {v['form'] for v in r['variants']}
        self.assertTrue({'cualli', 'qualli'} <= forms)
        self.assertEqual(self.e.ask('kali')['entries'][0]['written'], 'calli')
        self.assertEqual(self.e.ask('nimann')['interpreted_as'], 'niman')

    def test_spanish_question_returns_a_supported_root_not_a_definition(self):
        r = self.e.ask('¿cómo se dice mujer?')
        self.assertEqual(r['language'], 'es')
        self.assertEqual(r['candidates'][0]['stem_key'], 'siwa')
        self.assertGreaterEqual(r['candidates'][0]['support'], 8)
        for p in r['passages']:
            self.assertIn('mujer', p['es'].casefold())
        self.assertIn('asociación estadística', r['note'])

    def test_spanish_entry_comes_from_the_definition(self):
        r = self.e.ask('agua')
        self.assertEqual(r['entries'][0]['written'], 'atl')

    def test_without_supported_root_spanish_shows_translations_without_an_equivalent(self):
        r = self.e.ask('pájaro')
        self.assertEqual(r['candidates'], [])
        self.assertTrue(r['passages'])
        for p in r['passages']:
            self.assertIsNone(p['form'])
            self.assertIn('no se propone equivalente', p['why'])

    def test_abstains_without_evidence(self):
        r = self.e.ask('xyzq')
        self.assertTrue(r['abstained'])
        self.assertEqual(r['entries'], [])
        self.assertEqual(r['passages'], [])
        self.assertIn('evidencia', r['reason'])


class EvidenceEvaluationTests(unittest.TestCase):
    def test_question_set_is_well_formed(self):
        data = json.loads((ROOT / 'evaluation/evidence-questions-v1.json').read_text(encoding='utf-8'))
        ids = [q['id'] for q in data['questions']]
        self.assertEqual(len(ids), len(set(ids)))
        for q in data['questions']:
            self.assertIn(q['split'], ('dev', 'test'))
            self.assertTrue(q.get('abstain') or q['root'], q['id'])

    def test_evidence_beats_exact_search_on_held_out_questions(self):
        from nahuatl_local.evidence_evaluation import run
        r = run('test', write=False)
        base, ours = r['summary']['exact_search']['test'], r['summary']['evidence']['test']
        self.assertGreater(ours['entry_at1'], base['entry_at1'])
        self.assertGreaterEqual(ours['passage_hit'], base['passage_hit'])
        self.assertEqual(r['model_calls'], 0)


class EvidenceEndpointTests(unittest.TestCase):
    def test_api_ask(self):
        from nahuatl_local.corpus import CorpusStore
        import nahuatl_local.platform as platform
        with tempfile.TemporaryDirectory() as d:
            httpd = platform.make_server(CorpusStore(Path(d) / 'voces.sqlite3'), port=0)
            threading.Thread(target=httpd.serve_forever, daemon=True).start()
            try:
                base = f'http://127.0.0.1:{httpd.server_address[1]}'
                r = json.load(urllib.request.urlopen(base + '/api/ask?q=nocal'))
                self.assertEqual(r['entries'][0]['written'], 'calli')
                with self.assertRaises(urllib.error.HTTPError) as err:
                    urllib.request.urlopen(base + '/api/ask?q=dos%20palabras')
                self.assertEqual(err.exception.code, 400)
                self.assertIn('sola palabra', json.load(err.exception)['error'])
                self.assertIn('renderAsk', urllib.request.urlopen(base + '/evidence.js').read().decode())
            finally:
                httpd.shutdown(); httpd.server_close()


if __name__ == '__main__':
    unittest.main()
