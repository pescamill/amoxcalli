"""Fuentes abiertas: lote de Wiktionary (CC BY-SA) y notas de Carochi (dominio público)."""
import json
import tempfile
import unittest
from pathlib import Path

from nahuatl_local import grammar_notes, lexicon
from nahuatl_local.corpus import CorpusStore
from nahuatl_local.text import key_of

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / 'corpus/wiktionary-lexicon-v12.json'


class WiktionaryBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = json.loads(BUNDLE.read_text(encoding='utf-8'))
        cls.records = cls.bundle['records']

    def test_every_record_carries_licence_attribution_and_no_training(self):
        for r in self.records:
            rights = r['rights']
            self.assertEqual(rights['license'], 'CC BY-SA 4.0', r['id'])
            self.assertIs(rights['training'], False, r['id'])
            self.assertTrue(rights['share_alike'], r['id'])
            if r['kind'] != 'source':
                revid = r['url'].rsplit('oldid=', 1)[1]
                self.assertIn(f'revisión {revid}', rights['attribution'], r['id'])
                self.assertIn('oldid=', r['url'], r['id'])
                self.assertEqual(r['import_status'], 'automatic_transcription')
                self.assertEqual(r['import_source'], 'wiktionary')
                self.assertEqual(r['verification'], 'inherited')
                self.assertTrue(r['evidence'][0]['source_id'].startswith('src-wiktionary-'))

    def test_senses_mark_their_gloss_language(self):
        senses = [r for r in self.records if r['kind'] == 'sense']
        self.assertTrue(senses)
        self.assertEqual({r['gloss_language'] for r in senses}, {'es', 'en'})

    def test_no_new_form_shares_a_key_with_an_earlier_entry(self):
        # Deduplicación contra Molina/GDN y las fichas curadas: ninguna forma nueva cae en una entrada previa.
        earlier = {key_of(r.get('catalog_normalized') or r.get('written') or '')
                   for step, bundle in lexicon.steps() if step.path != 'corpus/wiktionary-lexicon-v12.json'
                   for r in bundle.get('records', []) if r.get('kind') == 'form'}
        clashes = [r['id'] for r in self.records if r['kind'] == 'form' and key_of(r['written']) in earlier]
        self.assertEqual(clashes, [])

    def test_loading_the_batch_preserves_every_earlier_record(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for step in lexicon.STEPS:
                if (ROOT / step.path).is_file() and step.path != 'corpus/wiktionary-lexicon-v12.json':
                    (root / step.path).parent.mkdir(parents=True, exist_ok=True)
                    (root / step.path).write_bytes((ROOT / step.path).read_bytes())
            (root / lexicon.RELEASES).write_bytes((ROOT / lexicon.RELEASES).read_bytes())
            for release, _ in lexicon.releases():
                (root / 'corpus' / release['bundle']).write_bytes((ROOT / 'corpus' / release['bundle']).read_bytes())
            before = {rid: {k: v for k, v in r.items() if k != 'version'}
                      for rid, r in CorpusStore(root / 'before.sqlite3', root=root).records().items()}
            after = {rid: {k: v for k, v in r.items() if k != 'version'}
                     for rid, r in CorpusStore(root / 'after.sqlite3').records().items()}
        self.assertEqual({rid: after.get(rid) for rid in before}, before)
        self.assertEqual(len(after) - len(before), len(self.records))

    def test_catalog_entries_show_licence_for_new_entries(self):
        catalog = lexicon.load()
        new = [e for e in catalog['entries'] if any(s.get('import_source') == 'wiktionary' for s in e['senses'])]
        self.assertTrue(new)
        for e in new:
            self.assertFalse(e['rights']['training'])
            self.assertTrue(e['review']['automatic'])
            self.assertTrue(any(s.startswith('src-wiktionary-') for s in e['sources']))


class GrammarNotesTests(unittest.TestCase):
    def test_every_unit_has_a_cited_note(self):
        data = grammar_notes.load()
        self.assertIn('archive.org', data['source']['facsimile']['url'])
        for unit in grammar_notes.UNITS:
            notes = grammar_notes.for_unit(unit)
            self.assertTrue(notes, unit)
            for note in notes:
                self.assertRegex(note['citation']['folios'], r'f\. \d+[rv]')
                self.assertTrue(note['citation']['chapter'].startswith('cap.'))


if __name__ == '__main__':
    unittest.main()
