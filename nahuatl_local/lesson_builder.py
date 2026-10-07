"""Assemble bounded reading selections from editorial recipes and original pairs.

Selection and explanations remain explicit recipes. Hashes, exact-form cloze
keys, dependencies and publication are deterministic; no network or LLM calls.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import tempfile

from .community import ROOT
from .corpus import normalize
from .editorial_pipeline import encoded, public_catalog, sha
from .learning import Learning
from .research import Archive


def build(config,output,base=None,apply=False):
    base=Path(base or ROOT/'corpus/learning-v1.json');output=Path(output).resolve()
    if not output.is_relative_to(ROOT/'editorial') or output.suffix!='.json':raise ValueError('Guarda la propuesta como JSON dentro de editorial/.')
    recipes=json.loads(Path(config).read_text())
    if recipes.get('schema_version')!=1 or recipes.get('review_status')!='editorial_draft' or not re.fullmatch(r'[a-z0-9][a-z0-9-]{1,79}',recipes.get('release_id','')):raise ValueError('Receta editorial inválida.')
    raw=base.read_bytes();data=json.loads(raw);archive=Archive();records=public_catalog()
    if output.exists():
        previous=json.loads(output.read_text())
        if previous.get('config_sha256')==sha(Path(config).read_bytes()) and raw==encoded(previous.get('learning')):
            current=Learning(archive,base)
            if len(current.catalog(records)['lessons'])!=len(data['lessons']):raise ValueError('Cambió una dependencia publicada.')
            return dict(state='already_published',output=str(output),**previous['summary'])
    known={normalize(r['written']) for r in records.values() if r['kind']=='form'}
    existing={l['id']:l for l in data['lessons']};used={e['archive_id'] for l in data['lessons'] for e in l['examples']}
    changes=[]
    for update in recipes.get('lesson_updates',[]):
        lesson=existing[update['id']]
        lesson['practice_version']=lesson.get('practice_version',lesson.get('version',data['version']))
        lesson['version']=lesson.get('version',data['version'])+1
        for key in ('title','objective','reading_tips'):
            if key in update:lesson[key]=copy.deepcopy(update[key])
        for edit in update.get('annotation_updates',[]):
            example=next(e for e in lesson['examples'] if e['archive_id']==edit['archive_id'])
            a=next(a for a in example['annotations'] if a['quote']==edit['quote'])
            a.update(relation=edit['relation'],note=edit['note'])
        changes.append(lesson['id'])
    for recipe in recipes['lessons']:
        if recipe['id'] in existing or not re.fullmatch(r'[a-z0-9][a-z0-9-]{1,79}',recipe['id']):raise ValueError('La receta solo puede añadir IDs de lectura nuevos y únicos.')
        if len(recipe['examples'])!=4:raise ValueError('Selecciona cuatro ejemplos por receta de lectura.')
        lesson={k:copy.deepcopy(recipe[k]) for k in ('id','title','objective','minutes','sense_ids','cover_glyph','reading_tips')}
        lesson.update(version=1,examples=[])
        for index,selection in enumerate(recipe['examples']):
            rid=selection['archive_id']
            if rid in used:raise ValueError('El pasaje ya se utiliza en la selección: '+rid)
            row=archive.get(rid);cloze=selection['cloze'];blank=cloze['blank'];distractors=cloze['distractors']
            if len(distractors)!=2 or normalize(blank) not in known or any(normalize(v) not in known for v in distractors):raise ValueError('La clave y sus distractores necesitan formas de diccionario conocidas.')
            if not any(a['quote']==blank and a.get('relation')=='full_word' for a in selection['annotations']):raise ValueError('El hueco necesita una anotación de palabra completa.')
            if len(set(map(normalize,[blank,*distractors])))!=3:raise ValueError('Las opciones necesitan tres formas distintas.')
            answer=index%3;options=list(distractors);options.insert(answer,blank)
            example=dict(archive_id=rid,source_hash=hashlib.sha256((row['nah']+'\0'+row['es']).encode()).hexdigest(),context=selection['context'],annotations=copy.deepcopy(selection['annotations']),exercise=dict(kind='cloze',question='Recupera la forma que aparece en el fragmento original.',options=options,answer=answer,explanation=f'El registro escribe «{blank}». Recupera esa grafía exacta; consulta la traducción completa para situarla en su contexto.',blank=blank))
            lesson['examples'].append(example);used.add(rid)
        data['lessons'].append(lesson);existing[lesson['id']]=lesson
    with tempfile.TemporaryDirectory() as directory:
        draft=Path(directory)/'learning.json';draft.write_bytes(encoded(data));validated=Learning(archive,draft)
        if len(validated.catalog(records)['lessons'])!=len(data['lessons']):raise ValueError('La selección tiene dependencias ausentes o privadas.')
    original=json.loads(raw)
    for old,new in zip(original['lessons'],data['lessons']):
        if old['id']!=new['id'] or [(e['archive_id'],e['source_hash'],e['exercise']) for e in old['examples']]!=[(e['archive_id'],e['source_hash'],e['exercise']) for e in new['examples']]:raise ValueError('Las aclaraciones no pueden cambiar pasajes ni claves existentes.')
    proof=dict(schema_version=1,release_id=recipes['release_id'],base_sha256=sha(raw),config_sha256=sha(Path(config).read_bytes()),learning=data,summary=dict(added_lessons=len(recipes['lessons']),added_examples=sum(len(l['examples']) for l in recipes['lessons']),clarified_lessons=changes,lessons=len(data['lessons']),examples=sum(len(l['examples']) for l in data['lessons']),llm_calls=0,network_requests=0,primary_review=False,linguistic_certification=False,original_passages_and_keys_preserved=True))
    if output.exists() and output.read_bytes()!=encoded(proof):raise ValueError('La propuesta ya existe con otra base; usa una versión nueva.')
    output.parent.mkdir(parents=True,exist_ok=True)
    if not output.exists():
        with output.open('xb') as file:file.write(encoded(proof))
    if apply:
        if base.resolve()!=ROOT/'corpus/learning-v1.json' or sha(base.read_bytes())!=proof['base_sha256']:raise ValueError('La base de publicación cambió.')
        backup=ROOT/'reports'/('learning-before-'+recipes['release_id'])/'learning-v1.json';backup.parent.mkdir(parents=True,exist_ok=True)
        if backup.exists() and backup.read_bytes()!=raw:raise ValueError('El respaldo pertenece a otra base.')
        if not backup.exists():backup.write_bytes(raw)
        staged=base.with_suffix('.json-writing');staged.write_bytes(encoded(data));staged.replace(base)
    return dict(state='published' if apply else 'prepared',output=str(output),**proof['summary'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--base',type=Path);parser.add_argument('--apply',action='store_true')
    print(json.dumps(build(**vars(parser.parse_args())),ensure_ascii=False,indent=2))


if __name__=='__main__':main()
