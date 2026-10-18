import copy
import json
import tempfile
import threading
import urllib.error
import urllib.parse
import urllib.request
import unittest
from pathlib import Path

from nahuatl_local import units
from nahuatl_local.corpus import CorpusStore
from nahuatl_local.learning import Learning
from nahuatl_local.lexicon import load_records
from nahuatl_local.research import Archive
from nahuatl_local.terms import TermIndex

ROOT = Path(__file__).resolve().parents[1]
KINDS = {'match', 'identify', 'build', 'cloze', 'translate'}


class UnitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.terms = TermIndex()
        cls.corpus = units.Corpus(cls.terms, load_records())
        cls.data = json.loads(units.UNITS.read_text())

    def test_generated_files_are_current(self):
        # Cambiar el analizador, el índice, el catálogo o las lecturas obliga a regenerar (y a revisar de nuevo).
        self.assertEqual(units.main(['--check']), 0)

    def test_every_answer_is_backed_by_passage_and_analysis(self):
        self.assertGreaterEqual(len(self.data['units']), 3)
        for unit in self.data['units']:
            self.assertEqual(units.check_unit(self.corpus, unit), [], unit['id'])
            self.assertEqual({e['kind'] for e in unit['exercises']}, KINDS)
            self.assertTrue(5 <= unit['minutes'] <= 10)
            self.assertEqual(unit['review_status'], 'automatic_draft')
            self.assertTrue(unit['closing']['forms'])

    def test_check_rejects_unbacked_answers(self):
        unit = self.data['units'][0]
        broken = []
        for kind, change in [('cloze', lambda e: e.update(answer=(e['answer'] + 1) % 3)),
                             ('translate', lambda e: e.update(answer=(e['answer'] + 1) % 3)),
                             ('identify', lambda e: e.update(answer=(e['answer'] + 1) % 3)),
                             ('build', lambda e: e.update(answer=list(reversed(e['answer'])))),
                             ('match', lambda e: e['pairs'][0].update(gloss=e['pairs'][1]['gloss'])),
                             ('cloze', lambda e: e['evidence'][0].update(source_hash='0' * 64)),
                             ('identify', lambda e: e['evidence'][0].update(segmentation='x-y'))]:
            copy_ = copy.deepcopy(unit)
            change(next(e for e in copy_['exercises'] if e['kind'] == kind))
            broken.append((kind, units.check_unit(self.corpus, copy_)))
        for kind, problems in broken:
            self.assertTrue(problems, kind)

    def test_cloze_distractors_share_the_root(self):
        for unit in self.data['units']:
            for e in (e for e in unit['exercises'] if e['kind'] == 'cloze'):
                stems = {self.corpus.analysis(ev['form'], ev['sense_id'])['stem_key'] for ev in e['evidence']}
                self.assertEqual(len(stems), 1, e['id'])
                self.assertEqual(len({o.casefold() for o in e['options']}), 3)

    def test_review_needs_reviewer_and_exact_fingerprint(self):
        recipe = json.loads(units.RECIPE.read_text())
        found = units.findings(self.data['units'], recipe)
        task = found[0]
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'decisions.json'

            def state(decision):
                path.write_text(json.dumps(dict(schema_version=1, decisions={task['id']: decision} if decision else {})))
                return units.review_state(found, path)[task['lesson_id']]
            complete = dict(fingerprint=task['fingerprint'], status='resolved', reviewer='Revisora de prueba', date='2026-10-15',
                            evidence=['cotejo'], resolution='Aceptada')
            self.assertEqual(state(None)['status'], 'automatic_draft')
            self.assertEqual(state(dict(complete, reviewer=''))['status'], 'automatic_draft')
            stale = state(dict(complete, fingerprint='0' * 64))
            self.assertEqual((stale['status'], stale['stale']), ('automatic_draft', True))
            reviewed = state(complete)
            self.assertEqual((reviewed['status'], reviewed['reviewer']), ('reviewed', 'Revisora de prueba'))
        # El archivo real de decisiones no revisa nada generado.
        self.assertEqual({s['status'] for s in units.review_state(found).values()}, {'automatic_draft'})

    def test_readings_are_proposed_not_published(self):
        proposal = json.loads(units.PROPOSAL.read_text())
        published = json.loads(units.LEARNING.read_text())
        new = [l for l in proposal['learning']['lessons'] if l['id'] not in {p['id'] for p in published['lessons']}]
        self.assertGreaterEqual(len(new), 6)
        self.assertFalse(any(l['id'].startswith('gen-') for l in published['lessons']))
        self.assertEqual(proposal['summary']['primary_review'], False)
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'learning.json'
            path.write_text(json.dumps(proposal['learning'], ensure_ascii=False))
            catalog = Learning(Archive(), path).catalog(CorpusStore(Path(d) / 'c.sqlite3').public_records())
        self.assertEqual(len(catalog['lessons']), len(published['lessons']) + len(new))
        for lesson in new:
            notes = [a['note'] for e in lesson['examples'] for a in e['annotations']]
            self.assertTrue(all('automáticamente' in n for n in notes), lesson['id'])
            for e in lesson['examples']:
                self.assertIn(e['comprehension']['options'][e['comprehension']['answer']], e['passage']['es'] if 'passage' in e else Archive().get(e['archive_id'])['es'])

    def test_coverage_names_morphemes_and_roots_per_unit(self):
        cov = json.loads(units.COVERAGE.read_text())
        self.assertEqual(cov['totals']['valid_answers'], cov['totals']['answers'])
        for u in cov['units']:
            self.assertTrue(u['morphemes'] and u['roots'] and u['passages'])
            self.assertEqual(u['validity']['problems'], [])
        self.assertTrue(all(s['reason'].startswith('insufficient') for s in cov['skipped']))


    def test_http_units_and_review_examples(self):
        from nahuatl_local import platform
        with tempfile.TemporaryDirectory() as d:
            httpd = platform.make_server(CorpusStore(Path(d) / 'voces.sqlite3'), port=0)
            threading.Thread(target=httpd.serve_forever, daemon=True).start()
            base = f'http://127.0.0.1:{httpd.server_address[1]}'
            get = lambda path, **q: json.load(urllib.request.urlopen(base + path + '?' + urllib.parse.urlencode(q)))
            try:
                data = get('/api/units')
                self.assertEqual(data['validation']['served'], len(self.data['units']))
                for unit in data['units']:
                    self.assertEqual(unit['review']['status'], 'automatic_draft')
                    self.assertIsNone(unit['review']['reviewer'])
                    self.assertIn(unit['closing']['archive_id'], unit['passages'])
                self.assertEqual(len(data['proposed_readings']), 6)
                self.assertTrue(all(r['review']['status'] == 'automatic_draft' for r in data['proposed_readings']))
                examples = get('/api/units/examples', sense='sense-calli')['examples']
                self.assertGreaterEqual(len(examples), 2)
                self.assertGreater(len({e['segmentation'].split('-')[0] for e in examples}), 1)
                for e in examples:
                    self.assertIn(e['form'], e['nah'])
                    self.assertTrue(e['automatic'])
                with self.assertRaises(urllib.error.HTTPError) as error:
                    urllib.request.urlopen(base + '/api/units/examples?sense=sense-inexistente')
                self.assertEqual(error.exception.code, 404)
            finally:
                httpd.shutdown()
                httpd.server_close()


if __name__ == '__main__':
    unittest.main()
