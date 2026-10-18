"""Build editorial lesson packets from local sources; never publish or train."""
import argparse
import copy
import re
from collections import Counter
import hashlib
import json
from pathlib import Path
import tempfile

from .community import ROOT
from .corpus import CorpusStore
from .text import fold
from .learning import Learning
from .research import Archive


def fingerprint(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True).encode()).hexdigest()


def audit(learning, records):
    data=copy.deepcopy(learning.data)
    findings=[];packets=[]
    def issue(id, priority, lesson, title, evidence, acceptance):
        finding=dict(id=id,priority=priority,lesson_id=lesson,title=title,evidence=evidence,acceptance=acceptance)
        finding['fingerprint']=fingerprint(finding)
        findings.append(finding)
    forms=[r for r in records.values() if r['kind']=='form']
    glyphs=[r for r in records.values() if r['kind']=='glyph']
    words={fold(f['written']) for f in forms}
    missing=[];works=Counter();exercise_types=Counter();targets=set()
    for lesson in data['lessons']:
        if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]*',lesson['id']):
            raise ValueError('Identificador de paquete inválido.')
        refs=set(lesson['sense_ids'])|{lesson['cover_glyph'],data['source_id']}
        refs.update(a['sense_id'] for e in lesson['examples'] for a in e['annotations'])
        refs.update(a['glyph_id'] for e in lesson['examples'] for a in e['annotations'] if a.get('glyph_id'))
        absent=sorted(refs-set(records))
        if absent:
            issue('lesson-'+lesson['id']+'-missing-dependencies','P1',lesson['id'],
                  'Completar referencias ausentes del borrador',dict(missing_ids=absent),
                  'Incorporar fuentes, acepciones o referencias con evidencia y validar el catálogo; no ocultar la lección para simular que no faltan registros.')
        if not lesson['examples']:
            issue('lesson-'+lesson['id']+'-example-count','P1',lesson['id'],
                  'Seleccionar ejemplos para la lectura',dict(examples=len(lesson['examples'])),
                  'Seleccionar pasajes originales y comprobar fuente, forma, objetivo y ejercicios.')
        rows=[];counts=Counter()
        for example in lesson['examples']:
            passage=learning.archive.get(example['archive_id']);works[passage['document']]+=1
            exercise_types[example['exercise']['kind']]+=1
            annotations=example['annotations']
            counts.update(set(a['sense_id'] for a in annotations))
            rows.append(dict(archive_id=passage['id'],nah=passage['nah'],es=passage['es'],
                document=passage['document'],locator=passage['locator'],source_url=passage['source_url'],
                iso=passage['iso'],source_hash=example['source_hash'],annotations=annotations,exercise=example['exercise']))
        targets.update(lesson['sense_ids'])
        packet=dict(id=lesson['id'],title=lesson['title'],objective=lesson['objective'],
            review_status=data['review_status'],target_sense_ids=lesson['sense_ids'],
            annotation_example_counts=dict(counts),examples=rows)
        packets.append(packet)
        issue('lesson-'+lesson['id']+'-source-review','P1',lesson['id'],
            'Cotejar los cuatro pasajes y sus ayudas lingüísticas' if len(rows)==4 else f'Cotejar los {len(rows)} pasajes y sus ayudas lingüísticas',
            dict(source_id=data['source_id'],review_status=data['review_status'],examples=rows),
            'Registrar edición primaria, página/folio y cotejo por pasaje; revisar traducción, forma→acepción y explicación con responsable y fecha. No sustituir el original ni marcar revisión por pasar validación técnica.')
        issue('lesson-'+lesson['id']+'-exercises','P2',lesson['id'],'Revisar ejercicios y el objetivo de aprendizaje',
            dict(objective=lesson['objective'],exercises=[dict(archive_id=e['archive_id'],exercise=e['exercise']) for e in rows]),
            'Justificar cada clave en el pasaje; revisar distractores y explicación; incluir una comprobación del objetivo que no dependa únicamente de leer el español.')
        issue('lesson-'+lesson['id']+'-learner-trial','P2',lesson['id'],'Probar la lectura con principiantes',
            dict(lesson_id=lesson['id'],has_recorded_trial=False),
            'Registrar las tareas propuestas, resultados observados, dificultades y cambios; distinguir propuesta de prueba y prueba realizada. Evitar datos personales innecesarios.')
    for sid in sorted(targets):
        sense=records.get(sid,{'label':'Acepción pendiente'});fs=[f for f in forms if f['sense_id']==sid]
        gs=[g for g in glyphs if g['sense_id']==sid]
        issue('word-'+sid+'-glyph-scope','P1' if any(g.get('association') for g in gs) else 'P2',None,
            'Revisar el alcance visual de '+next((f['written'] for f in fs if f['id'].startswith('lex-')),fs[0]['written'] if fs else sid),
            dict(sense_id=sid,meaning=sense['label'],forms=fs,glyphs=gs),
            'Elegir la referencia adecuada para cada uso de la lección y registrar si documenta una lectura, un componente, una comparación semántica o únicamente el contexto. Una imagen en un ejemplo no cuenta como glifo de esta palabra.')
    for packet in packets:
        lid=packet['id']
        for e in packet['examples']:
            for a in e['annotations']:
                if not any(fold(f['written']) == fold(a['quote']) and f['sense_id'] == a['sense_id'] for f in forms):
                    # A source-bound form candidate, not an invented lemma or meaning.
                    candidate=dict(written=a['quote'],archive_id=e['archive_id'],linked_sense_id=a['sense_id'],note=a['note'])
                    missing.append(candidate)
                    issue('form-'+e['archive_id']+'-'+a['sense_id'],'P1',lid,
                          'Revisar forma sin ficha: '+a['quote'],candidate,
                          'Determinar con evidencia si corresponde crear entrada del compuesto, añadir una forma a una acepción o conservar solo una comparación temática. Registrar fuente/localizador; no deducir morfología ni una acepción nueva automáticamente.')
    cuicatl_examples=[dict(archive_id=e['archive_id'],nah=e['nah'],es=e['es']) for p in packets for e in p['examples'] if 'cuicatl' in fold(e['nah'])]
    if 'cuicatl' not in words and cuicatl_examples:
        issue('entry-candidate-cuicatl','P1',None,'Preparar la entrada de cuicatl con fuente léxica',
              dict(written='cuicatl',examples=cuicatl_examples,exact_form_record_found=False),
              'Encontrar y registrar una entrada lexicográfica y su acepción; revisar los ejemplos de flor y canto. No convertir la traducción poética del pasaje en una definición automática.')
    sky=next((p for p in packets if p['id']=='cielo'),None)
    if sky and sky['annotation_example_counts'].get('sense-metztli',0)<2:
        issue('lesson-cielo-moon-coverage','P1','cielo','Equilibrar la presencia de la luna con el objetivo',
          dict(objective=sky['objective'],annotation_example_counts=sky['annotation_example_counts']),
          'Seleccionar al menos otro pasaje clásico breve con metztli en la acepción luna y revisarlo; documentar aparte mes cuando corresponda. No generar un ejemplo ni inventar su traducción.')
    issue('batch-source-diversity','P2',None,'Ampliar fuentes con contextos comparables',dict(works=dict(works)),
          'Preparar candidatos de otra obra con variedad, derechos y localizador explícitos. La diversidad bibliográfica no demuestra independencia de poemas o pasajes.')
    issue('batch-visual-policy','P1',None,'Definir qué cuenta como conexión correcta',
          dict(contextual_types=['related_meaning','definition_reference','passage_reference']),
          'Mantener dos métricas separadas: lecturas/componentes documentados y apoyos visuales contextuales. Revisar relaciones por uso, sin convertir coocurrencia en equivalencia.')
    if not any({'sense-atl','sense-tlalli'}.issubset(p['target_sense_ids']) and len(p['examples'])>=4 for p in packets):
        issue('batch-water-land','P2',None,'Preparar una lectura breve de agua y tierra',
              dict(existing_lesson_ids=[p['id'] for p in packets],candidate_sense_ids=['sense-atl','sense-tlalli','sense-tepetl','sense-tetl','sense-calli']),
              'Seleccionar cuatro pasajes originales y un solo objetivo; reutilizar entradas verificables. El borrador necesita cotejo y revisión antes de su incorporación al catálogo de lecciones.')
    return dict(schema_version=1,lessons=len(packets),examples=sum(len(p['examples']) for p in packets),
        target_senses=len(targets),works=dict(works),exercise_types=dict(exercise_types),
        source_review_status=data['review_status'],technical_validation='passed',
        visual_coverage=dict(target_meanings=len(targets),with_image=sum(any(g['sense_id']==sid and g.get('image') for g in glyphs) for sid in targets),with_recorded_primary_context=sum(any(g['sense_id']==sid and g.get('glyph_status')=='documented_context' for g in glyphs) for sid in targets)),
        missing_annotated_forms=missing,packets=packets,findings=findings,
        llm_calls=0,network_requests=0,note='Auditoría de los archivos de lecciones y catálogo seleccionados. Sin publicación, entrenamiento ni certificación lingüística.')


def merge_decisions(findings, decisions):
    """A review applies only to the exact evidence seen by the editor."""
    out=[]
    for finding in findings:
        item=dict(finding);decision=decisions.get(item['id'],{})
        status=decision.get('status','open')
        if status not in ('open','in_progress','blocked','resolved','deferred'):
            raise ValueError('Estado editorial desconocido: '+item['id'])
        stale=bool(decision and decision.get('fingerprint')!=item['fingerprint'])
        complete=all(decision.get(k) for k in ('reviewer','date','evidence','resolution'))
        item.update(status='open' if stale or status=='resolved' and not complete else status,
                    review_stale=stale,decision=decision)
        out.append(item)
    return out


def render_markdown(report, queue):
    lines=['# Lesson gap inventory', '',
        'Generated from local, source-bound records. Technical validation passed; linguistic and primary-source review remain pending.', '',
        f"{report['lessons']} lessons · {report['examples']} examples · {report['target_senses']} target meanings · {len(report['works'])} works · {len(report['missing_annotated_forms'])} annotated forms without an exact dictionary form.", '',
        '## Review packets', '', '| Packet | Objective | Target meanings | Examples |', '|---|---|---:|---:|']
    for p in report['packets']:
        lines.append(f"| {p['id']} | {p['objective']} | {len(p['target_sense_ids'])} | {len(p['examples'])} |")
    lines+=['','## Prioritized queue','','A resolved task requires a reviewer, date, evidence, resolution and matching fingerprint. This records an editorial decision; it does not publish a lesson or authorize training.','','| Priority | Task | Packet | State | Acceptance |','|---|---|---|---|---|']
    for f in sorted(queue,key=lambda f:(f['priority'],f['lesson_id'] or '',f['id'])):
        clean=lambda s:str(s).replace('|',' / ').replace('\n',' ')
        lines.append('| '+' | '.join(map(clean,[f['priority'],f['id'],f['lesson_id'] or 'shared',f['status'],f['acceptance']]))+' |')
    if report.get('historical_decisions'):
        lines+=['','## Decisions on findings no longer present','','These decisions preserve the earlier evidence snapshot. Absence from the current queue is not itself approval.','']
        for task, decision in report['historical_decisions'].items():
            lines.append(f"- {task}: {decision['status']} — {decision.get('resolution', '')}")
    lines+=['','## Scope','',report['note'],'','The queue identifies missing evidence and review work. It never treats an image count as a count of correct glyph readings.','']
    return '\n'.join(lines)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lessons',type=Path,default=ROOT/'corpus/learning-v1.json')
    parser.add_argument('--catalog',type=Path,help='Exportación pública research; por defecto, catálogo distribuido.')
    parser.add_argument('--output',type=Path,default=ROOT/'reports/learning-audit')
    parser.add_argument('--decisions',type=Path,default=ROOT/'editorial/lesson-decisions.json')
    args=parser.parse_args()
    with tempfile.TemporaryDirectory() as directory:
        store=CorpusStore(Path(directory)/'audit.sqlite3')
        records=store.public_records()
        if args.catalog:
            bundle=json.loads(args.catalog.read_text())
            if bundle.get('schema_version')!=1 or not isinstance(bundle.get('records'),list):
                raise ValueError('Exportación de catálogo inválida.')
            records={r['id']:r for r in bundle['records']}
            if len(records)!=len(bundle['records']):raise ValueError('IDs de catálogo duplicados.')
            for r in records.values():
                store.validate(r,records)
                if r['rights']['public'] is not True or r.get('withdrawn'):
                    raise ValueError('Usa una exportación pública research, sin registros privados o retirados.')
        report=audit(Learning(Archive(),args.lessons),records)
        report['inputs']=dict(lessons=str(args.lessons),lessons_sha256=hashlib.sha256(args.lessons.read_bytes()).hexdigest(),catalog=str(args.catalog) if args.catalog else 'distributed_catalog')
    if args.decisions.exists():
        stored=json.loads(args.decisions.read_text())
        if stored.get('schema_version')!=1 or not isinstance(stored.get('decisions'),dict):
            raise ValueError('Formato de decisiones inválido; no se sobrescribe.')
    else:
        args.decisions.parent.mkdir(parents=True,exist_ok=True)
        stored=dict(schema_version=1,decisions={})
        with args.decisions.open('x',encoding='utf-8') as f:f.write(json.dumps(stored,indent=2)+'\n')
    queue=merge_decisions(report['findings'],stored['decisions'])
    historical={key:value for key,value in stored['decisions'].items() if key not in {f['id'] for f in report['findings']}}
    for key, decision in historical.items():
        snapshot=decision.get('finding_snapshot')
        if not isinstance(snapshot,dict) or snapshot.get('id') != key or snapshot.get('fingerprint') != fingerprint({k:v for k,v in snapshot.items() if k!='fingerprint'}):
            raise ValueError('Una decisión histórica requiere su hallazgo original: '+key)
        checked=merge_decisions([snapshot],{key:decision})[0]
        if checked['status'] != decision['status']:
            raise ValueError('Decisión histórica sin evidencia suficiente: '+key)
    report['historical_decisions']=historical
    args.output.mkdir(parents=True,exist_ok=True)
    for name,value in [('inventory.json',report),('review-queue.json',dict(schema_version=1,tasks=queue))]:
        (args.output/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (args.output/'inventory.md').write_text(render_markdown(report,queue),encoding='utf-8')
    for packet in report['packets']:
        (args.output/(packet['id']+'-packet.json')).write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(lessons=report['lessons'],examples=report['examples'],target_senses=report['target_senses'],
        missing_forms=[m['written'] for m in report['missing_annotated_forms']],tasks=len(queue),
        states=dict(Counter(t['status'] for t in queue)),llm_calls=0,network_requests=0),ensure_ascii=False))


if __name__=='__main__':main()
