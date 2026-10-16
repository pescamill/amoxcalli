"""Measured-input boundary over isolated public copies; no new measurement."""
import copy
from pathlib import Path
import shutil
import tempfile
import unittest

from nahuatl_local.community import ROOT
from nahuatl_local import documentary_laboratory as lab
from nahuatl_local.documentary_evaluation import load_development
from nahuatl_local.documentary_retrieval import PublicSources
from nahuatl_local.documentary_retrieval_evaluation import manifest, validate_report

# Presentation is verified by the DOM suite, never hashed into measured evidence.
PRESENTATION = ('nahuatl_local/platform.py', 'nahuatl_local/laboratory.py',
                'nahuatl_local/platform_web/app.js', 'nahuatl_local/platform_web/reading.js',
                'nahuatl_local/platform_web/laboratory.js', 'nahuatl_local/platform_web/amoxcalli.css',
                'nahuatl_local/platform_web/index.html', 'tests/platform_ui.cjs', 'scripts/test-platform-ui.py')


class DocumentaryDependencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.retrieval = lab.read(lab.RETRIEVAL_REPORT)
        cls.comparison = lab.read(lab.REPORT)
        cls.queries = load_development(modality='textual')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        paths = set(self.retrieval['input_hashes']) | set(self.comparison['input_hashes']) | set(PRESENTATION)
        for relative in paths:
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)

    def test_presentation_change_keeps_measurement_and_comparison_valid(self):
        checked = dict(valid=True, errors=[])
        for relative in PRESENTATION:
            with self.subTest(relative=relative):
                path = self.root / relative
                path.write_bytes(path.read_bytes() + b'\n/* presentation changed */\n')
                self.assertEqual(manifest(PublicSources(self.root)), self.retrieval['input_hashes'])
                self.assertTrue(lab.validate_report(self.comparison, root=self.root, retrieval_validation=checked)['valid'])
        self.assertTrue(validate_report(self.retrieval, root=self.root)['valid'])

    def test_ranker_store_corpus_source_config_battery_and_evaluator_remain_measured_inputs(self):
        # Records come from the canonical lexicon catalog, so its builder and readers are measured,
        # not the server's store (a fresh store equals the catalog: tests/test_lexicon.py).
        for relative in ('nahuatl_local/documentary_retrieval.py', 'nahuatl_local/lexicon.py',
                         'nahuatl_local/passages.py', 'nahuatl_local/text.py', 'corpus/lexicon-catalog.json',
                         'corpus/seed.json', 'configs/sources.json', 'configs/documentary-evaluation-v1.json',
                         'nahuatl_local/documentary_retrieval_evaluation.py', 'nahuatl_local/documentary_evaluation.py'):
            with self.subTest(relative=relative):
                path = self.root / relative
                original = path.read_bytes()
                path.write_bytes(original + b'\n')
                checked = validate_report(self.retrieval, queries=self.queries, root=self.root, replay=False)
                self.assertFalse(checked['valid'])
                self.assertIn('stale_inputs', checked['errors'])
                path.write_bytes(original)

    def test_forged_response_still_fails_independent_replay(self):
        report = copy.deepcopy(self.retrieval)
        row = next(r for r in report['results'] if r['response']['results'])
        row['response']['results'][0]['label'] = 'Invented source-supported answer'
        checked = validate_report(report, root=self.root)
        self.assertFalse(checked['valid'])
        self.assertIn('response_replay:' + row['query_id'], checked['errors'])

    def test_measured_manifests_exclude_presentation(self):
        for measured in (self.retrieval['input_hashes'], self.comparison['input_hashes']):
            self.assertFalse(set(PRESENTATION).intersection(measured))
        # This document defines the fixed battery recipe, so it stays measured.
        self.assertIn('docs/EVALUACION_DOCUMENTAL.md', self.retrieval['input_hashes'])


if __name__ == '__main__':
    unittest.main()
