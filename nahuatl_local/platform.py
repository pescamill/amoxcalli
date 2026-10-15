"""Amoxcalli: la aplicación local (corpus, aprendizaje, investigación, laboratorio y Voces) en un solo servidor."""
import argparse
import hashlib
import json
import threading
from pathlib import Path
from .community import ASSETS as COMMUNITY_WEB, Problem, ROOT, DEFAULT_DB, text, routes as community_routes
from .corpus import CorpusStore
from .text import fold
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
from .web import Router, Server, Static, handler

WEB = Path(__file__).with_name('platform_web')
# Mismas URL de siempre: la página principal usa /corpus.*; /app.js, /style.css y /favicon.svg son de Voces.
STATIC = Static(WEB, {'/': WEB/'index.html', '/corpus.js': WEB/'app.js', '/corpus.css': WEB/'style.css',
                      '/app.js': COMMUNITY_WEB/'app.js', '/style.css': COMMUNITY_WEB/'style.css',
                      '/favicon.svg': COMMUNITY_WEB/'favicon.svg',
                      '/project/purpose.md': ROOT/'docs/PROPOSITO.md', '/project/pilot.md': ROOT/'docs/PILOTO_INSTITUCIONAL.md',
                      '/project/contributing.md': ROOT/'CONTRIBUTING.md'})
INSTALL_HEAD = '<meta name="theme-color" content="#812d37"><meta name="apple-mobile-web-app-capable" content="yes">\n<link rel="manifest" href="/manifest.webmanifest"><link rel="apple-touch-icon" href="/icon-192.png"><link rel="stylesheet" href="/install.css"><script src="/install.js" defer></script>\n'


def rule_query(store, value):
    """Porta las reglas acotadas de Amoxcalli; ninguna salida es validación."""
    records=store.public_records()
    q=fold(value.strip()).rstrip('.!?')
    q=q.removeprefix('yo ')

    def noun(phrase):
        for article in ('el ','la ','un ','una ','the ','a ','an '):
            if phrase.startswith(article):
                phrase=phrase[len(article):];break
        for r in records.values():
            if r['kind']=='sense' and r['pos']=='noun' and phrase in [fold(x) for x in [r['label'],*r.get('aliases',[])]]:
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


def make_app(store, model_enabled=None, adapter=None, word_study=None, explain_writer=None):
    """Tabla de rutas de la aplicación: corpus, investigación, laboratorio y Voces."""
    router=Router()
    community_routes(router,store)
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
    model=dict(loaded=None)
    documentary=dict(cache=None,lock=threading.Lock())

    def contribute_page(request):
        # Misma sesión, mismos datos y mismos permisos que el corpus.
        page=(COMMUNITY_WEB/'index.html').read_text()
        return request.reply(page.replace('</head>',INSTALL_HEAD+'<link rel="stylesheet" href="/minimal.css"><link rel="stylesheet" href="/edition.css"></head>').encode(),mime='text/html; charset=utf-8')

    def corpus(request):
        data=store.catalog_data();data.update(model_enabled=capability['ready'],model=capability,archive=archive.summary)
        return request.reply(data)

    def documentary_search(request):
        value=text(request.arg('query'),'Consulta',1000)
        with documentary['lock']:
            records=store.public_records();signature=documentary_digest(records);cache=documentary['cache']
            stale=cache is None or cache['signature']!=signature
            if not stale:
                stale=any(hashlib.sha256(public_path(ROOT,p).read_bytes()).hexdigest()!=h for p,h in cache['index'].sources.hashes.items())
            if stale:
                cache=documentary['cache']=dict(signature=signature,index=DocumentaryIndex(records))
            return request.reply(cache['index'].search(value))

    def word(request):
        try:return request.reply(word_study.word(request.arg('w'),request.arg('exclude') or None))
        except ValueError as error:raise Problem(str(error)) from None

    def ask(request):
        try:result=evidence_index.ask(request.arg('q'))
        except ValueError as error:raise Problem(str(error)) from None
        return request.reply(dict(result,explanation=explain(result),explain_models=['extractive']+(['claude'] if explain_writer else [])))

    def explanation(request):
        model_name=request.arg('model','extractive')
        if model_name not in ('extractive','claude'):raise Problem('Modelo de explicación desconocido.')
        if model_name=='claude' and not explain_writer:raise Problem('La explicación con Claude no está activada en este servidor (--explain-model claude).')
        try:result=evidence_index.ask(request.arg('q'))
        except ValueError as error:raise Problem(str(error)) from None
        return request.reply(explain(result,explain_writer if model_name=='claude' else None))

    def gloss(request):
        rid=request.arg('id')
        source=archive.get(rid)['nah'] if rid else request.arg('text')
        try:return request.reply(dict(word_study.gloss(source),archive_id=rid or None))
        except ValueError as error:raise Problem(str(error)) from None

    def visual_preparation(request):
        if request.query_string:raise Problem('El visor admite solo desarrollo, sin parámetros alternativos.')
        return request.reply(visual_preparation_review())

    def laboratory_context(request):
        value=text(request.arg('query'),'Consulta',1000,True)
        return request.reply(dict(passages=archive.context(value)))

    def laboratory_report(request):
        name=request.tail
        if name in ('documentary-comparison','documentary-retrieval'):
            return request.reply(documentary_laboratory_download(name))
        report=LAB_REPORTS.get(name)
        if not report or not (ROOT/report).is_file():raise Problem('Informe no disponible.',404)
        return request.reply(json.loads((ROOT/report).read_text(encoding='utf-8')))

    def training_search(request):
        return request.reply(training_data.search(**{k:request.arg(k,v) for k,v in [('dataset','seen'),('query',''),('document',''),('offset',0),('limit',20)]}))

    def research(request):
        return request.reply(archive.search(**{k:request.arg(k) for k in ('query','variant','document','period')},offset=request.arg('offset',0),limit=request.arg('limit',20)))

    def task(request):
        # Recordar y traducir usan el archivo completo; escuchar y revisar, las aportaciones de Voces.
        mode=request.arg('mode','recognize');person=request.get_person(True)
        source=(lambda *args:archive.task(store,*args)) if mode in ('recognize','translate') else store.task
        return request.reply(source(mode,person,request.arg('after')))

    def search(request):
        return request.reply(store.search(**{k:request.arg(k) for k in ('query','kind','period','variant')}))

    def withdraw_proposal(request):
        store.withdraw_proposal(request.get_person(True),request.tail)
        return request.reply({'ok':True})

    def withdraw_pair(request):
        pair_proposals.withdraw(request.get_person(True),request.tail);return request.reply(dict(ok=True))

    def compose(request):
        body=request.body();value=text(body.get('text',''),'Consulta',1000,True)
        result=rule_query(store,value)
        retrieved=[]
        if body.get('model',capability['ready']) is True:
            if not capability['ready']:
                raise Problem('Prepara el modelo con bash scripts/amoxcalli.sh setup en el servidor. No requiere una API.',503)
            if not model_lock.acquire(blocking=False):
                raise Problem('El modelo está ocupado. Inténtalo más tarde.',429)
            try:
                from .runtime import load_model,translate
                if model['loaded'] is None:
                    import torch
                    torch.set_num_threads(4)
                    model['loaded']=load_model(ROOT/'models/base',adapter,'auto')
                retrieved=archive.context(value)
                context_in_prompt=body.get('rag',False) is True
                output=translate(*model['loaded'],value,context=retrieved if context_in_prompt else None,max_new_tokens=128)
                result=dict(status='proposal',method='local_model',segments=[dict(text=output['text'],record_ids=[])],
                            note='Borrador pendiente de revisión lingüística. Los pasajes recuperados aportan contexto, no certifican la traducción.',model=capability['name'],seconds=output['seconds'],truncated=output['truncated'],context_in_prompt=context_in_prompt)
            except Exception:
                raise Problem('No se pudo ejecutar el modelo local. Revisa sus dependencias y pesos; la consulta del corpus funciona.',503) from None
            finally:model_lock.release()
        if result['method']=='local_model':
            words=fold(' '.join(s['text'] for s in result['segments'])).strip('. ').split()
            repeated=len(words)>=4 and len(words)%2==0 and words[:len(words)//2]==words[len(words)//2:]
            result['quality_issues']=(['repeated_phrase'] if repeated else [])+(['length_limit'] if result.get('truncated') else [])
            if result['quality_issues']:result['note']+=' Se detectó repetición o un límite de longitud; la salida requiere corrección.'
        cited_ids={i for s in result['segments'] for i in s['record_ids']}
        evidence=[r for r in store.public_records().values() if r['id'] in cited_ids]
        draft=dict(input=value,text=''.join(s['text'] for s in result['segments']),related_passages=evidence+retrieved)
        result['context_passages']=retrieved
        result.update(review_request=request_bundle(draft),review=local_review(draft))
        return request.reply(result)

    for path,function in [
            ('/aportar',contribute_page),('/aportar/',contribute_page),
            ('/api/corpus',corpus),('/api/documentary',documentary_search),
            ('/api/pictography',lambda r:r.reply(public_catalog(store.public_records()))),
            ('/api/word',word),('/api/ask',ask),('/api/explain',explanation),('/api/gloss',gloss),
            ('/api/system',lambda r:r.reply(dict(model=capability,archive=archive.summary))),
            ('/api/laboratory',lambda r:r.reply(laboratory_snapshot(capability,adapter))),
            ('/api/laboratory/visual-preparation',visual_preparation),('/api/laboratory/context',laboratory_context),
            ('/api/training-data',training_search),
            ('/api/training-pairs',lambda r:r.reply(pair_proposals.mine(r.get_person(True)))),
            ('/api/training-pairs/export',lambda r:r.reply(pair_proposals.export(r.get_person(True)).encode(),mime='text/csv; charset=utf-8')),
            ('/api/learning',lambda r:r.reply(learning.catalog(store.public_records()))),
            ('/api/research',research),
            ('/archive.csv',lambda r:r.reply(archive.path.read_bytes(),mime='text/csv; charset=utf-8')),
            ('/api/task',task),('/api/search',search),
            ('/api/corpus/export',lambda r:r.reply(store.export_data())),
            ('/api/proposals',lambda r:r.reply(store.proposals(r.get_person(True))))]:
        router.add('GET',path,function)
    router.add('GET','/api/laboratory/reports/',laboratory_report,prefix=True)
    router.add('GET','/api/research/',lambda r:r.reply(archive.get(r.tail)),prefix=True)
    router.add('POST','/api/proposals',lambda r:r.reply(store.propose(r.get_person(True),r.body()),201))
    router.add('POST','/api/training-pairs',lambda r:r.reply(pair_proposals.propose(r.get_person(True),r.body()),201))
    router.add('POST','/api/compose',compose)
    router.add('DELETE','/api/proposals/',withdraw_proposal,prefix=True)
    router.add('DELETE','/api/training-pairs/',withdraw_pair,prefix=True)
    return handler(store,router,STATIC)


def make_server(store,host='127.0.0.1',port=8766,public_origin=None,model_enabled=None,adapter=None,prewarm=False,explain_model=None):
    word_study=WordStudy(records_fn=store.public_records)
    if prewarm:
        # El primer arranque estima frecuencias y pistas (~1 min); después se usa data/derived/.
        threading.Thread(target=word_study.warm,daemon=True,name='word-study-warmup').start()
    # Claude solo redacta si se pide al arrancar: la explicación envía la pregunta y los pasajes citados a Anthropic.
    writer=ClaudeWriter() if explain_model=='claude' else None
    return Server((host,port),make_app(store,model_enabled,adapter,word_study,writer),public_origin)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--db',type=Path,default=DEFAULT_DB)
    sub=p.add_subparsers(dest='command',required=True)
    serve=sub.add_parser('serve',help='Sirve la aplicación, Voces (/aportar) y la API en un solo proceso.')
    serve.add_argument('--host',default='127.0.0.1',help='Interfaz de escucha (por omisión solo este equipo).')
    serve.add_argument('--port',type=int,default=8766)
    serve.add_argument('--public-origin',help='Origen HTTPS de un proxy (https://dominio); se acepta como Host y como Origin de escritura.')
    serve.add_argument('--enable-model',action='store_true',default=None,help='Comportamiento por omisión: ofrece el modelo local si base, adaptador y dependencias están instalados.')
    serve.add_argument('--disable-model',action='store_true',help='No ofrece generación con el modelo local aunque esté instalado.')
    serve.add_argument('--adapter',default=str(ROOT/'outputs/continued-unseen/run/best'),help='Adaptador LoRA del modelo local.')
    serve.add_argument('--explain-model',choices=['claude'],help='Activa explicaciones redactadas por Claude (envía la pregunta y los pasajes citados a la API de Anthropic).')
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
