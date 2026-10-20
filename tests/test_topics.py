import json
import tempfile
import threading
import unittest
import urllib.parse
import urllib.request
from pathlib import Path

from nahuatl_local.stems import WordStudy
from nahuatl_local.terms import TermIndex
from nahuatl_local.topics import MAX_QUERY, TopicIndex

ROOT = Path(__file__).resolve().parents[1]


class TopicSearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t = TopicIndex(TermIndex(WordStudy(ROOT)))

    def ids(self, query, n=5):
        return [it['id'] for it in self.t.search(query)['top'][:n]]

    def test_accepts_phrases_and_questions(self):
        r = self.t.search('¿qué dice sobre el calendario?')
        self.assertEqual(r['mode'], 'topic')
        self.assertFalse(r['abstained'])
        self.assertIn('calendar', r['interpreted']['intents'])
        self.assertTrue({'calendar:tonalpohualli', 'calendar:xiuhpohualli', 'calendar-unit:calendario'} & set(self.ids('¿qué dice sobre el calendario?')))

    def test_nahuatl_names_match_in_any_spelling(self):
        self.assertEqual(self.ids('¿quién fue Quetzalcóatl?', 1), ['entity:quetzalcoatl'])
        self.assertIn('entity:huitzilopochtli', self.ids('Huitzilopuchtli y los mexicas'))

    def test_intent_words_describe_the_kind(self):
        self.assertTrue({'note:objeto', 'unit:sujeto-objeto'} & set(self.ids('gramática del objeto')))
        self.assertTrue({'lesson:flor', 'lesson:flores-cantos'} & set(self.ids('lecturas sobre flores')))

    def test_every_result_says_why_and_links(self):
        for it in self.t.search('el sol y la luna')['top']:
            self.assertTrue(it['why'].startswith('coincide: '))
            self.assertTrue(it['label'])
        drafts = [it for it in self.t.search('los soles de antes')['top'] if it['kind'] == 'lesson-draft']
        self.assertTrue(drafts and all('revisión' in it['review'] for it in drafts))

    def test_abstains_without_coverage(self):
        r = self.t.search('criptomonedas y bolsa de valores')
        self.assertTrue(r['abstained'])
        self.assertEqual(r['top'], [])
        with self.assertRaises(ValueError):
            self.t.search('x' * (MAX_QUERY + 1))
        with self.assertRaises(ValueError):
            self.t.search('   ')

    def test_evaluation_set_is_well_formed_and_passes_dev(self):
        from nahuatl_local.topic_evaluation import run
        data = json.loads((ROOT / 'evaluation/topic-questions-v1.json').read_text(encoding='utf-8'))
        self.assertEqual(len({q['id'] for q in data['questions']}), len(data['questions']))
        r = run('dev', self.t)
        self.assertEqual(r['summary']['dev']['at5'], 100.0)
        self.assertEqual(r['summary']['dev']['abstention'], 100.0)


class TopicEndpointTests(unittest.TestCase):
    def test_ask_accepts_phrases_and_adds_related_content_to_words(self):
        from nahuatl_local.corpus import CorpusStore
        import nahuatl_local.platform as platform
        with tempfile.TemporaryDirectory() as d:
            httpd = platform.make_server(CorpusStore(Path(d) / 'v.sqlite3'), port=0)
            threading.Thread(target=httpd.serve_forever, daemon=True).start()
            try:
                base = f'http://127.0.0.1:{httpd.server_address[1]}/api/ask?'
                phrase = json.load(urllib.request.urlopen(base + urllib.parse.urlencode({'q': 'dioses de la lluvia'})))
                self.assertEqual(phrase['mode'], 'topic')
                self.assertTrue(phrase['groups'])
                word = json.load(urllib.request.urlopen(base + urllib.parse.urlencode({'q': 'calendario'})))
                self.assertNotEqual(word.get('mode'), 'topic')
                self.assertTrue(word['related']['groups'])
                self.assertTrue(all(g['id'] not in ('passages', 'senses') for g in word['related']['groups']))
            finally:
                httpd.shutdown(); httpd.server_close()


if __name__ == '__main__':
    unittest.main()
