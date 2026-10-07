import copy
import json
from pathlib import Path
import tempfile
import unittest
from nahuatl_local.corpus import CorpusStore
from nahuatl_local.dictionary_import import parse_page, bundle_from_pages


class DictionaryImportTests(unittest.TestCase):
    page="""<script>var mydata = [{pk:'123456',paleografia:'PalabraQA',grafiaNormalizada:'palabraqa',traduccion:'definición histórica ç.',fuente:'1571 Molina 2',}];</script>"""
    def test_preserves_unicode_and_separates_catalog_normalization(self):
        records=parse_page(self.page)
        self.assertEqual(records[0]['traduccion'],'definición histórica ç.')
        b,r=bundle_from_pages([(self.page.encode(),'https://gdn.iib.unam.mx/')])
        self.assertEqual(b['records'][0]['definition'],'definición histórica ç.')
        self.assertEqual(b['records'][1]['written'],'PalabraQA')
        self.assertEqual(b['records'][1]['catalog_normalized'],'palabraqa')
        self.assertFalse(b['records'][1]['rights']['training'])
        self.assertFalse(any(x['kind']=='glyph' for x in b['records']))
        self.assertEqual(r['llm_calls'],0)

    def test_unknown_format_or_executable_content_fails_closed(self):
        for value in ['<html>blocked</html>',self.page.replace("pk:'123456'","pk:call()"),self.page.replace('];',', attack()];')]:
            with self.assertRaises(ValueError):parse_page(value)

    def test_skips_generated_entries_and_duplicate_curated_words(self):
        b,r=bundle_from_pages([(self.page.encode(),'https://gdn.iib.unam.mx/')],excluded=['palabraqa'])
        self.assertEqual(b['records'],[])
        b,r=bundle_from_pages([(self.page.replace("grafiaNormalizada:'palabraqa'","grafiaNormalizada:'palabraqa +' ").encode(),'https://gdn.iib.unam.mx/')])
        self.assertEqual(b['records'],[])

    def test_import_is_additive_and_preserves_local_edits(self):
        b,_=bundle_from_pages([(self.page.encode(),'https://gdn.iib.unam.mx/')])
        with tempfile.TemporaryDirectory() as tmp:
            s=CorpusStore(Path(tmp)/'dictionary.sqlite3');before=s.records()
            s.import_bundle(b,'Parser','QA',migration_key='qa-gdn')
            self.assertTrue(all(s.records()[i]==r for i,r in before.items()))
            r=copy.deepcopy(s.records()[b['records'][0]['id']]);r.update(label='Edición local',expected_version=r['version'])
            s.import_bundle(dict(schema_version=1,records=[r]),'Editora','QA')
            s.import_bundle(b,'Parser','Otro lote',migration_key='qa-gdn-new')
            self.assertEqual(s.records()[r['id']]['label'],'Edición local')
