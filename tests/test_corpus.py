import copy
import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest
from nahuatl_local.community import Store, Problem
from nahuatl_local.corpus import CorpusStore, editorial_releases
from nahuatl_local.platform import make_server, rule_query
from nahuatl_local.pictography import load_catalog


class CorpusTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'corpus.db'
        self.store=CorpusStore(self.path)
        self.person,self.token=self.store.save_profile(dict(alias='Prueba',variant_id='inali-04',own_name='',community='',experience='childhood',historical='none',participation_consent=True))

    def tearDown(self):self.tmp.cleanup()

    def proposal(self,**kw):
        body=dict(kind='form',label='Agua: prueba sintética',source_id='src-community',locator='sesión de prueba',period='modern',orthography='Prueba sin valor lingüístico',sense_id='sense-atl',written='FORMA_QA',variation_kind='dialectal',notes='No es un ejemplo lingüístico.',review_consent=True,authorship=True,public_consent=True,training_consent=False)
        body.update(kw);return self.store.propose(self.person,body)['id']

    def accept(self,id,**kw):self.store.decide(id,'accepted','Revisor de pruebas','Solo para comprobar el flujo',rights_checked=True,**kw)

    def test_migration_preserves_voices_and_all_legacy_ids(self):
        again=CorpusStore(self.path)
        self.assertEqual(again.person(self.token)['id'],self.person['id'])
        legacy=json.loads((Path(__file__).resolve().parents[1]/'corpus/scriptorium-legacy.json').read_text())['corpus']
        self.assertTrue({r['id'] for r in legacy}.issubset(again.records()))
        self.assertEqual(len(again.records()),7934)
        self.assertEqual(len(Store(self.path).catalog['tasks']),12)
        self.assertTrue(again.records()['glyph-atl']['image'].startswith('https://aztecglyphs'))

    def test_glyph_image_backfill_and_validation(self):
        recs=self.store.records()
        imaged={rid for rid,r in recs.items() if r['kind']=='glyph' and r.get('image')}
        self.assertTrue({'glyph-xochitl','glyph-atl','glyph-calli','glyph-xochicuahuitl'}.issubset(imaged))
        for rid in imaged:
            self.assertTrue(recs[rid]['image'].startswith('https://aztecglyphs'))
            self.assertTrue(recs[rid]['image_credit'])
        for rid in ('glyph-tetl',):
            self.assertNotIn('image',recs[rid])
        r=copy.deepcopy(recs['glyph-atl']);r['image']='javascript:alert(1)'
        with self.assertRaises(Problem):self.store.validate(r,recs)
        again=CorpusStore(self.path)
        self.assertEqual(len(again.records()),7934)
        self.assertEqual(again.records()['glyph-atl']['image'],recs['glyph-atl']['image'])

    def test_senses_spelling_and_missing_modern_coverage(self):
        # La búsqueda vive en terms.TermIndex (tests/test_terms.py); aquí, los datos que la sostienen.
        recs=self.store.public_records()
        self.assertEqual({recs[i]['sense_id'] for i in ('lex-cuahuitl','form-quauitl')},{'sense-cuahuitl'})
        self.assertEqual(recs['form-quauitl']['written'],'quauitl')
        self.assertFalse([r for r in recs.values() if r['kind']=='form' and r.get('period')=='modern'])
        self.assertNotEqual(self.store.records()['sense-madera']['id'],self.store.records()['sense-cuahuitl']['id'])
        self.assertTrue(any(r['kind']=='glyph' and r['sense_id']=='sense-madera' for r in self.store.records().values()))

    def test_glyph_update_preserves_edits_and_adds_missing_links(self):
        # Simula una base previa sin el lote, con un vínculo ya añadido por su editor.
        keep=self.store.records()['glyph-metztli-osu14v']
        keep['context']='Nota de la persona editora';keep['expected_version']=keep['version']
        self.store.import_bundle(dict(schema_version=1,records=[keep]),'QA','Edición local')
        with self.store.db() as db:
            # Simula también el estado previo a las referencias que dependen
            # del glifo v2; no deja entidades dependientes con claves rotas.
            v7=json.loads((Path(__file__).resolve().parents[1]/'corpus/glyph-associations-v7.json').read_text())['records']
            v7+=json.loads((Path(__file__).resolve().parents[1]/'corpus/flor-lexicon-v8.json').read_text())['records']
            for release,bundle in editorial_releases():v7+=bundle['records']
            for r in v7:db.execute('DELETE FROM corpus_links WHERE owner=?',(r['id'],))
            for r in v7:
                db.execute('DELETE FROM corpus_history WHERE record_id=?',(r['id'],))
                db.execute('DELETE FROM corpus_records WHERE id=?',(r['id'],))
            db.execute("DELETE FROM corpus_meta WHERE key LIKE 'glyph-v7-%' OR key LIKE 'flor-v8-%' OR key LIKE 'editorial-release-%'")
            db.execute("DELETE FROM corpus_meta WHERE key='glyph-links-v2'")
            db.execute("DELETE FROM corpus_links WHERE owner='glyph-cuahuitl-mdz7v'")
            db.execute("DELETE FROM corpus_history WHERE record_id='glyph-cuahuitl-mdz7v'")
            db.execute("DELETE FROM corpus_records WHERE id='glyph-cuahuitl-mdz7v'")
        again=CorpusStore(self.path)
        self.assertEqual(len(again.records()),7934)
        self.assertEqual(again.records()['glyph-metztli-osu14v']['context'],'Nota de la persona editora')
        self.assertEqual(again.records()['glyph-metztli-osu14v']['version'],3)
        self.assertEqual(again.records()['glyph-metztli-osu14v']['sense_id'],'sense-mes')
        self.assertEqual(len([r for r in again.records().values() if r['kind']=='glyph']),140)
        self.assertEqual(CorpusStore(self.path).records(),again.records())

    def test_pending_private_training_permissions_and_retraction(self):
        id=self.proposal(training_consent=True)
        self.assertNotIn(id,self.store.public_records())
        self.accept(id)
        self.assertIn(id,self.store.public_records())
        self.assertIn(id,{r['id'] for r in self.store.export_data('training')['records']})
        self.store.withdraw_proposal(self.person,id)
        self.assertNotIn(id,self.store.public_records())
        self.assertNotIn(id,{r['id'] for r in self.store.export_data('training')['records']})
        with self.store.db() as db:
            self.assertFalse(db.execute('SELECT 1 FROM corpus_history WHERE record_id=?',(id,)).fetchone())
        self.assertEqual(self.store.proposals(self.person)[0]['payload'],{})

    def test_publication_and_training_are_independent(self):
        public=self.proposal(written='PUBLIC_ONLY');private=self.proposal(written='TRAIN_ONLY',public_consent=False,training_consent=True)
        self.accept(public);self.accept(private)
        self.assertIn(public,self.store.public_records());self.assertNotIn(private,self.store.public_records())
        ids={r['id'] for r in self.store.export_data('training')['records']}
        self.assertIn(private,ids);self.assertNotIn(public,ids)

    def test_profile_snapshot_duplicate_and_no_unprivileged_withdrawal(self):
        id=self.proposal();self.assertEqual(id,self.proposal())
        other,_=self.store.save_profile(dict(alias='Otra',variant_id='inali-03',experience='learning',historical='none',participation_consent=True))
        with self.assertRaises(Problem):self.store.withdraw_proposal(other,id)
        self.store.save_profile(dict(alias='Prueba',variant_id='inali-03',experience='childhood',historical='none',participation_consent=True),self.person)
        self.accept(id);self.assertEqual(self.store.records()[id]['variant'],'inali-04')

    def test_import_atomic_refs_and_optimistic_edits(self):
        r=copy.deepcopy(self.store.records()['sense-atl']);r['label']='AGUA';r['expected_version']=r['version']
        bad=copy.deepcopy(self.store.records()['lex-atl']);bad.update(id='bad-form',sense_id='missing')
        with self.assertRaises(Problem):self.store.import_bundle(dict(schema_version=1,records=[r,bad]),'QA','prueba')
        self.assertEqual(self.store.records()['sense-atl']['label'],'agua')
        self.store.import_bundle(dict(schema_version=1,records=[r]),'QA','prueba')
        self.assertEqual(self.store.records()['sense-atl']['version'],2)
        with self.assertRaises(Problem):self.store.import_bundle(dict(schema_version=1,records=[r]),'QA','versión caducada')

    def test_glyph_requires_primary_context_and_secondary_is_not_primary(self):
        id=self.proposal(kind='glyph',source_id='src-mendoza',period='historical',reading='Prueba',context='Folio ficticio de prueba',url='https://example.org')
        self.accept(id)
        self.assertEqual(self.store.records()[id]['glyph_status'],'proposed')
        r=copy.deepcopy(self.store.records()[id]);r['id']='invalid';r['glyph_status']='documented_context'
        with self.assertRaises(Problem):self.store.import_bundle(dict(schema_version=1,records=[r]),'QA','prueba')
        sid=self.proposal(written='OTHER',source_id='src-oregon',period='historical')
        with self.assertRaises(Problem):self.accept(sid,primary_checked=True)

    def test_training_requires_source_permission_and_historical_check(self):
        id=self.proposal(source_id='src-molina',period='historical',training_consent=True)
        self.accept(id,primary_checked=True)
        self.assertEqual(self.store.export_data('training')['records'],[])
        # Una obra primaria permitida no habilita una edición mediadora restringida.
        r=copy.deepcopy(self.store.records()['lex-atl']);r.update(id='form-qa-mediated',verification='reviewed')
        r['rights'].update(training=True,basis='Supuesto de prueba')
        r['evidence']=[dict(source_id='src-community',via_source_id='src-oregon',locator='prueba',status='inherited')]
        r['period']='modern';r['variant']='inali-04'
        self.store.import_bundle(dict(schema_version=1,records=[r]),'QA','prueba de derechos mediadores')
        self.assertNotIn(r['id'],{x['id'] for x in self.store.export_data('training')['records']})

    def test_import_after_withdrawal_and_private_source_hides_dependents(self):
        id=self.proposal();self.accept(id);self.store.withdraw_proposal(self.person,id)
        src=copy.deepcopy(self.store.records()['src-molina']);src['expected_version']=src['version'];src['rights']['public']=False
        self.store.import_bundle(dict(schema_version=1,records=[src]),'QA','restringir fuente')
        self.assertNotIn('lex-atl',self.store.public_records())

    def test_urls_and_required_rights_review(self):
        with self.assertRaises(Problem):self.proposal(kind='glyph',source_id='src-mendoza',reading='x',context='x',url='javascript:alert(1)')
        id=self.proposal()
        with self.assertRaises(Problem):self.store.decide(id,'accepted','QA','sin derechos')
        self.assertNotIn(id,self.store.records())

    def test_rules_ported_without_faking_general_translation(self):
        self.assertEqual(rule_query(self.store,'Veo una flor.')['status'],'proposal')
        self.assertEqual(rule_query(self.store,'El sol y la luna')['status'],'proposal')
        self.assertEqual(rule_query(self.store,'No veo tres casas mañana')['status'],'insufficient')

    def test_http_shared_origin_session_and_no_admin_route(self):
        server=make_server(self.store,port=0,model_enabled=False);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        port=server.server_address[1];conn=http.client.HTTPConnection('127.0.0.1',port)
        def req(method,path,body=None,**headers):
            conn.request(method,path,body=json.dumps(body) if body is not None else None,headers=headers);r=conn.getresponse();return r.status,r.read()
        try:
            conn.request('GET','/')
            response=conn.getresponse();policy=response.getheader('Content-Security-Policy');response.read()
            self.assertIn("img-src 'self' data: https://aztecglyphs.wired-humanities.org https://tlachia.iib.unam.mx;",policy)
            self.assertIn("script-src 'self';",policy)
            self.assertIn("connect-src 'self';",policy)
            self.assertNotIn('*',policy)
            self.assertEqual(req('GET','/')[0],200);self.assertEqual(req('GET','/aportar')[0],200)
            self.assertEqual(req('GET','/api/proposals')[0],401)
            self.assertEqual(req('GET','/learning.js')[0],200)
            self.assertEqual(req('GET','/learning.css')[0],200)
            self.assertEqual(req('GET','/pictography.js')[0],200)
            self.assertEqual(req('GET','/pictography.css')[0],200)
            status,payload=req('GET','/api/pictography');self.assertEqual(status,200)
            catalog = load_catalog()
            expected_glyphs = sum(row['kind'] == 'glyph' for row in catalog['occurrences'])
            self.assertEqual(json.loads(payload)['summary']['glyphs'], expected_glyphs)
            self.assertEqual(req('GET','/project.js')[0],200)
            self.assertEqual(req('GET','/project.css')[0],200)
            for path,phrase in [('/project/purpose.md','Propósito actual'),('/project/pilot.md','No enviada'),('/project/contributing.md','Mejorar Amoxcalli')]:
                status,payload=req('GET',path);self.assertEqual(status,200)
                self.assertIn(phrase,payload.decode())
            for path in ('/project/../../data/community/voces.sqlite3','/project/PROGRESO_INTERNO.md'):
                self.assertIn(req('GET',path)[0],(401,404))
            self.assertEqual(req('GET','/laboratory.js')[0],200)
            self.assertEqual(req('GET','/laboratory.css')[0],200)
            status,lab=req('GET','/api/laboratory');self.assertEqual(status,200);lab=json.loads(lab)
            self.assertFalse(lab['model']['ready'])
            self.assertEqual(lab['training']['completed_steps'],250)
            self.assertFalse(lab['training']['current_data_matches'])
            self.assertTrue(lab['retrieval']['current_data_matches'])
            self.assertEqual(req('GET','/api/laboratory/reports/training')[0],200)
            self.assertEqual(req('GET','/api/laboratory/reports/state.pt')[0],404)
            self.assertEqual(req('GET','/training-data.js')[0],200)
            status,payload=req('GET','/api/training-data');self.assertEqual(status,200)
            self.assertEqual(json.loads(payload)['total'],650)
            self.assertEqual(req('GET','/api/training-pairs')[0],401)
            self.assertEqual(req('GET','/api/laboratory/context?query=flor')[0],200)
            status,payload=req('GET','/api/learning');self.assertEqual(status,200)
            self.assertEqual(sum(len(l['examples']) for l in json.loads(payload)['lessons']),48)
            headers={'Cookie':'voces_session='+self.token,'Origin':f'http://127.0.0.1:{port}'}
            self.assertEqual(req('GET','/api/proposals',**headers)[0],200)
            self.assertEqual(req('POST','/api/compose',{'text':'agua'},Origin='https://attacker.example')[0],403)
            status,payload=req('POST','/api/compose',{'text':'agua'},**headers)
            self.assertEqual(status,200);self.assertIn('review_request',json.loads(payload));self.assertNotIn('jev_request',json.loads(payload))
            status,payload=req('GET','/manifest.webmanifest');self.assertEqual(status,200)
            manifest=json.loads(payload);self.assertEqual(manifest['scope'],'/');self.assertEqual(manifest['display'],'standalone')
            for item in manifest['icons']:self.assertEqual(req('GET',item['src'])[0],200)
            self.assertEqual(req('GET','/sw.js')[0],200);self.assertEqual(req('GET','/offline.html')[0],200)
            self.assertEqual(req('POST','/api/compose',{'text':'agua','model':True},**headers)[0],503)
            self.assertEqual(req('POST','/api/review',{},**headers)[0],404)
        finally:conn.close();server.shutdown();server.server_close();thread.join()


if __name__=='__main__':unittest.main()
