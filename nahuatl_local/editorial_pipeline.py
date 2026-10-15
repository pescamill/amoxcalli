"""Batch editorial preparation: cached sources → candidates → explicit review → bundle.

No model calls, source rewriting, live imports or training. Generated candidates
remain drafts; exact matching never certifies a meaning or a glyph reading.
"""
import argparse
from collections import Counter, defaultdict
import copy
import hashlib
import json
from pathlib import Path
import re
import ssl
import tempfile
from urllib.parse import urlencode
from urllib.request import urlopen

from .community import ROOT
from .corpus import CorpusStore
from .passages import AXOLOTL
from .text import fold
from .dictionary_import import parse_page, bundle_from_pages
from .glyph_linker import build_bundle
from .learning import Learning
from .lesson_audit import audit, fingerprint, merge_decisions, render_markdown
from .lexicon_candidates import mine_candidates, written_tokens
from .research import Archive


def encoded(value):
    return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()


def sha(raw):return hashlib.sha256(raw).hexdigest()


def source_pages(config,fetch=False):
    """One cached request per prefix; failures stop the batch before output."""
    pages=[];metadata=[];requests=0
    prefixes=config.get('gdn_prefixes',[])
    size=config.get('per_prefix',100)
    if size not in (50,100,500,1000,1500) or len(prefixes)>24 or len(set(prefixes))!=len(prefixes):
        raise ValueError('Usa hasta 24 prefijos distintos y un tamaño GDN admitido.')
    context=None
    cache=ROOT/'data/dictionary-cache'
    for prefix in prefixes:
        if not isinstance(prefix,str) or not re.fullmatch(r'[a-z]{1,4}',prefix):
            raise ValueError('Prefijo GDN inválido.')
        url='https://gdn.iib.unam.mx/termino/search?'+urlencode(dict(action='search',queryBuscarEn='nahuatlGrafiaNormalizada',queryCreiterio=prefix,**{'queryEnDiccionarios[]':'Molina_2'},queryPartePalabra='inicio',queryLimiteRegistros=size))
        path=cache/f'molina2-{prefix}-{size}.html'
        if not path.exists():
            if not fetch:
                metadata.append(dict(prefix=prefix,url=url,state='missing_cache',records=0));continue
            if context is None:
                import certifi
                context=ssl.create_default_context(cafile=certifi.where())
            with urlopen(url,context=context,timeout=25) as response:
                requests+=1
                if response.geturl().split('/')[2]!='gdn.iib.unam.mx':raise ValueError('Redirección fuera de GDN.')
                raw=response.read(5_000_001)
            if len(raw)>5_000_000:raise ValueError('Página GDN demasiado grande.')
        else:raw=path.read_bytes()
        try:entries=parse_page(raw)
        except ValueError:
            if b'mydata' in raw or not re.search(rb'<article class="terminos">\s*No se han encontrado registros\s*</article>',raw):raise
            entries=[]
        if not path.exists():
            cache.mkdir(parents=True,exist_ok=True)
            path.write_bytes(raw)
        metadata.append(dict(prefix=prefix,url=url,state='cached',sha256=sha(raw),records=len(entries),possibly_capped=len(entries)>=size))
        if entries:pages.append((raw,url))
    return pages,metadata,requests


def public_catalog(path=None):
    # Only a temporary store; never initializes or opens the user database.
    with tempfile.TemporaryDirectory() as directory:
        store=CorpusStore(Path(directory)/'catalog.sqlite3')
        if path is None:return store.public_records()
        bundle=json.loads(Path(path).read_text())
        if bundle.get('schema_version')!=1 or not isinstance(bundle.get('records'),list):raise ValueError('Catálogo research inválido.')
        records={r['id']:r for r in bundle['records']}
        if len(records)!=len(bundle['records']):raise ValueError('IDs duplicados en el catálogo.')
        for r in records.values():
            store.validate(r,records)
            if not r['rights']['public'] or r.get('withdrawn'):raise ValueError('El pipeline necesita un catálogo público, sin datos privados o retirados.')
        return records


def annotation_candidates(learning,records):
    forms=defaultdict(set)
    for r in records.values():
        if r['kind']=='form':forms[fold(r['written'])].add(r['sense_id'])
    result=[]
    for lesson in learning.data['lessons']:
        for example in lesson['examples']:
            row=learning.archive.get(example['archive_id'])
            for word,start,end in written_tokens(row['nah']):
                if any(a['start']<=len(row['nah'][:start].encode('utf-16-le'))//2<a['end'] for a in example['annotations']):continue
                result.append(dict(lesson_id=lesson['id'],archive_id=row['id'],source_hash=example['source_hash'],written=word,start=start,end=end,index_units='unicode_code_points',candidate_sense_ids=sorted(forms[fold(word)]),status='ambiguous_match' if len(forms[fold(word)])>1 else 'exact_form_candidate' if forms[fold(word)] else 'unmatched_source_form'))
    return result


def review_items(lexical,visual):
    items=[]
    for sense in (r for r in lexical['records'] if r['kind']=='sense'):
        records=[sense]+[r for r in lexical['records'] if r.get('sense_id')==sense['id']]
        items.append(dict(id='lexical-'+sense['id'],kind='catalog_transcription',records=records,scope='Transcripción de catálogo; no asigna el significado a un pasaje ni certifica análisis lingüístico.'))
    for record in visual['records']:
        items.append(dict(id='visual-'+record['id'],kind='contextual_visual',records=[record],scope='Apoyo contextual explícito; no equivale a escribir la palabra completa.'))
    for item in items:item['fingerprint']=fingerprint(item)
    return items


def review_groups(items):
    groups=[]
    for kind in ('catalog_transcription','contextual_visual'):
        selected=[item for item in items if item['kind']==kind]
        if not selected:continue
        group=dict(id='group-'+kind,kind=kind,item_fingerprints={item['id']:item['fingerprint'] for item in selected},
                   scope='Decisión compartida del lote; overrides por item para rechazos o excepciones. No acredita cotejo primario ni asigna una acepción a todos los pasajes.')
        group['fingerprint']=fingerprint(group);groups.append(group)
    return groups


def lexical_priorities(forms,occurrences,lesson_forms):
    priorities=[]
    for sid,form in forms.items():
        written=fold(form['written']);head=fold(form['catalog_normalized'])
        priorities.append(dict(sense_id=sid,written=form['written'],normalized=form['catalog_normalized'],
            in_current_lessons=written in lesson_forms,exact_corpus_occurrences=occurrences[written],
            catalog_head_occurrences=occurrences[head],catalog_head_differs=written!=head))
    priorities.sort(key=lambda item:(not item['in_current_lessons'],-item['exact_corpus_occurrences'],fold(item['written']),item['sense_id']))
    return priorities


def validate_candidates(records,base):
    ids=[r['id'] for r in records]
    if len(ids)!=len(set(ids)) or set(ids)&set(base):raise ValueError('El lote de candidatos solo puede añadir IDs nuevos y únicos.')
    merged={**base,**{r['id']:r for r in records}}
    with tempfile.TemporaryDirectory() as directory:
        store=CorpusStore(Path(directory)/'validation.sqlite3')
        for r in records:
            store.validate(r,merged)
            if r['rights']['training'] or not r['rights']['public'] or r['verification']=='reviewed' or r.get('glyph_status')=='documented_context':
                raise ValueError('Un candidato no concede entrenamiento ni revisión primaria/lingüística.')
    return merged


def write_batch(output,files):
    output=Path(output).resolve()
    # Generated batches have a separate home; never overwrite corpus or models.
    if not any(output.is_relative_to(ROOT/directory) and output!=ROOT/directory for directory in ('reports','editorial')):
        raise ValueError('Guarda el lote en una subcarpeta de reports/ o editorial/.')
    contents={name:encoded(value) if not isinstance(value,str) else value.encode() for name,value in files.items()}
    manifest=json.loads(contents['manifest.json'])
    manifest['files']={name:sha(raw) for name,raw in contents.items() if name!='manifest.json'}
    contents['manifest.json']=encoded(manifest)
    if output.exists():
        previous=json.loads((output/'manifest.json').read_text()) if (output/'manifest.json').is_file() else {}
        same_manifest={k:v for k,v in previous.items() if k!='first_run'}=={k:v for k,v in manifest.items() if k!='first_run'}
        if same_manifest and all((output/name).is_file() and (output/name).read_bytes()==raw for name,raw in contents.items() if name!='manifest.json'):return 'unchanged'
        raise ValueError('El lote ya existe con otro contenido. Usa una carpeta nueva; no se sobrescriben decisiones o borradores.')
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent,prefix='.editorial-writing-') as directory:
        staging=Path(directory)/'batch';staging.mkdir()
        for name,raw in contents.items():(staging/name).write_bytes(raw)
        staging.rename(output)
    return 'prepared'


def prepare(config_path,lessons_path,output,catalog_path=None,fetch=False,decisions_path=ROOT/'editorial/lesson-decisions.json'):
    config_raw=Path(config_path).read_bytes();config=json.loads(config_raw)
    if config.get('schema_version')!=1:raise ValueError('Configuración de pipeline inválida.')
    limit=config.get('lexical_limit',50);concordance_limit=config.get('concordance_limit',100)
    if type(limit) is not int or not 1<=limit<=200 or type(concordance_limit) is not int or not 1<=concordance_limit<=100:
        raise ValueError('Límite léxico 1–200, concordancias 1–100.')
    records=public_catalog(catalog_path);archive=Archive();learning=Learning(archive,Path(lessons_path))
    # Validates chosen glyph references even though missing draft dependencies are audited separately.
    learning.catalog(records)
    report=audit(learning,records)
    stored=json.loads(Path(decisions_path).read_text())
    if stored.get('schema_version')!=1 or not isinstance(stored.get('decisions'),dict):raise ValueError('Decisiones editoriales inválidas.')
    queue=merge_decisions(report['findings'],stored['decisions'])
    pages,sources,requests=source_pages(config,fetch)
    excluded={fold(r.get('catalog_normalized',r['written'])) for r in records.values() if r['kind']=='form'}
    excluded.update(fold(r['written']) for r in records.values() if r['kind']=='form')
    lexical,extraction=bundle_from_pages(pages,excluded,4000)
    forms={r['sense_id']:r for r in lexical['records'] if r['kind']=='form'}
    occurrences=Counter(fold(word) for row in archive.rows if row['iso']=='nci' for word,_,_ in written_tokens(row['nah']))
    lesson_forms={fold(word) for lesson in learning.data['lessons'] for e in lesson['examples'] for word,_,_ in written_tokens(archive.get(e['archive_id'])['nah'])}
    priorities=lexical_priorities(forms,occurrences,lesson_forms)
    chosen={item['sense_id'] for item in priorities[:limit]}
    lexical['records']=[r for r in lexical['records'] if r.get('sense_id',r['id']) in chosen]
    extraction['eligible_before_batch_limit']=len(priorities)
    extraction['deferred_by_batch_limit']=max(0,len(priorities)-limit)
    extraction['entries']=len(chosen)
    merged=validate_candidates(lexical['records'],records)
    rules=json.loads((ROOT/'corpus/glyph-link-rules-v7.json').read_text())
    visual,coverage=build_bundle(merged,rules,archive.rows)
    visual['records']=[r for r in visual['records'] if r['id'] not in merged]
    validate_candidates(lexical['records']+visual['records'],records)
    with tempfile.TemporaryDirectory() as directory:
        seed=Path(directory)/'public-catalog.json';seed.write_bytes(encoded(dict(schema_version=1,records=list(records.values()))))
        concordance=mine_candidates(ROOT/AXOLOTL,seed_path=seed,limit=concordance_limit)
    concordance['seed_exclusions']['path']='selected_public_catalog';concordance['seed_exclusions']['sha256']=sha(encoded(records))
    items=review_items(lexical,visual);groups=review_groups(items)
    # Prefixes organize source requests; they are not inferred roots or lemmas.
    next_prefixes=[]
    for candidate in concordance['candidates']:
        key=candidate['comparison_form'][:2]
        if re.fullmatch(r'[a-z]{2}',key) and key not in next_prefixes:next_prefixes.append(key)
        if len(next_prefixes)==8:break
    next_config=dict(schema_version=1,gdn_prefixes=next_prefixes,per_prefix=500,lexical_limit=limit,concordance_limit=concordance_limit)
    if extraction['deferred_by_batch_limit']:
        next_config=dict(config)
    summary=dict(lessons=report['lessons'],examples=report['examples'],catalog_records=len(records),source_pages=len(sources),cached_pages=sum(s['state']=='cached' for s in sources),missing_cache=sum(s['state']=='missing_cache' for s in sources),possibly_capped_pages=sum(s.get('possibly_capped',False) for s in sources),lexical_entries=extraction['entries'],visual_candidates=len(visual['records']),concordance_candidates=len(concordance['candidates']),review_items=len(items),lesson_tasks=len(queue),lesson_task_states=dict(Counter(t['status'] for t in queue)),llm_calls=0)
    draft=dict(schema_version=1,records=lexical['records']+visual['records'])
    md=['# Editorial batch','','Prepared candidates; source text and live catalogue remain unchanged.','','```json',json.dumps(summary,ensure_ascii=False,indent=2),'```','','## Review once and reuse','','| Item | Type | Records | Scope |','|---|---|---:|---|']
    for item in items:md.append(f"| {item['id']} | {item['kind']} | {len(item['records'])} | {item['scope']} |")
    md+=['','## Exceptions and next source pass','','Missing cache and capped prefix pages appear in sources.json. A capped page does not establish source exhaustiveness. next-source-config.json groups up to eight prefix requests, drawn from frequent unmatched forms; prefixes are search partitions, not inferred roots. Unmatched tokens and exact/ambiguous form candidates appear in annotation-candidates.json; none is applied automatically. Concordances preserve evaluation reservations and empty meanings.','','Review-groups.json allows one source/scope decision per group, with individual exceptions in items. Record accepted/rejected/deferred decisions in the separate editorial/pipeline-decisions.json. Acceptance needs matching fingerprint, reviewer, date, evidence and a scope-limited resolution. Assemble produces a validated append-only bundle; it does not import it or train the model.','']
    files={'manifest.json':dict(schema_version=1,pipeline_version=1,inputs=dict(config_sha256=sha(config_raw),lessons_sha256=sha(Path(lessons_path).read_bytes()),catalog_sha256=sha(encoded(records)),decisions_sha256=sha(Path(decisions_path).read_bytes()),corpus_sha256=concordance['source']['sha256'],glyph_rules_sha256=sha((ROOT/'corpus/glyph-link-rules-v7.json').read_bytes())),summary=summary),'catalog-baseline.json':dict(schema_version=1,records=list(records.values())),'lesson-inventory.json':report,'lesson-queue.json':dict(schema_version=1,tasks=queue),'sources.json':dict(schema_version=1,pages=sources,extraction=extraction),'dictionary-candidates.json':lexical,'visual-candidates.json':visual,'concordances.json':concordance,'annotation-candidates.json':dict(schema_version=1,candidates=annotation_candidates(learning,records)),'review-items.json':dict(schema_version=1,items=items),'draft-bundle.json':draft,'README.md':'\n'.join(md),'lesson-inventory.md':render_markdown(report,queue)}
    files['review-groups.json']=dict(schema_version=1,groups=groups)
    files['next-source-config.json']=next_config
    files['lexical-priorities.json']=dict(schema_version=1,candidates=priorities[:limit],deferred=extraction['deferred_by_batch_limit'],scope='Prioridad por grafías completas de las lecciones y frecuencia del corpus; no es una aprobación de acepción o morfología.')
    files['visual-inventory.json']=dict(schema_version=1,current_meanings_with_image=sum(any(g['kind']=='glyph' and g['sense_id']==r['id'] and g.get('image') for g in records.values()) for r in records.values() if r['kind']=='sense'),candidate_coverage=coverage,note='La cobertura de candidatos no cuenta como revisión ni publicación. Los vínculos contextuales no son lecturas documentadas.')
    files['manifest.json']['pipeline_version']=2
    files['manifest.json']['first_run']=dict(network_requests=requests,llm_calls=0)
    for packet in report['packets']:files[packet['id']+'-packet.json']=packet
    state=write_batch(output,files)
    return dict(state=state,output=str(Path(output).resolve()),network_requests=requests,**summary)


def assemble(batch,decisions,output,lessons_path=ROOT/'corpus/learning-v1.json',catalog_path=None):
    batch=Path(batch);manifest=json.loads((batch/'manifest.json').read_text())
    if manifest.get('schema_version')!=1 or manifest.get('pipeline_version')!=2 or not isinstance(manifest.get('files'),dict):raise ValueError('Manifiesto inválido o versión anterior; prepara un lote nuevo.')
    for name,digest in manifest['files'].items():
        if Path(name).name!=name or sha((batch/name).read_bytes())!=digest:raise ValueError('El lote fue modificado; prepara uno nuevo para revisión.')
    records=public_catalog(catalog_path)
    if sha(encoded(records))!=manifest['inputs']['catalog_sha256'] or sha(Path(lessons_path).read_bytes())!=manifest['inputs']['lessons_sha256']:
        raise ValueError('El catálogo o las lecciones cambiaron desde la preparación; prepara un lote nuevo.')
    if sha((ROOT/AXOLOTL).read_bytes())!=manifest['inputs']['corpus_sha256'] or sha((ROOT/'corpus/glyph-link-rules-v7.json').read_bytes())!=manifest['inputs'].get('glyph_rules_sha256'):
        raise ValueError('Cambió el corpus o las reglas glíficas; prepara un lote nuevo.')
    stored=json.loads(Path(decisions).read_text())
    if stored.get('schema_version')!=1 or not isinstance(stored.get('items'),dict):raise ValueError('Decisiones de pipeline inválidas.')
    items=json.loads((batch/'review-items.json').read_text())['items'];known={i['id'] for i in items}
    for item in items:
        if item['fingerprint']!=fingerprint({k:v for k,v in item.items() if k!='fingerprint'}):raise ValueError('Fingerprint de candidato inválido.')
    if set(stored['items'])-known:raise ValueError('Hay decisiones para otro lote; separa sus archivos.')
    group_decisions=stored.get('groups',{})
    groups={g['id']:g for g in json.loads((batch/'review-groups.json').read_text())['groups']}
    if not isinstance(group_decisions,dict) or set(group_decisions)-set(groups):raise ValueError('Grupos de otro lote o formato incorrecto.')
    effective={}
    for gid,decision in group_decisions.items():
        group=groups[gid]
        if group['fingerprint']!=fingerprint({k:v for k,v in group.items() if k!='fingerprint'}) or any(next((item['fingerprint'] for item in items if item['id']==iid),None)!=digest for iid,digest in group['item_fingerprints'].items()):raise ValueError('Fingerprint de grupo inválido.')
        if decision.get('fingerprint')!=group['fingerprint']:raise ValueError('La decisión del grupo tiene evidencia obsoleta.')
        for iid,digest in group['item_fingerprints'].items():
            effective[iid]=dict(decision,fingerprint=digest,group_id=gid)
    effective.update(stored['items'])
    accepted=[];review=[]
    for item in items:
        decision=effective.get(item['id'])
        if not decision:continue
        if decision.get('status') not in ('accepted','rejected','deferred'):raise ValueError('Estado de revisión inválido.')
        if decision.get('fingerprint')!=item['fingerprint']:raise ValueError('La decisión tiene evidencia obsoleta.')
        if decision['status']=='accepted':
            if not all(decision.get(k) for k in ('reviewer','date','evidence','resolution')):raise ValueError('Una aceptación necesita responsable, fecha, evidencia y alcance.')
            accepted.extend(item['records']);review.append(dict(item_id=item['id'],**decision))
    validate_candidates(accepted,records)
    result=dict(schema_version=1,records=accepted,editorial_review=review,batch_manifest_sha256=sha((batch/'manifest.json').read_bytes()),note='Lote añadido tras revisión declarada; no actualiza registros existentes ni concede entrenamiento. Sin importación automática.')
    if not accepted:raise ValueError('No hay candidatos aceptados; no se produce un lote vacío.')
    output=Path(output).resolve()
    if not output.is_relative_to(ROOT/'editorial') or output.suffix!='.json':raise ValueError('Guarda el lote revisado como JSON dentro de editorial/.')
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('xb') as file:file.write(encoded(result))
    return dict(state='assembled',records=len(accepted),output=str(output),imported=False,training=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    prep=sub.add_parser('prepare');prep.add_argument('--config',type=Path,default=ROOT/'configs/editorial-pipeline.json');prep.add_argument('--lessons',type=Path,default=ROOT/'corpus/learning-v1.json');prep.add_argument('--catalog',type=Path);prep.add_argument('--output',type=Path,required=True);prep.add_argument('--fetch',action='store_true');prep.add_argument('--decisions',type=Path,default=ROOT/'editorial/lesson-decisions.json')
    assembly=sub.add_parser('assemble');assembly.add_argument('--batch',type=Path,required=True);assembly.add_argument('--decisions',type=Path,required=True);assembly.add_argument('--output',type=Path,required=True);assembly.add_argument('--lessons',type=Path,default=ROOT/'corpus/learning-v1.json');assembly.add_argument('--catalog',type=Path)
    verification=sub.add_parser('verify');verification.add_argument('--batch',type=Path,required=True);verification.add_argument('--output',type=Path,required=True);verification.add_argument('--date')
    publication=sub.add_parser('publish');publication.add_argument('--batch',type=Path,required=True);publication.add_argument('--bundle',type=Path,required=True);publication.add_argument('--release-id',required=True);publication.add_argument('--db',type=Path,default=ROOT/'data/community/voces.sqlite3')
    publication.add_argument('--lessons',type=Path)
    cycle=sub.add_parser('run');cycle.add_argument('--release-id',required=True);cycle.add_argument('--config',type=Path);cycle.add_argument('--db',type=Path);cycle.add_argument('--fetch',action='store_true');cycle.add_argument('--apply',action='store_true')
    args=vars(parser.parse_args());command=args.pop('command')
    if command=='prepare':args['config_path']=args.pop('config');args['lessons_path']=args.pop('lessons');args['catalog_path']=args.pop('catalog');args['decisions_path']=args.pop('decisions');result=prepare(**args)
    elif command=='assemble':args['lessons_path']=args.pop('lessons');args['catalog_path']=args.pop('catalog');result=assemble(**args)
    elif command=='verify':
        from .editorial_release import verify
        result=verify(**args)
    elif command=='run':
        from .editorial_release import run
        args['config_path']=args.pop('config');args['db_path']=args.pop('db');result=run(**args)
    else:
        from .editorial_release import publish
        args['bundle_path']=args.pop('bundle');args['db_path']=args.pop('db');args['lessons_path']=args.pop('lessons');result=publish(**args)
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
