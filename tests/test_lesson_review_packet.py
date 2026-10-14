import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from nahuatl_local.community import ROOT, DEFAULT_DB
from nahuatl_local.editorial_pipeline import encoded
from nahuatl_local.learning import Learning
from nahuatl_local.iteration import main as diagnose_current
from nahuatl_local.lesson_review_packet import (blank_decisions, build, checked_hashes,
                                                digest, file_contents, prepare,
                                                safe_path, verify)
from nahuatl_local.research import Archive


class LessonReviewPacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(dir=ROOT / 'reports', prefix='test-reading-review-')
        cls.root = Path(cls.temp.name)
        cls.inventory = cls.root / 'inventory.json'
        cls.queue = cls.root / 'queue.json'
        cls.state = cls.root / 'state.json'
        # Generate coherent current inputs in the fixture, preserving live state
        # and historical diagnostics rather than requiring an old UI hash.
        cls.state.write_bytes((ROOT / 'reports/iterations/state.json').read_bytes())
        diagnose_current(['--output', str(cls.root), '--state', str(cls.state)])
        cls.originals = {p: p.read_bytes() for p in (cls.inventory, cls.queue, cls.state)}
        cls.package, cls.sources = build('aves', cls.inventory, cls.queue, cls.state)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        for p, raw in self.originals.items():
            p.write_bytes(raw)
        self.output = self.root / self._testMethodName

    def write_packet(self, package=None):
        self.output.mkdir()
        for name, raw in file_contents(package or self.package, self.sources).items():
            (self.output / name).write_bytes(raw)

    def test_originals_ids_citations_and_all_existing_questions(self):
        source = next(l for l in Learning(Archive()).data['lessons'] if l['id'] == 'aves')
        self.assertEqual([e['archive_id'] for e in self.package['lesson']['examples']],
                         ['axolotl-14546', 'axolotl-14253', 'axolotl-08856', 'axolotl-00751'])
        archive = Archive()
        for expected, actual in zip(source['examples'], self.package['lesson']['examples']):
            self.assertEqual(actual['passage'], archive.get(expected['archive_id']))
            for key in ('source_hash', 'exercise', 'comprehension', 'context', 'explore_words', 'annotations'):
                self.assertEqual(actual[key], expected[key])
            p = actual['passage']
            self.assertEqual(digest((p['nah'] + '\0' + p['es']).encode()), actual['source_hash'])
            self.assertIn('edición primaria pendiente', p['locator'])
            self.assertIn('157f34300f4ca92c3d75b74ec14142916d75c30b', p['source_url'])
            for a in actual['annotations']:
                text = p['nah'].encode('utf-16-le')[a['start']*2:a['end']*2].decode('utf-16-le')
                self.assertEqual(text, a['quote'])

    def test_relevant_tasks_preserve_both_fingerprints_and_evidence(self):
        selected = {entry['task']['id']: entry['task'] for entry in self.package['tasks']}
        self.assertEqual(set(selected), {'lesson-aves-source-review', 'lesson-aves-exercises',
                                        'lesson-aves-learner-trial', 'word-sense-tototl-glyph-scope',
                                        'batch-visual-policy'})
        queue = json.loads(self.queue.read_text())['tasks']
        self.assertEqual(list(selected.values()), [t for t in queue if t['id'] in selected])
        self.assertTrue(all(t['status'] == 'open' and t['category'] == 'human' for t in selected.values()))

    def test_visual_scope_rights_and_unfilled_human_notes(self):
        glyph = next(r for r in self.package['catalog_records'] if r['kind'] == 'glyph')
        self.assertEqual(glyph['id'], 'glyph-tototl-mdz46r')
        self.assertEqual(glyph['glyph_status'], 'proposed')
        self.assertIn('Tototepec', glyph['context'])
        self.assertEqual(glyph['evidence'][0]['locator'], 'Códice Mendoza, f. 46r; VLA tototl (Mdz46r)')
        self.assertFalse(glyph['rights']['training'])
        self.assertIn('Stephanie Wood', glyph['image_credit'])
        self.assertTrue({'src-mendoza', 'src-vla'}.issubset({r['id'] for r in self.package['catalog_records']}))
        notes = blank_decisions(self.package)
        self.assertEqual(notes['status'], 'pending')
        for decision in notes['decisions']:
            self.assertEqual(decision['status'], 'pending')
            self.assertEqual([decision[k] for k in ('reviewer', 'date', 'resolution', 'notes')], ['', '', '', ''])
            self.assertEqual(decision['evidence'], [])
        trial = notes['comprehension_trial']
        self.assertEqual(trial['status'], 'pending')
        self.assertTrue(all(not v for k, v in trial.items() if k != 'status'))

    def test_idempotence_and_reconstruction(self):
        self.assertEqual(prepare('aves', self.inventory, self.queue, self.state, self.output), 'prepared')
        before = {p.name: p.read_bytes() for p in self.output.iterdir()}
        self.assertEqual(prepare('aves', self.inventory, self.queue, self.state, self.output), 'unchanged')
        self.assertEqual(verify(self.output), 'valid')
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.output.iterdir()})

    def test_notes_cannot_be_overwritten(self):
        self.write_packet()
        notes = self.output / 'human-decisions.blank.json'
        saved = notes.read_bytes() + b'\n'
        notes.write_bytes(saved)
        with self.assertRaisesRegex(ValueError, 'no se sobrescriben'):
            prepare('aves', self.inventory, self.queue, self.state, self.output)
        self.assertEqual(notes.read_bytes(), saved)
        with self.assertRaises(ValueError):
            verify(self.output)

    def test_semantic_forgery_even_with_recalculated_manifest(self):
        fake = copy.deepcopy(self.package)
        fake['lesson']['examples'][0]['comprehension']['explanation'] = 'Invented approval'
        self.write_packet(fake)
        with self.assertRaises(ValueError):
            verify(self.output)

    def test_stale_hash_and_source_manifest(self):
        source = self.root / 'public-source.json'
        source.write_text('original')
        hashes = {str(source.relative_to(ROOT)): digest(source.read_bytes())}
        checked_hashes(hashes)
        source.write_text('changed!')
        with self.assertRaisesRegex(ValueError, 'obsoleta'):
            checked_hashes(hashes)
        with patch('nahuatl_local.lesson_review_packet.source_manifest', return_value={}):
            with self.assertRaisesRegex(ValueError, 'inventario es obsoleto'):
                build('aves', self.inventory, self.queue, self.state)

    def test_forged_queue_or_state_and_invalid_lesson(self):
        queue = json.loads(self.queue.read_text())
        queue['tasks'][0]['fingerprint'] = 'forged'
        self.queue.write_bytes(encoded(queue))
        with self.assertRaisesRegex(ValueError, 'inconsistentes'):
            build('aves', self.inventory, self.queue, self.state)
        self.queue.write_bytes(self.originals[self.queue])
        state = json.loads(self.state.read_text())
        state['tasks']['lesson-aves-source-review']['status'] = 'resolved'
        self.state.write_bytes(encoded(state))
        with self.assertRaisesRegex(ValueError, 'inconsistentes'):
            build('aves', self.inventory, self.queue, self.state)
        self.state.write_bytes(self.originals[self.state])
        with self.assertRaisesRegex(ValueError, 'no está disponible'):
            build('missing', self.inventory, self.queue, self.state)

    def test_private_traversal_external_and_output_paths(self):
        for path in (DEFAULT_DB, ROOT / 'data/secret.json', ROOT / '.git/config',
                     ROOT / 'reports/../data/secret.json', Path('/private/tmp/external.json')):
            with self.assertRaises(ValueError):
                safe_path(path)
        for path in (ROOT / 'reports', ROOT / 'corpus/review', ROOT / 'editorial/review'):
            with self.assertRaises(ValueError):
                safe_path(path, output=True)
        with self.assertRaises(ValueError):
            build('../aves', self.inventory, self.queue, self.state)

    def test_symlink_input_ancestor_output_and_members(self):
        link = self.root / 'linked.json'
        link.symlink_to(self.inventory)
        with self.assertRaisesRegex(ValueError, 'simbólicos'):
            build('aves', link, self.queue, self.state)
        directory = self.root / 'linked-dir'
        directory.symlink_to(self.root, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'simbólicos'):
            safe_path(directory / 'new/output', output=True)
        self.write_packet()
        md = self.output / 'package.md'
        md.unlink()
        md.symlink_to(self.inventory)
        with self.assertRaisesRegex(ValueError, 'simbólicos'):
            verify(self.output)

    def test_extra_files_and_manifest_names_are_rejected(self):
        self.write_packet()
        (self.output / 'human-decisions.json').write_text('real notes')
        with self.assertRaisesRegex(ValueError, 'archivos distintos'):
            verify(self.output)
        (self.output / 'human-decisions.json').unlink()
        manifest = json.loads((self.output / 'manifest.json').read_text())
        manifest['files']['../private.json'] = 'bad'
        (self.output / 'manifest.json').write_bytes(encoded(manifest))
        with self.assertRaisesRegex(ValueError, 'Manifiesto'):
            verify(self.output)

    def test_markdown_has_both_keys_and_scope_citations(self):
        md = file_contents(self.package, self.sources)['package.md'].decode()
        self.assertEqual(md.count('### Reconocimiento de la forma'), 4)
        self.assertEqual(md.count('### Comprensión del contexto'), 4)
        self.assertIn('Códice Mendoza, f. 46r', md)
        self.assertIn('"training": false', md)
        self.assertIn('ruta desde la raíz del proyecto', md)
        self.assertIn('no demuestran comprensión independiente', md)


if __name__ == '__main__':
    unittest.main()
