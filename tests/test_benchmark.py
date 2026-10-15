import csv,hashlib,importlib.util,io,json,socket,sys,tempfile,unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
from nahuatl_local.data import work_group,passage_group,load_rows
from nahuatl_local.benchmark import select_sample,bootstrap_ci,hermetic_network,review_sheet,eligible,retrieval_benchmark,main,_cached_chrf
from nahuatl_local.retrieval import Index
from nahuatl_local.nahuatl_orthography import ORTHOGRAPHY_VERSION,STORAGE_RULE_IDS,COMPARISON_RULE_IDS
ROOT=Path(__file__).resolve().parents[1]

def row(id,es='hola mundo',nah='niltze cemanahuatl',document='Obra A',locator='axolotl.csv, fila 1'):
    return dict(id=id,es=es,nah=nah,document=document,locator=locator)

def mean(items):return sum(items)/len(items)

class GroupingTests(unittest.TestCase):
    def test_work_group_collapses_chimalpahin(self):
        self.assertEqual(work_group('Tercera Relación (Libro las ocho relaciones)'),'Chimalpahin: las ocho relaciones')
        self.assertEqual(work_group('Documentos nauas de la Ciudad de México del siglo XVI'),'Documentos nauas de la Ciudad de México del siglo XVI')
    def test_passage_group_distinguishes_works_and_locators(self):
        a=row('a',document='Obra A',locator='axolotl.csv, fila 1');b=row('b',document='Obra B',locator='axolotl.csv, fila 1');c=row('c',document='Obra A',locator='axolotl.csv, fila 2')
        self.assertNotEqual(passage_group(a),passage_group(b))
        self.assertNotEqual(passage_group(a),passage_group(c))
        self.assertEqual(passage_group(a),passage_group(row('a',document='Obra A',locator='axolotl.csv, fila 1')))
    def test_passage_group_uses_chimalpahin_collapse(self):
        self.assertTrue(passage_group(row('x',document='Memorial Breve (Libro las ocho relaciones)',locator='fila 1')).startswith('Chimalpahin: las ocho relaciones'))

class SelectionTests(unittest.TestCase):
    def test_eligibility_filter(self):
        self.assertTrue(eligible(row('a',es='hola mundo',nah='niltze cemanahuatl')))
        self.assertFalse(eligible(row('a',es='hola')))
        self.assertFalse(eligible(row('a',es=' '.join(str(i) for i in range(16)))))
        self.assertFalse(eligible(row('a',nah=' '.join(str(i) for i in range(26)))))
    def test_deterministic_full_selection(self):
        rows=[row(f'r{i}',document='Obra A' if i%2 else 'Obra B',locator=f'axolotl.csv, fila {i}') for i in range(6)]
        self.assertEqual(select_sample(rows),select_sample(rows))
    def test_limit_interleaves_groups(self):
        rows=[row(f'r{i}',document='Obra A',locator=f'fila {i}') for i in range(4)]+[row(f's{i}',document='Obra B',locator=f'fila {i}') for i in range(4)]
        sel=select_sample(rows,limit=3)
        self.assertEqual(len(sel),3)
        self.assertGreater(len({r['document'] for r in sel}),1)
    def test_selection_does_not_mutate_input_order(self):
        rows=[row(f'r{i}',document='Obra B' if i%2 else 'Obra A') for i in range(5)]
        before=[r['id'] for r in rows];select_sample(rows);self.assertEqual([r['id'] for r in rows],before)
    def test_heldout_selection_is_reproducible_and_larger(self):
        rows=load_rows(ROOT/'data/prepared/test.jsonl')
        a=select_sample(rows);b=select_sample(rows)
        self.assertEqual([r['id'] for r in a],[r['id'] for r in b])
        self.assertEqual(hashlib.sha256(json.dumps([r['id'] for r in a]).encode()).hexdigest(),hashlib.sha256(json.dumps([r['id'] for r in b]).encode()).hexdigest())
        self.assertGreater(len(a),20)

class BootstrapTests(unittest.TestCase):
    def test_deterministic(self):
        vals=[1,2,3,4,5]
        a=bootstrap_ci(vals,mean,seed=7,n_resamples=200);b=bootstrap_ci(vals,mean,seed=7,n_resamples=200)
        self.assertEqual((a['lower'],a['upper']),(b['lower'],b['upper']))
    def test_records_n_and_estimate(self):
        ci=bootstrap_ci([1,2,3,4],mean,seed=7,n_resamples=200)
        self.assertEqual(ci['n'],4);self.assertEqual(ci['estimate'],2.5)
    def test_constant_zero_width(self):
        ci=bootstrap_ci([2,2,2,2],mean,seed=7,n_resamples=100)
        self.assertEqual(ci['lower'],ci['upper'])
        self.assertEqual(ci['lower'],2.0)
    def test_bounds_order(self):
        ci=bootstrap_ci([1,5,9,2,8],mean,seed=3,n_resamples=300)
        self.assertLessEqual(ci['lower'],ci['estimate']);self.assertLessEqual(ci['estimate'],ci['upper'])
    def test_iid_equals_self_clusters(self):
        vals=[1,2,3,4,5,6]
        a=bootstrap_ci(vals,mean,seed=5,n_resamples=200);b=bootstrap_ci(vals,mean,clusters=list(range(len(vals))),seed=5,n_resamples=200)
        self.assertEqual((a['lower'],a['upper']),(b['lower'],b['upper']))
    def test_single_cluster_degenerate(self):
        ci=bootstrap_ci([1,2,3],mean,clusters=[0,0,0],seed=5,n_resamples=100)
        self.assertEqual(ci['lower'],ci['upper'])
        self.assertEqual(ci['clusters'],1)
        self.assertTrue(ci['degenerate']);self.assertEqual(ci['degeneracy_reason'],'single_cluster')
    def test_cluster_reporting(self):
        ci=bootstrap_ci([1,1,1,3,3,3],mean,clusters=[0,0,0,1,1,1],seed=5,n_resamples=200)
        self.assertEqual(ci['clusters'],2);self.assertEqual(ci['n'],6)
    def test_empty(self):
        ci=bootstrap_ci([],mean)
        self.assertEqual(ci['n'],0);self.assertIsNone(ci['estimate'])

@unittest.skipUnless(importlib.util.find_spec('sacrebleu'),'sacrebleu no instalado (extra de medición)')
class RetrievalBenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory();self.addCleanup(self.folder.cleanup)
        self.data=Path(self.folder.name)
        self.train=[row('train-house',es='la casa grande',nah='in calli hueyi',document='Obra de entrenamiento'),
                    row('train-flower',es='flor blanca',nah='iztac xochitl',document='Obra de entrenamiento')]
        self.validation=[row('validation-es-overlap',es='la casa grande',nah='teotl tlatolli',document='Obra A'),
                         row('validation-nah-overlap',es='llueve cada tarde',nah='in calli hueyi',document='Obra A'),
                         row('validation-clean',es='flor nueva pequeña',nah='nican tlalli',document='Obra B')]
        for split,rows in [('train',self.train),('validation',self.validation),('test',[row('test-only')])]:
            (self.data/f'{split}.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')
        normalization=dict(version=ORTHOGRAPHY_VERSION,storage_rules=list(STORAGE_RULE_IDS),comparison_rules=list(COMPARISON_RULE_IDS))
        (self.data/'manifest.json').write_text(json.dumps(dict(normalization=normalization)),encoding='utf-8')
    def run_retrieval(self,**kwargs):
        with redirect_stdout(io.StringIO()):return retrieval_benchmark(self.data,n_resamples=20,**kwargs)
    def test_only_train_index_and_all_predictions_with_both_overlap_fields(self):
        with patch('nahuatl_local.benchmark.Index',wraps=Index) as build:
            report=self.run_retrieval()
        build.assert_called_once_with(self.data/'train.jsonl')
        self.assertEqual(report['split'],'validation');self.assertEqual(report['n'],3)
        self.assertEqual(len(report['predictions']),3)
        self.assertEqual({r['id'] for r in report['predictions']},{r['id'] for r in self.validation})
        self.assertTrue(all(set(r['retrieval_ids'])<={t['id'] for t in self.train} for r in report['predictions']))
        overlaps={r['id']:r['overlap'] for r in report['predictions']}
        self.assertEqual(overlaps['validation-es-overlap'],'train-house')
        self.assertEqual(overlaps['validation-nah-overlap'],'train-house')
        self.assertIsNone(overlaps['validation-clean'])
        self.assertEqual((report['filtered_examples'],report['unflagged_examples']),(2,1))
        self.assertEqual(report['overlap_audit']['threshold'],.65)
        self.assertEqual(report['overlap_audit']['fields'],['es','nah'])
        clean_ci=report['unflagged_chrF_plus_plus_ci']['clusters']
        self.assertTrue(clean_ci['degenerate']);self.assertEqual(clean_ci['degeneracy_reason'],'single_cluster')
        self.assertEqual(report['chrF_plus_plus_ci']['clusters']['clusters'],2)
    def test_hashes_rules_and_retrieval_settings(self):
        report=self.run_retrieval(limit=2)
        self.assertEqual(report['dataset_sha256'],hashlib.sha256((self.data/'validation.jsonl').read_bytes()).hexdigest())
        self.assertEqual(report['train_sha256'],hashlib.sha256((self.data/'train.jsonl').read_bytes()).hexdigest())
        self.assertEqual(report['train_rows'],2)
        self.assertEqual(report['normalization']['version'],ORTHOGRAPHY_VERSION)
        self.assertTrue(report['prepared_normalization_matches_current'])
        self.assertEqual(report['retrieval']['index_split'],'train')
        self.assertEqual(report['retrieval']['nahuatl_comparison_rules'],list(COMPARISON_RULE_IDS))
        self.assertEqual(report['generated_examples'],0)
        self.assertIn('20 ejemplos de test',report['limitations'])
        self.assertEqual(report['ids'],[r['id'] for r in select_sample(self.validation,2)])
    def test_retrieval_cli_needs_no_model_or_torch_and_writes_full_summary_review(self):
        output=self.data/'retrieval-full.json'
        with patch.dict(sys.modules,{'torch':None,'transformers':None,'peft':None,'nahuatl_local.runtime':None}),redirect_stdout(io.StringIO()):
            report=main(['--retrieval-only','--data',str(self.data),'--limit','3','--bootstrap-resamples','20','--output',str(output)])
        full=json.loads(output.read_text(encoding='utf-8'));summary=json.loads((self.data/'retrieval.json').read_text(encoding='utf-8'))
        self.assertEqual(len(full['predictions']),3)
        self.assertNotIn('predictions',summary)
        self.assertEqual(full['split'],'validation')
        self.assertEqual(full['chrF_plus_plus_ci']['iid']['n_resamples'],20)
        lines=list(csv.reader(io.StringIO(Path(report['review_sheet']).read_text(encoding='utf-8'))))
        self.assertEqual(len(lines),4)
        self.assertEqual({line[0]:line[2] for line in lines[1:]},{r['id']:r['text'] for r in full['predictions']})
    def test_model_cli_keeps_test_default(self):
        load_model=Mock(return_value=('model','tokenizer','cpu'))
        translate=Mock(return_value=dict(text='niltze',seconds=0,tokens=1,truncated=False,reviewed=False))
        fake_runtime=SimpleNamespace(load_model=load_model,translate=translate)
        with patch.dict(sys.modules,{'torch':SimpleNamespace(set_num_threads=Mock()),'nahuatl_local.runtime':fake_runtime}),redirect_stdout(io.StringIO()):
            main(['--data',str(self.data),'--bootstrap-resamples','20','--output',str(self.data/'model-full.json')])
        report=json.loads((self.data/'model-full.json').read_text(encoding='utf-8'))
        self.assertEqual(report['split'],'test');self.assertEqual(report['ids'],['test-only'])
        load_model.assert_called_once();translate.assert_called_once()
    def test_cached_corpus_chrf_equals_direct_score_including_resampled_duplicates(self):
        from sacrebleu.metrics import CHRF
        predictions=[dict(id='a',text='in calli',reference='in calli hueyi'),dict(id='b',text='atl',reference='xochitl')]
        metric=CHRF(word_order=2);cached=_cached_chrf(metric,predictions)
        for records in [predictions,[predictions[0],predictions[0],predictions[1]],[predictions[1]]]:
            direct=metric.corpus_score([r['text'] for r in records],[[r['reference'] for r in records]]).score
            self.assertAlmostEqual(cached(records),direct)
        self.assertIsNone(cached([]))
    def test_train_cannot_be_held_out_split(self):
        with self.assertRaises(ValueError):self.run_retrieval(split='train')

class HermeticTests(unittest.TestCase):
    def test_network_blocked_inside(self):
        with hermetic_network():
            with self.assertRaises(RuntimeError):socket.create_connection(('127.0.0.1',1))
            s=socket.socket()
            try:
                with self.assertRaises(RuntimeError):s.connect(('127.0.0.1',1))
            finally:s.close()
    def test_network_restored_after(self):
        original_connect=socket.socket.connect;original_create=socket.create_connection
        with hermetic_network():pass
        self.assertIs(socket.socket.connect,original_connect)
        self.assertIs(socket.create_connection,original_create)

class ReviewSheetTests(unittest.TestCase):
    def test_header_matches_template(self):
        header=(ROOT/'templates/review_labels.csv').read_text(encoding='utf-8').splitlines()[0]
        sheet=review_sheet([row('a')])
        self.assertEqual(sheet.splitlines()[0],header)
    def test_rows_and_candidate(self):
        rows=[row('a'),row('b')]
        sheet=review_sheet(rows,[dict(id='a',text='CANDIDATO')])
        lines=list(csv.reader(io.StringIO(sheet)))
        self.assertEqual(len(lines),3)
        self.assertEqual(lines[1][2],'CANDIDATO');self.assertEqual(lines[2][2],'')
        self.assertEqual(lines[1][3],passage_group(rows[0]))
        self.assertTrue(all(len(l)==12 for l in lines))

if __name__=='__main__':unittest.main()
