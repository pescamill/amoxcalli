import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from nahuatl_local.community import ROOT, DEFAULT_DB
from nahuatl_local.corpus import CorpusStore
from nahuatl_local.iteration import (diagnose, empty_state, evidence_hashes, main,
                                     queue_from_state, reconcile, record_decision,
                                     source_manifest, task, technical_progress, fingerprint)
from nahuatl_local.documentary_evaluation import build, validate
from nahuatl_local.documentary_retrieval_evaluation import REPORT as RETRIEVAL_REPORT
from nahuatl_local.documentary_laboratory import build as build_laboratory
from nahuatl_local.learning import Learning
from nahuatl_local.pictography import load_catalog
from nahuatl_local.research import Archive


class IterationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.records = CorpusStore(Path(cls.directory.name) / 'public.sqlite3').public_records()
        cls.learning = Learning(Archive())
        cls.pictography = load_catalog()
        cls.sources = source_manifest()
        cls.retrieval = json.loads((ROOT / RETRIEVAL_REPORT).read_text())

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def fixture(self, dependency='hash-one', evidence='observed'):
        finding = dict(id='synthetic-task', priority='P1', lesson_id=None,
                       title='Synthetic test, never editorial review', evidence=evidence,
                       acceptance='Synthetic acceptance')
        return task(finding, 'technical', {'public-source': dependency})

    def decision(self, finding, status='resolved'):
        return dict(id=finding['id'], fingerprint=finding['fingerprint'], status=status,
                    reviewer='Synthetic QA only', date='2026-10-07',
                    evidence=['docs/PROPOSITO.md'],
                    resolution='Synthetic test only; no real linguistic review.',
                    notes='Keep the decision note.')

    def test_inventory_is_calculated_and_does_not_infer_links(self):
        report, tasks = diagnose(self.records, self.learning, self.pictography, self.sources, {})
        self.assertEqual((report['counts']['lessons'], report['counts']['passages']), (12, 48))
        self.assertEqual(report['counts']['public_records']['sense'], 575)
        self.assertEqual(report['counts']['public_records']['form'], 578)
        self.assertEqual(report['counts']['designations'], len({e['designation'] for e in self.pictography['elements']}))
        self.assertEqual(report['counts']['pictography']['elements'], len(self.pictography['elements']))
        self.assertEqual(report['counts']['pictography']['occurrences'], len(self.pictography['occurrences']))
        self.assertEqual(len(report['gaps']['elements_without_lexical_links']),
                         sum(not e.get('lexical_links') for e in self.pictography['elements']))
        self.assertEqual(len(report['gaps']['occurrences_without_citations']),
                         sum(not o['citations'] for o in self.pictography['occurrences']))
        self.assertEqual(len(report['gaps']['occurrences_without_components']),
                         sum(not o['components'] for o in self.pictography['occurrences']))
        self.assertEqual(report['gaps']['broken_lexical_links'], [])
        self.assertEqual(len({t['id'] for t in tasks}), len(tasks))
        self.assertNotIn('pictography-missing-lexical-links', {t['id'] for t in tasks})
        expected_technical = set()
        if not report['technical_progress']['laboratory']['ready']:
            expected_technical.add('laboratory-documentary-multimodal-comparison')
        if not report['technical_progress']['retrieval']['ready']:
            expected_technical.add('retrieval-documentary-baseline')
        if not report['technical_progress']['evaluation']['ready']:
            expected_technical.add('evaluation-documentary-development-reserve')
        if len(self.pictography['occurrences']) < 300:
            expected_technical.add('pictography-next-documentary-batch')
        self.assertEqual({t['id'] for t in tasks if t['category'] == 'technical'}, expected_technical)
        self.assertEqual(report['lessons_remaining_to_proposed_target'],0)
        self.assertTrue(report['technical_progress']['evaluation']['ready'])
        self.assertEqual(report['occurrences_remaining_to_proposed_target'], max(0, 300-len(self.pictography['occurrences'])))
        _, capped_tasks = diagnose(self.records, self.learning, self.pictography, self.sources, {}, occurrence_target=len(self.pictography['occurrences']))
        self.assertNotIn('pictography-next-documentary-batch', {t['id'] for t in capped_tasks})
        _, pending_tasks = diagnose(self.records, self.learning, self.pictography, self.sources, {},
                                    occurrence_target=len(self.pictography['occurrences'])+1)
        self.assertIn('pictography-next-documentary-batch', {t['id'] for t in pending_tasks})
        self.assertFalse(report['privacy']['private_database_opened'])

    def artifacts(self):
        evaluation=build()
        retrieval=copy.deepcopy(self.retrieval)
        laboratory=build_laboratory()
        return dict(evaluation=evaluation,evaluation_validation=validate(evaluation),retrieval=retrieval,laboratory=laboratory)

    def test_milestones_are_conditional_and_preserve_history_when_complete(self):
        _,tasks=diagnose(self.records,self.learning,self.pictography,self.sources,{},artifacts={})
        milestone_ids={'evaluation-documentary-development-reserve','retrieval-documentary-baseline',
                       'laboratory-documentary-multimodal-comparison'}
        self.assertTrue(milestone_ids.issubset({t['id'] for t in tasks}))
        state=reconcile(tasks,empty_state(),'incomplete')
        artifacts=self.artifacts()
        report,complete=diagnose(self.records,self.learning,self.pictography,self.sources,{},artifacts=artifacts)
        self.assertTrue(all(row['ready'] for row in report['technical_progress'].values()))
        self.assertFalse(milestone_ids.intersection({t['id'] for t in complete}))
        result=reconcile(complete,state,'prepared')
        for rid in milestone_ids:
            self.assertFalse(result['tasks'][rid]['present'])
            self.assertEqual(result['tasks'][rid]['status'],'open')
            self.assertTrue(result['tasks'][rid]['snapshots'])
        # Reading preparation remains a technical task below the requested target.
        _,pending=diagnose(self.records,self.learning,self.pictography,self.sources,{},lesson_target=13,artifacts=artifacts)
        reading=next(t for t in pending if t['id']=='learning-next-source-backed-readings')
        self.assertEqual(reading['evidence']['current'],12)
        self.assertEqual(reading['category'],'technical')

    def test_counts_or_old_sft_reports_cannot_complete_documentary_evaluation(self):
        self.assertFalse(technical_progress(dict(evaluation=dict(textual=100,visual=50)))['evaluation']['ready'])
        self.assertFalse(technical_progress(dict(evaluation=dict(queries={})))['evaluation']['ready'])
        for change in ('group_overlap','stale_hash','generated_reference','missing_reserve','invalid_rights'):
            artifacts=self.artifacts();evaluation=artifacts['evaluation']
            if change=='group_overlap':evaluation['queries'][-1]['group_id']=evaluation['queries'][0]['group_id']
            if change=='stale_hash':evaluation['queries'][0]['source_hashes']={'docs/PROPOSITO.md':'old'}
            if change=='generated_reference':evaluation['queries'][0]['reference_authority']='model'
            if change=='missing_reserve':evaluation['queries']=[q for q in evaluation['queries'] if q['split']=='development']
            if change=='invalid_rights':evaluation['queries'][0]['rights']='not-a-rights-record'
            with self.subTest(change=change):self.assertFalse(technical_progress(artifacts)['evaluation']['ready'])
        artifacts=self.artifacts();artifacts['retrieval']['results'].pop()
        self.assertFalse(technical_progress(artifacts)['retrieval']['ready'])
        artifacts=self.artifacts();artifacts['laboratory']['runs'][-1].pop('reason')
        self.assertFalse(technical_progress(artifacts)['laboratory']['ready'])

    def test_broken_connections_become_technical_tasks_with_exact_evidence(self):
        pictography = copy.deepcopy(self.pictography)
        pictography['elements'][0]['lexical_links'] = [dict(sense_id='missing-sense',
                                                           relation='designation', note='Synthetic link')]
        report, tasks = diagnose(self.records, self.learning, pictography, self.sources, {})
        finding = next(t for t in tasks if t['id'] == 'pictography-broken-lexical-links')
        self.assertEqual(finding['category'], 'technical')
        self.assertEqual(finding['evidence'], report['gaps']['broken_lexical_links'])
        self.assertEqual(finding['evidence'][0]['sense_id'], 'missing-sense')
        self.assertNotIn('missing-sense', self.records)

    def test_decision_and_notes_survive_reruns_and_disappearing_findings(self):
        finding = self.fixture()
        state = reconcile([finding], empty_state(), 'run-one')
        state = record_decision(state, self.decision(finding))
        state['tasks'][finding['id']]['notes'] = ['Persistent human note.']
        original = copy.deepcopy(state)
        self.assertEqual(reconcile([finding], state, 'run-one'), state)
        self.assertEqual(state, original)
        absent = reconcile([], state, 'run-two')
        self.assertFalse(absent['tasks'][finding['id']]['present'])
        self.assertEqual(queue_from_state(absent), [])
        present = reconcile([finding], absent, 'run-three')
        row = present['tasks'][finding['id']]
        self.assertEqual(row['status'], 'resolved')
        self.assertEqual(row['notes'], ['Persistent human note.'])
        self.assertEqual(row['decision']['notes'], 'Keep the decision note.')
        self.assertIn('absent', [h['kind'] for h in row['history']])
        self.assertIn('reappeared', [h['kind'] for h in row['history']])

    def test_source_change_reopens_with_snapshot_and_decision_preserved(self):
        first = self.fixture()
        state = record_decision(reconcile([first], empty_state(), 'run-one'), self.decision(first))
        changed = self.fixture(dependency='hash-two')
        result = reconcile([changed], state, 'run-two')
        row = result['tasks'][first['id']]
        self.assertEqual(row['status'], 'open')
        self.assertEqual(row['stale_reasons'], ['finding_or_source_changed'])
        self.assertEqual(len(row['snapshots']), 2)
        self.assertEqual(row['decision'], state['tasks'][first['id']]['decision'])
        self.assertEqual(reconcile([changed], result, 'run-two'), result)
        other = reconcile([self.fixture(evidence='new-evidence')], state, 'run-other')
        self.assertTrue(other['tasks'][first['id']]['decision_stale'])

    def test_resolution_evidence_hash_is_checked_without_losing_history(self):
        finding = self.fixture()
        with patch('nahuatl_local.iteration.evidence_hashes', return_value={'public-reference': 'old'}):
            state = record_decision(reconcile([finding], empty_state(), 'run-one'), self.decision(finding))
        with patch('nahuatl_local.iteration.evidence_hashes', return_value={'public-reference': 'new'}):
            result = reconcile([finding], state, 'run-one')
        row = result['tasks'][finding['id']]
        self.assertEqual(row['status'], 'open')
        self.assertEqual(row['stale_reasons'], ['decision_evidence_changed'])
        self.assertEqual(row['decision']['evidence_hashes'], {'public-reference': 'old'})
        self.assertTrue(any(h['kind'] == 'decision' for h in row['history']))

    def test_resolution_requires_current_fingerprint_and_real_evidence(self):
        finding = self.fixture()
        state = reconcile([finding], empty_state(), 'run-one')
        for change in ({'fingerprint': 'stale'}, {'reviewer': ''}, {'resolution': ''},
                       {'date': 'not-a-date'}, {'evidence': []},
                       {'evidence': ['docs/nonexistent-test-file.md']}, {'status': 'publish'}):
            decision = dict(self.decision(finding), **change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                record_decision(state, decision)
        self.assertEqual(state['tasks'][finding['id']]['history'][0]['kind'], 'observed')

    def test_legacy_decisions_are_imported_without_inventing_human_review(self):
        finding = self.fixture()
        legacy = self.decision(finding, status='blocked')
        legacy['fingerprint'] = finding['finding_fingerprint']
        before = copy.deepcopy(legacy)
        state = reconcile([finding], empty_state(), 'run-one', {finding['id']: legacy})
        row = state['tasks'][finding['id']]
        self.assertEqual(row['status'], 'blocked')
        self.assertEqual(row['decision']['original_decision'], before)
        self.assertEqual(legacy, before)
        self.assertTrue(row['decision']['evidence_hashes_observed_at_import'])

    def test_private_paths_and_symlink_evidence_are_rejected_before_reading(self):
        for evidence in (['data/community/voces.sqlite3'], ['../private.db'],
                         [str(DEFAULT_DB)], ['https://example.com'], ['reports/../data/private.db']):
            with self.subTest(evidence=evidence), patch('nahuatl_local.iteration.sha256') as hashed:
                with self.assertRaises(ValueError):
                    evidence_hashes(evidence)
                hashed.assert_not_called()
        with tempfile.TemporaryDirectory(dir=ROOT / 'reports') as directory:
            link = Path(directory) / 'private-link'
            link.symlink_to(DEFAULT_DB)
            with patch('nahuatl_local.iteration.sha256') as hashed:
                with self.assertRaises(ValueError):
                    evidence_hashes([str(link.relative_to(ROOT))])
                hashed.assert_not_called()

    def test_real_cli_is_byte_deterministic_and_never_opens_private_database(self):
        before_sources = source_manifest()
        opened = []
        original_connect = __import__('sqlite3').connect

        def public_connection(database, *args, **kwargs):
            path = Path(database)
            self.assertNotEqual(path.resolve(), DEFAULT_DB.resolve())
            self.assertFalse(path.resolve().is_relative_to((ROOT / 'data').resolve()))
            self.assertTrue(path.name == 'public.sqlite3')
            opened.append(path)
            return original_connect(database, *args, **kwargs)

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'output'
            state = Path(directory) / 'state.json'
            args = ['--output', str(output), '--state', str(state)]
            with patch('sqlite3.connect', side_effect=public_connection), patch('socket.socket', side_effect=AssertionError('No network')):
                with contextlib.redirect_stdout(io.StringIO()):
                    main(args)
                baseline = {p.name: p.read_bytes() for p in output.iterdir()}
                baseline['state.json'] = state.read_bytes()
                with contextlib.redirect_stdout(io.StringIO()):
                    main(args)
                repeated = {p.name: p.read_bytes() for p in output.iterdir()}
                repeated['state.json'] = state.read_bytes()
            self.assertEqual(baseline, repeated)
            self.assertGreater(len(opened), 0)
            self.assertTrue(all(not p.exists() for p in opened))
        self.assertEqual(source_manifest(), before_sources)

    def test_invalid_state_and_destinations_do_not_modify_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / 'state.json'
            state.write_text('{"schema_version": 2, "notes": "preserve"}')
            before = state.read_bytes()
            with self.assertRaises(ValueError):
                main(['--state', str(state), '--output', str(Path(directory) / 'output')])
            self.assertEqual(state.read_bytes(), before)
        for path in (ROOT / 'corpus/output', ROOT / 'data/output', ROOT / 'nahuatl_local/output'):
            with self.assertRaises(ValueError):
                main(['--output', str(path)])
        with self.assertRaises(ValueError), patch('nahuatl_local.iteration.source_manifest') as sources:
            main(['--record-decision', str(DEFAULT_DB)])
            sources.assert_not_called()


if __name__ == '__main__':
    unittest.main()
