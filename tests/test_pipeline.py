import unittest,tempfile,csv,json
from pathlib import Path
from unittest.mock import patch
from nahuatl_local import data as data_module
from nahuatl_local.data import prepare,load_rows,canonical,default_corpus_path
from nahuatl_local.nahuatl_orthography import storage,comparison,ORTHOGRAPHY_VERSION
from nahuatl_local.retrieval import Index
class PipelineTests(unittest.TestCase):
    def test_split_and_variant_isolation(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);raw=root/'raw.csv'
            with raw.open('w',newline='') as f:
                writer=csv.writer(f)
                for i in range(10):writer.writerow([f'casa palabra{i}',f'calli texto{i}','Classical Nahuatl',f'obra{i}','nci'])
                writer.writerow(['moderno ejemplo','modern target','Central Nahuatl','moderno','nhn'])
                writer.writerow(['casa palabra0','duplicate target','Classical Nahuatl','otra','nci'])
            report=prepare(raw,root/'prepared');self.assertEqual(report['retained'],10)
            splits=[load_rows(root/'prepared'/f'{s}.jsonl') for s in ['train','validation','test']]
            for i in range(3):
                for j in range(i):self.assertFalse({r['group'] for r in splits[i]} & {r['group'] for r in splits[j]})
            index=Index(root/'prepared/train.jsonl');hits=index.search('casa',100)
            self.assertTrue({r['id'] for r in hits}<={r['id'] for r in splits[0]})
            self.assertEqual(index.search('xyzzy'),[])
    def test_preserves_diacritics_storage(self):
        self.assertNotEqual(storage('ātl'),storage('atl'))
    def test_canonical_delegates_to_comparison(self):
        self.assertEqual(canonical('Ç'),'tz')
        self.assertEqual(canonical('Tlahtōlli,'),comparison('tlahtolli'))
    def test_length_ratio_reject(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);raw=root/'raw.csv'
            with raw.open('w',newline='') as f:
                writer=csv.writer(f)
                for doc in ['obraA','obraB','obraC']:writer.writerow([f'casa {doc.lower()}',f'calli {doc.lower()}','Classical Nahuatl',doc,'nci'])
                long_es=' '.join(f'palabra{i}' for i in range(20))
                writer.writerow([long_es,'calli cualli','Classical Nahuatl','obraD','nci'])
            report=prepare(raw,root/'prepared')
            self.assertEqual(report['rejected'].get('length_ratio',0),1)
            self.assertEqual(report['retained'],3)
    def test_dedup_uses_comparison(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);raw=root/'raw.csv'
            with raw.open('w',newline='') as f:
                writer=csv.writer(f)
                for i in range(5):writer.writerow([f'casa palabra{i}',f'calli texto{i}','Classical Nahuatl',f'obra{i}','nci'])
                writer.writerow(['casa primera','Tlahtōlli calli','Classical Nahuatl','obraF','nci'])
                writer.writerow(['casa segunda','tlahtolli calli','Classical Nahuatl','obraG','nci'])
            report=prepare(raw,root/'prepared')
            self.assertEqual(report['rejected'].get('duplicate_source_or_target',0),1)
            self.assertEqual(report['retained'],6)
    def test_path_fallback(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            with patch.object(data_module,'ROOT',root):
                with self.assertRaises(FileNotFoundError):default_corpus_path()
                (root/'data/raw').mkdir(parents=True);(root/'data/raw/axolotl.csv').write_text('x')
                self.assertEqual(default_corpus_path(),root/'data/raw/axolotl.csv')
                (root/'corpus/axolotl').mkdir(parents=True);(root/'corpus/axolotl/axolotl.csv').write_text('y')
                self.assertEqual(default_corpus_path(),root/'corpus/axolotl/axolotl.csv')
    def test_manifest_records_normalization(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);raw=root/'raw.csv'
            with raw.open('w',newline='') as f:
                writer=csv.writer(f)
                for i in range(6):writer.writerow([f'casa palabra{i}',f'calli texto{i}','Classical Nahuatl',f'obra{i}','nci'])
            prepare(raw,root/'prepared')
            manifest=json.loads((root/'prepared/manifest.json').read_text())
            self.assertEqual(manifest['normalization']['version'],ORTHOGRAPHY_VERSION)
            self.assertEqual(manifest['length_ratio']['tau'],2.5)
            self.assertIsNone(manifest['token_length'])
            self.assertIn('token_length_note',manifest)
if __name__=='__main__':unittest.main()
