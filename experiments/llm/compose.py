"""Composición de la antigua ruta POST /api/compose (archivada el 16 oct 2026; la aplicación ya no la sirve).

Reunía tres modos del Laboratorio: reglas léxicas acotadas («Veo una flor» → «Niquitta xochitl.»),
consulta léxica y borrador del LLM local (Qwen3-0.6B + LoRA, con o sin pasajes recuperados en el
mensaje). Se conserva tal como estaba dentro de ``platform.make_app`` para documentar qué se
probó; para volver a usarla hay que registrar ``compose`` en un ``Router`` con ``store``,
``archive``, ``capability``, ``adapter`` y un candado de modelo (ver ``LABORATORIO.md``).
"""
import threading
from nahuatl_local.community import Problem, ROOT, text
from nahuatl_local.text import fold
from .review import request_bundle, local_review


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


def make_compose(store, archive, capability, adapter):
    """Devuelve el manejador HTTP histórico de /api/compose."""
    model_lock=threading.Lock()
    model=dict(loaded=None)

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

    return compose
