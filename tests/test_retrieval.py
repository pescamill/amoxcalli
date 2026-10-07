import csv,json,tempfile,unittest
from pathlib import Path
from nahuatl_local.data import prepare,load_rows
from nahuatl_local.retrieval import Index,full_index

ROWS=[
    dict(id='r1',es='la casa es grande',nah='in calli hueyi',iso='nci',variant='Classical Nahuatl',document='clásico'),
    dict(id='r2',es='el agua corre',nah='in atl motlaloa',iso='nci',variant='Classical Nahuatl',document='clásico'),
    dict(id='r3',es='la casa es roja',nah='nin kali chichiltik',iso='nhw',variant='Western Huasteca Nahuatl',document='huasteca'),
]

class RetrievalTests(unittest.TestCase):
    def test_both_languages_indexed(self):
        idx=Index(rows=ROWS)
        self.assertEqual([r['id'] for r in idx.search('calli',field='nah')][:1],['r1'])
        self.assertEqual({r['id'] for r in idx.search('casa',field='es')},{'r1','r3'})
        self.assertEqual(idx.search('casa',field='nah'),[])
    def test_safe_nahuatl_equivalents_match_in_both_directions(self):
        pairs=[('Çacatl','tzacatl'),('Hvehuetl','huehuetl'),('Tlahtōlli,','tlahtolli'),('Tlahto\u0304lli','tlahtolli')]
        for historical,modern in pairs:
            for document,query in [(historical,modern),(modern,historical)]:
                with self.subTest(document=document,query=query):
                    row=dict(id='historical',es='palabra',nah=document,iso='nci',document='obra')
                    idx=Index(rows=[row])
                    self.assertEqual([r['id'] for r in idx.search(query,field='nah')],['historical'])
                    self.assertEqual([r['id'] for r in idx.search(query)],['historical'])
    def test_nahuatl_normalization_preserves_original_text_and_provenance(self):
        row=dict(id='historical',es='Voz española',nah='Çacatl Hvehuetl Tlahtōlli,',iso='nci',
                 variant='Classical Nahuatl',document='obra',locator='folio 2',source_url='https://example.test/obra')
        original=dict(row)
        idx=Index(rows=[row])
        hit=idx.search('tzacatl huehuetl tlahtolli',field='nah')[0]
        self.assertEqual({key:hit[key] for key in original},original)
        self.assertEqual(row,original)
        self.assertEqual(idx.rows,[original])
    def test_spanish_keeps_its_original_tokenization(self):
        idx=Index(rows=[dict(id='spanish',es='Viento año ça más',nah='calli',iso='nci')])
        for query in ['viento','año','ça','más']:
            self.assertEqual([r['id'] for r in idx.search(query,field='es')],['spanish'])
        for query in ['uiento','ano','tza','mas']:
            with self.subTest(query=query):
                self.assertEqual(idx.search(query,field='es'),[])
                self.assertEqual(idx.search(query),[])
    def test_aggressive_nahuatl_equivalences_stay_disabled(self):
        for document,query in [('huel','uel'),('qualli','cualli'),('yn','in')]:
            with self.subTest(document=document,query=query):
                idx=Index(rows=[dict(id='historical',es='palabra',nah=document,iso='nci')])
                self.assertEqual(idx.search(query,field='nah'),[])
                self.assertEqual([r['id'] for r in idx.search(document,field='nah')],['historical'])
    def test_search_argument_validation(self):
        idx=Index(rows=ROWS)
        for field in ['nci','other',1]:
            with self.subTest(field=field),self.assertRaises(ValueError):
                idx.search('calli',field=field)
        for k in [-1,1.5,'3',True,None]:
            with self.subTest(k=k),self.assertRaises(ValueError):
                idx.search('calli',k=k)
        self.assertEqual(idx.search('calli',k=0),[])
    def test_variant_filter(self):
        idx=Index(rows=ROWS)
        self.assertEqual({r['id'] for r in idx.search('casa')},{'r1','r3'})
        self.assertEqual([r['id'] for r in idx.search('casa',variant='nci')],['r1'])
        self.assertEqual([r['id'] for r in idx.search('casa',variant='nhw')],['r3'])
        self.assertTrue(all(r['iso']=='nci' for r in idx.search('casa',100,variant='nci')))
    def test_variant_filter_with_historical_equivalence(self):
        rows=[dict(id='classical',es='palabra',nah='Çacatl',iso='nci'),
              dict(id='huasteca',es='palabra',nah='tzacatl',iso='nhw')]
        idx=Index(rows=rows)
        self.assertEqual([r['id'] for r in idx.search('tzacatl',field='nah',variant='nci')],['classical'])
        self.assertEqual([r['id'] for r in idx.search('Çacatl',field='nah',variant='nhw')],['huasteca'])
    def test_score_and_provenance_preserved(self):
        idx=Index(rows=ROWS)
        hits=idx.search('casa')
        self.assertTrue(all('retrieval_score' in r and r['es'] and r['nah'] and r['iso'] for r in hits))
        self.assertEqual([r['retrieval_score'] for r in hits],sorted([r['retrieval_score'] for r in hits],reverse=True))
    def test_path_indexes_only_that_file(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'train.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in ROWS[:2]),encoding='utf-8')
            (root/'test.jsonl').write_text(json.dumps(ROWS[2],ensure_ascii=False)+'\n',encoding='utf-8')
            idx=Index(root/'train.jsonl')
            self.assertEqual({r['id'] for r in idx.rows},{'r1','r2'})
            self.assertEqual([r['id'] for r in idx.search('casa')],['r1'])
    def test_benchmark_clean_separation(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);raw=root/'raw.csv'
            with raw.open('w',newline='') as f:
                writer=csv.writer(f)
                for i in range(6):writer.writerow([f'casa palabra{i}',f'calli texto{i}','Classical Nahuatl',f'obra{i}','nci'])
            prepare(raw,root/'prepared')
            splits={s:load_rows(root/'prepared'/f'{s}.jsonl') for s in ['train','validation','test']}
            idx=Index(root/'prepared/train.jsonl')
            train_ids={r['id'] for r in splits['train']}
            self.assertEqual({r['id'] for r in idx.rows},train_ids)
            for split in ['validation','test']:
                held_out={r['id'] for r in splits[split]}
                self.assertFalse(train_ids & held_out)
                for row in splits[split]:
                    self.assertFalse(held_out & {r['id'] for r in idx.search(row['es'])})
    def test_full_index_covers_corpus_and_variants(self):
        idx=full_index()
        self.assertEqual(len(idx.rows),16111)
        nah=idx.search('chalchihuitl',field='nah',variant='nci')
        self.assertTrue(nah and all(r['iso']=='nci' for r in nah))
        self.assertTrue(idx.search('casa',100,variant='nhw'))
if __name__=='__main__':unittest.main()
