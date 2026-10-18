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
from .text import fold, loose_key
from .editorial_pipeline import encoded, public_catalog, sha
from .learning import Learning
from .research import Archive


def _whole_words(text):
    return {loose_key(w) for w in re.findall(r'[\w\u00c0-\u024f]+',text)}


def _same_root(terms,form,blank):
    stem=terms.analyzer.best_stem(blank)
    return bool(stem) and len(stem)>=3 and terms.analyzer.best_stem(form)==stem


def revise_exercise(example,row,edit,known,terms,senses):
    """Práctica nueva para un ejemplo: mismo pasaje, misma respuesta y misma forma del hueco.

    Cada distractor del hueco es una forma flexionada de la misma raíz atestiguada en el archivo
    (grupo de término del hueco) o una forma conocida del diccionario; nunca aparece en el pasaje.
    Las opciones de comprensión nuevas sustituyen solo a las incorrectas."""
    exercise=copy.deepcopy(example['exercise'])
    if set(edit)-{'archive_id','distractors','comprehension_distractors'}:raise ValueError('Solo puedes cambiar distractores del hueco o de comprensión.')
    if 'distractors' in edit:
        blank=exercise.get('blank');distractors=edit['distractors']
        if exercise['kind']!='cloze' or len(distractors)!=len(exercise['options'])-1:raise ValueError('Los distractores sustituyen a todas las opciones incorrectas de un hueco.')
        found=terms.resolve(blank)
        if not found:raise ValueError('El hueco no tiene grupo de término: '+blank)
        group=terms.group(found[0]['id'])
        inflected={loose_key(f):v.get('segmentation') for v in group['spellings']['inflected'] for f in v['forms']}
        present=_whole_words(row['nah']);notes=[]
        if len({loose_key(x) for x in [blank,*distractors]})!=len(distractors)+1:raise ValueError('Las opciones necesitan formas distintas: '+row['id'])
        for form in distractors:
            key=loose_key(form)
            if key in present:raise ValueError(f'El distractor {form} aparece en el pasaje {row["id"]}.')
            if key in inflected:notes.append(f'«{form}»'+(f' ({inflected[key]})' if inflected[key] else '')+' tiene la misma raíz con otros afijos.')
            elif _same_root(terms,form,blank):
                # Una forma derivada con entrada propia (cuicani «cantor») forma su propio grupo
                # de término, pero el analizador reconoce la misma raíz que el hueco.
                notes.append(f'«{form}» ({terms.analyzer.analyze(form,1)[0]["segmentation"]}) tiene la misma raíz con otros afijos.')
            elif fold(form) in known:notes.append(f'«{form}» significa «{senses[fold(form)]}».')
            else:raise ValueError(f'{form} no es forma flexionada atestiguada de {blank} ni forma del diccionario.')
        options=list(distractors);options.insert(exercise['answer'],blank);exercise['options']=options
        exercise['explanation']=f'El registro escribe «{blank}». '+' '.join(notes)+' Consulta la traducción completa para situarla en su contexto.'
    comprehension=copy.deepcopy(example.get('comprehension'))
    if 'comprehension_distractors' in edit:
        distractors=edit['comprehension_distractors']
        if not comprehension or len(distractors)!=len(comprehension['options'])-1:raise ValueError('Faltan opciones de comprensión: '+row['id'])
        answer=comprehension['options'][comprehension['answer']]
        if any(not isinstance(d,str) or not d.strip() or len(d)>160 or fold(d)==fold(answer) for d in distractors):raise ValueError('Opción de comprensión inválida: '+row['id'])
        options=list(distractors);options.insert(comprehension['answer'],answer);comprehension['options']=options
    return exercise,comprehension


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
    known={fold(r['written']) for r in records.values() if r['kind']=='form'}
    existing={l['id']:l for l in data['lessons']};used={e['archive_id'] for l in data['lessons'] for e in l['examples']}
    changes=[];practice={};terms=senses=None
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
        for edit in update.get('example_updates',[]):
            example=next(e for e in lesson['examples'] if e['archive_id']==edit['archive_id'])
            if set(edit)-{'archive_id','comprehension','explore_words'}:raise ValueError('Solo puedes añadir comprensión o palabras para explorar.')
            for key in ('comprehension','explore_words'):
                if key in edit:example[key]=copy.deepcopy(edit[key])
        if update.get('exercise_updates'):
            # Cambian las claves: nueva edición de práctica; el progreso anterior de esta lectura no se mezcla con ella.
            if terms is None:
                from .stems import WordStudy
                from .terms import TermIndex
                terms=TermIndex(WordStudy(),records_fn=public_catalog)
                senses={fold(r['written']):records[r['sense_id']]['label'] for r in records.values() if r['kind']=='form' and r.get('sense_id') in records}
            lesson['practice_version']+=1
            for edit in update['exercise_updates']:
                example=next(e for e in lesson['examples'] if e['archive_id']==edit['archive_id'])
                example['exercise'],comprehension=revise_exercise(example,archive.get(edit['archive_id']),edit,known,terms,senses)
                if comprehension is not None:example['comprehension']=comprehension
            practice[lesson['id']]=lesson['practice_version']
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
            if len(distractors)!=2 or fold(blank) not in known or any(fold(v) not in known for v in distractors):raise ValueError('La clave y sus distractores necesitan formas de diccionario conocidas.')
            if not any(a['quote']==blank and a.get('relation')=='full_word' for a in selection['annotations']):raise ValueError('El hueco necesita una anotación de palabra completa.')
            if len(set(map(fold,[blank,*distractors])))!=3:raise ValueError('Las opciones necesitan tres formas distintas.')
            answer=index%3;options=list(distractors);options.insert(answer,blank)
            example=dict(archive_id=rid,source_hash=hashlib.sha256((row['nah']+'\0'+row['es']).encode()).hexdigest(),context=selection['context'],annotations=copy.deepcopy(selection['annotations']),exercise=dict(kind='cloze',question='Recupera la forma que aparece en el fragmento original.',options=options,answer=answer,explanation=f'El registro escribe «{blank}». Recupera esa grafía exacta; consulta la traducción completa para situarla en su contexto.',blank=blank))
            for key in ('comprehension','explore_words'):
                if key in selection:example[key]=copy.deepcopy(selection[key])
            lesson['examples'].append(example);used.add(rid)
        data['lessons'].append(lesson);existing[lesson['id']]=lesson
    with tempfile.TemporaryDirectory() as directory:
        draft=Path(directory)/'learning.json';draft.write_bytes(encoded(data));validated=Learning(archive,draft)
        if len(validated.catalog(records)['lessons'])!=len(data['lessons']):raise ValueError('La selección tiene dependencias ausentes o privadas.')
    original=json.loads(raw)
    def keys(lesson,full):
        # Con una edición de práctica nueva cambian las opciones, nunca el pasaje, la respuesta ni la forma del hueco.
        return [(e['archive_id'],e['source_hash'],e['exercise'] if full else (e['exercise']['kind'],e['exercise'].get('blank'),e['exercise']['answer'],e['exercise']['options'][e['exercise']['answer']],
                 e.get('comprehension') and e['comprehension']['options'][e['comprehension']['answer']])) for e in lesson['examples']]
    for old,new in zip(original['lessons'],data['lessons']):
        full=new['id'] not in practice
        if old['id']!=new['id'] or keys(old,full)!=keys(new,full):raise ValueError('Las aclaraciones no pueden cambiar pasajes ni claves existentes.')
    proof=dict(schema_version=1,release_id=recipes['release_id'],base_sha256=sha(raw),config_sha256=sha(Path(config).read_bytes()),learning=data,summary=dict(added_lessons=len(recipes['lessons']),added_examples=sum(len(l['examples']) for l in recipes['lessons']),clarified_lessons=changes,practice_versions=practice,lessons=len(data['lessons']),examples=sum(len(l['examples']) for l in data['lessons']),llm_calls=0,network_requests=0,primary_review=False,linguistic_certification=False,original_passages_and_keys_preserved=not practice,original_passages_and_answers_preserved=True))
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
