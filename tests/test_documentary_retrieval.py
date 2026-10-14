import copy
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.request import urlopen

from nahuatl_local.community import ROOT, DEFAULT_DB
from nahuatl_local.corpus import CorpusStore
from nahuatl_local.documentary_retrieval import DocumentaryIndex, PublicSources, public_path
from nahuatl_local.documentary_retrieval_evaluation import audit, validate_report
from nahuatl_local.platform import make_server


class DocumentaryRetrievalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.store = CorpusStore(Path(cls.directory.name)/'public.sqlite3')
        cls.records = cls.store.public_records()
        cls.sources = PublicSources()
        cls.index = DocumentaryIndex(cls.records, cls.sources)

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def test_lookup_ambiguity_comparison_and_bilingual_form_evidence(self):
        response = self.index.search('ic')
        forms = [r for r in response['results'] if r['kind']=='form' and r['comparison']['written'].casefold()=='ic']
        self.assertGreaterEqual(len(forms), 2)
        self.assertEqual(len({r['comparison']['sense_id'] for r in forms}), len(forms))
        self.assertEqual(response['source_ids'], sorted(set(response['source_ids'])))
        for hit in forms:
            self.assertTrue(all(self.sources.citation_valid(f) for f in hit['fields']))
            self.assertIn('definition', {f['field'] for f in hit['fields']})
        water = self.index.search('agua')
        self.assertTrue(any(r['kind']=='form' and r['comparison']['written']=='atl' for r in water['results']))
        self.assertTrue(self.index.search('a')['results'])
        comparison = self.index.search('Ecacoatl')
        entry = next(r for r in comparison['results'] if r['id']=='lex-gdn-m2-147139')
        self.assertFalse(entry['comparison']['equal_literal'])
        self.assertEqual(entry['comparison']['written'],'Ecacoatl')
        self.assertEqual(entry['comparison']['catalog_normalized'],'ecacoatl')

    def test_whole_public_corpus_identifiers_and_unanswerable(self):
        self.assertEqual(len(self.sources.archive), 16111)
        passage = self.index.search('original y traducción axolotl-14546')
        row = next(r for r in passage['results'] if r['id']=='axolotl-14546')
        self.assertEqual(row['passage']['nah'],self.sources.archive['axolotl-14546']['nah'])
        self.assertEqual({f['field'] for f in row['fields']},{'nah','es','document','iso','variant'})
        self.assertTrue(all(self.sources.citation_valid(f) for f in row['fields']))
        occurrence = next(iter(self.sources.tables['occurrences']))
        self.assertEqual(self.index.search(occurrence)['results'][0]['id'], occurrence)
        self.assertTrue(self.index.search('zzzz-no-evidence-7821')['abstained'])
        self.assertFalse(self.index.search('zzzz-no-evidence-7821')['results'])
        with self.assertRaises(ValueError): self.index.search(dict(question='ic',expected='hidden'))

    def test_oracle_independence_and_immutable_evidence(self):
        before = copy.deepcopy(self.records)
        with patch('nahuatl_local.documentary_evaluation.load_development',side_effect=AssertionError('Oracle accessed')):
            independent = DocumentaryIndex(self.records, self.sources)
            self.assertEqual(independent.search('ic'), self.index.search('ic'))
        response = self.index.search('ic')
        response['results'][0]['fields'][0]['value']='fabrication'
        self.assertNotEqual(response, self.index.search('ic'))
        self.assertEqual(self.records,before)
        source = (ROOT/'nahuatl_local/documentary_retrieval.py').read_text()
        self.assertNotIn('documentary_evaluation',source)
        self.assertNotIn('query_id',source)

    def test_public_only_dependency_closure_and_withdrawn_bridge(self):
        rows = copy.deepcopy(self.records)
        element = next(r for r in self.sources.tables['elements'].values() if r['lexical_links'])
        hidden_id = element['lexical_links'][0]['sense_id']
        rows[hidden_id]['rights']['public']=False
        rows[hidden_id]['definition']='PRIVATE_SENTINEL'
        filtered = DocumentaryIndex(rows,self.sources)
        result = filtered.search(element['id'])
        self.assertNotIn(hidden_id,json.dumps(result))
        self.assertNotIn('PRIVATE_SENTINEL',json.dumps(result))
        self.assertNotIn(hidden_id,filtered.records)
        for form in self.records.values():
            if form.get('sense_id')==hidden_id: self.assertNotIn(form['id'],filtered.records)
        glyph = next(r for r in result['results'] if r['id']==element['id'])
        self.assertFalse(any(link['sense_id']==hidden_id for link in glyph['documentary_record']['lexical_links']))
        projection = next(f for f in glyph['fields'] if f['field']=='lexical_links')
        self.assertEqual(projection['table'],'public_catalog')
        self.assertIsNone(projection['file_sha256'])

    def test_untrusted_urls_changed_originals_and_public_paths(self):
        hit = next(r for r in self.index.search('Ecacoatl')['results'] if r['id']=='lex-gdn-m2-147139')
        citation = copy.deepcopy(hit['fields'][0])
        for change in ('url','value','hash'):
            tampered=copy.deepcopy(citation)
            if change=='url':tampered['url']='https://invented.invalid/'
            if change=='value':tampered['value']='invented'
            if change=='hash':tampered['row_sha256']='0'*64
            self.assertFalse(self.sources.citation_valid(tampered))
        rows=copy.deepcopy(self.records);rows['lex-gdn-m2-147139']['url']='javascript:alert(1)'
        unsafe=DocumentaryIndex(rows,self.sources).search('Ecacoatl')
        self.assertFalse(any(u.startswith('javascript:') for h in unsafe['results'] for u in h['urls']))
        for path in ('data/voces.sqlite3','../data/secret','/etc/passwd'):
            with self.assertRaises(ValueError):public_path(ROOT,path)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'reports').symlink_to(ROOT/'data',target_is_directory=True)
            with self.assertRaises(ValueError):public_path(root,'reports/sentinel',writing=True)
            # No read of a private sentinel, even if an explicit public route links to it.

    def test_shared_source_does_not_satisfy_missing_required_entity(self):
        response=self.index.search('Ecacoatl')
        wanted=next(h for h in response['results'] if h['id']=='lex-gdn-m2-147139')
        wrong=next(h for h in self.index.search('ic')['results'] if h['kind']=='form')
        refs=[{k:f[k] for k in ('path','table','record_id','field','value','row_sha256','file_sha256')}
              for f in wanted['fields'] if f['field'] in ('written','catalog_normalized','sense_id','evidence','definition')]
        query=dict(reference=dict(fields=refs,source_ids=wanted['source_ids'],urls=[wanted['urls'][0]]))
        response['results']=[wrong];response['source_ids']=wrong['source_ids']
        checked=audit(query,response,self.sources)
        self.assertFalse(checked['correct_source'])
        self.assertTrue(checked['supported_citations'])
        self.assertEqual(checked['exact_fields']['matched'],0)

    def test_old_boolean_only_or_fabricated_report_does_not_complete_gate(self):
        report=dict(schema_version=1,method='public_documentary_retrieval',elapsed_seconds=1,
                    results=[dict(query_id='invented',correct_source=True,supported_citations=True,reference_checked=True)])
        self.assertFalse(validate_report(report,queries=[])['valid'])

    def test_report_replay_rejects_fabricated_fields_and_duplicate_queries(self):
        report=json.loads((ROOT/'reports/documentary-retrieval-v1.json').read_text())
        tampered=copy.deepcopy(report)
        row=next(r for r in tampered['results'] if r['correct_source'])
        field=next(f for h in row['response']['results'] for f in h['fields'] if f['field']=='written')
        field['value']='Fabricated model output'
        row['correct_source']=True;row['supported_citations']=True
        invalid=validate_report(tampered)
        self.assertFalse(invalid['valid'])
        self.assertTrue(any(e.startswith('response_replay:') for e in invalid['errors']))
        duplicate=copy.deepcopy(report);duplicate['results'][-1]=copy.deepcopy(duplicate['results'][0])
        self.assertFalse(validate_report(duplicate)['valid'])

    def test_http_lookup_rechecks_public_state_and_preserves_private_sentinel(self):
        with tempfile.TemporaryDirectory() as d:
            store=CorpusStore(Path(d)/'sentinel.sqlite3')
            with store.db() as db:
                db.execute('CREATE TABLE documentary_private_sentinel(value TEXT)')
                db.execute('INSERT INTO documentary_private_sentinel VALUES(?)',('PRIVATE_HTTP_SENTINEL',))
            server=make_server(store,port=0,model_enabled=False)
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            try:
                url=f'http://127.0.0.1:{server.server_address[1]}/api/documentary?query=lex-gdn-m2-147139'
                with urlopen(url) as r:before=json.load(r)
                self.assertTrue(any(h['id']=='lex-gdn-m2-147139' for h in before['results']))
                with store.db() as db:
                    row=store.records(db)['lex-gdn-m2-147139'];row['rights']['public']=False
                    db.execute('UPDATE corpus_records SET payload=? WHERE id=?',(json.dumps(row),'lex-gdn-m2-147139'))
                with urlopen(url) as r:after=json.load(r)
                self.assertTrue(after['abstained'])
                self.assertNotIn('PRIVATE_HTTP_SENTINEL',json.dumps(before)+json.dumps(after))
                with store.db() as db:self.assertEqual(db.execute('SELECT value FROM documentary_private_sentinel').fetchone()[0],'PRIVATE_HTTP_SENTINEL')
            finally:server.shutdown();server.server_close();thread.join()
