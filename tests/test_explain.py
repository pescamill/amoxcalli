import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from types import SimpleNamespace

from nahuatl_local.evidence import Evidence
from nahuatl_local.explain import ClaudeWriter, bundle, explain, extractive, sentences_of, validate
from nahuatl_local.stems import WordStudy

ROOT = Path(__file__).resolve().parents[1]
ITEMS = {'axolotl-00001': dict(kind='passage', id='axolotl-00001', text='niquitta in xochitl || veo la flor'),
         'sense-xochitl': dict(kind='entry', id='sense-xochitl', text='xochitl: flor')}


class FakeClient:
    """Imita ``client.beta.messages.create`` y registra la petición."""

    def __init__(self, text='', stop_reason='end_turn'):
        self.text, self.stop_reason, self.calls = text, stop_reason, []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self.create))

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(stop_reason=self.stop_reason, model=kwargs['model'],
                               content=[SimpleNamespace(type='text', text=self.text)],
                               usage=SimpleNamespace(input_tokens=10, output_tokens=5))


class ValidatorTests(unittest.TestCase):
    def test_accepts_cited_sentences_with_supported_quotes(self):
        v = validate('«xochitl» significa «flor» [sense-xochitl]. Aparece en «niquitta in xochitl» [axolotl-00001].', ITEMS)
        self.assertTrue(v['valid'], v['errors'])
        self.assertEqual([s['citations'] for s in v['sentences']], [['sense-xochitl'], ['axolotl-00001']])
        self.assertNotIn('[', v['sentences'][0]['text'])

    def test_rejects_missing_unknown_and_unsupported(self):
        self.assertIn('frase_sin_cita', validate('Significa flor.', ITEMS)['errors'][0])
        self.assertIn('cita_fuera_de_evidencia', validate('Significa flor [axolotl-99999].', ITEMS)['errors'][0])
        self.assertIn('cita_textual_no_respaldada', validate('Se dice «cihuatl» [sense-xochitl].', ITEMS)['errors'][0])
        self.assertFalse(validate('', ITEMS)['valid'])

    def test_sentence_split_ignores_periods_inside_quotes(self):
        self.assertEqual(len(sentences_of('Dice «Hola. Adiós.» [axolotl-00001]. Otra frase [sense-xochitl].')), 2)


class ExplainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.e = Evidence(WordStudy(ROOT))

    def test_extractive_explanations_validate_on_the_question_set(self):
        questions = json.loads((ROOT / 'evaluation/evidence-questions-v1.json').read_text(encoding='utf-8'))['questions']
        for q in questions:
            r = self.e.ask(q['query'])
            x = explain(r)
            with self.subTest(q=q['query']):
                self.assertTrue(x['valid'], x.get('errors'))
                self.assertEqual(x['model_calls'], 0)
                if not r['abstained']:
                    self.assertTrue(x['sentences'])
                    for s in x['sentences']:
                        self.assertTrue(set(s['citations']) <= set(bundle(r)))

    def test_claude_answer_is_used_only_when_it_validates(self):
        r = self.e.ask('nocal')
        cite = r['passages'][0]['id']
        good = FakeClient(f'«nocal» contiene la raíz de «calli», «casa» [{r["entries"][0]["sense_id"]}]. Hay un ejemplo en el archivo [{cite}].')
        x = explain(r, ClaudeWriter(client=good))
        self.assertEqual(x['method'], 'claude')
        self.assertEqual(x['model_calls'], 1)
        call = good.calls[0]
        self.assertEqual(call['model'], 'claude-opus-5-5')
        self.assertEqual(call['fallbacks'], 'default')
        self.assertIn(cite, call['messages'][0]['content'])
        bad = explain(r, ClaudeWriter(client=FakeClient('Significa «mi casa grande» [axolotl-99999].')))
        self.assertEqual(bad['method'], 'extractive')
        self.assertIn('validación de citas', bad['fallback_reason'])
        refused = explain(r, ClaudeWriter(client=FakeClient('', stop_reason='refusal')))
        self.assertEqual(refused['method'], 'extractive')
        self.assertIn('declinó', refused['fallback_reason'])
        unsure = explain(r, ClaudeWriter(client=FakeClient('No hay evidencia suficiente.')))
        self.assertEqual(unsure['method'], 'extractive')

    def test_abstention_has_no_explanation(self):
        x = explain(self.e.ask('xyzq'), ClaudeWriter(client=FakeClient('Inventado [sense-x].')))
        self.assertEqual(x['method'], 'none')
        self.assertEqual(x['model_calls'], 0)


class ExplainEndpointTests(unittest.TestCase):
    def serve(self, **kwargs):
        from nahuatl_local.corpus import CorpusStore
        import nahuatl_local.platform as platform
        self.tmp = tempfile.TemporaryDirectory()
        httpd = platform.make_server(CorpusStore(Path(self.tmp.name) / 'v.sqlite3'), port=0, **kwargs)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        self.addCleanup(lambda: (httpd.shutdown(), httpd.server_close(), self.tmp.cleanup()))
        return f'http://127.0.0.1:{httpd.server_address[1]}'

    def test_claude_is_off_unless_enabled(self):
        base = self.serve()
        r = json.load(urllib.request.urlopen(base + '/api/ask?q=nocal'))
        self.assertEqual(r['explain_models'], ['extractive'])
        self.assertEqual(r['explanation']['method'], 'extractive')
        with self.assertRaises(urllib.error.HTTPError) as err:
            urllib.request.urlopen(base + '/api/explain?q=nocal&model=claude')
        self.assertEqual(err.exception.code, 400)

    def test_enabled_claude_without_sdk_or_credentials_falls_back(self):
        import nahuatl_local.platform as platform
        original = platform.ClaudeWriter
        platform.ClaudeWriter = lambda: ClaudeWriter(client=FakeClient('', stop_reason='refusal'))
        try:
            base = self.serve(explain_model='claude')
        finally:
            platform.ClaudeWriter = original
        r = json.load(urllib.request.urlopen(base + '/api/ask?q=nocal'))
        self.assertIn('claude', r['explain_models'])
        x = json.load(urllib.request.urlopen(base + '/api/explain?q=nocal&model=claude'))
        self.assertEqual(x['method'], 'extractive')
        self.assertTrue(x['fallback_reason'])


if __name__ == '__main__':
    unittest.main()
