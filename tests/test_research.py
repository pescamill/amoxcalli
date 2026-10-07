import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from nahuatl_local.research import Archive
from nahuatl_local.retrieval import Index
from nahuatl_local.corpus import CorpusStore
from nahuatl_local.community import Problem

class ResearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.archive=Archive()
    def test_complete_archive_and_pagination(self):
        a=self.archive;self.assertEqual(a.summary['total'],16111);self.assertEqual(a.summary['works'],33)
        self.assertEqual(a.search(variant='nci')['total'],5993)
        self.assertEqual(a.search(variant='unknown')['total'],2157)
        self.assertFalse({r['id'] for r in a.search()['results']}&{r['id'] for r in a.search(offset=20)['results']})
        self.assertEqual(a.search(document='__unknown__')['total'],1)
    def test_search_and_context_preserve_provenance(self):
        a=self.archive;rows=a.search('maiz',variant='nci')['results'];self.assertTrue(rows)
        self.assertTrue(all(r['iso']=='nci' and r['locator'] and r['source_url'] for r in rows))
        self.assertTrue(all(r['iso']=='nci' for r in a.context('La casa y la flor.')))
        self.assertEqual(a.search('unapalabraquenoexiste')['total'],0)
        for kw in ({'offset':-1},{'limit':101}):
            with self.assertRaises(Problem):a.search(**kw)
    def small_archive(self,rows):
        a=Archive();a.rows=rows;a.index={r['id']:r for r in rows}
        return a
    def ranked_rows(self):
        return [dict(id='both',es='flor casa',nah='calli',iso='nci',document='Obra clásica',period='historical'),
                dict(id='classical',es='casa',nah='in calpolco',iso='nci',document='',period='historical'),
                dict(id='modern',es='casa',nah='kali',iso='nhw',document='Obra moderna',period='modern'),
                dict(id='unknown',es='casa',nah='kali',iso='unknown',document='Obra desconocida',period='unknown'),
                dict(id='metadata',es='casamiento',nah='tlahtolli',iso='nci',document='casa',period='historical')]
    def test_lazy_full_archive_index_and_empty_query_browsing(self):
        rows=self.ranked_rows();a=self.small_archive(rows)
        with patch('nahuatl_local.research.Index',wraps=Index) as build:
            self.assertEqual(a.search()['results'],rows)
            self.assertEqual(a.search('  ',offset='1',limit='2')['results'],rows[1:3])
            self.assertEqual(a.context('  '),[])
            build.assert_not_called()
            self.assertTrue(a.search('calli')['results'])
            self.assertTrue(a.context('casa'))
            build.assert_called_once_with(rows=rows)
            self.assertEqual(a._bm25.rows,rows)
    def test_bilingual_bm25_ranking_and_pagination(self):
        a=self.small_archive(self.ranked_rows())
        page=a.search('flor casa',limit=2)
        self.assertEqual((page['total'],page['offset'],page['limit']),(4,0,2))
        self.assertEqual([r['id'] for r in page['results']],['both','classical'])
        second=a.search('flor casa',offset=2,limit=2)
        self.assertEqual(second['total'],4)
        self.assertEqual([r['id'] for r in second['results']],['modern','unknown'])
        self.assertGreater(page['results'][0]['retrieval_score'],page['results'][1]['retrieval_score'])
        self.assertEqual([r['id'] for r in a.search('calli')['results']],['both'])
        self.assertEqual(a.search('casa',offset=20)['results'],[])
    def test_ranked_filters_keep_unknown_document_period_and_variant(self):
        a=self.small_archive(self.ranked_rows())
        for filters,expected in [({'variant':'nci'},['both','classical']),
                                 ({'variant':'unknown'},['unknown']),
                                 ({'document':'__unknown__'},['classical']),
                                 ({'document':'Obra moderna'},['modern']),
                                 ({'period':'unknown'},['unknown']),
                                 ({'period':'historical','variant':'nci','document':'Obra clásica'},['both'])]:
            with self.subTest(filters=filters):
                result=a.search('flor casa',**filters)
                self.assertEqual(result['total'],len(expected))
                self.assertEqual([r['id'] for r in result['results']],expected)
    def test_safe_historical_equivalences_and_original_passage(self):
        row=dict(id='historical',es='palabra',nah='Çacatl Hvehuetl Tlahtōlli,',iso='nci',
                 variant='Classical Nahuatl',document='Obra',period='historical',locator='folio 2',source_url='https://example.test/obra')
        original=dict(row);a=self.small_archive([row])
        for result in [a.search('tzacatl huehuetl tlahtolli')['results'],a.context('tzacatl huehuetl tlahtolli')]:
            self.assertEqual(len(result),1)
            self.assertEqual({key:result[0][key] for key in original},original)
            self.assertIn('retrieval_score',result[0])
        self.assertEqual(a.get(row['id']),original)
        self.assertEqual(row,original)
    def test_context_uses_same_ranking_and_skips_long_or_nonclassical_passages(self):
        rows=self.ranked_rows()
        rows.insert(0,dict(id='long',es='flor casa '*80,nah='calli',iso='nci',document='Obra larga',period='historical'))
        a=self.small_archive(rows)
        expected=[r for r in a.search('flor casa',variant='nci',limit=100)['results'] if len(r['es'])+len(r['nah'])<=600][:2]
        context=a.context('flor casa')
        self.assertEqual(context,expected)
        self.assertEqual([r['id'] for r in context],['both','classical'])
        self.assertTrue(all(r['iso']=='nci' and len(r['es'])+len(r['nah'])<=600 for r in context))
        self.assertEqual(a.context('kali'),[])
        self.assertEqual(a.context('unapalabraquenoexiste'),[])
    def test_real_tasks_and_correction_keep_original_variant(self):
        with tempfile.TemporaryDirectory() as d:
            store=CorpusStore(Path(d)/'test.db');person,_=store.save_profile(dict(alias='QA',variant_id='inali-04',experience='learning',historical='none',participation_consent=True))
            a=self.archive;task=a.task(store,'translate',person)
            self.assertEqual(task['remaining'],16111);self.assertEqual(task['task']['source']['archive_id'],'axolotl-00001')
            next_task=a.task(store,'translate',person,task['task']['id']);self.assertNotEqual(task['task']['id'],next_task['task']['id'])
            original=a.search(variant='azz',limit=1)['results'][0]
            p=store.propose(person,dict(kind='text',archive_id=original['id'],label='Cotejo QA',nah=original['nah'],es=original['es'],source_id='src-axolotl',locator='será reemplazado por el registro real',period='modern',orthography='Sin normalizar',review_consent=True,authorship=True,public_consent=False,training_consent=False))
            stored=store.proposals(person)[0]['payload']['record']
            self.assertEqual(stored['variant'],'azz');self.assertEqual(stored['archive_id'],original['id'])
            self.assertNotIn(p['id'],store.public_records())
if __name__=='__main__':unittest.main()
