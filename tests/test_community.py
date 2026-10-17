import io
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
import wave
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from nahuatl_local.community import Problem, Store
from nahuatl_local.corpus import CorpusStore
from nahuatl_local.platform import make_server


def profile(variant='inali-04'):
    return dict(alias='Participante de prueba', variant_id=variant, own_name='', community='',
                experience='childhood', historical='none', participation_consent=True)


def answer(task='write-001', **changes):
    return dict(task_id=task,text='Texto de prueba, no traducción validada.',audio_id=None,
                review_consent=True,rights_confirm=True,train_text=True,train_audio=False,**changes)


def wav():
    data=io.BytesIO()
    with wave.open(data,'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(8000);w.writeframes(b'\0'*1600)
    return data.getvalue()


class CommunityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.store=Store(self.root/'voces.sqlite3')
        self.person,self.token=self.store.save_profile(profile())

    def tearDown(self):
        self.temp.cleanup()

    def test_consent_required_and_training_optional_with_equal_points(self):
        bad=answer();bad['review_consent']=False
        with self.assertRaises(Problem):self.store.contribute(self.person,bad)
        bad['review_consent']=True;bad['train_text']=False
        self.store.contribute(self.person,bad)
        self.store.contribute(self.person,answer('write-002'))
        self.assertEqual(self.store.bootstrap(self.person)['stats']['points'],20)

    def test_same_mission_awarded_once_even_with_parallel_retries(self):
        def submit(_):
            try:return self.store.contribute(self.person,answer())
            except Problem as error:return error.status
        with ThreadPoolExecutor(max_workers=2) as workers:results=list(workers.map(submit,range(2)))
        self.assertEqual(sum(isinstance(x,dict) for x in results),1)
        self.assertIn(409,results)
        self.assertEqual(self.store.bootstrap(self.person)['stats']['points'],10)

    def test_audio_header_owner_and_cross_variant_access(self):
        audio=self.store.save_audio(self.person,'audio/wav',wav())
        other,_=self.store.save_profile(profile('inali-03'))
        with self.assertRaises(Problem):self.store.get_audio(audio,other)
        with self.assertRaises(Problem):self.store.save_audio(self.person,'audio/wav',b'<html>not audio</html>')
        payload=answer();payload['audio_id']=audio
        with self.assertRaises(Problem):self.store.contribute(other,payload)
        self.store.contribute(self.person,payload)
        with self.assertRaises(Problem):self.store.get_audio(audio,other)
        same,_=self.store.save_profile(profile())
        self.assertEqual(self.store.get_audio(audio,same)[1],wav())

    def test_profile_edits_preserve_original_variant_snapshot(self):
        self.store.contribute(self.person,answer())
        updated,_=self.store.save_profile(profile('inali-03'),self.person)
        item=self.store.mine(updated)['contributions'][0]
        self.assertEqual(item['answer']['profile']['variant_id'],'inali-04')

    def test_reviews_are_independent_same_variant_and_not_auto_approval(self):
        record=self.store.contribute(self.person,answer())
        data=dict(contribution_id=record['id'],verdict='matches',correction='',transcript='',review_consent=True)
        with self.assertRaises(Problem):self.store.review(self.person,data)
        other,_=self.store.save_profile(profile('inali-03'))
        with self.assertRaises(Problem):self.store.review(other,data)
        for _ in range(3):
            peer,_=self.store.save_profile(profile());self.store.review(peer,data)
        self.assertEqual(self.store.mine(self.person)['contributions'][0]['status'],'pending')
        with self.assertRaises(Problem):self.store.review(peer,data)

    def test_historical_impression_cannot_be_exported_as_translation(self):
        data=answer('read-001');data.update(recognition='yes',perceived='historical',certainty='sure')
        record=self.store.contribute(self.person,data)
        with self.assertRaises(Problem):self.store.curate(record['id'],'accepted','Revisor','nci','Revisado',source_url='https://example.org',locator='f. 1r')
        with self.assertRaises(Problem):self.store.export(self.root/'classic.jsonl','nci')

    def test_export_requires_approval_text_consent_and_classical_evidence(self):
        a=self.store.contribute(self.person,answer())
        with self.assertRaises(Problem):self.store.export(self.root/'pending.jsonl','modern')
        self.store.curate(a['id'],'accepted','Revisor','modern','Ejemplo revisado para prueba')
        self.store.export(self.root/'modern.jsonl','modern')
        exported=json.loads((self.root/'modern.jsonl').read_text())
        self.assertIsNone(exported['iso']);self.assertFalse(exported['public_redistribution'])
        with self.assertRaises(Problem):self.store.export(self.root/'classic.jsonl','nci')
        with self.assertRaises(Problem):self.store.curate(a['id'],'accepted','Revisor','nci','Sin referencia')
        self.store.curate(a['id'],'accepted','Revisor','nci','Revisión histórica declarada',source_url='https://example.org/source',locator='folio de prueba')
        self.store.export(self.root/'classic.jsonl','nci')
        self.assertEqual(json.loads((self.root/'classic.jsonl').read_text())['iso'],'nci')
        data=answer('write-002');data['train_text']=False
        b=self.store.contribute(self.person,data)
        self.store.curate(b['id'],'accepted','Revisor','modern','Revisión')
        with self.assertRaises(Problem):self.store.export(self.root/'no-consent.jsonl','modern')

    def test_audio_export_needs_separate_permission_and_transcript(self):
        data=answer();data.update(text='',audio_id=self.store.save_audio(self.person,'audio/wav',wav()))
        a=self.store.contribute(self.person,data)
        with self.assertRaises(Problem):self.store.curate(a['id'],'accepted','Revisor','modern','Revisión')
        self.store.curate(a['id'],'accepted','Revisor','modern','Revisión',final_text='Transcripción de prueba')
        out=self.root/'text.jsonl';self.store.export(out,'modern',include_audio=True)
        self.assertIsNone(json.loads(out.read_text())['audio_id'])
        data=answer('write-002');data.update(audio_id=self.store.save_audio(self.person,'audio/wav',wav()),train_audio=True)
        b=self.store.contribute(self.person,data);self.store.curate(b['id'],'accepted','Revisor','modern','Revisión')
        result=self.store.export(self.root/'with-audio.jsonl','modern',True)
        self.assertEqual(result['audios'],1)

    def test_withdrawal_deletes_audio_and_excludes_future_exports(self):
        data=answer();data['audio_id']=self.store.save_audio(self.person,'audio/wav',wav())
        record=self.store.contribute(self.person,data);self.store.curate(record['id'],'accepted','Revisor','modern','Revisión')
        self.store.withdraw(self.person,record['id'])
        with self.assertRaises(Problem):self.store.get_audio(data['audio_id'],self.person)
        with self.assertRaises(Problem):self.store.export(self.root/'withdrawn.jsonl','modern')
        self.assertEqual(self.store.bootstrap(self.person)['stats']['points'],0)
        with self.store.db() as db:
            self.assertTrue(all(r['detail']=='{}' for r in db.execute('SELECT detail FROM audit WHERE record=?',(record['id'],))))

    def test_observations_preserve_uncertainty_and_require_both_permissions(self):
        data=answer('read-001');data.update(recognition='partly',perceived='historical',certainty='unsure')
        record=self.store.contribute(self.person,data)
        output=self.root/'observations.jsonl';self.store.export_observations(output)
        exported=json.loads(output.read_text());self.assertFalse(exported['expert_verified']);self.assertEqual(exported['certainty'],'unsure')
        self.assertNotIn('iso',exported)
        data=answer();data['train_text']=False
        translation=self.store.contribute(self.person,data);peer,_=self.store.save_profile(profile())
        self.store.review(peer,dict(contribution_id=translation['id'],verdict='unsure',review_consent=True,train_text=True))
        result=self.store.export_observations(self.root/'second.jsonl');self.assertEqual(result['observations'],1)
        self.store.withdraw(self.person,record['id'])
        with self.assertRaises(Problem):self.store.export_observations(self.root/'empty.jsonl')

    def test_review_withdrawal_returns_curated_record_to_pending(self):
        record=self.store.contribute(self.person,answer());peer,_=self.store.save_profile(profile())
        review=self.store.review(peer,dict(contribution_id=record['id'],verdict='matches',review_consent=True))
        self.store.curate(record['id'],'accepted','Revisor','modern','Revisión')
        self.store.withdraw(peer,review['id'],review=True)
        self.assertEqual(self.store.mine(self.person)['contributions'][0]['status'],'pending')

    def test_import_rejects_reserved_evaluation_transactionally(self):
        path=self.root/'tasks.jsonl'
        task=dict(id='new',kind='translate',text='Ejemplo',source=dict(label='Fuente',rights='Propio',split='train'))
        reserved=dict(task,id='reserved',source=dict(task['source'],split='test'))
        path.write_text(json.dumps(task)+'\n'+json.dumps(reserved))
        with self.assertRaises(Problem):self.store.import_tasks(path)
        with self.store.db() as db:self.assertIsNone(db.execute("SELECT id FROM tasks WHERE id='new'").fetchone())

    def test_http_session_and_origin_protection(self):
        # Voces no tiene servidor propio: la aplicación única la sirve en /aportar.
        httpd=make_server(CorpusStore(self.root/'http.sqlite3'),port=0);thread=threading.Thread(target=httpd.serve_forever,daemon=True);thread.start()
        origin='http://127.0.0.1:'+str(httpd.server_address[1])
        try:
            req=urllib.request.Request(origin+'/api/profile',json.dumps(profile()).encode(),{'Content-Type':'application/json','Origin':origin})
            response=urllib.request.urlopen(req);cookie=response.headers['Set-Cookie'];self.assertIn('HttpOnly',cookie)
            self.assertNotIn('session_hash',response.read().decode())
            with self.assertRaises(urllib.error.HTTPError) as error:
                urllib.request.urlopen(urllib.request.Request(origin+'/api/profile',json.dumps(profile()).encode(),{'Origin':'http://evil.example'}))
            self.assertEqual(error.exception.code,403)
            with self.assertRaises(urllib.error.HTTPError) as error:urllib.request.urlopen(origin+'/api/mine')
            self.assertEqual(error.exception.code,401)
            with self.assertRaises(urllib.error.HTTPError) as error:
                urllib.request.urlopen(urllib.request.Request(origin+'/api/bootstrap',headers={'Host':'evil.example'}))
            self.assertEqual(error.exception.code,403)
        finally:httpd.shutdown();httpd.server_close();thread.join()


if __name__=='__main__':unittest.main()
