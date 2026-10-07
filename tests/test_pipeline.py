import unittest,tempfile,csv,json
from pathlib import Path
from unittest.mock import patch
from nahuatl_local import data as data_module
from nahuatl_local.data import prepare,load_rows,canonical,default_corpus_path
from nahuatl_local.nahuatl_orthography import storage,comparison,ORTHOGRAPHY_VERSION
from nahuatl_local.tokenizer_audit import audit_tokenizer,tokenizer_settings
from nahuatl_local.runtime import encode_pair
from nahuatl_local.retrieval import Index
class FakeTokenizer:
    eos_token_id=9
    def apply_chat_template(self,*args,**kwargs):return [1,2,3]
    def __call__(self,*args,**kwargs):return {'input_ids':[4,5]}
class FakeAuditTokenizer:
    """Un token por carácter; fallback explícito separado de letras ASCII."""
    def __init__(self,fallback_chars=()):
        self.fallback_ids={ord(c) for c in fallback_chars}
    def __call__(self,text,add_special_tokens=False):
        return {'input_ids':[ord(c) for c in text]}
    def convert_ids_to_tokens(self,token_id):
        c=chr(token_id)
        return '<0x%02X>' % token_id if token_id in self.fallback_ids else c
    def decode(self,ids,skip_special_tokens=True):
        return ''.join(chr(i) for i in ids)
class PipelineTests(unittest.TestCase):
    def test_label_mask_and_no_truncation(self):
        row={'es':'casa bonita','nah':'test target'}
        encoded=encode_pair(FakeTokenizer(),row,6)
        self.assertEqual(encoded['labels'],[-100,-100,-100,4,5,9])
        self.assertIsNone(encode_pair(FakeTokenizer(),row,5))
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
    def test_tokenizer_audit_fake(self):
        tok=FakeAuditTokenizer(fallback_chars='ñ')
        report=audit_tokenizer(tok,['casa ñandú','calli'],settings={'model':{'type':'BPE','byte_fallback':True}})
        self.assertEqual(report['rows'],2)
        self.assertEqual(report['roundtrip_failures'],0)
        self.assertEqual(report['byte_fallback_tokens'],1)
        self.assertIn('ñ',report['non_ascii_inventory'])
        self.assertEqual(report['verdict'],'warn')
        ok=audit_tokenizer(FakeAuditTokenizer(),['casa bonita','calli'])
        self.assertEqual(ok['verdict'],'ok')
        self.assertEqual(ok['single_character_token_fraction'],1.0)
        self.assertIsNone(ok['byte_fallback_tokens'])
    def test_bytelevel_ascii_is_not_fallback(self):
        report=audit_tokenizer(FakeAuditTokenizer(),['a b'],settings={'model':{'type':'BPE','byte_fallback':False},'decoder':{'type':'ByteLevel'}})
        self.assertEqual(report['single_character_tokens'],3)
        self.assertEqual(report['byte_fallback_tokens'],0)
        self.assertEqual(report['verdict'],'ok')
        self.assertEqual(report['warning_reasons'],[])
    def test_literal_byte_representation_is_not_fallback_when_disabled(self):
        report=audit_tokenizer(FakeAuditTokenizer(fallback_chars='a'),['a'],settings={'model':{'byte_fallback':False}})
        self.assertEqual(report['explicit_byte_tokens'],1)
        self.assertEqual(report['byte_fallback_tokens'],0)
        self.assertEqual(report['verdict'],'ok')
    def test_unknown_tokens_and_roundtrip_warn(self):
        tok=FakeAuditTokenizer();tok.unk_token_id=ord('a')
        report=audit_tokenizer(tok,['a'])
        self.assertEqual(report['roundtrip_failures'],0)
        self.assertEqual(report['unknown_token_tokens'],1)
        self.assertEqual(report['warning_reasons'],['unknown_token_tokens'])
        tok=FakeAuditTokenizer();tok.decode=lambda *args,**kwargs:'changed'
        report=audit_tokenizer(tok,['a'])
        self.assertEqual(report['warning_reasons'],['roundtrip_failures'])
    def test_tokenizer_settings_read_local_json_without_vocab(self):
        with tempfile.TemporaryDirectory() as folder:
            config={'model':{'type':'BPE','byte_fallback':False,'vocab':{'a':0},'merges':[]},'pre_tokenizer':{'type':'ByteLevel'},'decoder':{'type':'ByteLevel'}}
            (Path(folder)/'tokenizer.json').write_text(json.dumps(config))
            settings=tokenizer_settings(path=folder)
            self.assertEqual(settings['model'],{'type':'BPE','byte_fallback':False})
            self.assertEqual(settings['pre_tokenizer'],config['pre_tokenizer'])
            self.assertEqual(settings['decoder'],config['decoder'])
if __name__=='__main__':unittest.main()
