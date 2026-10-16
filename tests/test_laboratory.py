import hashlib
import copy
import os
import shutil
from unittest.mock import patch
import json
from pathlib import Path
import tempfile
import unittest
from nahuatl_local.laboratory import snapshot, REPORTS

PRESENTATION = 'nahuatl_local/platform_web/amoxcalli.css'


class LaboratoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.capability = dict(ready=False, disabled=True)

    def tearDown(self):
        self.tmp.cleanup()

    def put(self, path, value):
        p = self.root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(value))
        return hashlib.sha256(p.read_bytes()).hexdigest()

    def test_missing_reports_do_not_claim_progress(self):
        d = snapshot(self.capability, root=self.root)
        self.assertFalse(d['training']['available'])
        self.assertIsNone(d['training']['current_data_matches'])
        self.assertFalse(d['generation']['comparable'])
        self.assertFalse(d['retrieval']['current_data_matches'])
        self.assertEqual(d['reports'], [])
        self.assertEqual(d['model'], self.capability)

    def test_hashes_distinguish_archived_training_and_current_retrieval(self):
        hashes = {s:self.put(f'data/prepared/{s}.jsonl', [s]) for s in ('train', 'validation')}
        self.put(REPORTS['training'], dict(dataset_sha256=hashes, completed_steps=250))
        self.put(REPORTS['retrieval'], dict(train_sha256=hashes['train'], dataset_sha256=hashes['validation'], n=100))
        d = snapshot(self.capability, self.root/'outputs/continued-unseen/run/best', self.root)
        self.assertTrue(d['active_is_reference'])
        self.assertTrue(d['training']['current_data_matches'])
        self.assertTrue(d['retrieval']['current_data_matches'])
        self.put('data/prepared/train.jsonl', ['changed'])
        d = snapshot(self.capability, self.root/'outputs/another/best', self.root)
        self.assertFalse(d['active_is_reference'])
        self.assertFalse(d['training']['current_data_matches'])
        self.assertFalse(d['retrieval']['current_data_matches'])

    def test_changed_evaluation_sample_or_format_is_not_comparable(self):
        before = dict(ids=['one'], dataset_sha256='hash', split='validation', metric_signature='sig', rag=False, chrF_plus_plus=22.58)
        self.put(REPORTS['before'], before)
        after = dict(before, chrF_plus_plus=27.96)
        self.put(REPORTS['after'], after)
        self.assertTrue(snapshot(self.capability, root=self.root)['generation']['comparable'])
        for key,value in [('ids',['other']), ('dataset_sha256','other'), ('split','test'), ('metric_signature','other'), ('rag',True)]:
            self.put(REPORTS['after'], dict(after, **{key:value}))
            self.assertFalse(snapshot(self.capability, root=self.root)['generation']['comparable'], key)
        self.put(REPORTS['before'], dict(ids=['one']))
        self.put(REPORTS['after'], dict(ids=['one']))
        self.assertFalse(snapshot(self.capability, root=self.root)['generation']['comparable'])

    def test_corrupt_report_is_unavailable(self):
        p = self.root / REPORTS['training']; p.parent.mkdir(parents=True)
        p.write_text('{unfinished')
        self.assertFalse(snapshot(self.capability, root=self.root)['training']['available'])


class DocumentaryLaboratoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from nahuatl_local import documentary_laboratory as lab
        from nahuatl_local.documentary_retrieval_evaluation import validate_report
        cls.lab = lab
        cls.retrieval = lab.read(lab.RETRIEVAL_REPORT)
        cls.retrieval_validation = validate_report(cls.retrieval)
        cls.report = lab.read(lab.REPORT)

    def checked(self, report):
        return self.lab.validate_report(report, retrieval=self.retrieval,
                                        retrieval_validation=self.retrieval_validation)

    def test_current_artifact_matches_independently_replayed_retrieval(self):
        self.assertTrue(self.retrieval_validation['valid'], self.retrieval_validation)
        self.assertTrue(self.checked(self.report)['valid'])
        self.assertEqual([r['status'] for r in self.report['runs']], ['measured', 'not_run', 'not_run'])
        self.assertEqual(self.report['runs'][0]['metrics'], self.retrieval['metrics'])
        self.assertEqual(self.report['runs'][0]['metrics']['complete'], 119)
        self.assertEqual(len(self.report['runs'][0]['failures']), 4)
        self.assertNotIn(self.lab.REPORT, self.report['input_hashes'])

    def test_metrics_costs_method_states_and_sources_cannot_be_fabricated(self):
        for change in ('stale_hash', 'generated_metrics', 'fake_not_run_cost', 'fake_model_score',
                       'missing_method', 'duplicate_method', 'measured_model', 'missing_reason',
                       'private_path', 'raised_rights', 'human_review', 'wrong_battery', 'boolean_number'):
            r = copy.deepcopy(self.report)
            if change == 'stale_hash':r['input_hashes']['docs/LABORATORIO.md'] = '0' * 64
            if change == 'generated_metrics':r['runs'][0]['metrics']['complete'] = 123
            if change == 'fake_not_run_cost':r['runs'][1]['cost'] = dict(elapsed_seconds=0)
            if change == 'fake_model_score':r['runs'][2]['metrics'] = dict(complete=123)
            if change == 'missing_method':r['runs'].pop()
            if change == 'duplicate_method':r['runs'][2]['method'] = 'textual_model'
            if change == 'measured_model':r['runs'][1]['status'] = 'measured'
            if change == 'missing_reason':r['runs'][2].pop('reason')
            if change == 'private_path':r['input_hashes']['data/community/private.sqlite3'] = '0' * 64
            if change == 'raised_rights':r['rights']['image_model_input'] = True
            if change == 'human_review':r['human_review'] = 'reviewed'
            if change == 'wrong_battery':r['battery']['evaluated_split'] = 'reserve'
            if change == 'boolean_number':r['schema_version'] = True
            with self.subTest(change=change):self.assertFalse(self.checked(r)['valid'])

    def test_private_evidence_is_never_opened_and_symlink_inputs_rejected(self):
        r = copy.deepcopy(self.report)
        r['input_hashes']['data/community/private.sqlite3'] = '0' * 64
        original = Path.read_bytes
        reads = []
        def guarded(path):
            reads.append(str(path))
            self.assertNotIn('data/community', str(path))
            return original(path)
        with patch.object(Path, 'read_bytes', guarded):
            self.assertFalse(self.checked(r)['valid'])
        self.assertTrue(reads)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'reports').mkdir()
            (root / 'reports' / 'alias').symlink_to(root / 'private-data')
            with self.assertRaises(ValueError):self.lab.sha('reports/alias/file.json', root)

    def test_public_downloads_exclude_expected_fields_and_reserve_queries(self):
        # Core/replay has already been tested independently above. This check
        # inspects the production download projection, never reserve keys.
        summary = dict(self.lab.projection(self.report), available=True)
        with patch.object(self.lab, 'public_summary', return_value=summary):
            exports = [self.lab.public_download(kind) for kind in ('documentary-comparison', 'documentary-retrieval')]
            with self.assertRaises(ValueError):self.lab.public_download('documentary-reserve')
        forbidden = {'reference', 'expected_fields', 'expected_target_ids', 'missing_fields', 'source_conditions'}
        def inspect(value):
            if isinstance(value, dict):
                self.assertFalse(forbidden.intersection(value))
                if 'queries' in value:self.assertIs(type(value['queries']), int)
                for child in value.values():inspect(child)
            elif isinstance(value, list):
                for child in value:inspect(child)
        for export in exports:
            inspect(export)
            self.assertFalse(export['battery']['reserve_used'])
            self.assertEqual(export['battery']['evaluated_split'], 'development')
        self.assertIsNone(exports[0]['runs'][1]['cost'])
        self.assertIsNone(exports[0]['runs'][2]['metrics'])

    def test_retrieval_from_another_run_cannot_be_substituted(self):
        wrong = copy.deepcopy(self.retrieval)
        wrong['metrics']['complete'] = 123
        result = self.lab.validate_report(self.report, retrieval=wrong,
                                         retrieval_validation=self.retrieval_validation)
        self.assertIn('retrieval_not_current', result['errors'])


class DocumentarySummaryCacheTests(unittest.TestCase):
    """Real validators/replays over isolated copies of the public dependencies."""
    def setUp(self):
        from nahuatl_local import documentary_laboratory as lab
        self.lab = lab
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / 'one'
        self.report = lab.read(lab.REPORT)
        self.paths = set(self.report['input_hashes']) | set(lab.EVALUATION_INPUTS) | {lab.REPORT, PRESENTATION}
        self.copy_root(self.root)
        with lab._SUMMARY_LOCK:
            lab._SUMMARY_CACHE.clear()
        self.spy = patch.object(lab, 'validate_retrieval', wraps=lab.validate_retrieval)
        self.replay = self.spy.start()

    def copy_root(self, root):
        for relative in self.paths:
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(self.lab.ROOT / relative, destination)

    def tearDown(self):
        self.spy.stop()
        with self.lab._SUMMARY_LOCK:
            self.lab._SUMMARY_CACHE.clear()
        self.tmp.cleanup()

    def summary(self):
        return self.lab.public_summary(self.root)

    def test_gets_and_downloads_reuse_one_replay_and_defensive_copies(self):
        first = self.summary()
        self.assertTrue(first['ready'], first)
        expected = copy.deepcopy(first)
        first['runs'][0]['metrics']['complete'] = -1
        first['input_hashes'].clear()
        self.assertEqual(self.summary(), expected)
        comparison = self.lab.public_download('documentary-comparison', self.root)
        retrieval = self.lab.public_download('documentary-retrieval', self.root)
        comparison['runs'][0]['metrics']['complete'] = -2
        retrieval['metrics']['complete'] = -3
        self.assertEqual(self.summary(), expected)
        self.assertEqual(self.replay.call_count, 1)
        # Completion/CLI gate must still independently replay in a warm process.
        self.assertTrue(self.lab.validate_report(self.report, root=self.root)['valid'])
        self.assertEqual(self.replay.call_count, 2)

    def test_presentation_change_reuses_validated_summary(self):
        self.assertTrue(self.summary()['ready'])
        path = self.root / PRESENTATION
        path.write_bytes(path.read_bytes() + b'\n/* presentation changed */\n')
        self.assertTrue(self.summary()['ready'])
        self.assertEqual(self.replay.call_count, 1)

    def test_same_size_and_mtime_content_change_invalidates(self):
        self.assertTrue(self.summary()['ready'])
        path = self.root / 'nahuatl_local/documentary_retrieval.py'
        stat = path.stat()
        original = path.read_bytes()
        path.write_bytes(bytes([original[0] ^ 1]) + original[1:])
        os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
        self.assertEqual(path.stat().st_size, stat.st_size)
        self.assertEqual(path.stat().st_mtime_ns, stat.st_mtime_ns)
        self.assertFalse(self.summary()['available'])
        self.assertEqual(self.replay.call_count, 2)
        path.write_bytes(original)
        self.assertTrue(self.summary()['ready'])
        self.assertEqual(self.replay.call_count, 3)

    def test_battery_learning_dependency_invalidates(self):
        self.assertTrue(self.summary()['ready'])
        path = self.root / 'corpus/learning-v1.json'
        self.assertIn('corpus/learning-v1.json', self.report['input_hashes'])
        source = json.loads(path.read_text())
        source['lessons'][0]['title'] += ' changed'
        path.write_text(json.dumps(source))
        self.assertFalse(self.summary()['available'])
        self.assertEqual(self.replay.call_count, 2)

    def test_report_tampering_and_missing_input_do_not_serve_previous_summary(self):
        self.assertTrue(self.summary()['ready'])
        path = self.root / self.lab.REPORT
        original = path.read_bytes()
        changed = copy.deepcopy(self.report)
        changed['runs'][0]['metrics']['complete'] = 123
        path.write_text(json.dumps(changed))
        self.assertFalse(self.summary()['available'])
        path.write_bytes(original)
        self.assertTrue(self.summary()['ready'])
        (self.root / self.lab.BATTERY_VALIDATION).unlink()
        self.assertFalse(self.summary()['available'])
        self.assertEqual(self.replay.call_count, 3)

    def test_symlink_and_private_report_path_rejected_before_target_open(self):
        self.assertTrue(self.summary()['ready'])
        target = Path(self.tmp.name) / 'private.sqlite3'
        target.write_bytes(b'private sentinel')
        path = self.root / self.lab.BATTERY_VALIDATION
        path.unlink()
        path.symlink_to(target)
        original = Path.read_bytes
        def guarded(p):
            self.assertNotEqual(p, target)
            self.assertFalse(p == path and p.is_symlink())
            self.assertNotIn('data/community', str(p))
            return original(p)
        with patch.object(Path, 'read_bytes', guarded):
            self.assertFalse(self.summary()['available'])
        path.unlink()
        shutil.copyfile(self.lab.ROOT / self.lab.BATTERY_VALIDATION, path)
        bad = copy.deepcopy(self.report)
        bad['input_hashes']['data/community/private.sqlite3'] = '0' * 64
        (self.root / self.lab.REPORT).write_text(json.dumps(bad))
        with patch.object(Path, 'read_bytes', guarded):
            self.assertFalse(self.summary()['available'])
        alias = Path(self.tmp.name) / 'alias'
        alias.symlink_to(self.root, target_is_directory=True)
        self.assertFalse(self.lab.public_summary(alias)['available'])
