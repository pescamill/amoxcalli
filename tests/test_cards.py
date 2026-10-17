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
from nahuatl_local.cards import Cards, PublicSources, public_path
from nahuatl_local.evaluate_all import audit, stable
from nahuatl_local.terms import TermIndex
from nahuatl_local.platform import make_server


class CardsTests(unittest.TestCase):
    """Fichas de Preguntar (antes Consultar fichas): IDs y grupos de término, con procedencia verificable."""
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.store = CorpusStore(Path(cls.directory.name)/'public.sqlite3')
        cls.records = cls.store.public_records()
        cls.sources = PublicSources()
        cls.terms = TermIndex(records_fn=lambda: cls.records)
        cls.index = Cards(cls.records, cls.sources)
        cls.search = lambda self, q, index=None: (index or cls.index).lookup(q, cls.terms)

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def test_lookup_ambiguity_comparison_and_bilingual_form_evidence(self):
        response = self.search('ic')
        forms = [r for r in response['results'] if r['kind']=='form' and r['comparison']['written'].casefold()=='ic']
        self.assertGreaterEqual(len(forms), 2)
        self.assertEqual(len({r['comparison']['sense_id'] for r in forms}), len(forms))
        self.assertEqual(response['source_ids'], sorted(set(response['source_ids'])))
        for hit in forms:
            self.assertTrue(all(self.sources.citation_valid(f) for f in hit['fields']))
            self.assertIn('definition', {f['field'] for f in hit['fields']})
        water = self.search('agua')
        self.assertTrue(any(r['kind']=='form' and r['comparison']['written']=='atl' for r in water['results']))
        self.assertTrue(self.search('a')['results'])
        comparison = self.search('Ecacoatl')
        entry = next(r for r in comparison['results'] if r['id']=='lex-gdn-m2-147139')
        self.assertFalse(entry['comparison']['equal_literal'])
        self.assertEqual(entry['comparison']['written'],'Ecacoatl')
        self.assertEqual(entry['comparison']['catalog_normalized'],'ecacoatl')

    def test_whole_public_corpus_identifiers_and_unanswerable(self):
        self.assertEqual(len(self.sources.archive), 16111)
        passage = self.search('original y traducción axolotl-14546')
        row = next(r for r in passage['results'] if r['id']=='axolotl-14546')
        self.assertEqual(row['passage']['nah'],self.sources.archive['axolotl-14546']['nah'])
        self.assertEqual({f['field'] for f in row['fields']},{'nah','es','document','iso','variant'})
        self.assertTrue(all(self.sources.citation_valid(f) for f in row['fields']))
        occurrence = next(iter(self.sources.tables['occurrences']))
        self.assertEqual(self.search(occurrence)['results'][0]['id'], occurrence)
        # Sin palabras reales: «no» ya es la glosa de una entrada (amo, Wiktionary).
        self.assertTrue(self.search('zzzz-qqqq-evidence-7821')['abstained'])
        self.assertFalse(self.search('zzzz-qqqq-evidence-7821')['results'])
        with self.assertRaises(ValueError): self.search(dict(question='ic',expected='hidden'))

    def test_oracle_independence_and_immutable_evidence(self):
        before = copy.deepcopy(self.records)
        with patch('nahuatl_local.documentary_evaluation.load_development',side_effect=AssertionError('Oracle accessed')):
            independent = Cards(self.records, self.sources)
            self.assertEqual(self.search('ic', independent), self.search('ic'))
        response = self.search('ic')
        response['results'][0]['fields'][0]['value']='fabrication'
        self.assertNotEqual(response, self.search('ic'))
        self.assertEqual(self.records,before)
        source = (ROOT/'nahuatl_local/cards.py').read_text()
        self.assertNotIn('documentary_evaluation',source)
        self.assertNotIn('query_id',source)

    def test_public_only_dependency_closure_and_withdrawn_bridge(self):
        rows = copy.deepcopy(self.records)
        element = next(r for r in self.sources.tables['elements'].values() if r['lexical_links'])
        hidden_id = element['lexical_links'][0]['sense_id']
        rows[hidden_id]['rights']['public']=False
        rows[hidden_id]['definition']='PRIVATE_SENTINEL'
        filtered = Cards(rows,self.sources)
        result = self.search(element['id'], filtered)
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
        hit = next(r for r in self.search('Ecacoatl')['results'] if r['id']=='lex-gdn-m2-147139')
        citation = copy.deepcopy(hit['fields'][0])
        for change in ('url','value','hash'):
            tampered=copy.deepcopy(citation)
            if change=='url':tampered['url']='https://invented.invalid/'
            if change=='value':tampered['value']='invented'
            if change=='hash':tampered['row_sha256']='0'*64
            self.assertFalse(self.sources.citation_valid(tampered))
        rows=copy.deepcopy(self.records);rows['lex-gdn-m2-147139']['url']='javascript:alert(1)'
        unsafe=self.search('Ecacoatl',Cards(rows,self.sources))
        self.assertFalse(any(u.startswith('javascript:') for h in unsafe['results'] for u in h['urls']))
        for path in ('data/voces.sqlite3','../data/secret','/etc/passwd'):
            with self.assertRaises(ValueError):public_path(ROOT,path)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'reports').symlink_to(ROOT/'data',target_is_directory=True)
            with self.assertRaises(ValueError):public_path(root,'reports/sentinel',writing=True)
            # No read of a private sentinel, even if an explicit public route links to it.

    def test_shared_source_does_not_satisfy_missing_required_entity(self):
        response=self.search('Ecacoatl')
        wanted=next(h for h in response['results'] if h['id']=='lex-gdn-m2-147139')
        wrong=next(h for h in self.search('ic')['results'] if h['kind']=='form')
        refs=[{k:f[k] for k in ('path','table','record_id','field','value','row_sha256','file_sha256')}
              for f in wanted['fields'] if f['field'] in ('written','catalog_normalized','sense_id','evidence','definition')]
        query=dict(reference=dict(fields=refs,source_ids=wanted['source_ids'],urls=[wanted['urls'][0]]))
        response['results']=[wrong];response['source_ids']=wrong['source_ids']
        checked=audit(query,response,self.sources)
        self.assertFalse(checked['correct_source'])
        self.assertTrue(checked['supported_citations'])
        self.assertEqual(checked['exact_fields']['matched'],0)

    def test_gate_ignores_timing_but_not_metrics(self):
        report=dict(summary=dict(all=dict(complete=121)),timing=dict(build_seconds=1.0),seconds=3)
        self.assertEqual(stable(report),stable(dict(report,timing=dict(build_seconds=9.0),seconds=7)))
        self.assertNotEqual(stable(report),stable(dict(report,summary=dict(all=dict(complete=120)))))

    def test_documentary_question_finds_ids_and_mentioned_spellings(self):
        passage=self.search('En Cantares mexicanos, registro axolotl-14546, ¿qué original náhuatl acompaña a la traducción?')
        self.assertEqual([h['id'] for h in passage['results'] if h['kind']=='passage'],['axolotl-14546'])
        self.assertNotIn('lemma-nahuatl',passage['groups'])  # «náhuatl» con acento español no es mención
        both=self.search('Compara la escritura original de ca / auh')
        self.assertTrue({h['comparison']['written'].casefold() for h in both['results'] if h['kind']=='form'}>={'ca','auh'})
        self.assertFalse(self.search('de la y que')['results'])

    def test_http_lookup_rechecks_public_state_and_preserves_private_sentinel(self):
        with tempfile.TemporaryDirectory() as d:
            store=CorpusStore(Path(d)/'sentinel.sqlite3')
            with store.db() as db:
                db.execute('CREATE TABLE documentary_private_sentinel(value TEXT)')
                db.execute('INSERT INTO documentary_private_sentinel VALUES(?)',('PRIVATE_HTTP_SENTINEL',))
            server=make_server(store,port=0)
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            try:
                url=f'http://127.0.0.1:{server.server_address[1]}/api/ask/cards?q=lex-gdn-m2-147139'
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
