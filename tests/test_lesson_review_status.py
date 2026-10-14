import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from nahuatl_local.community import ROOT
from nahuatl_local.editorial_pipeline import encoded
from nahuatl_local.iteration import main as diagnose_current
from nahuatl_local.lesson_review_packet import build, digest, file_contents, verify
from nahuatl_local.lesson_review_status import (PUBLIC_SOURCES, inspect_package, main,
                                               render, write_report)


class LessonReviewStatusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(dir=ROOT / 'reports', prefix='test-review-status-')
        cls.root = Path(cls.temp.name)
        cls.inputs = {name: cls.root / name for name in ('inventory.json', 'queue.json', 'state.json')}
        # Reconcile a copy of live state in a temporary diagnosis; historical
        # artifacts remain evidence of their original sources, not fixtures.
        cls.inputs['state.json'].write_bytes((ROOT / 'reports/iterations/state.json').read_bytes())
        diagnose_current(['--output', str(cls.root), '--state', str(cls.inputs['state.json'])])
        cls.original_inputs = {p: p.read_bytes() for p in cls.inputs.values()}
        cls.package, cls.sources = build('aves', *cls.inputs.values())
        protected = set(PUBLIC_SOURCES) | {'reports/iterations/state.json'}
        protected.update(str(p.relative_to(ROOT)) for p in (ROOT / 'reports/reading-review').glob('aves-009*/*'))
        protected.update({'tests/test_lesson_review_packet.py', 'reports/REVISION_LECTURA_009_2026-10-08.md'})
        cls.protected = {p: digest((ROOT / p).read_bytes()) for p in protected}

    @classmethod
    def tearDownClass(cls):
        try:
            for name, expected in cls.protected.items():
                if digest((ROOT / name).read_bytes()) != expected:
                    raise AssertionError('Original alterado: ' + name)
        finally:
            cls.temp.cleanup()

    def setUp(self):
        for path, raw in self.original_inputs.items():
            if path.is_symlink():
                path.unlink()
            path.write_bytes(raw)
        self.output = self.root / self._testMethodName
        self.output.mkdir()
        self.files = file_contents(self.package, self.sources)
        for name, raw in self.files.items():
            (self.output / name).write_bytes(raw)

    def manifest(self, mutate):
        path = self.output / 'manifest.json'
        data = json.loads(path.read_bytes())
        mutate(data)
        path.write_bytes(encoded(data))

    def codes(self, report):
        return {item['code'] for item in report['issues']}

    def test_real_historical_packages_show_all_changes_and_current_valid(self):
        names = {'aves-009': {'docs/REVISION_LECTURA.md', 'nahuatl_local/lesson_review_packet.py'},
                 'aves-009-v2': {'docs/REVISION_LECTURA.md'}, 'aves-009-v1': set()}
        for folder, historical_changes in names.items():
            with self.subTest(folder=folder):
                output = ROOT / 'reports/reading-review' / folder
                manifest = json.loads((output / 'manifest.json').read_bytes())
                # Independent byte comparison allows later cycles to change
                # public dependencies without rewriting the immutable packet.
                changed = {p for p, expected in manifest['sources'].items()
                           if digest((ROOT / p).read_bytes()) != expected}
                self.assertTrue(historical_changes <= changed)
                report = inspect_package(output)
                self.assertEqual({item['reference'] for item in report['issues'] if item['code'] == 'source_changed'}, changed)
                self.assertEqual(report['state'], 'stale' if changed else 'valid')
                self.assertEqual(report['ready'], not changed)
                self.assertEqual(report['human_review'], 'pending')
                self.assertEqual(report['semantic_validation'], 'not_run' if changed else 'passed')
        current = inspect_package(self.output)
        self.assertEqual(current['issues'], [])
        self.assertEqual(current['state'], 'valid')
        self.assertEqual(current['semantic_validation'], 'passed')

    def test_valid_requires_real_verify_and_does_not_change_package(self):
        with patch('nahuatl_local.lesson_review_status.verify', wraps=verify) as check:
            report = inspect_package(self.output)
        self.assertTrue(report['ready'])
        check.assert_called_once_with(self.output)
        self.assertEqual(self.files, {p.name: p.read_bytes() for p in self.output.iterdir()})
        with patch('nahuatl_local.lesson_review_status.verify', return_value='other'):
            self.assertFalse(inspect_package(self.output)['ready'])

    def test_multiple_changed_missing_sources_ignore_size_and_mtime(self):
        inventory, queue, state = self.inputs.values()
        before = inventory.stat()
        raw = inventory.read_bytes()
        altered = raw.replace(b'142', b'143', 1)
        self.assertNotEqual(raw, altered)
        inventory.write_bytes(altered)
        os.utime(inventory, ns=(before.st_atime_ns, before.st_mtime_ns))
        self.assertEqual(inventory.stat().st_size, before.st_size)
        self.assertEqual(inventory.stat().st_mtime_ns, before.st_mtime_ns)
        queue.unlink()
        state.write_bytes(state.read_bytes() + b'\n')
        with patch('nahuatl_local.lesson_review_status.verify') as check:
            report = inspect_package(self.output)
        check.assert_not_called()
        changed = {item['reference']: item for item in report['issues']}
        self.assertEqual(set(changed), {str(p.relative_to(ROOT)) for p in self.inputs.values()})
        self.assertEqual(report['state'], 'stale')
        self.assertIn('source_missing', self.codes(report))
        self.assertEqual(changed[str(inventory.relative_to(ROOT))]['current_sha256'], digest(altered))
        self.assertFalse(report['ready'])

    def test_member_changes_missing_and_extra_are_aggregated_without_notes(self):
        (self.output / 'package.md').write_text('Changed public text')
        (self.output / 'human-decisions.blank.json').unlink()
        (self.output / 'private participant notes.txt').write_text('Confidential participant identity')
        report = inspect_package(self.output)
        self.assertTrue({'member_changed', 'member_missing', 'member_extra'} <= self.codes(report))
        self.assertEqual(report['state'], 'invalid')
        rendered = encoded(report).decode() + render(report)
        self.assertNotIn('participant', rendered)
        self.assertNotIn('Changed public text', rendered)

    def test_recalculated_manifest_and_entire_package_do_not_validate_forgery(self):
        fake = copy.deepcopy(self.package)
        fake['lesson']['examples'][0]['comprehension']['explanation'] = 'False human approval'
        for name, raw in file_contents(fake, self.sources).items():
            (self.output / name).write_bytes(raw)
        report = inspect_package(self.output)
        self.assertEqual(report['semantic_validation'], 'failed')
        self.assertEqual(self.codes(report), {'semantic_failed'})
        self.assertFalse(report['ready'])
        self.assertNotIn('False human approval', encoded(report).decode())

    def test_internal_unregistered_inventory_and_state_evidence_never_open(self):
        unknown = self.root / 'unregistered-internal.json'
        unknown.write_text('Private review notes kept in a public folder')
        reference = str(unknown.relative_to(ROOT))
        original_read = Path.read_bytes
        def guard(path):
            if path == unknown:
                raise AssertionError('Indirect unregistered read')
            return original_read(path)
        for role in ('inventory.json', 'state.json'):
            with self.subTest(role=role):
                path = self.inputs[role]
                data = json.loads(self.original_inputs[path])
                if role == 'inventory.json':
                    data['sources'][reference] = digest(b'known')
                else:
                    next(iter(data['tasks'].values()))['decision'] = {'evidence': [reference]}
                path.write_bytes(encoded(data))
                self.manifest(lambda d: d['sources'].update({str(path.relative_to(ROOT)): digest(path.read_bytes())}))
                with patch.object(Path, 'read_bytes', guard), patch('nahuatl_local.lesson_review_status.verify') as check:
                    report = inspect_package(self.output)
                self.assertEqual(self.codes(report), {'internal_references_invalid'})
                self.assertFalse(report['ready'])
                check.assert_not_called()
                self.assertNotIn('unregistered-internal', encoded(report).decode())
                path.write_bytes(self.original_inputs[path])
                (self.output / 'manifest.json').write_bytes(self.files['manifest.json'])

    def test_strict_manifest_missing_fields_types_hashes_and_unknown_fields(self):
        original = self.files['manifest.json']
        mutations = [lambda d: d.pop('files'), lambda d: d.update(schema_version=True),
                     lambda d: d.update(schema_version='1'), lambda d: d.update(sources=[]),
                     lambda d: d.update(lesson_id=[]), lambda d: d.update(diagnostic_fingerprint=7),
                     lambda d: d.update(extra='x'), lambda d: d.update(files=[]),
                     lambda d: d['files'].update({'package.md': 1}),
                     lambda d: d['files'].update({'../secret': 'a'*64}),
                     lambda d: d.update(sources={}), lambda d: d.update(kind=None)]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                (self.output / 'manifest.json').write_bytes(original)
                self.manifest(mutation)
                with patch('nahuatl_local.lesson_review_status.verify') as check:
                    report = inspect_package(self.output)
                self.assertIn('manifest_invalid', self.codes(report))
                self.assertFalse(report['ready'])
                check.assert_not_called()

    def test_source_hash_types_and_missing_declared_source_fail_closed(self):
        name = sorted(self.sources)[0]
        self.manifest(lambda d: d['sources'].update({name: ['fake']}))
        self.assertIn('source_hash_invalid', self.codes(inspect_package(self.output)))
        self.manifest(lambda d: d['sources'].pop(name))
        self.assertIn('source_unlisted', self.codes(inspect_package(self.output)))

    def test_duplicate_json_noncanonical_manifest_and_malformed_package(self):
        path = self.output / 'manifest.json'
        path.write_bytes(self.files['manifest.json'].replace(b'{', b'{"schema_version":1,', 1))
        self.assertIn('json_invalid', self.codes(inspect_package(self.output)))
        path.write_bytes(self.files['manifest.json'] + b'\n')
        self.assertIn('manifest_noncanonical', self.codes(inspect_package(self.output)))
        path.write_bytes(self.files['manifest.json'])
        (self.output / 'package.json').write_bytes(b'null')
        report = inspect_package(self.output)
        self.assertIn('diagnostic_inputs_invalid', self.codes(report))
        (self.output / 'package.json').write_bytes(b'{ broken')
        self.assertIn('json_invalid', self.codes(inspect_package(self.output)))

    def test_private_unknown_and_traversal_sources_never_open_or_leak(self):
        unknown = self.root / 'unregistered.json'
        unknown.write_text('Do not open this file')
        private = ROOT / 'data/never-read-secret.json'
        references = [str(unknown.relative_to(ROOT)), str(private.relative_to(ROOT)),
                      '/private/tmp/outside.json', 'reports/../data/never-read-secret.json']
        self.manifest(lambda d: d['sources'].update({name: 'a'*64 for name in references}))
        original = Path.read_bytes
        reads = []
        def spy(path):
            reads.append(path)
            if path in {private, unknown}:
                raise AssertionError('Forbidden read')
            return original(path)
        with patch.object(Path, 'read_bytes', spy):
            report = inspect_package(self.output)
        self.assertTrue({'source_unsafe', 'source_unknown'} <= self.codes(report))
        self.assertNotIn(private, reads)
        self.assertNotIn(unknown, reads)
        self.assertNotIn('never-read-secret', encoded(report).decode())
        self.assertNotIn('unregistered.json', encoded(report).decode())

    def test_symlink_member_and_ancestor_checked_before_open(self):
        md = self.output / 'package.md'
        md.unlink()
        md.symlink_to(self.inputs['inventory.json'])
        link = self.root / 'linked-directory'
        link.symlink_to(self.output, target_is_directory=True)
        for path, code in [(self.output, 'member_unsafe'), (link, 'package_unsafe'),
                           (link / 'child', 'package_unsafe')]:
            with self.subTest(path=path):
                report = inspect_package(path)
                self.assertIn(code, self.codes(report))
                self.assertFalse(report['ready'])

    def test_symlink_source_rejected_and_other_change_still_reported(self):
        inventory = self.inputs['inventory.json']
        inventory.unlink()
        inventory.symlink_to(self.inputs['queue.json'])
        self.inputs['state.json'].write_bytes(self.inputs['state.json'].read_bytes() + b'\n')
        report = inspect_package(self.output)
        self.assertIn('source_unsafe', self.codes(report))
        self.assertIn('source_changed', self.codes(report))
        self.assertFalse(report['ready'])

    def test_diagnostic_reference_types_paths_and_private_inputs_rejected(self):
        for value in [None, [], {'inventory': {}},
                      {'inventory': 'data/private.json', 'queue': 'reports/a/queue.json', 'state': 'reports/a/state.json'},
                      {'inventory': 'reports/a/inventory.json', 'queue': 'reports/b/queue.json', 'state': 'reports/a/state.json'}]:
            with self.subTest(value=value):
                fake = copy.deepcopy(self.package)
                fake['diagnostic_inputs'] = value
                (self.output / 'package.json').write_bytes(encoded(fake))
                self.assertIn('diagnostic_inputs_invalid', self.codes(inspect_package(self.output)))

    def test_missing_and_unsafe_package_paths_return_diagnostics(self):
        for path, code in [(self.root / 'missing', 'package_missing'),
                           (ROOT / 'data/private', 'package_unsafe'),
                           (ROOT / 'reports/../data/private', 'package_unsafe')]:
            self.assertIn(code, self.codes(inspect_package(path)))

    def test_outputs_idempotent_preserve_edits_notes_and_refuse_protected_paths(self):
        (self.output / 'package.md').write_text('changed')
        report = inspect_package(self.output)
        for suffix in ('json', 'md'):
            dst = self.root / ('report.' + suffix)
            self.assertEqual(write_report(report, dst, self.output), 'written')
            raw = dst.read_bytes()
            self.assertEqual(write_report(report, dst, self.output), 'unchanged')
            self.assertEqual(raw, dst.read_bytes())
            dst.write_bytes(raw + b'Human notes\n')
            with self.assertRaisesRegex(ValueError, 'No se sobrescriben'):
                write_report(report, dst, self.output)
            self.assertEqual(dst.read_bytes(), raw + b'Human notes\n')
        for dst in (self.output / 'status.json', ROOT / 'reports/documentary-retrieval-v1.json',
                    ROOT / 'data/output.json', self.root / 'report.txt',
                    self.root / 'missing/state.json'):
            with self.assertRaises(ValueError):
                write_report(report, dst, self.output)
        link = self.root / 'linked-report.json'
        link.symlink_to(self.root / 'report.json')
        with self.assertRaises(ValueError):
            write_report(report, link, self.output)

    def test_cli_exit_status_and_deterministic_stdout(self):
        (self.output / 'package.md').write_text('changed')
        from contextlib import redirect_stdout
        from io import StringIO
        out1, out2 = StringIO(), StringIO()
        with redirect_stdout(out1):
            status = main(['--package', str(self.output)])
        with redirect_stdout(out2):
            self.assertEqual(main(['--package', str(self.output)]), status)
        self.assertEqual(status, 1)
        self.assertEqual(out1.getvalue(), out2.getvalue())
        self.assertEqual(json.loads(out1.getvalue())['state'], 'invalid')
        md = StringIO()
        with redirect_stdout(md):
            main(['--package', str(self.output), '--format', 'md'])
        self.assertIn('Revisión humana: **pendiente**', md.getvalue())


if __name__ == '__main__':
    unittest.main()
