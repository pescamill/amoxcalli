import csv
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from nahuatl_local.community import Problem
from nahuatl_local.corpus import CorpusStore
from nahuatl_local.training_data import TrainingData, PairProposals


class TrainingDataTests(unittest.TestCase):
    def test_reference_matches_training_hashes_and_seen_cursor(self):
        d=TrainingData();result=d.search()
        self.assertEqual(result['total'],650)
        self.assertEqual(len(result['results']),20)
        self.assertEqual(d.search(dataset='historical')['total'],2248)
        self.assertEqual(d.search(dataset='train')['total'],2161)
        self.assertTrue(all(r['iso']=='nci' for r in d.datasets['seen']['rows']))
        self.assertTrue(all(r in d.datasets['historical']['rows'] for r in d.datasets['seen']['rows']))
        selected=d.search(query=result['results'][0]['nah'][:20])
        self.assertIn(result['results'][0],selected['results'])
        self.assertEqual(d.search(document=result['results'][0]['document'])['results'][0]['document'],result['results'][0]['document'])

    def test_tampered_reference_is_not_presented_as_training(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);ref=root/'data/training-reference/continued-unseen';ref.mkdir(parents=True)
            (ref/'train.jsonl').write_text('changed')
            (ref/'manifest.json').write_text(json.dumps(dict(dataset_sha256={'train':'expected'})))
            with self.assertRaises(ValueError):TrainingData(root)
            historical=Path(__file__).resolve().parents[1]/'data/training-reference/continued-unseen'
            for file in historical.iterdir():
                if file.is_file():(ref/file.name).write_bytes(file.read_bytes())
            seen=json.loads((ref/'seen.json').read_text())
            seen['ids'].reverse()
            (ref/'seen.json').write_text(json.dumps(seen))
            with self.assertRaises(ValueError):TrainingData(root)

    def test_invalid_dataset_and_pagination(self):
        d=TrainingData()
        for kw in [dict(dataset='../test'),dict(offset=-1),dict(limit=101),dict(query='x'*301)]:
            with self.assertRaises(Problem):d.search(**kw)


class PairProposalTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.store=CorpusStore(Path(self.tmp.name)/'pairs.sqlite3')
        self.person,_=self.store.save_profile(dict(alias='Pruebas',variant_id='inali-04',experience='learning',historical='none',participation_consent=True))
        self.other,_=self.store.save_profile(dict(alias='Otra',variant_id='inali-03',experience='learning',historical='none',participation_consent=True))
        self.data=TrainingData();self.pairs=PairProposals(self.store,self.data)
        self.body=dict(es='TEXTO SINTÉTICO DE PRUEBA',nah='FORMA SINTÉTICA SIN VALOR LINGÜÍSTICO',document='Colección de pruebas técnicas',locator='Registro 1',source_url='https://example.org/source',license='CC-BY-4.0',iso='nci',authorship=True,review_consent=True,training_consent=True)

    def tearDown(self):self.tmp.cleanup()

    def test_pending_pair_is_private_and_not_exported_or_added_to_data(self):
        before=len(self.data.datasets['train']['rows']);r=self.pairs.propose(self.person,self.body)
        self.assertEqual(r['status'],'pending');self.assertEqual(self.pairs.mine(self.other),[])
        self.assertEqual(len(list(csv.DictReader(io.StringIO(self.pairs.export(self.person))))),0)
        self.assertEqual(len(self.data.datasets['train']['rows']),before)
        self.assertTrue(self.pairs.propose(self.person,self.body)['duplicate'])
        with self.assertRaises(Problem):self.pairs.withdraw(self.other,r['id'])

    def test_consent_license_iso_source_and_heldout_guards(self):
        for change in [dict(authorship=False),dict(training_consent=False),dict(iso='nhm'),dict(source_url='javascript:alert(1)'),dict(license='unknown'),dict(document='Trece Poetas del Mundo Azteca'),dict(es=self.data.datasets['seen']['rows'][0]['es'])]:
            with self.assertRaises(Problem):self.pairs.propose(self.person,{**self.body,**change})

    def test_reviewed_export_and_withdrawal(self):
        r=self.pairs.propose(self.person,self.body)
        with self.assertRaises(Problem):self.pairs.decide(r['id'],'Revisora','QA',rights_checked=True)
        self.pairs.decide(r['id'],'Revisora de pruebas','Prueba técnica',True,True)
        rows=list(csv.DictReader(io.StringIO(self.pairs.export(self.person))))
        self.assertEqual(rows[0]['es'],self.body['es']);self.assertEqual(rows[0]['nah'],self.body['nah']);self.assertEqual(rows[0]['reviewer'],'Revisora de pruebas')
        self.pairs.withdraw(self.person,r['id']);self.assertEqual(len(list(csv.DictReader(io.StringIO(self.pairs.export())))),0)
