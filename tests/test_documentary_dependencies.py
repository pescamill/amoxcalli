"""Dependency boundaries over isolated public copies; no new measurement."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from nahuatl_local.community import ROOT
from nahuatl_local import documentary_laboratory as lab, iteration
from nahuatl_local.documentary_evaluation import load_development
from nahuatl_local.documentary_retrieval import PublicSources
from nahuatl_local.documentary_retrieval_evaluation import manifest, validate_report


class DocumentaryDependencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.retrieval = lab.read(lab.RETRIEVAL_REPORT)
        cls.comparison = lab.read(lab.REPORT)
        cls.diagnostic = iteration.source_manifest()
        cls.queries = load_development(modality='textual')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        paths = set(self.retrieval['input_hashes']) | set(lab.DISPLAY_SOURCES) | set(self.diagnostic)
        for relative in paths:
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)

    def diagnostic_manifest(self):
        with patch.object(iteration, 'ROOT', self.root), patch.object(iteration, 'CATALOG', self.root / 'corpus/pictography/catalog.json'):
            return iteration.source_manifest()

    def test_learning_and_css_change_display_diagnosis_without_changing_retrieval(self):
        self.assertTrue(validate_report(self.retrieval, root=self.root)['valid'])
        self.assertTrue(lab.validate_report(self.comparison, root=self.root)['valid'])
        for relative in ('nahuatl_local/platform_web/learning.js', 'nahuatl_local/platform_web/style.css'):
            with self.subTest(relative=relative):
                path = self.root / relative
                before = path.read_bytes()
                path.write_bytes(before + b'\n/* presentation changed */\n')
                self.assertEqual(manifest(PublicSources(self.root)), self.retrieval['input_hashes'])
                self.assertTrue(validate_report(self.retrieval, root=self.root)['valid'])
                checked = dict(valid=True, errors=[])
                self.assertTrue(lab.validate_report(self.comparison, root=self.root, retrieval_validation=checked,
                                                    require_display=False)['valid'])
                invalid = lab.validate_report(self.comparison, root=self.root, retrieval_validation=checked)
                self.assertIn('display_contract_or_stale_inputs', invalid['errors'])
                self.assertNotEqual(self.diagnostic_manifest()[relative], self.diagnostic[relative])
                path.write_bytes(before)

    def test_process_guides_change_diagnosis_without_changing_measurement_or_display(self):
        for relative in ('docs/TRABAJO_AUTONOMO.md', 'docs/PROPOSITO.md', 'docs/ITERACIONES.md',
                         'docs/LABORATORIO.md', 'docs/CONSULTA_DOCUMENTAL.md'):
            with self.subTest(relative=relative):
                path = self.root / relative
                path.write_bytes(path.read_bytes() + b'\nProcess guidance changed.\n')
                self.assertEqual(manifest(PublicSources(self.root)), self.retrieval['input_hashes'])
                self.assertTrue(lab.validate_report(self.comparison, root=self.root,
                                                    retrieval_validation=dict(valid=True, errors=[]))['valid'])
                self.assertNotEqual(self.diagnostic_manifest()[relative], self.diagnostic[relative])

    def test_ranker_store_corpus_source_config_battery_and_evaluator_remain_measured_inputs(self):
        for relative in ('nahuatl_local/documentary_retrieval.py', 'nahuatl_local/corpus.py',
                         'corpus/seed.json', 'configs/sources.json',
                         'nahuatl_local/community_web/catalog.json', 'configs/documentary-evaluation-v1.json',
                         'nahuatl_local/documentary_retrieval_evaluation.py'):
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

    def test_contracts_exclude_process_guides_and_presentation_from_measured_manifest(self):
        measured = self.retrieval['input_hashes']
        self.assertFalse(set(lab.DISPLAY_SOURCES).intersection(measured))
        self.assertNotIn('nahuatl_local/iteration.py', measured)
        self.assertNotIn('nahuatl_local/lesson_audit.py', measured)
        self.assertNotIn('docs/TRABAJO_AUTONOMO.md', measured)
        self.assertNotIn('tests/test_laboratory.py', lab.DISPLAY_SOURCES)
        self.assertNotIn('tests/test_iteration.py', lab.DISPLAY_SOURCES)
        self.assertIn('tests/test_laboratory.py', self.diagnostic)
        self.assertIn('tests/test_iteration.py', self.diagnostic)
        # This document defines the fixed battery recipe, not execution cadence.
        self.assertIn('docs/EVALUACION_DOCUMENTAL.md', measured)
        self.assertTrue(set(lab.DISPLAY_SOURCES).issubset(lab.display_contract(self.comparison)['presentation_hashes']))
