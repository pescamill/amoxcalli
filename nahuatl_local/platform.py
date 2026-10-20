"""Amoxcalli: la aplicación local (corpus, aprendizaje, investigación y Voces) en un solo servidor."""
import argparse
import hashlib
import json
import threading
from pathlib import Path
from .community import ASSETS as COMMUNITY_WEB, Problem, ROOT, DEFAULT_DB, text, routes as community_routes
from .corpus import CorpusStore
from .research import Archive
from .learning import Learning
from .pictography import public_catalog
from .cards import Cards, digest as records_digest, public_path
from .stems import WordStudy
from .evidence import Evidence
from .topics import TopicIndex
from .terms import TermIndex
from .spelling import Search as SpellingSearch, routes as spelling_routes
from .entities import routes as entity_routes
from .units import Units
from .explain import ClaudeWriter, explain
from .web import Router, Server, Static, handler

WEB = Path(__file__).with_name('platform_web')
# La página principal usa /corpus.js (su app.js) y /amoxcalli.css; /app.js, /style.css y /favicon.svg son de Voces.
STATIC = Static(WEB, {'/': WEB/'index.html', '/corpus.js': WEB/'app.js',
                      '/app.js': COMMUNITY_WEB/'app.js', '/style.css': COMMUNITY_WEB/'style.css',
                      '/favicon.svg': COMMUNITY_WEB/'favicon.svg',
                      '/project/purpose.md': ROOT/'docs/PROPOSITO.md', '/project/pilot.md': ROOT/'docs/PILOTO_INSTITUCIONAL.md',
                      '/project/contributing.md': ROOT/'CONTRIBUTING.md'})
INSTALL_HEAD = '<meta name="theme-color" content="#812d37"><meta name="apple-mobile-web-app-capable" content="yes">\n<link rel="manifest" href="/manifest.webmanifest"><link rel="apple-touch-icon" href="/icon-192.png"><script src="/install.js" defer></script>\n'


def make_app(store, word_study=None, explain_writer=None):
    """Tabla de rutas de la aplicación: corpus, investigación y Voces."""
    router=Router()
    community_routes(router,store)
    archive=Archive()
    # Análisis morfológico, concordancia por raíz y pistas de glosa (sin modelo).
    word_study=word_study or WordStudy(records_fn=store.public_records)
    # Una sola búsqueda de términos para Diccionario, Archivo y Preguntar (también elige sus fichas).
    terms=TermIndex(word_study,records_fn=store.public_records)
    evidence_index=Evidence(word_study,terms=terms)
    # Grafías: escribir como uno escribe y ver las posibilidades con sus fuentes (sobre el índice de términos).
    spellings=SpellingSearch(terms)
    # Preguntar por tema: lecturas, fichas, unidades, notas y obras relacionadas con una frase (sin modelo).
    topics=TopicIndex(terms)
    learning=Learning(archive)
    # Unidades de gramática: borradores generados, validados contra el análisis y con su estado en la cola editorial.
    units=Units(terms,store.public_records)
    # Fichas de Preguntar (campos citados con su procedencia); se reconstruyen si cambian registros o fuentes.
    cards_cache=dict(value=None,lock=threading.Lock())

    def contribute_page(request):
        # Misma sesión, mismos datos y mismos permisos que el corpus.
        page=(COMMUNITY_WEB/'index.html').read_text()
        return request.reply(page.replace('</head>',INSTALL_HEAD+'<link rel="stylesheet" href="/amoxcalli.css"></head>').encode(),mime='text/html; charset=utf-8')

    def corpus(request):
        data=store.catalog_data();data.update(archive=archive.summary)
        return request.reply(data)

    def cards(request):
        """Fichas de una consulta de Preguntar: IDs que contiene y registros de su grupo de término."""
        value=text(request.arg('q'),'Consulta',1000)
        with cards_cache['lock']:
            records=store.public_records();signature=records_digest(records);cache=cards_cache['value']
            stale=cache is None or cache['signature']!=signature
            if not stale:
                stale=any(hashlib.sha256(public_path(ROOT,p).read_bytes()).hexdigest()!=h for p,h in cache['index'].sources.hashes.items())
            if stale:
                cache=cards_cache['value']=dict(signature=signature,index=Cards(records))
            index=cache['index']
        try:return request.reply(index.lookup(value,terms))
        except ValueError as error:raise Problem(str(error)) from None

    def terms_search(request):
        try:return request.reply(terms.search(request.arg('q'),limit=int(request.arg('limit',5))))
        except ValueError as error:raise Problem(str(error)) from None

    def word(request):
        try:return request.reply(word_study.word(request.arg('w'),request.arg('exclude') or None))
        except ValueError as error:raise Problem(str(error)) from None

    def ask(request):
        query=request.arg('q')
        try:result=evidence_index.ask(query)
        except ValueError:
            # Una frase o una pregunta («dioses de la lluvia», «¿quién fue Quetzalcóatl?»): búsqueda por tema.
            try:return request.reply(dict(topics.search(query),preparing=word_study.pending()))
            except ValueError as error:raise Problem(str(error)) from None
        # Una sola palabra: su respuesta de siempre y, además, las lecturas, fichas y obras donde aparece como tema.
        try:
            topic=topics.search(query)
            related=None if topic['abstained'] else dict(interpreted=topic['interpreted'],
                groups=[g for g in topic['groups'] if g['id'] not in ('passages','senses')])
        except ValueError:related=None
        return request.reply(dict(result,explanation=explain(result),explain_models=['extractive']+(['claude'] if explain_writer else []),
                                  preparing=word_study.pending(),related=related))

    def preparation():
        # Etapas del arranque en frío: la interfaz muestra «Preparando el análisis…» con este avance.
        status=word_study.status()
        stages=status['stages'][:2]+[dict(id='terms',label='Índice de términos',state='ready' if terms._ready else 'building' if status['ready'] else 'pending',seconds=None)]+status['stages'][2:]
        return dict(status,stages=stages,done=sum(s['state']=='ready' for s in stages),total=len(stages),
                    complete=all(s['state']=='ready' for s in stages),ready=status['ready'] and terms._ready)

    def explanation(request):
        model_name=request.arg('model','extractive')
        if model_name not in ('extractive','claude'):raise Problem('Modelo de explicación desconocido.')
        if model_name=='claude' and not explain_writer:raise Problem('La explicación con Claude no está activada en este servidor (--explain-model claude).')
        try:result=evidence_index.ask(request.arg('q'))
        except ValueError as error:raise Problem(str(error)) from None
        return request.reply(explain(result,explain_writer if model_name=='claude' else None))

    def unit_examples(request):
        try:return request.reply(units.examples(request.arg('sense')))
        except KeyError:raise Problem('Acepción no encontrada.',404) from None

    def gloss(request):
        rid=request.arg('id')
        source=archive.get(rid)['nah'] if rid else request.arg('text')
        try:return request.reply(dict(word_study.gloss(source),archive_id=rid or None))
        except ValueError as error:raise Problem(str(error)) from None

    def research(request):
        return request.reply(archive.search(**{k:request.arg(k) for k in ('query','variant','document','period')},offset=request.arg('offset',0),limit=request.arg('limit',20),terms=terms))

    def task(request):
        # Recordar y traducir usan el archivo completo; escuchar y revisar, las aportaciones de Voces.
        mode=request.arg('mode','recognize');person=request.get_person(True)
        source=(lambda *args:archive.task(store,*args)) if mode in ('recognize','translate') else store.task
        return request.reply(source(mode,person,request.arg('after')))

    def withdraw_proposal(request):
        store.withdraw_proposal(request.get_person(True),request.tail)
        return request.reply({'ok':True})

    for path,function in [
            ('/aportar',contribute_page),('/aportar/',contribute_page),
            ('/api/corpus',corpus),('/api/ask/cards',cards),
            ('/api/pictography',lambda r:r.reply(public_catalog(store.public_records()))),
            ('/api/word',word),('/api/ask',ask),('/api/explain',explanation),('/api/gloss',gloss),
            ('/api/system',lambda r:r.reply(dict(archive=archive.summary,preparation=preparation()))),
            ('/api/learning',lambda r:r.reply(learning.catalog(store.public_records()))),
            ('/api/units',lambda r:r.reply(units.catalog())),('/api/units/examples',unit_examples),
            ('/api/research',research),
            ('/archive.csv',lambda r:r.reply(archive.path.read_bytes(),mime='text/csv; charset=utf-8')),
            ('/api/task',task),('/api/terms',terms_search),
            ('/api/corpus/export',lambda r:r.reply(store.export_data())),
            ('/api/proposals',lambda r:r.reply(store.proposals(r.get_person(True))))]:
        router.add('GET',path,function)
    spelling_routes(router,spellings,Problem,person=lambda r:r.get_person(True)['id'])
    # Dioses y calendario: fichas con procedencia, calendario, lecturas y unidad (grafías no reunidas → buscador de grafías).
    entity_routes(router,spellings=spellings)
    router.add('GET','/api/research/',lambda r:r.reply(archive.get(r.tail)),prefix=True)
    router.add('POST','/api/proposals',lambda r:r.reply(store.propose(r.get_person(True),r.body()),201))
    router.add('DELETE','/api/proposals/',withdraw_proposal,prefix=True)
    app=handler(store,router,STATIC)
    # Orden de preparación: lo que pide la primera consulta (palabra, Archivo, Preguntar) antes que las pistas.
    app.warm=lambda:(word_study.core(),terms._build(),spellings._build(),word_study.hints(wait=True),topics._build())
    return app


def make_server(store,host='127.0.0.1',port=8766,public_origin=None,prewarm=False,explain_model=None,demo=False):
    # El servidor no espera las pistas de glosa: responde sin ellas (y lo indica) mientras se estiman.
    word_study=WordStudy(records_fn=store.public_records,wait_for_hints=False)
    # Claude solo redacta si se pide al arrancar: la explicación envía la pregunta y los pasajes citados a Anthropic.
    writer=ClaudeWriter() if explain_model=='claude' else None
    app=make_app(store,word_study,writer)
    if prewarm:
        # Primer arranque: análisis listo en segundos; después se reutiliza data/derived/.
        def warm():
            try:app.warm()
            except Exception:pass  # el arranque no debe fallar por el análisis opcional
        threading.Thread(target=warm,daemon=True,name='analysis-warmup').start()
    return Server((host,port),app,public_origin,demo)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--db',type=Path,default=DEFAULT_DB)
    sub=p.add_subparsers(dest='command',required=True)
    serve=sub.add_parser('serve',help='Sirve la aplicación, Voces (/aportar) y la API en un solo proceso.')
    serve.add_argument('--host',default='127.0.0.1',help='Interfaz de escucha (por omisión solo este equipo).')
    serve.add_argument('--port',type=int,default=8766)
    serve.add_argument('--public-origin',help='Origen HTTPS de un proxy (https://dominio); se acepta como Host y como Origin de escritura.')
    serve.add_argument('--open',action='store_true',help='Abre la aplicación en el navegador al arrancar (lo usan los lanzadores de doble clic).')
    serve.add_argument('--demo',action='store_true',help='Demostración pública de solo lectura: rechaza aportaciones, perfiles y grabaciones.')
    # El modelo local se archivó (experiments/llm/); estas opciones se aceptan y no hacen nada, para no romper arranques guardados.
    for retired in ('--enable-model','--disable-model'):serve.add_argument(retired,action='store_true',help=argparse.SUPPRESS)
    serve.add_argument('--adapter',help=argparse.SUPPRESS)
    serve.add_argument('--explain-model',choices=['claude'],help='Activa explicaciones redactadas por Claude (envía la pregunta y los pasajes citados a la API de Anthropic).')
    imp=sub.add_parser('import');imp.add_argument('path');imp.add_argument('--reviewer',required=True);imp.add_argument('--reason',required=True)
    sub.add_parser('queue')
    review=sub.add_parser('review');review.add_argument('id');review.add_argument('--decision',choices=['accepted','rejected'],required=True);review.add_argument('--reviewer',required=True);review.add_argument('--reason',required=True);review.add_argument('--primary-checked',action='store_true');review.add_argument('--rights-checked',action='store_true')
    export=sub.add_parser('export');export.add_argument('--purpose',choices=['research','training'],default='research');export.add_argument('--period',choices=['historical','modern'],default='');export.add_argument('--output',required=True)
    args=p.parse_args()
    try:
        store=CorpusStore(args.db)
        if args.command=='serve':
            httpd=make_server(store,args.host,args.port,args.public_origin,prewarm=True,explain_model=args.explain_model,demo=args.demo)
            url=f'http://127.0.0.1:{httpd.server_address[1]}'
            print(f'Amoxcalli · {url} · Voces en /aportar',flush=True)
            if args.open:
                import webbrowser
                threading.Timer(0.5,webbrowser.open,args=(url,)).start()
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
