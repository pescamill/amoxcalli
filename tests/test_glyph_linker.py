import copy
import json
from pathlib import Path
import tempfile
import unittest

from nahuatl_local.community import ROOT, Problem
from nahuatl_local.corpus import CorpusStore, editorial_releases
from nahuatl_local.text import fold
from nahuatl_local.glyph_linker import build_bundle, tokens
from nahuatl_local.research import Archive


class GlyphLinkerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = json.loads((ROOT/'corpus/glyph-link-rules-v7.json').read_text())
        cls.bundle = json.loads((ROOT/'corpus/glyph-associations-v7.json').read_text())
        cls.tmp = tempfile.TemporaryDirectory()
        cls.store = CorpusStore(Path(cls.tmp.name)/'test.sqlite3')
        cls.records = cls.store.records()
        cls.archive = Archive()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_repeat_is_identical_and_never_changes_original_records(self):
        excluded = {r['id'] for r in self.bundle['records']}
        # Reproduce v7 against its original catalogue, before the flor v8 batch.
        for later in ('corpus/flor-lexicon-v8.json', 'corpus/wiktionary-lexicon-v12.json'):
            excluded.update(r['id'] for r in json.loads((ROOT/later).read_text())['records'])
        for release,bundle in editorial_releases():excluded.update(r['id'] for r in bundle['records'])
        base = {k:v for k,v in self.records.items() if k not in excluded}
        snapshot = copy.deepcopy(base)
        result, report = build_bundle(base, self.rules, self.archive.rows)
        self.assertEqual(result, self.bundle)
        self.assertEqual(base, snapshot)
        self.assertEqual((report['with_image'], report['pending']), (99, 424))
        self.assertEqual((report['llm_calls'], report['network_requests']), (0, 0))

    def test_every_featured_word_has_a_persisted_image_and_source(self):
        self.assertEqual(len(self.rules['featured_sense_ids']), 24)
        for sid in self.rules['featured_sense_ids']:
            gs = [r for r in self.records.values() if r['kind']=='glyph' and r['sense_id']==sid]
            self.assertTrue(any(g.get('image') and g.get('url') for g in gs), sid)
        with self.store.db() as db:
            for g in self.bundle['records']:
                if 'association' not in g:
                    continue
                for key in ('reference_form_id', 'reference_glyph_id'):
                    target=g['association'].get(key)
                    if target:
                        self.assertTrue(db.execute('SELECT 1 FROM corpus_links WHERE owner=? AND target=? AND relation=?', (g['id'], target, key)).fetchone())
                self.assertFalse(g['rights']['training'])

    def test_passages_match_the_written_form_not_a_trimmed_catalog_headword(self):
        for g in self.bundle['records']:
            a=g.get('association', {})
            if a.get('type')!='passage_reference':
                continue
            row=self.archive.get(a['passage']['id'])
            self.assertEqual(a['passage']['nah'],row['nah'])
            self.assertEqual(a['passage']['es'],row['es'])
            self.assertEqual(row['iso'],'nci')
            self.assertIn(fold(self.records[a['reference_form_id']]['written']),tokens(row['nah']))
            ref=self.records[a['reference_glyph_id']]
            self.assertIn(fold(ref['reading']),tokens(row['nah']))
            self.assertIn(a['matched_term'],tokens(row['es']))
        self.assertNotIn('glyph-link-v7-sense-gdn-m2-161535',self.records)  # Titi ≠ normalized i.

    def test_invalid_dependencies_fail_and_private_source_hides_related_images(self):
        g=copy.deepcopy(self.records['glyph-link-v7-sense-ihuan'])
        for key,value in [('reference_glyph_id','sense-atl'),('reference_form_id','lex-atl'),('evidence_url','javascript:alert(1)')]:
            bad=copy.deepcopy(g);bad['association'][key]=value
            with self.assertRaises(Problem):self.store.validate(bad,self.records)
        source=copy.deepcopy(self.records[g['association']['reference_glyph_id']])
        source['rights']['public']=False;source['expected_version']=source['version']
        # Restore afterwards: this shared fixture is otherwise read-only.
        self.store.import_bundle(dict(schema_version=1,records=[source]),'QA','Prueba de dependencia privada')
        self.assertNotIn(g['id'],self.store.public_records())
        source['rights']['public']=True;source['expected_version']+=1
        self.store.import_bundle(dict(schema_version=1,records=[source]),'QA','Restaurar fixture')


if __name__=='__main__':
    unittest.main()
