import copy
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from nahuatl_local import lexical_link_review as review
from nahuatl_local.community import ROOT, DEFAULT_DB
from nahuatl_local.editorial_pipeline import encoded
from nahuatl_local.lesson_review_packet import safe_path


class LexicalLinkReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (ROOT / 'reports' / 'lexical-link-review').mkdir(exist_ok=True)
        cls.actual = review.build()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / 'reports' / 'lexical-link-review', prefix='test-')
        self.output = Path(self.temp.name) / 'package'
        self.addCleanup(self.temp.cleanup)
        c = copy.deepcopy(self.actual['candidates'][0])
        self.element = c['element']
        self.form, self.sense = c['form']['record'], c['sense']['record']
        self.records = {r['record']['id']: r['record'] for r in c['sources']}
        self.records.update({self.form['id']: self.form, self.sense['id']: self.sense})
        ctx = c['contexts']['occurrences'][0]
        occurrence = ctx['occurrence']
        occurrence['components'] = [comp for comp in occurrence['components']
                                    if comp['element_id'] == self.element['id']]
        self.catalog = dict(schema_version=1, rights=c['catalog_rights'],
                            documents=[c['document']], pages=[ctx['page']], zones=[ctx['zone']],
                            elements=[self.element], occurrences=[occurrence])
        self.origins = {r['record']['id']: r['source_rows'] for r in [c['form'], c['sense'], *c['sources']]}

    def selected(self):
        return review.build_candidates(self.records, self.catalog, {'public': 'hash'}, self.origins)

    def write_package(self, report=None):
        report = report or self.actual
        self.output.mkdir()
        (self.output / 'candidates.json').write_bytes(encoded(report))
        (self.output / 'candidates.md').write_text(review.render(report), encoding='utf-8')

    def test_real_candidates_preserve_originals_sources_and_pending_reviews(self):
        self.assertEqual(self.actual['counts']['matched_form_pairs'], 17)
        self.assertEqual(self.actual['counts']['excluded_existing_sense_pairs'], 9)
        self.assertEqual({c['element']['designation'] for c in self.actual['candidates']},
                         {'ehecatl', 'mazatl', 'nacayotl', 'tletl', 'xayacatl', 'michin', 'xiquipilli', 'tonatiuh'})
        self.assertEqual(len(self.actual['candidates']), 8)
        for c in self.actual['candidates']:
            self.assertEqual(c['human_review'], review.blank_review())
            self.assertFalse(c['catalog_rights']['training'])
            self.assertFalse(c['match']['accent_removal'])
            self.assertEqual(c['element_row_sha256'], review.fingerprint(c['element']))
            for snapshot in [c['form'], c['sense'], *c['sources']]:
                self.assertEqual(snapshot['public_row_sha256'], review.fingerprint(snapshot['record']))
                self.assertTrue(snapshot['source_rows'])
                for original in snapshot['source_rows']:
                    self.assertEqual(original['row_sha256'], review.fingerprint(original['row']))
                    self.assertTrue(original['row']['rights']['public'])
            self.assertTrue(c['form']['record']['variant'])
            self.assertTrue(c['form']['record']['evidence'])

    def test_homonyms_and_each_form_remain_separate(self):
        other_sense = dict(self.sense, id='sense-other', definition='another meaning')
        other_form = dict(self.form, id='form-other', sense_id=other_sense['id'])
        variant = dict(self.form, id='form-variant', variant='other', variant_label='Other variety')
        self.records.update({r['id']: r for r in (other_sense, other_form, variant)})
        selected = self.selected()['candidates']
        self.assertEqual(len(selected), 3)
        self.assertEqual(len({c['id'] for c in selected}), 3)
        self.assertEqual({c['form_id'] for c in selected}, {self.form['id'], 'form-other', 'form-variant'})

    def test_exclusion_applies_only_to_the_registered_sense(self):
        other_sense = dict(self.sense, id='sense-other')
        other_form = dict(self.form, id='form-other', sense_id=other_sense['id'])
        self.records.update({r['id']: r for r in (other_sense, other_form)})
        self.element['lexical_links'] = [dict(sense_id=self.sense['id'], relation='designation', note='existing')]
        result = self.selected()
        self.assertEqual(result['counts']['excluded_existing_sense_pairs'], 1)
        self.assertEqual([c['sense_id'] for c in result['candidates']], ['sense-other'])

    def test_nfc_case_and_outer_spaces_without_accent_removal(self):
        self.element['designation'] = 'Éhecatl'
        self.form['written'] = '  E\u0301HECATL  '
        original = copy.deepcopy((self.form, self.element))
        candidate = self.selected()['candidates'][0]
        self.assertEqual(candidate['match']['method'], 'NFC_casefold_strip')
        self.assertEqual(candidate['form']['record']['written'], original[0]['written'])
        self.assertEqual((self.form, self.element), original)
        self.form['written'] = 'ehecatl'
        self.assertEqual(self.selected()['candidates'], [])
        self.form['written'] = 'é hecatl'
        self.assertEqual(self.selected()['candidates'], [])

    def test_private_and_withdrawn_forms_senses_and_sources_remove_dependents(self):
        baseline = copy.deepcopy(self.records)
        targets = [self.form['id'], self.sense['id'], *[r for r in self.records if self.records[r]['kind'] == 'source']]
        for rid in targets:
            for state in ('private', 'withdrawn'):
                with self.subTest(rid=rid, state=state):
                    self.records = copy.deepcopy(baseline)
                    if state == 'private':
                        self.records[rid]['rights']['public'] = False
                    else:
                        self.records[rid]['withdrawn'] = True
                    self.assertEqual(self.selected()['candidates'], [])

    def test_private_withdrawn_and_hidden_dependency_originals_never_reappear(self):
        original = copy.deepcopy(self.form)
        private = copy.deepcopy(original)
        private['rights']['public'] = False
        withdrawn = dict(original, withdrawn=True)
        obsolete = dict(original, evidence=[dict(source_id='hidden-source', locator='secret', status='inherited')])
        hidden = dict(next(r for r in self.records.values() if r['kind'] == 'source'), id='hidden-source')
        hidden['rights'] = dict(hidden['rights'], public=False)
        self.records[hidden['id']] = hidden
        self.origins[self.form['id']] = [dict(row=r, row_sha256=review.fingerprint(r))
                                        for r in (original, private, withdrawn, obsolete)]
        candidates = self.selected()['candidates']
        self.assertEqual(len(candidates), 1)
        self.assertEqual([r['row'] for r in candidates[0]['form']['source_rows']], [original])
        self.assertNotIn('secret', json.dumps(candidates))

    def test_contexts_sorted_capped_deduplicated_and_hashed_without_inference(self):
        prototype = copy.deepcopy(self.catalog['occurrences'][0])
        rows = []
        for i in (4, 2, 3, 1):
            row = dict(copy.deepcopy(prototype), id=f'occurrence-{i}')
            row['components'] *= 2
            if i == 1:
                for component in row['components']:
                    component['values'] = []
            rows.append(row)
        self.catalog['occurrences'] = rows
        contexts = self.selected()['candidates'][0]['contexts']
        self.assertEqual((contexts['total'], contexts['shown'], contexts['omitted']), (4, 3, 1))
        self.assertEqual([ctx['occurrence']['id'] for ctx in contexts['occurrences']],
                         ['occurrence-1', 'occurrence-2', 'occurrence-3'])
        self.assertEqual(contexts['occurrences'][0]['catalogued_values'], [[], []])
        for ctx in contexts['occurrences']:
            self.assertEqual(ctx['occurrence_row_sha256'], review.fingerprint(ctx['occurrence']))
            self.assertEqual(ctx['page_row_sha256'], review.fingerprint(ctx['page']))
            self.assertEqual(ctx['page']['source_hash'], self.catalog['pages'][0]['source_hash'])

    def test_ids_stable_but_changed_gloss_is_detectable(self):
        first = self.selected()['candidates'][0]
        self.sense['definition'] += ' revised'
        second = self.selected()['candidates'][0]
        self.assertEqual(first['id'], second['id'])
        self.assertNotEqual(first['fingerprint'], second['fingerprint'])

    def test_prepare_check_repeat_are_byte_identical(self):
        with patch.object(review, 'build', return_value=self.actual):
            self.assertEqual(review.prepare(self.output)[0], 'prepared')
            before = {p.name: p.read_bytes() for p in self.output.iterdir()}
            self.assertEqual(review.prepare(self.output, check=True)[0], 'valid')
            self.assertEqual(review.prepare(self.output)[0], 'unchanged')
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.output.iterdir()})

    def test_edited_notes_and_extra_members_never_overwritten(self):
        self.write_package()
        target = self.output / 'candidates.json'
        report = copy.deepcopy(self.actual)
        report['candidates'][0]['human_review']['notes'] = 'Human note'
        saved = encoded(report)
        target.write_bytes(saved)
        with patch.object(review, 'build', return_value=self.actual):
            for check in (False, True):
                with self.assertRaisesRegex(ValueError, 'No se sobrescriben notas'):
                    review.prepare(self.output, check)
        self.assertEqual(target.read_bytes(), saved)
        (self.output / 'decision.txt').write_text('Human decision')
        with patch.object(review, 'build') as build:
            with self.assertRaisesRegex(ValueError, 'no se sobrescriben notas'):
                review.prepare(self.output)
            build.assert_not_called()

    def test_stale_source_and_semantic_changes_reject_existing_package(self):
        self.write_package()
        before = {p.name: p.read_bytes() for p in self.output.iterdir()}
        for mutation in ('source', 'gloss'):
            changed = copy.deepcopy(self.actual)
            if mutation == 'source':
                changed['source_hashes']['corpus/seed.json'] = 'changed'
            else:
                changed['candidates'][0]['sense']['record']['definition'] = 'Invented equivalence'
            with patch.object(review, 'build', return_value=changed):
                with self.assertRaisesRegex(ValueError, 'obsoletas'):
                    review.prepare(self.output, check=True)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.output.iterdir()})

    def test_source_change_during_build_aborts(self):
        snapshot = review.source_snapshot()
        changed = ({**snapshot[0], 'corpus/seed.json': 'changed'}, snapshot[1])
        with patch.object(review, 'source_snapshot', side_effect=[snapshot, changed]):
            with self.assertRaisesRegex(ValueError, 'cambió durante'):
                review.build()

    def test_private_traversal_and_external_outputs_rejected_before_build(self):
        with patch.object(review, 'build') as build:
            for path in (DEFAULT_DB, ROOT / '.git/config', ROOT / 'data/private',
                         ROOT / 'reports/../data/private', Path('/private/tmp/candidates'),
                         ROOT / 'corpus/candidates', ROOT / 'reports/another/package'):
                with self.subTest(path=path), self.assertRaises(ValueError):
                    review.prepare(path)
            build.assert_not_called()

    def test_symlink_package_member_ancestor_and_source_rejected_before_reads(self):
        self.write_package()
        member = self.output / 'candidates.md'
        member.unlink()
        member.symlink_to(self.output / 'candidates.json')
        with patch.object(review, 'build') as build:
            with self.assertRaisesRegex(ValueError, 'simbólicos'):
                review.prepare(self.output, check=True)
            ancestor = Path(self.temp.name) / 'alias'
            ancestor.symlink_to(self.output, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'simbólicos'):
                review.prepare(ancestor / 'new')
            build.assert_not_called()
        source_link = Path(self.temp.name) / 'source-link'
        source_link.symlink_to(ROOT / 'corpus/seed.json')
        def guarded(path, **kwargs):
            return safe_path(source_link if str(path) == 'corpus/seed.json' else path, **kwargs)
        with patch.object(review, 'safe_path', side_effect=guarded), patch.object(review, 'CorpusStore') as store:
            with self.assertRaisesRegex(ValueError, 'simbólicos'):
                review.build()
            store.assert_not_called()

    def test_real_build_reads_public_allowlist_and_explicit_temporary_db_only(self):
        paths, databases = [], []
        original_open, original_connect = io.open, sqlite3.connect
        def observed_open(path, *args, **kwargs):
            if isinstance(path, (str, Path)):
                paths.append(Path(path))
            return original_open(path, *args, **kwargs)
        def observed_connect(path, *args, **kwargs):
            databases.append(Path(path))
            return original_connect(path, *args, **kwargs)
        with patch('io.open', side_effect=observed_open), patch('sqlite3.connect', side_effect=observed_connect):
            rebuilt = review.build()
        self.assertEqual(rebuilt, self.actual)
        allowed = {ROOT / p for p in rebuilt['source_hashes']}
        self.assertTrue(paths)
        self.assertTrue(set(paths).issubset(allowed), set(paths) - allowed)
        self.assertTrue(databases)
        self.assertEqual({p.name for p in databases}, {'public.sqlite3'})
        self.assertTrue(all(p != DEFAULT_DB and 'amoxcalli-lexical-link-review-' in str(p.parent)
                            and not p.exists() for p in databases))


if __name__ == '__main__':
    unittest.main()
