"""Literal source checks and append-only publication of editorial batches.

The automated review accepts catalogue transcriptions and explicit contextual
references only. It never certifies a linguistic analysis or primary reading.
"""
from collections import Counter
from datetime import datetime
from contextlib import closing
import fcntl
import json
from pathlib import Path
import re
import sqlite3
import tempfile
from urllib.parse import parse_qs, urlparse
from zoneinfo import ZoneInfo

from .community import ROOT
from .corpus import CorpusStore, editorial_releases, normalize
from .dictionary_import import parse_page
from .editorial_pipeline import encoded, sha, validate_candidates
from .glyph_linker import tokens
from .lesson_audit import fingerprint
from .research import Archive


def load_batch(batch):
    batch=Path(batch);manifest=json.loads((batch/'manifest.json').read_text())
    if manifest.get('pipeline_version')!=2 or manifest.get('schema_version')!=1:raise ValueError('Versión de lote no admitida.')
    for name,digest in manifest['files'].items():
        if Path(name).name!=name or sha((batch/name).read_bytes())!=digest:raise ValueError('Lote alterado; generar una versión nueva.')
    items=json.loads((batch/'review-items.json').read_text())['items']
    for item in items:
        if item['fingerprint']!=fingerprint({k:v for k,v in item.items() if k!='fingerprint'}):raise ValueError('Fingerprint de candidato inválido.')
    groups=json.loads((batch/'review-groups.json').read_text())['groups']
    index={i['id']:i for i in items}
    for g in groups:
        if g['fingerprint']!=fingerprint({k:v for k,v in g.items() if k!='fingerprint'}) or any(index.get(iid,{}).get('fingerprint')!=digest for iid,digest in g['item_fingerprints'].items()):raise ValueError('Grupo de revisión inválido.')
    baseline=json.loads((batch/'catalog-baseline.json').read_text())['records']
    return manifest,items,groups,{r['id']:r for r in baseline}


def write_once(path,value):
    path=Path(path);raw=encoded(value)
    if path.exists():
        if path.read_bytes()!=raw:raise ValueError('La salida ya existe con otro contenido; usa una versión nueva.')
        return 'unchanged'
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as file:file.write(raw)
    return 'created'


def verify(batch,output,date=None):
    output=Path(output).resolve()
    if not output.is_relative_to(ROOT/'editorial') or output.suffix!='.json':raise ValueError('Guarda el cotejo como JSON dentro de editorial/.')
    if output.exists() and date is None:
        previous=json.loads(output.read_text())
        date=next((g['date'] for g in previous.get('groups',{}).values()),None)
    manifest,items,groups,baseline=load_batch(batch)
    source_pages=json.loads((Path(batch)/'sources.json').read_text())['pages']
    source_index={};page_errors={}
    for page in source_pages:
        if page.get('state')!='cached':continue
        url=page['url'];params=parse_qs(urlparse(url).query)
        prefix=params.get('queryCreiterio',[''])[0];size=params.get('queryLimiteRegistros',[''])[0]
        if urlparse(url).hostname!='gdn.iib.unam.mx' or not re.fullmatch(r'[a-z]{1,4}',prefix) or size not in ('50','100','500','1000','1500'):
            raise ValueError('Referencia de caché no admitida.')
        path=ROOT/'data/dictionary-cache'/f'molina2-{prefix}-{size}.html'
        if not path.exists():page_errors[url]='missing_cache';continue
        raw=path.read_bytes()
        if sha(raw)!=page.get('sha256'):page_errors[url]='changed_cache';continue
        if page['records']:
            for row in parse_page(raw):source_index[(url,row['pk'])]=(row,sha(raw))
    available={**baseline,**{r['id']:r for item in items for r in item['records']}}
    archive=Archive();checks=[]
    for item in items:
        errors=[];proof=[]
        if item['kind']=='catalog_transcription':
            if len(item['records'])!=2:errors.append('unexpected_record_count')
            else:
                sense=next(r for r in item['records'] if r['kind']=='sense');form=next(r for r in item['records'] if r['kind']=='form')
                origin=form.get('source_entry',{});key=(origin.get('query_url'),origin.get('id'));found=source_index.get(key)
                if found is None:errors.append(page_errors.get(origin.get('query_url'),'source_entry_not_found'))
                else:
                    row,digest=found
                    if (row['fuente']!='1571 Molina 2' or form['written']!=row['paleografia'] or form['catalog_normalized']!=row['grafiaNormalizada'] or sense['definition']!=row['traduccion'] or sense['label']!=row['traduccion'] or origin.get('sha256')!=digest or form['sense_id']!=sense['id']):errors.append('source_transcription_mismatch')
                    proof.append(dict(source_entry=row['pk'],query_url=key[0],sha256=digest,checks=['written','catalog_normalized','historical_gloss','sense_id']))
        elif item['kind']=='contextual_visual':
            g=item['records'][0];a=g.get('association',{});form=available.get(a.get('reference_form_id'));reference=baseline.get(a.get('reference_glyph_id'))
            if not form or not reference or form.get('sense_id')!=g['sense_id']:errors.append('missing_reference')
            else:
                for field in ('image','image_credit','url','reading','glyph_type'):
                    if g.get(field)!=reference.get(field):errors.append('changed_reference_'+field)
                if not reference.get('image'):errors.append('reference_has_no_image')
                if a.get('type')=='passage_reference':
                    p=a['passage'];row=archive.get(p['id'])
                    if any(p.get(key)!=row.get(key) for key in ('nah','es','iso','line','document')) or p['sha256']!=sha((row['nah']+'\n'+row['es']).encode()):errors.append('changed_passage')
                    if row['iso']!='nci' or normalize(form['written']) not in tokens(row['nah']) or normalize(reference['reading']) not in tokens(row['nah']) or a.get('matched_term') not in tokens(row['es']):errors.append('unsubstantiated_cooccurrence')
                    proof.append(dict(archive_id=row['id'],source_hash=p['sha256'],checks=['original_pair','exact_form_token','reference_reading_token','spanish_referent']))
                elif a.get('type')=='definition_reference':
                    definition=available[g['sense_id']]['definition']
                    if a.get('definition_quote')!=definition or a.get('matched_term') not in tokens(definition) or a.get('evidence_url')!=form['url']:errors.append('definition_reference_mismatch')
                    proof.append(dict(form_id=form['id'],checks=['original_definition','referent_token','lexical_source_url']))
                else:errors.append('requires_editorial_interpretation')
                if not a.get('note') or g.get('glyph_status')!='proposed' or g['rights']['training']:errors.append('scope_or_permission_changed')
                proof.append(dict(reference_glyph_id=reference['id'],checks=['same_image','same_reading','same_credit','contextual_scope']))
        else:errors.append('unsupported_review_kind')
        checks.append(dict(item_id=item['id'],fingerprint=item['fingerprint'],status='accepted' if not errors else 'deferred',errors=errors,proof=proof))
    # A visual candidate can only use a new form whose transcription also passed.
    accepted_records={r['id'] for item in items if next(c for c in checks if c['item_id']==item['id'])['status']=='accepted' for r in item['records']}
    for item,check in zip(items,checks):
        if check['status']=='accepted' and any(r.get('association',{}).get('reference_form_id') not in set(baseline)|accepted_records for r in item['records'] if r['kind']=='glyph'):
            check['status']='deferred';check['errors'].append('lexical_dependency_not_accepted')
    stamp=date or datetime.now(ZoneInfo('America/Mexico_City')).date().isoformat()
    decision=lambda digest,status:dict(status=status,fingerprint=digest,reviewer='Script de cotejo literal · editorial_release v1',date=stamp,evidence=[str(Path(batch).resolve()/'sources.json'),str(Path(output).resolve())+'#checks'],resolution='Aceptación limitada a transcripción histórica literal o apoyo contextual verificado por tokens y referencias; cotejo primario y análisis lingüístico pendientes.',review_method='automated_source_comparison')
    grouped={};exceptions={}
    check_by_id={c['item_id']:c for c in checks}
    for group in groups:
        grouped[group['id']]=decision(group['fingerprint'],'accepted')
        for iid in group['item_fingerprints']:
            check=check_by_id[iid]
            if check['status']!='accepted':exceptions[iid]=dict(decision(check['fingerprint'],'deferred'),resolution='; '.join(check['errors']))
    report=dict(schema_version=1,groups=grouped,items=exceptions,checks=checks,batch_manifest_sha256=sha((Path(batch)/'manifest.json').read_bytes()),review_method='automated_source_comparison',primary_review=False,linguistic_certification=False,llm_calls=0,network_requests=0)
    state=write_once(output,report)
    return dict(state=state,output=str(Path(output).resolve()),states=dict(Counter(c['status'] for c in checks)),primary_review=False,llm_calls=0,network_requests=0)


def snapshot(db):
    return {row[0]:[tuple(r) for r in db.execute('SELECT * FROM "'+row[0]+'"').fetchall()] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()}


def publish(batch,bundle_path,release_id,db_path,release_dir=None,lessons_path=None):
    """Serialize publishers; a committed import can finish registration on retry."""
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{1,79}',release_id):raise ValueError('ID de publicación inválido.')
    lock=ROOT/'editorial/.pipeline-publish.lock';lock.parent.mkdir(parents=True,exist_ok=True)
    with lock.open('a') as file:
        fcntl.flock(file,fcntl.LOCK_EX)
        return _publish_locked(batch,bundle_path,release_id,db_path,release_dir,lessons_path)


def _publish_locked(batch,bundle_path,release_id,db_path,release_dir,lessons_path):
    directory=Path(release_dir) if release_dir else ROOT/'corpus';directory.mkdir(parents=True,exist_ok=True)
    manifest_path=directory/'editorial-releases.json';bundle_raw=Path(bundle_path).read_bytes();bundle=json.loads(bundle_raw);digest=sha(bundle_raw)
    existing=editorial_releases(manifest_path)
    prior=next((r for r,b in existing if r['id']==release_id),None)
    marker='editorial-release-'+release_id+'-'+digest[:16]
    if prior:
        if prior['sha256']!=digest:raise ValueError('El ID ya identifica otro contenido; publica una versión nueva.')
        store=CorpusStore(db_path)
        store.import_bundle(bundle,prior['reviewer'],prior['reason'],migration_key=marker)
        return dict(state='already_published',release_id=release_id,records=len(bundle['records']),catalogue_records=len(store.records()))
    manifest,items,groups,baseline=load_batch(batch)
    if bundle.get('batch_manifest_sha256')!=sha((Path(batch)/'manifest.json').read_bytes()):raise ValueError('El lote ensamblado no corresponde a este paquete.')
    inputs=manifest['inputs']
    paths={'corpus_sha256':ROOT/'corpus/axolotl/axolotl.csv','glyph_rules_sha256':ROOT/'corpus/glyph-link-rules-v7.json','lessons_sha256':Path(lessons_path) if lessons_path else ROOT/'corpus/learning-v1.json'}
    if any(sha(path.read_bytes())!=inputs[key] for key,path in paths.items()):raise ValueError('Cambió el corpus, las lecciones o las reglas; prepara un lote nuevo.')
    for page in json.loads((Path(batch)/'sources.json').read_text())['pages']:
        if page.get('state')!='cached' or not page.get('records'):continue
        prefix=page.get('prefix','');size=parse_qs(urlparse(page['url']).query).get('queryLimiteRegistros',[''])[0]
        if not re.fullmatch(r'[a-z]{1,4}',prefix) or size not in ('50','100','500','1000','1500'):raise ValueError('Referencia de caché no admitida.')
        cache=ROOT/'data/dictionary-cache'/f'molina2-{prefix}-{size}.html'
        if not cache.exists() or sha(cache.read_bytes())!=page['sha256']:raise ValueError('Cambió o falta una página de fuente; repetir el cotejo en un lote nuevo.')
    item_index={item['id']:item for item in items};expected=[];reviewed=set()
    for review in bundle.get('editorial_review',[]):
        item=item_index.get(review.get('item_id'))
        if not item or item['id'] in reviewed or review.get('status')!='accepted' or review.get('fingerprint')!=item['fingerprint'] or not all(review.get(k) for k in ('reviewer','date','evidence','resolution')):raise ValueError('Aceptación inexistente, incompleta u obsoleta.')
        reviewed.add(item['id']);expected.extend(item['records'])
    if not expected or encoded(expected)!=encoded(bundle.get('records')):raise ValueError('El JSON ensamblado difiere de los candidatos aceptados.')
    validate_candidates(expected,baseline)
    store=CorpusStore(db_path);current=store.records()
    with store.db() as db:committed=bool(db.execute('SELECT 1 FROM corpus_meta WHERE key=?',(marker,)).fetchone())
    strip=lambda r:{k:v for k,v in r.items() if k!='version'}
    if committed:
        if any(r['id'] not in current or encoded(strip(current[r['id']]))!=encoded(r) for r in expected):raise ValueError('El intento previo cambió; conserva el respaldo y revisa las fichas antes de registrar.')
    elif set(r['id'] for r in expected)&set(current):raise ValueError('Los IDs nuevos ya existen en la base; no se reemplaza ninguna ficha local.')
    deps={ref for r in expected for ref in [r.get('sense_id'),r.get('association',{}).get('reference_form_id'),r.get('association',{}).get('reference_glyph_id'),*(e.get(k) for e in r.get('evidence',[]) for k in ('source_id','via_source_id'))] if ref in baseline}
    for rid in deps:
        if rid not in current or encoded(strip(current[rid]))!=encoded(strip(baseline[rid])):raise ValueError('Cambió una dependencia local de la evidencia: '+rid)
    reviewer='Publicación de lote editorial';reason='Transcripciones históricas y apoyos contextuales aceptados con alcance explícito; sin certificación lingüística ni entrenamiento.'
    release=dict(id=release_id,bundle=f'editorial-{release_id}.json',sha256=digest,reviewer=reviewer,reason=reason)
    backup_dir=ROOT/'data/backups';backup_dir.mkdir(parents=True,exist_ok=True)
    backup=backup_dir/f'voces-before-{release_id}.sqlite3';published=directory/release['bundle']
    if published.exists() and published.read_bytes()!=bundle_raw:raise ValueError('Ya existe otro archivo con ese ID de publicación.')
    if backup.exists():
        with closing(sqlite3.connect(backup)) as db:before=snapshot(db)
        if not committed:
            with store.db() as db:current_snapshot=snapshot(db)
            if before!=current_snapshot:raise ValueError('La base cambió desde el intento previo; conserva el respaldo y usa una versión nueva.')
    else:
        if committed:raise ValueError('Falta el respaldo del intento previo; detener registro.')
        with closing(sqlite3.connect(db_path)) as src,closing(sqlite3.connect(backup)) as dest:src.backup(dest)
        backup.chmod(0o600)
        with closing(sqlite3.connect(backup)) as db:before=snapshot(db)
    if not published.exists():
        with published.open('xb') as file:file.write(bundle_raw)
    added=store.import_bundle(bundle,reviewer,reason,migration_key=marker)
    with store.db() as db:after=snapshot(db)
    preserved={table:set(rows).issubset(set(after.get(table,[]))) if table.startswith('corpus_') else rows==after.get(table,[]) for table,rows in before.items()}
    if not all(preserved.values()):raise RuntimeError('La comprobación de preservación falló; conservar respaldo y detener publicación.')
    report=dict(schema_version=1,release_id=release_id,state='published',added_records=len(expected) if committed else added,existing_records_preserved=len(before['corpus_records']),tables_preserved=preserved,backup=str(backup),bundle=release['bundle'],sha256=digest,training_changed=False,linguistic_certification=False)
    proof=ROOT/'reports'/f'publication-{release_id}.json';write_once(proof,report)
    registry=dict(schema_version=1,releases=[r for r,b in existing]+[release])
    temporary=manifest_path.with_suffix('.json-writing');temporary.write_bytes(encoded(registry));temporary.replace(manifest_path)
    return report


def run(release_id,config_path=None,db_path=None,fetch=False,apply=False):
    """Prepare, compare and assemble one bounded batch; publication is explicit."""
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{1,79}',release_id):raise ValueError('ID de publicación inválido.')
    batch=ROOT/'reports/editorial-pipeline'/release_id
    decisions=ROOT/'editorial'/f'{release_id}-source-check.json'
    bundle=ROOT/'editorial'/f'{release_id}-accepted.json'
    db_path=Path(db_path) if db_path else ROOT/'data/community/voces.sqlite3'
    released=next(((r,b) for r,b in editorial_releases() if r['id']==release_id),None)
    if released:
        result=dict(state='already_published',release_id=release_id,records=len(released[1]['records']))
        if apply:result['catalogue_records']=len(CorpusStore(db_path).records())
        return result
    from .editorial_pipeline import prepare,assemble
    prepared=None
    if batch.exists() and config_path is not None:
        manifest=json.loads((batch/'manifest.json').read_text())
        if sha(Path(config_path).read_bytes())!=manifest['inputs']['config_sha256']:raise ValueError('El ID ya tiene otra configuración; usa un lote nuevo.')
    if not batch.exists():prepared=prepare(config_path or ROOT/'configs/editorial-pipeline.json',ROOT/'corpus/learning-v1.json',batch,fetch=fetch)
    checked=verify(batch,decisions)
    # Recompute even after a partial run: stale catalogue or decisions stop here.
    with tempfile.TemporaryDirectory(dir=ROOT/'editorial',prefix='.assemble-') as directory:
        candidate=Path(directory)/'accepted.json';assembly=assemble(batch,decisions,candidate,lessons_path=ROOT/'corpus/learning-v1.json')
        write_once(bundle,json.loads(candidate.read_text()))
    result=dict(state='ready',release_id=release_id,batch=str(batch),source_check=checked,records=assembly['records'],bundle=str(bundle),llm_calls=0,network_requests=prepared['network_requests'] if prepared else 0)
    if apply:result['publication']=publish(batch,bundle,release_id,db_path);result['state']='published'
    return result
