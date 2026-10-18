import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from nahuatl_local.community import ROOT
from nahuatl_local.corpus import CorpusStore
from nahuatl_local.learning import Learning
from nahuatl_local.lesson_audit import audit, main, merge_decisions
from nahuatl_local.research import Archive


class LessonAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        cls.records=CorpusStore(Path(cls.tmp.name)/'audit.sqlite3').public_records()
        cls.archive=Archive()

    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()

    def test_inventory_distinguishes_images_from_recorded_primary_review(self):
        report=audit(Learning(self.archive),self.records)
        self.assertEqual((report['lessons'],report['examples'],report['target_senses']),(12,48,20))
        self.assertEqual(report['visual_coverage'],dict(target_meanings=20,with_image=20,with_recorded_primary_context=0))
        self.assertEqual({r['written'] for r in report['missing_annotated_forms']},{'NIQUITTA','xochitli','tlacuilolcalli'})
        ids=[f['id'] for f in report['findings']]
        self.assertEqual(len(ids),len(set(ids)))
        self.assertNotIn('entry-candidate-cuicatl',ids)
        self.assertNotIn('batch-water-land',ids)
        self.assertGreater(len(report['works']),1)
        self.assertIn('word-sense-cuicatl-glyph-scope',ids)
        self.assertEqual(sum(p['annotation_example_counts'].get('sense-metztli',0) for p in report['packets']),3)

    def test_custom_lesson_and_missing_dependency_are_audited_not_hidden(self):
        learning=Learning(self.archive)
        learning.data['lessons']=learning.data['lessons'][:1]
        learning.data['lessons'][0]['id']='new-reading'
        records=dict(self.records);records.pop('sense-itta')
        report=audit(learning,records)
        self.assertEqual(report['lessons'],1)
        issue=next(f for f in report['findings'] if f['id']=='lesson-new-reading-missing-dependencies')
        self.assertIn('sense-itta',issue['evidence']['missing_ids'])
        self.assertNotIn('lesson-cielo-moon-coverage',[f['id'] for f in report['findings']])

    def test_resolution_requires_evidence_and_reopens_when_evidence_changes(self):
        f=audit(Learning(self.archive),self.records)['findings'][0]
        decision=dict(status='resolved',fingerprint=f['fingerprint'],reviewer='Synthetic QA',date='2026-09-30',evidence=['Synthetic test only'],resolution='Test decision, not editorial approval')
        stored={f['id']:decision};before=copy.deepcopy(stored)
        self.assertEqual(merge_decisions([f],stored)[0]['status'],'resolved')
        altered=dict(f,fingerprint='changed-evidence')
        task=merge_decisions([altered],stored)[0]
        self.assertEqual(task['status'],'open');self.assertTrue(task['review_stale'])
        self.assertEqual(stored,before)
        decision['evidence']=[]
        self.assertEqual(merge_decisions([f],stored)[0]['status'],'open')
        decision['status']='publish_and_train'
        with self.assertRaises(ValueError):merge_decisions([f],stored)

    def test_cli_rerun_preserves_human_decision_file_and_original_lessons(self):
        original=(ROOT/'corpus/learning-v1.json').read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'reports';decisions=Path(directory)/'decisions.json'
            args=['lesson_audit','--output',str(output),'--decisions',str(decisions)]
            with patch('sys.argv',args),contextlib.redirect_stdout(io.StringIO()):main()
            generated=json.loads((output/'review-queue.json').read_text());task=generated['tasks'][0]
            human=dict(schema_version=1,decisions={task['id']:dict(status='in_progress',fingerprint=task['fingerprint'],reviewer='Synthetic QA',notes='Do not overwrite this note.')})
            decisions.write_text(json.dumps(human,indent=3)+'\n');before=decisions.read_bytes()
            with patch('sys.argv',args),contextlib.redirect_stdout(io.StringIO()):main()
            self.assertEqual(decisions.read_bytes(),before)
            self.assertEqual(json.loads((output/'review-queue.json').read_text())['tasks'][0]['status'],'in_progress')
        self.assertEqual((ROOT/'corpus/learning-v1.json').read_bytes(),original)

    def test_snapshot_input_is_validated_and_does_not_change_catalog(self):
        with tempfile.TemporaryDirectory() as directory:
            file=Path(directory)/'catalog.json'
            file.write_text(json.dumps(dict(schema_version=1,records=list(self.records.values()))))
            before=file.read_bytes()
            args=['lesson_audit','--catalog',str(file),'--output',str(Path(directory)/'reports'),'--decisions',str(Path(directory)/'decisions.json')]
            with patch('sys.argv',args),contextlib.redirect_stdout(io.StringIO()):main()
            self.assertEqual(file.read_bytes(),before)
            report=json.loads((Path(directory)/'reports/inventory.json').read_text())
            self.assertEqual(report['inputs']['catalog'],str(file))

if __name__=='__main__':unittest.main()
