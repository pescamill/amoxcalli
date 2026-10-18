import hashlib
import copy
import os
import shutil
from unittest.mock import patch
import json
from pathlib import Path
import tempfile
import unittest
from experiments.llm.laboratory import snapshot, REPORTS

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


if __name__ == '__main__':
    unittest.main()
