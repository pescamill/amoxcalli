import contextlib
import copy
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from nahuatl_local.community import ROOT, DEFAULT_DB
from nahuatl_local.corpus import CorpusStore
from nahuatl_local.documentary_evaluation import (build, digest, encoded, families, inputs,
    load_development, main, overlap_report, partition_families, public_dependency_filter, validate)


class DocumentaryEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = inputs()
        cls.battery = build()

    def test_reconstruction_is_deterministic_and_reference_fields_are_original(self):
        before = copy.deepcopy(self.data)
        self.assertEqual(encoded(build()), encoded(self.battery))
        self.assertTrue(validate(self.battery)['valid'])
        self.assertEqual(self.data, before)
        counts = validate(self.battery)['counts']
        self.assertEqual(counts, dict(development=dict(textual=123, visual=51),
                                      reserve=dict(textual=37, visual=15)))
        ids = [q['id'] for q in self.battery['queries']]
        self.assertEqual(len(ids), len(set(ids)))
        for q in self.battery['queries']:
            self.assertEqual(q['reference_authority'], 'documentary')
            self.assertEqual(q['review_status'], 'source_derived_not_human_validated')
            self.assertTrue(q['reference']['attributed_responsibility'])
            for ref in q['reference']['fields']:
                if ref['table'] == 'csv':
                    row = self.data['passages'][ref['record_id']]
                    original = row[{'es': 0, 'nah': 1, 'document': 3, 'iso': 4}[ref['field']]]
                else:
                    row = next(r for r in self.data['docs'][ref['path']][ref['table']] if r['id'] == ref['record_id'])
                    original = row[ref['field']]
                self.assertEqual(ref['value'], original)
                self.assertEqual(ref['row_sha256'], digest(row))
                self.assertEqual(ref['file_sha256'], self.data['hashes'][ref['path']])

    def test_queries_are_diverse_documentary_tasks_and_reserve_is_disjoint(self):
        self.assertFalse(any(overlap_report(self.battery).values()))
        visual = [q for q in self.battery['queries'] if q['modality'] == 'visual']
        self.assertGreaterEqual(len({q['question'] for q in visual}), 50)
        visual_dev = [q for q in visual if q['split'] == 'development']
        self.assertGreater(len({r['record_id'] for q in visual_dev for r in q['reference']['fields'] if r['table'] == 'pages'}), 1)
        self.assertEqual({q['task'] for q in self.battery['queries']}, {'lexical', 'comparison', 'observation'})
        ambiguous = [q for q in self.battery['queries'] if q['task'] == 'lexical' and len(q['entity_ids']) > 1]
        self.assertTrue(ambiguous)
        for q in visual:
            o = next(r for r in q['reference']['fields'] if r['table'] == 'occurrences')
            self.assertEqual(o['record_id'].startswith('telleriano:'), q['split'] == 'development')

    def test_evidenced_grouping_joins_variants_versions_pages_and_shared_images(self):
        data = copy.deepcopy(self.data)
        form = next(r for r in data['records'].values() if r['kind'] == 'form')
        variant = copy.deepcopy(form)
        variant['id'] = 'synthetic-form-version'
        variant['written'] = 'synthetic spelling'
        variant['catalog_normalized'] = 'synthetic spelling'
        data['records'][variant['id']] = variant
        pid, passage = next(iter(data['passages'].items()))
        data['passages']['synthetic-passage-version'] = list(passage)
        cat = data['docs']['corpus/pictography/catalog.json']
        original = cat['occurrences'][0]
        duplicate = copy.deepcopy(cat['occurrences'][-1])
        duplicate['id'] = 'synthetic-image-copy'
        duplicate['image'] = original['image']
        cat['occurrences'].append(duplicate)
        _, membership = families(data)
        self.assertEqual(membership['lex:' + form['id']], membership['lex:synthetic-form-version'])
        self.assertEqual(membership['passage:' + pid], membership['passage:synthetic-passage-version'])
        self.assertEqual(membership['visual:occurrences:' + original['id']], membership['visual:pages:' + original['page_id']])
        self.assertEqual(membership['visual:occurrences:' + original['id']], membership['visual:occurrences:synthetic-image-copy'])
        with self.assertRaises(ValueError):
            partition_families([dict(id='duplicate', resources=[]), dict(id='duplicate', resources=[])])

    def test_rename_group_cannot_hide_reference_or_image_leakage(self):
        battery = copy.deepcopy(self.battery)
        development = next(q for q in battery['queries'] if q['split'] == 'development' and q['modality'] == 'visual')
        reserve = next(q for q in battery['queries'] if q['split'] == 'reserve' and q['modality'] == 'visual')
        reserve['reference']['fields'] = copy.deepcopy(development['reference']['fields'])
        overlap = overlap_report(battery)
        self.assertTrue(overlap['referenced_records'])
        self.assertTrue(overlap['images'])
        self.assertFalse(validate(battery)['valid'])
        reserve['group_id'] = development['group_id']
        self.assertTrue(overlap_report(battery)['family_resources'])

    def test_stale_sources_and_tampered_original_keys_are_rejected(self):
        battery = copy.deepcopy(self.battery)
        for change in ('value', 'id', 'hash', 'source_ids', 'responsibility', 'url', 'group', 'question'):
            altered = copy.deepcopy(battery)
            q = altered['queries'][0]
            if change == 'value': q['reference']['fields'][0]['value'] = 'fabricated original'
            if change == 'id': q['reference']['fields'][0]['record_id'] = 'nonexistent'
            if change == 'hash': q['source_hashes'][next(iter(q['source_hashes']))] = '0' * 64
            if change == 'source_ids': q['reference']['source_ids'] = ['model']
            if change == 'responsibility': q['reference']['attributed_responsibility'] = ['AI author']
            if change == 'url': q['reference']['urls'] = ['https://invented.invalid/']
            if change == 'group': q['group_id'] = 'invented'
            if change == 'question': q['question'] = ''
            with self.subTest(change=change): self.assertFalse(validate(altered)['valid'])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for path in self.data['hashes']:
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / path, target)
            source = root / 'corpus/gdn-lexicon-v6.json'
            d = json.loads(source.read_text())
            next(r for r in d['records'] if r['kind'] == 'form')['written'] += ' tampered'
            source.write_text(encoded(d))
            self.assertFalse(validate(battery, root)['valid'])
            source.unlink()
            source.symlink_to(ROOT / 'corpus/gdn-lexicon-v6.json')
            with self.assertRaises(ValueError): inputs(root)

    def test_permissions_never_escalate_and_conditions_are_literal(self):
        for q in self.battery['queries']:
            self.assertEqual(q['rights']['local_documentary_fields'], 'authorized_local_scope')
            for key in ('evaluation', 'training', 'image_model_input', 'image_copy', 'external_send'):
                self.assertIs(q['rights'][key], False)
            self.assertTrue(q['rights']['source_conditions'])
        for key in ('evaluation', 'training', 'image_model_input', 'image_copy', 'external_send'):
            b = copy.deepcopy(self.battery)
            b['queries'][0]['rights'][key] = True
            with self.subTest(key=key): self.assertFalse(validate(b)['valid'])
        b = copy.deepcopy(self.battery)
        b['scope']['visual_model_executed'] = True
        self.assertFalse(validate(b)['valid'])

    def test_development_helper_returns_no_reserve_or_mutable_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in self.data['hashes']:
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, target)
            path = root / 'configs/documentary-evaluation-v1.json'
            path.write_text(encoded(self.battery))
            dev = load_development(path, root=root)
            self.assertEqual(len(dev), 174)
            self.assertTrue(all(q['split'] == 'development' for q in dev))
            self.assertFalse({q['id'] for q in dev} & {q['id'] for q in self.battery['queries'] if q['split'] == 'reserve'})
            dev[0]['reference']['fields'][0]['value'] = 'changed by consumer'
            self.assertNotEqual(dev[0], load_development(path, root=root)[0])
            with self.assertRaises(TypeError): load_development(path, root=root, split='reserve')
            b = copy.deepcopy(self.battery)
            b['queries'][0]['rights']['training'] = True
            path.write_text(encoded(b))
            with self.assertRaises(ValueError): load_development(path, root=root)

    def test_private_and_symlink_loader_paths_are_rejected_before_read(self):
        with patch.object(Path, 'read_text', side_effect=AssertionError('No read before authorization')):
            with self.assertRaises(ValueError): load_development(ROOT / 'data/community.sqlite3')
            with self.assertRaises(ValueError): load_development('/tmp/arbitrary-private.json')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'configs').mkdir()
            (root / 'configs/documentary-evaluation-v1.json').symlink_to(ROOT / 'configs/documentary-evaluation-v1.json')
            with patch.object(Path, 'read_text', side_effect=AssertionError('No symlink read')):
                with self.assertRaises(ValueError): load_development(root=root)

    def test_public_eligibility_matches_temporary_store_and_hides_dependencies(self):
        with tempfile.TemporaryDirectory() as directory:
            public = CorpusStore(Path(directory) / 'public.sqlite3').public_records()
        for q in self.battery['queries']:
            for ref in q['reference']['fields']:
                if ref['table'] == 'records':
                    self.assertIn(ref['record_id'], public)
                    self.assertEqual(ref['value'], public[ref['record_id']][ref['field']])
        self.assertEqual(set(self.data['records']), set(public))
        rows = dict(source=dict(rights=dict(public=False)),
                    form=dict(rights=dict(public=True), evidence=[dict(source_id='source')]),
                    dependent=dict(rights=dict(public=True), sense_id='form'))
        self.assertEqual(public_dependency_filter(rows), {})

    def test_cli_preserves_previous_bytes_and_repeats_without_network_or_private_db(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for path in self.data['hashes']:
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / path, target)
            (root / 'reports').mkdir(exist_ok=True)
            path = root / 'configs/documentary-evaluation-v1.json'
            original = b'{"old": "preserve these exact bytes"}\n'
            path.write_bytes(original)
            with patch('nahuatl_local.documentary_evaluation.ROOT', root), patch('socket.socket', side_effect=AssertionError('No network')), patch('sqlite3.connect', side_effect=AssertionError('No database')):
                # Explicit root is passed by main; the default ROOT bound at
                # definition is patched by wrapping build/validate here.
                from nahuatl_local import documentary_evaluation as module
                real_build, real_validate = build, validate
                with patch.object(module, 'build', side_effect=lambda *args: real_build(root)), patch.object(module, 'validate', side_effect=lambda b: real_validate(b, root)):
                    with contextlib.redirect_stdout(io.StringIO()): main([])
                    before = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*.json')}
                    with contextlib.redirect_stdout(io.StringIO()): main([]); main(['--check'])
                    after = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*.json')}
                    self.assertEqual(before, after)
            backups = list((root / 'reports/documentary-evaluation-backups').glob('*.json'))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
