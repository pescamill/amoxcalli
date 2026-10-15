"""Amoxcalli: corpus, investigación y extractor Voces en un solo servidor local."""
import argparse
import hashlib
import json
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from .community import handler as community_handler, Problem, ROOT, DEFAULT_DB, text
from .corpus import CorpusStore, normalize
from .review import request_bundle, local_review
from .research import Archive
from .learning import Learning
from .laboratory import snapshot as laboratory_snapshot, REPORTS as LAB_REPORTS
from .documentary_laboratory import public_download as documentary_laboratory_download
from .visual_preparation import review as visual_preparation_review
from .training_data import TrainingData, PairProposals
from .model_status import status as model_status, DEFAULT_ADAPTER
from .pictography import public_catalog
from .documentary_retrieval import DocumentaryIndex, PublicSources, digest as documentary_digest, public_path
from .stems import WordStudy
from .evidence import Evidence
from .explain import ClaudeWriter, explain

WEB = Path(__file__).with_name('platform_web')
INSTALL_HEAD = '<meta name="theme-color" content="#812d37"><meta name="apple-mobile-web-app-capable" content="yes">\n<link rel="manifest" href="/manifest.webmanifest"><link rel="apple-touch-icon" href="/icon-192.png"><link rel="stylesheet" href="/install.css"><script src="/install.js" defer></script>\n'


def rule_query(store, value):
    """Porta las reglas acotadas de Amoxcalli; ninguna salida es validación."""
    records=store.public_records()
    q=normalize(value.strip()).rstrip('.!?')
    q=q.removeprefix('yo ')

    def noun(phrase):
        for article in ('el ','la ','un ','una ','the ','a ','an '):
            if phrase.startswith(article):
                phrase=phrase[len(article):];break
        for r in records.values():
            if r['kind']=='sense' and r['pos']=='noun' and phrase in [normalize(x) for x in [r['label'],*r.get('aliases',[])]]:
                if phrase in ('flores','arboles','flowers','trees'):
                    continue
                # Usa solo el lema histórico heredado por la regla original.
                f=next((f for f in records.values() if f['kind']=='form' and f.get('sense_id')==r['id'] and f['id'].startswith('lex-')),None)
                if f:return f
        return None

    segments=[];status='insufficient';method='lookup'
    f=noun(q)
    if f:
        segments=[dict(text=f['written'],record_ids=[f['id']])];status='lexical'
    else:
        for prefix in ('veo ','miro ','i see ','i look at '):
            if q.startswith(prefix) and (f:=noun(q[len(prefix):])):
                segments=[dict(text='Niquitta ',record_ids=['grammar-niquitta']),dict(text=f['written']+'.',record_ids=[f['id']])]
                status='proposal';method='rules';break
        if not segments:
            for conj in (' y ',' and '):
                parts=q.split(conj)
                if len(parts)==2 and (a:=noun(parts[0])) and (b:=noun(parts[1])):
                    segments=[dict(text=a['written'],record_ids=[a['id']]),dict(text=' ihuan ',record_ids=['lex-ihuan']),dict(text=b['written'],record_ids=[b['id']])]
                    status='proposal';method='rules';break
    return dict(status=status,method=method,segments=segments,
                note='Palabra asociada a una acepción; revisar el contexto.' if status=='lexical' else
                'Composición nueva por una regla limitada; no es una cita histórica ni una traducción validada.' if status=='proposal' else
                'Las reglas disponibles no cubren esta expresión. Consulta palabras o textos por separado.')


def make_handler(store, model_enabled=None, adapter=None, word_study=None, explain_writer=None):
    base=community_handler(store)
    archive=Archive()
    # Análisis morfológico, concordancia por raíz y pistas de glosa (sin modelo).
    word_study=word_study or WordStudy(records_fn=store.public_records)
    evidence_index=Evidence(word_study)
    learning=Learning(archive)
    training_data=TrainingData()
    pair_proposals=PairProposals(store,training_data)
    adapter=adapter or DEFAULT_ADAPTER
    capability=model_status(adapter,model_enabled)
    model_lock=threading.Lock()
    loaded=None
    documentary_cache=None
    documentary_lock=threading.Lock()

    class Handler(base):
        # Solo el catálogo glífico aprobado puede servir imágenes externas.
        content_security_policy = base.content_security_policy.replace(
            "img-src 'self' data:",
            "img-src 'self' data: https://aztecglyphs.wired-humanities.org https://tlachia.iib.unam.mx")

        def dispatch(self):
            nonlocal loaded, documentary_cache
            parsed=urlparse(self.path);path=parsed.path
            static={'/':('index.html','text/html; charset=utf-8'),
                    '/corpus.js':('app.js','text/javascript; charset=utf-8'),
                    '/corpus.css':('style.css','text/css; charset=utf-8'),
                    '/minimal.css':('minimal.css','text/css; charset=utf-8'),
                    '/learning.css':('learning.css','text/css; charset=utf-8'),
                    '/learning.js':('learning.js','text/javascript; charset=utf-8'),
                    '/morphology.js':('morphology.js','text/javascript; charset=utf-8'),
                    '/morphology.css':('morphology.css','text/css; charset=utf-8'),
                    '/evidence.js':('evidence.js','text/javascript; charset=utf-8'),
                    '/evidence.css':('evidence.css','text/css; charset=utf-8'),
                    '/documentary.js':('documentary.js','text/javascript; charset=utf-8'),
                    '/pictography.js':('pictography.js','text/javascript; charset=utf-8'),
                    '/pictography.css':('pictography.css','text/css; charset=utf-8'),
                    '/project.js':('project.js','text/javascript; charset=utf-8'),
                    '/project.css':('project.css','text/css; charset=utf-8'),
                    '/edition.css':('edition.css','text/css; charset=utf-8'),
                    '/edition-border.svg':('edition-border.svg','image/svg+xml'),
                    '/laboratory.js':('laboratory.js','text/javascript; charset=utf-8'),
                    '/laboratory.css':('laboratory.css','text/css; charset=utf-8'),
                    '/training-data.js':('training-data.js','text/javascript; charset=utf-8'),
                    '/manifest.webmanifest':('manifest.webmanifest','application/manifest+json'),
                    '/install.js':('install.js','text/javascript; charset=utf-8'),
                    '/install.css':('install.css','text/css; charset=utf-8'),
                    '/sw.js':('sw.js','text/javascript; charset=utf-8'),
                    '/offline.html':('offline.html','text/html; charset=utf-8'),
                    '/offline.css':('offline.css','text/css; charset=utf-8'),
                    '/icon-192.png':('icon-192.png','image/png'),
                    '/icon-512.png':('icon-512.png','image/png')}
            if self.command=='GET':
                if path in static:
                    name,mime=static[path];return self.reply((WEB/name).read_bytes(),mime=mime)
                project_docs={'/project/purpose.md':'docs/PROPOSITO.md',
                              '/project/pilot.md':'docs/PILOTO_INSTITUCIONAL.md',
                              '/project/contributing.md':'CONTRIBUTING.md'}
                if path in project_docs:
                    return self.reply((ROOT/project_docs[path]).read_bytes(),mime='text/plain; charset=utf-8')
                if path in ('/aportar','/aportar/'):
                    # Misma sesión, mismos datos y mismos permisos que el corpus.
                    page=(Path(__file__).with_name('community_web')/'index.html').read_text()
                    return self.reply(page.replace('</head>',INSTALL_HEAD+'<link rel="stylesheet" href="/minimal.css"><link rel="stylesheet" href="/edition.css"></head>').encode(),mime='text/html; charset=utf-8')
                if path=='/api/corpus':
                    data=store.catalog_data();data.update(model_enabled=capability['ready'],model=capability,archive=archive.summary)
                    return self.reply(data)
                if path=='/api/documentary':
                    q=parse_qs(parsed.query);value=text(q.get('query',[''])[0],'Consulta',1000)
                    with documentary_lock:
                        records=store.public_records();signature=documentary_digest(records)
                        stale=documentary_cache is None or documentary_cache['signature']!=signature
                        if not stale:
                            sources=documentary_cache['index'].sources
                            stale=any(hashlib.sha256(public_path(ROOT,p).read_bytes()).hexdigest()!=h for p,h in sources.hashes.items())
                        if stale:
                            documentary_cache=dict(signature=signature,index=DocumentaryIndex(records))
                        return self.reply(documentary_cache['index'].search(value))
                if path=='/api/pictography':return self.reply(public_catalog(store.public_records()))
                if path=='/api/word':
                    q=parse_qs(parsed.query);exclude=q.get('exclude',[''])[0] or None
                    try:return self.reply(word_study.word(q.get('w',[''])[0],exclude))
                    except ValueError as error:raise Problem(str(error)) from None
                if path=='/api/ask':
                    try:result=evidence_index.ask(parse_qs(parsed.query).get('q',[''])[0])
                    except ValueError as error:raise Problem(str(error)) from None
                    return self.reply(dict(result,explanation=explain(result),explain_models=['extractive']+(['claude'] if explain_writer else [])))
                if path=='/api/explain':
                    q=parse_qs(parsed.query);model=q.get('model',['extractive'])[0]
                    if model not in ('extractive','claude'):raise Problem('Modelo de explicación desconocido.')
                    if model=='claude' and not explain_writer:raise Problem('La explicación con Claude no está activada en este servidor (--explain-model claude).')
                    try:result=evidence_index.ask(q.get('q',[''])[0])
                    except ValueError as error:raise Problem(str(error)) from None
                    return self.reply(explain(result,explain_writer if model=='claude' else None))
                if path=='/api/gloss':
                    q=parse_qs(parsed.query);rid=q.get('id',[''])[0]
                    source=archive.get(rid)['nah'] if rid else q.get('text',[''])[0]
                    try:return self.reply(dict(word_study.gloss(source),archive_id=rid or None))
                    except ValueError as error:raise Problem(str(error)) from None
                if path=='/api/system':return self.reply(dict(model=capability,archive=archive.summary))
                if path=='/api/laboratory':return self.reply(laboratory_snapshot(capability,adapter))
                if path=='/api/laboratory/visual-preparation':
                    if parsed.query:raise Problem('El visor admite solo desarrollo, sin parámetros alternativos.')
                    return self.reply(visual_preparation_review())
                if path=='/api/laboratory/context':
                    q=parse_qs(parsed.query);value=text(q.get('query',[''])[0],'Consulta',1000,True)
                    return self.reply(dict(passages=archive.context(value)))
                if path=='/api/training-data':
                    q=parse_qs(parsed.query)
                    return self.reply(training_data.search(**{k:q.get(k,[v])[0] for k,v in [('dataset','seen'),('query',''),('document',''),('offset',0),('limit',20)]}))
                if path=='/api/training-pairs':return self.reply(pair_proposals.mine(self.get_person(True)))
                if path=='/api/training-pairs/export':return self.reply(pair_proposals.export(self.get_person(True)).encode(),mime='text/csv; charset=utf-8')
                if path.startswith('/api/laboratory/reports/'):
                    name=path.rsplit('/',1)[1]
                    if name in ('documentary-comparison','documentary-retrieval'):
                        return self.reply(documentary_laboratory_download(name))
                    report=LAB_REPORTS.get(name)
                    if not report or not (ROOT/report).is_file():raise Problem('Informe no disponible.',404)
                    return self.reply(json.loads((ROOT/report).read_text(encoding='utf-8')))
                if path=='/api/learning':return self.reply(learning.catalog(store.public_records()))
                if path=='/api/research':
                    q=parse_qs(parsed.query)
                    return self.reply(archive.search(**{k:q.get(k,[''])[0] for k in ('query','variant','document','period')},offset=q.get('offset',[0])[0],limit=q.get('limit',[20])[0]))
                if path.startswith('/api/research/'):return self.reply(archive.get(path.rsplit('/',1)[1]))
                if path=='/archive.csv':return self.reply(archive.path.read_bytes(),mime='text/csv; charset=utf-8')
                if path=='/api/task':
                    q=parse_qs(parsed.query);mode=q.get('mode',['recognize'])[0]
                    if mode in ('recognize','translate'):return self.reply(archive.task(store,mode,self.get_person(True),q.get('after',[''])[0]))
                if path=='/api/search':
                    q=parse_qs(parsed.query)
                    return self.reply(store.search(**{k:q.get(k,[''])[0] for k in ('query','kind','period','variant')}))
                if path=='/api/corpus/export':
                    return self.reply(store.export_data())
                if path=='/api/proposals':
                    return self.reply(store.proposals(self.get_person(True)))
            if path in ('/api/proposals','/api/compose','/api/training-pairs') or path.startswith(('/api/proposals/','/api/training-pairs/')):
                origin=self.headers.get('Origin','')
                expected=self.server.public_origin or f'http://{self.headers.get("Host","")}'
                if origin!=expected:
                    raise Problem('Origen de envío no permitido.',403)
                if path=='/api/training-pairs' and self.command=='POST':
                    return self.reply(pair_proposals.propose(self.get_person(True),self.body()),201)
                if path.startswith('/api/training-pairs/') and self.command=='DELETE':
                    pair_proposals.withdraw(self.get_person(True),path.rsplit('/',1)[1]);return self.reply(dict(ok=True))
                if path=='/api/proposals' and self.command=='POST':
                    return self.reply(store.propose(self.get_person(True),self.body()),201)
                if path.startswith('/api/proposals/') and self.command=='DELETE':
                    store.withdraw_proposal(self.get_person(True),path.rsplit('/',1)[1])
                    return self.reply({'ok':True})
                if path=='/api/compose' and self.command=='POST':
                    body=self.body();value=text(body.get('text',''),'Consulta',1000,True)
                    result=rule_query(store,value)
                    retrieved=[]
                    if body.get('model',capability['ready']) is True:
                        if not capability['ready']:
                            raise Problem('Prepara el modelo con bash scripts/iniciar.sh en el servidor. No requiere una API.',503)
                        if not model_lock.acquire(blocking=False):
                            raise Problem('El modelo está ocupado. Inténtalo más tarde.',429)
                        try:
                            from .runtime import load_model,translate
                            if loaded is None:
                                import torch
                                torch.set_num_threads(4)
                                loaded=load_model(ROOT/'models/base',adapter,'auto')
                            retrieved=archive.context(value)
                            context_in_prompt=body.get('rag',False) is True
                            output=translate(*loaded,value,context=retrieved if context_in_prompt else None,max_new_tokens=128)
                            result=dict(status='proposal',method='local_model',segments=[dict(text=output['text'],record_ids=[])],
                                        note='Borrador pendiente de revisión lingüística. Los pasajes recuperados aportan contexto, no certifican la traducción.',model=capability['name'],seconds=output['seconds'],truncated=output['truncated'],context_in_prompt=context_in_prompt)
                        except Exception:
                            raise Problem('No se pudo ejecutar el modelo local. Revisa sus dependencias y pesos; la consulta del corpus funciona.',503) from None
                        finally:model_lock.release()
                    if result['method']=='local_model':
                        words=normalize(' '.join(s['text'] for s in result['segments'])).strip('. ').split()
                        repeated=len(words)>=4 and len(words)%2==0 and words[:len(words)//2]==words[len(words)//2:]
                        result['quality_issues']=(['repeated_phrase'] if repeated else [])+(['length_limit'] if result.get('truncated') else [])
                        if result['quality_issues']:result['note']+=' Se detectó repetición o un límite de longitud; la salida requiere corrección.'
                    cited_ids={i for s in result['segments'] for i in s['record_ids']}
                    evidence=[r for r in store.public_records().values() if r['id'] in cited_ids]
                    draft=dict(input=value,text=''.join(s['text'] for s in result['segments']),related_passages=evidence+retrieved)
                    result['context_passages']=retrieved
                    result.update(review_request=request_bundle(draft),review=local_review(draft))
                    return self.reply(result)
                raise Problem('Método no permitido.',405)
            return super().dispatch()
    return Handler


class PlatformServer(ThreadingHTTPServer):
    # La página pide ~20 recursos a la vez; macOS descarta conexiones por encima de la cola (5 por omisión).
    request_queue_size=64


def make_server(store,host='127.0.0.1',port=8766,public_origin=None,model_enabled=None,adapter=None,prewarm=False,explain_model=None):
    word_study=WordStudy(records_fn=store.public_records)
    if prewarm:
        # El primer arranque estima frecuencias y pistas (~1 min); después se usa data/derived/.
        threading.Thread(target=word_study.warm,daemon=True,name='word-study-warmup').start()
    # Claude solo redacta si se pide al arrancar: la explicación envía la pregunta y los pasajes citados a Anthropic.
    writer=ClaudeWriter() if explain_model=='claude' else None
    httpd=PlatformServer((host,port),make_handler(store,model_enabled,adapter,word_study,writer))
    actual=httpd.server_address[1]
    httpd.public_origin=None
    httpd.allowed_hosts={f'localhost:{actual}',f'127.0.0.1:{actual}',f'{host}:{actual}'}
    if public_origin:
        p=urlparse(public_origin)
        if p.scheme!='https' or not p.hostname or p.path not in ('','/') or p.query or p.fragment or p.username:
            httpd.server_close();raise Problem('--public-origin requiere un origen HTTPS sin ruta.')
        httpd.public_origin=public_origin.rstrip('/')
        httpd.allowed_hosts.add(p.netloc)
    return httpd


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--db',type=Path,default=DEFAULT_DB)
    sub=p.add_subparsers(dest='command',required=True)
    serve=sub.add_parser('serve');serve.add_argument('--host',default='127.0.0.1');serve.add_argument('--port',type=int,default=8766);serve.add_argument('--public-origin');serve.add_argument('--enable-model',action='store_true',default=None);serve.add_argument('--disable-model',action='store_true');serve.add_argument('--adapter',default=str(ROOT/'outputs/continued-unseen/run/best'));serve.add_argument('--explain-model',choices=['claude'],help='Activa explicaciones redactadas por Claude (envía la pregunta y los pasajes citados a la API de Anthropic).')
    imp=sub.add_parser('import');imp.add_argument('path');imp.add_argument('--reviewer',required=True);imp.add_argument('--reason',required=True)
    sub.add_parser('queue')
    review=sub.add_parser('review');review.add_argument('id');review.add_argument('--decision',choices=['accepted','rejected'],required=True);review.add_argument('--reviewer',required=True);review.add_argument('--reason',required=True);review.add_argument('--primary-checked',action='store_true');review.add_argument('--rights-checked',action='store_true')
    export=sub.add_parser('export');export.add_argument('--purpose',choices=['research','training'],default='research');export.add_argument('--period',choices=['historical','modern'],default='');export.add_argument('--output',required=True)
    args=p.parse_args()
    try:
        store=CorpusStore(args.db)
        if args.command=='serve':
            httpd=make_server(store,args.host,args.port,args.public_origin,False if args.disable_model else args.enable_model,args.adapter,prewarm=True,explain_model=args.explain_model)
            print(f'Amoxcalli · http://127.0.0.1:{httpd.server_address[1]} · Voces en /aportar',flush=True)
            try:httpd.serve_forever()
            except KeyboardInterrupt:pass
            finally:httpd.server_close()
        elif args.command=='import':
            print('Registros incorporados:',store.import_bundle(json.loads(Path(args.path).read_text()),args.reviewer,args.reason))
        elif args.command=='queue':
            print(json.dumps(store.proposals(),ensure_ascii=False,indent=2))
        elif args.command=='review':
            store.decide(args.id,args.decision,args.reviewer,args.reason,args.primary_checked,args.rights_checked)
            print('Revisión guardada.')
        elif args.command=='export':
            with Path(args.output).open('x',encoding='utf-8') as f:
                json.dump(store.export_data(args.purpose,args.period),f,ensure_ascii=False,indent=2)
            print(args.output)
    except (Problem,ValueError,OSError) as error:
        p.exit(1,str(error)+'\n')


if __name__=='__main__':main()
