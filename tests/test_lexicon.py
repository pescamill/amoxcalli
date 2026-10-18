import shutil
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from nahuatl_local import lexicon
from nahuatl_local.corpus import CorpusStore
from nahuatl_local.stems import load_records

ROOT = Path(__file__).resolve().parents[1]


def without_version(records):
    return {rid: {k: v for k, v in r.items() if k != 'version'} for rid, r in records.items()}


class LexiconTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = lexicon.load()
        cls.records = lexicon.records_of(cls.catalog)

    def test_catalog_is_current_and_equals_a_fresh_store(self):
        self.assertEqual((ROOT / lexicon.CATALOG).read_text(encoding='utf-8'), lexicon.encode(lexicon.build()))
        with tempfile.TemporaryDirectory() as directory:
            fresh = CorpusStore(Path(directory) / 'fresh.sqlite3').public_records()
        self.assertEqual(without_version(fresh), self.records)

    def test_server_analyzer_and_evaluations_read_the_same_records(self):
        self.assertEqual(load_records(), self.records)
        self.assertEqual(set(self.catalog['inputs']), set(lexicon.input_paths()))
        self.assertEqual(lexicon.BUNDLE_PATHS, tuple(s.path for s in lexicon.STEPS))

    def test_stale_catalog_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for path in list(self.catalog['inputs']) + [lexicon.CATALOG, lexicon.RELEASES]:
                (root / path).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(ROOT / path, root / path)
            self.assertEqual(lexicon.load_records(root), self.records)
            flor = root / 'corpus/flor-lexicon-v8.json'
            flor.write_text(flor.read_text(encoding='utf-8') + '\n', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'obsoleto'):
                lexicon.load(root)

    def test_entry_schema_groups_every_lexical_record_once(self):
        entries = self.catalog['entries']
        members = [m['id'] for e in entries for m in e['senses'] + e['forms'] + e['glyphs']]
        self.assertEqual(len(members), len(set(members)))
        kinds = {r['id'] for r in self.records.values() if r['kind'] in ('sense', 'form', 'glyph')}
        self.assertEqual(set(members), kinds)
        self.assertEqual(len({e['id'] for e in entries}), len(entries))
        for e in entries:
            self.assertEqual(set(e), {'id', 'lemma', 'key', 'loose_key', 'senses', 'forms', 'glyphs', 'spellings',
                                      'sources', 'rights', 'review'})
            self.assertTrue(e['senses'])
            self.assertIn(e['review']['status'], lexicon.REVIEW_ORDER)
            for g in e['glyphs']:
                self.assertIn(g['sense_id'], {s['id'] for s in e['senses']})

    def test_spelling_variants_meet_in_one_entry(self):
        by_spelling = {s: e for e in self.catalog['entries'] for s in e['spellings']}
        self.assertIs(by_spelling['quauitl'], by_spelling['cuahuitl'])
        self.assertIs(by_spelling['iuan'], by_spelling['ihuan'])
        self.assertIs(by_spelling['eecatl'], by_spelling['ehecatl'])
        tree = by_spelling['cuahuitl']
        self.assertEqual({s['id'] for s in tree['senses']}, {'sense-cuahuitl', 'sense-madera'})
        self.assertFalse(tree['rights']['training'])

    def test_closure_hides_dependents_of_private_records(self):
        rows = dict(source=dict(rights=dict(public=False)),
                    form=dict(rights=dict(public=True), evidence=[dict(source_id='source')]),
                    glyph=dict(rights=dict(public=True), sense_id='form'),
                    alone=dict(rights=dict(public=True)))
        self.assertEqual(set(lexicon.public_closure(rows)), {'alone'})


class MigrationTests(unittest.TestCase):
    def test_local_edits_and_contributions_survive_and_are_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / 'voces.sqlite3'
            store = CorpusStore(db)
            # Una aportación de Voces aceptada y una edición local de una ficha del catálogo.
            person, _ = store.save_profile(dict(alias='Prueba', variant_id='inali-04', own_name='', community='',
                                                experience='childhood', historical='none', participation_consent=True))
            proposal = store.propose(person, dict(kind='form', label='Agua: prueba sintética', source_id='src-community',
                                                  locator='sesión de prueba', period='modern', orthography='Prueba',
                                                  sense_id='sense-atl', written='FORMA_QA', variation_kind='dialectal',
                                                  notes='Sin valor lingüístico.', review_consent=True, authorship=True,
                                                  public_consent=True, training_consent=False))['id']
            store.decide(proposal, 'accepted', 'Revisor de pruebas', 'Solo para comprobar el flujo', rights_checked=True)
            edited = dict(store.records()['sense-atl'])
            edited['expected_version'] = edited.pop('version')
            edited['definition'] = 'Agua (edición local).'
            store.import_bundle(dict(schema_version=1, records=[edited]), 'Persona revisora', 'Edición local de prueba')
            with closing(sqlite3.connect(db)) as conn:
                before = lexicon.snapshot(conn)
            report = lexicon.migrate(db, backup_dir=Path(directory) / 'backups')
            self.assertTrue(all(report['tables_preserved'].values()))
            self.assertEqual(report['edited'], 1)
            self.assertEqual(report['local_only'], 1)
            self.assertEqual((report['proposals'], report['people']), (1, 1))
            self.assertTrue(Path(report['backup']).is_file())
            with closing(sqlite3.connect(report['backup'])) as conn:
                self.assertEqual(lexicon.snapshot(conn), before)
            self.assertEqual(CorpusStore(db).records()['sense-atl']['definition'], 'Agua (edición local).')
            again = lexicon.migrate(db, backup_dir=Path(directory) / 'backups')
            self.assertEqual(again['records_after'], report['records_after'])
            with closing(sqlite3.connect(db)) as conn:
                markers = [r[0] for r in conn.execute("SELECT key FROM corpus_meta WHERE key LIKE 'lexicon-catalog-%'")]
            self.assertEqual(len(markers), 1)


if __name__ == '__main__':
    unittest.main()
