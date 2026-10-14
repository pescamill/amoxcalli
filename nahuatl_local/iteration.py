"""Diagnóstico público reproducible y registro de tareas; sin red, modelo ni publicación."""
import argparse
import copy
from collections import Counter
from datetime import date
import hashlib
import json
from pathlib import Path
import tempfile

from .community import ROOT
from .corpus import CorpusStore, editorial_releases
from .learning import Learning
from .lesson_audit import audit, fingerprint, merge_decisions
from .pictography import CATALOG, load_catalog
from .research import Archive

STATUSES = {'open', 'in_progress', 'blocked', 'deferred', 'resolved'}
PUBLIC_PREFIXES = ('corpus', 'configs', 'editorial', 'docs', 'reports', 'tests', 'nahuatl_local', 'scripts')


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_manifest():
    """Explicit public inputs used by the distributed store; never enumerate data/."""
    paths = [ROOT / 'corpus' / name for name in (
        'seed.json', 'glyph-links-v2.json', 'archive-source-v3.json',
        'glyph-images-v4.json', 'glyph-lexicon-v5.json', 'glyph-source-images-v5.json',
        'gdn-lexicon-v6.json', 'glyph-associations-v7.json', 'flor-lexicon-v8.json',
        'editorial-releases.json', 'learning-v1.json')]
    paths += [ROOT / 'corpus' / release['bundle'] for release, _ in editorial_releases()]
    paths += [ROOT / relative for relative in MILESTONE_FILES.values()]
    paths += [CATALOG, ROOT / 'corpus/axolotl/axolotl.csv', ROOT / 'configs/sources.json',
              ROOT / 'nahuatl_local/community_web/catalog.json',
              ROOT / 'editorial/lesson-decisions.json',
              ROOT / 'docs/PROPOSITO.md', ROOT / 'docs/TRABAJO_AUTONOMO.md',
              ROOT / 'docs/EVALUACION_DOCUMENTAL.md', ROOT / 'docs/ITERACIONES.md', ROOT / 'docs/CONSULTA_DOCUMENTAL.md']
    paths += [ROOT / relative for relative in ('docs/LABORATORIO.md', 'reports/documentary-laboratory-display-v1.json',
              'tests/platform_ui.cjs', 'tests/test_laboratory.py', 'tests/test_iteration.py', 'scripts/test-platform-ui.py')]
    paths += [ROOT / 'nahuatl_local/platform_web' / name for name in ('app.js', 'documentary.js', 'style.css', 'index.html', 'learning.js', 'laboratory.js', 'laboratory.css', 'training-data.js')]
    paths += [ROOT / 'nahuatl_local' / (name + '.py') for name in
              ('iteration', 'lesson_audit', 'learning', 'corpus', 'community', 'research', 'pictography', 'documentary_evaluation', 'documentary_retrieval', 'documentary_retrieval_evaluation', 'documentary_laboratory', 'laboratory', 'model_status', 'platform')]
    return evidence_hashes([str(path.relative_to(ROOT)) for path in sorted(set(paths))])


def evidence_hashes(evidence):
    """Hash only project-public files. URLs and private paths are not followed."""
    if not isinstance(evidence, list) or not evidence:
        raise ValueError('La evidencia requiere al menos un archivo público del proyecto.')
    hashes = {}
    for reference in evidence:
        if not isinstance(reference, str) or not reference.strip():
            raise ValueError('Referencia de evidencia inválida.')
        relative = Path(reference)
        path = ROOT / relative
        if (relative.is_absolute() or not relative.parts or relative.parts[0] not in PUBLIC_PREFIXES
                or '..' in relative.parts or path.is_symlink()):
            raise ValueError('La evidencia debe ser una ruta pública relativa, sin enlaces simbólicos.')
        # Also refuse symlinks in ancestors, including ones pointing into private data.
        for parent in path.parents:
            if parent == ROOT:
                break
            if parent.is_symlink():
                raise ValueError('La evidencia no puede atravesar enlaces simbólicos.')
        hashes[reference] = sha256(path) if path.is_file() else None
    return dict(sorted(hashes.items()))


def task(finding, category, dependencies):
    result = copy.deepcopy(finding)
    result['finding_fingerprint'] = result.pop('fingerprint', fingerprint(finding))
    result['category'] = category
    result['source_hashes'] = dict(sorted(dependencies.items()))
    result['fingerprint'] = fingerprint(result)
    return result


MILESTONE_FILES = {
    'evaluation': 'configs/documentary-evaluation-v1.json',
    'evaluation_validation': 'reports/documentary-evaluation-validation-v1.json',
    'retrieval': 'reports/documentary-retrieval-v1.json',
    'laboratory': 'reports/documentary-laboratory-v1.json',
}


def checked_references(references):
    """Completion evidence must name current public files, never private inputs."""
    if not isinstance(references, dict) or not references:
        return False
    try:
        actual = evidence_hashes(list(references))
    except ValueError:
        return False
    return all(isinstance(value, str) and value == actual[key]
               for key, value in references.items())


def technical_progress(artifacts):
    """Derive preparation from documentary evidence, not historical SFT scores.

    An absent, malformed or stale artifact keeps the relevant task open. A
    completed technical preparation disappears from the current queue; reconcile
    retains its history without inventing a resolved human decision.
    """
    from .documentary_evaluation import validate as validate_evaluation
    evaluation = artifacts.get('evaluation') or {}
    queries = evaluation.get('queries', []) if isinstance(evaluation, dict) else []
    try:
        validation = validate_evaluation(evaluation, ROOT)
    except (ValueError, OSError, KeyError, TypeError):
        validation = dict(valid=False, counts={}, overlaps={}, errors=['source_or_contract_invalid'])
    # The persisted report must match recomputation. Scope is local documentary
    # fields only; image/model use and legal permissions remain explicitly pending.
    report_matches = artifacts.get('evaluation_validation') == validation
    evaluation_ready = validation['valid'] and report_matches
    valid_queries = queries if validation['valid'] else []
    counts = validation.get('counts') or {split: {kind: 0 for kind in ('textual', 'visual')}
                                         for split in ('development', 'reserve')}
    separated = bool(validation['valid']) and not any(validation.get('overlaps', {}).values())
    evaluation_hash = fingerprint(evaluation)
    textual_ids = {q['id'] for q in valid_queries
                   if q['split'] == 'development' and q['modality'] == 'textual'}
    textual_tasks = {q['task'] for q in valid_queries
                     if q['split'] == 'development' and q['modality'] == 'textual'}
    retrieval = artifacts.get('retrieval') or {}
    results = retrieval.get('results', [])
    from .documentary_retrieval_evaluation import validate_report as validate_retrieval
    retrieval_validation = validate_retrieval(retrieval, queries=[q for q in valid_queries
        if q['split'] == 'development' and q['modality'] == 'textual']) if evaluation_ready else dict(valid=False, errors=['evaluation_not_ready'])
    retrieval_ready = bool(evaluation_ready and retrieval_validation['valid'])
    laboratory = artifacts.get('laboratory') or {}
    runs = laboratory.get('runs', [])
    from .documentary_laboratory import validate_report as validate_laboratory
    laboratory_validation = validate_laboratory(laboratory, retrieval=retrieval,
        retrieval_validation=retrieval_validation) if retrieval_ready else dict(valid=False, errors=['retrieval_not_ready'])
    laboratory_ready = bool(evaluation_ready and retrieval_ready and laboratory_validation['valid'])
    return dict(evaluation=dict(ready=evaluation_ready, counts=counts,
                               invalid_queries=len(queries)-len(valid_queries) if isinstance(queries, list) else None,
                               reserve_groups_independent=separated,
                               validation_errors=validation.get('errors', []) + ([] if report_matches else ['missing_or_stale_validation_report']),
                               scope='local_documentary_fields_only', visual_model_evaluation_enabled=False,
                               fingerprint=evaluation_hash),
                retrieval=dict(ready=retrieval_ready, measured_queries=len(results) if isinstance(results, list) else 0,
                               validation_errors=retrieval_validation['errors']),
                laboratory=dict(ready=laboratory_ready, validation_errors=laboratory_validation['errors'], measured_methods=[r['method'] for r in runs
                               if isinstance(r, dict) and r.get('status') == 'measured'] if isinstance(runs, list) else []))


def milestone_artifacts():
    result = {}
    for name, relative in MILESTONE_FILES.items():
        path = ROOT / relative
        # Evidence inputs stay in the same public boundary as recorded decisions.
        try:
            if evidence_hashes([relative])[relative] is None:
                continue
            value = json.loads(path.read_text(encoding='utf-8'))
            if isinstance(value, dict):
                result[name] = value
        except (ValueError, OSError):
            continue
    return result


def diagnose(records, learning, pictography, sources, decisions, occurrence_target=300,
             lesson_target=12, artifacts=None):
    """Compute gaps; catalogue omissions do not imply missing linguistic truth."""
    lesson_report = audit(learning, records)
    lesson_queue = merge_decisions(lesson_report['findings'], decisions)
    lesson_sources = {key: value for key, value in sources.items()
                      if key.startswith('corpus/') and key != str(CATALOG.relative_to(ROOT))
                      or key in ('configs/sources.json', 'nahuatl_local/learning.py', 'nahuatl_local/lesson_audit.py')}
    tasks = []
    for finding in lesson_report['findings']:
        category = 'technical' if finding['id'].endswith('-missing-dependencies') else 'human'
        tasks.append(task(finding, category, lesson_sources))
    progress = technical_progress(milestone_artifacts() if artifacts is None else artifacts)
    milestone_sources = {key: value for key, value in sources.items()
                         if key in MILESTONE_FILES.values() or key in
                         ('corpus/learning-v1.json', 'corpus/pictography/catalog.json',
                          'docs/TRABAJO_AUTONOMO.md', 'nahuatl_local/iteration.py')}

    def milestone(rid, title, evidence, acceptance):
        finding = dict(id=rid, priority='P1', lesson_id=None, title=title,
                       evidence=evidence, acceptance=acceptance)
        tasks.append(task(finding, 'technical', milestone_sources))

    if lesson_report['lessons'] < lesson_target:
        milestone('learning-next-source-backed-readings', 'Preparar lecturas con nuevos pasajes sustentados',
                  dict(current=lesson_report['lessons'], target=lesson_target,
                       passages=lesson_report['examples'], review_status=learning.data['review_status']),
                  'Seleccionar pares originales clásicos nuevos con lesson_builder; conservar IDs, hashes, claves, versiones y progreso; añadir cuatro pasajes por receta solo con citas completas, formas y referencias existentes. Publicación editorial_draft no resuelve revisión humana.')
    if not progress['evaluation']['ready']:
        milestone('evaluation-documentary-development-reserve', 'Preparar desarrollo textual/visual y reserva independiente',
                  dict(progress['evaluation'], artifact=MILESTONE_FILES['evaluation'],
                       target_development=dict(textual=100, visual=50)),
                  'Preparar 100 consultas textuales y 50 observaciones visuales documentales de desarrollo, con campos originales, atribución, hashes, incertidumbre, condiciones de uso separadas y validador reproducible. Reservar casos agrupados sin solapamiento de entradas, pasajes o imágenes; el alcance local documental no habilita evaluación VLM ni entrenamiento. Benchmarks SFT históricos no acreditan este hito.')
    if not progress['retrieval']['ready']:
        milestone('retrieval-documentary-baseline', 'Medir recuperación documental con citas comprobables',
                  dict(progress['retrieval'], artifact=MILESTONE_FILES['retrieval'],
                       evaluation_ready=progress['evaluation']['ready']),
                  'Resolver consultas léxicas y comparaciones sobre fichas públicas con fuente, campo original y enlaces; medir todos los casos textuales de desarrollo contra sus referencias, incluyendo fallos, citas, abstenciones y tiempo. Mantener la reserva fuera de selección y ajuste; el BM25 train-only de traducción no demuestra recuperación documental.')
    if not progress['laboratory']['ready']:
        milestone('laboratory-documentary-multimodal-comparison', 'Mostrar el estado real de la comparación multimodal',
                  dict(progress['laboratory'], artifact=MILESTONE_FILES['laboratory'],
                       evaluation_ready=progress['evaluation']['ready'], retrieval_ready=progress['retrieval']['ready'],
                       training_allowed=False),
                  'Mostrar recuperación, modelo textual y candidato multimodal en una comparación reproducible con batería y hashes comunes, resultados y coste medidos o not_run con razón explícita, y evidencia de su presentación en la app. Conservar pesos y training:false; una ficha de candidato no acredita un experimento.')
    senses = {rid for rid, row in records.items() if row['kind'] == 'sense'}
    elements = pictography['elements']
    occurrences = pictography['occurrences']
    used = {component['element_id'] for row in occurrences for component in row['components']}
    gaps = dict(
        elements_without_lexical_links=sorted(e['id'] for e in elements if not e.get('lexical_links')),
        elements_without_occurrences=sorted(e['id'] for e in elements if e['id'] not in used),
        elements_without_images=sorted(e['id'] for e in elements if not e.get('image')),
        elements_without_meanings=sorted(e['id'] for e in elements if not e.get('meanings')),
        broken_lexical_links=sorted(
            [dict(element_id=e['id'], sense_id=link['sense_id']) for e in elements
             for link in e.get('lexical_links', []) if link['sense_id'] not in senses],
            key=lambda row: (row['element_id'], row['sense_id'])),
        occurrences_without_components=sorted(o['id'] for o in occurrences if not o['components']),
        occurrences_without_citations=sorted(o['id'] for o in occurrences if not o['citations']),
        occurrences_without_images=sorted(o['id'] for o in occurrences if not o.get('image')),
        components_without_values=sorted(
            [dict(occurrence_id=o['id'], element_id=c['element_id'])
             for o in occurrences for c in o['components'] if not c['values']],
            key=lambda row: (row['occurrence_id'], row['element_id'])))
    pict_sources = {key: sources[key] for key in (str(CATALOG.relative_to(ROOT)), 'nahuatl_local/pictography.py')}

    def issue(rid, category, title, evidence, acceptance, priority='P2'):
        finding = dict(id=rid, priority=priority, lesson_id=None, title=title,
                       evidence=evidence, acceptance=acceptance)
        tasks.append(task(finding, category, pict_sources))

    if gaps['broken_lexical_links']:
        issue('pictography-broken-lexical-links', 'technical', 'Reparar destinos léxicos ausentes',
              gaps['broken_lexical_links'], 'Recuperar referencias sustentadas o registrar su retirada editorial; validar contra acepciones públicas.', 'P1')
    if gaps['elements_without_images'] or gaps['occurrences_without_images']:
        issue('pictography-missing-image-references', 'technical', 'Comprobar referencias documentales de imagen',
              {key: gaps[key] for key in ('elements_without_images', 'occurrences_without_images')},
              'Consultar los localizadores documentales y conservar ausencias explícitas; añadir enlaces solo si la fuente los proporciona.')
    pages = {p['id']: p for p in pictography['pages']}
    for document in sorted(pictography['documents'], key=lambda d: d['id']):
        rows = [o for o in occurrences if pages[o['page_id']]['document_id'] == document['id']]
        incomplete = [o for o in rows if not o['components'] or not o['citations']
                      or any(not c['values'] for c in o['components'])]
        if incomplete:
            issue('pictography-'+document['id']+'-documentary-gaps', 'human',
                  'Decidir el alcance de datos ausentes: '+document['title'],
                  dict(document=document, occurrences=incomplete),
                  'Cotejar fuente/localizador y registrar qué omisiones son documentales o requieren extracción. No inventar componentes, valores ni lecturas para completar campos.')
    if len(occurrences) < occurrence_target:
        finding = dict(id='pictography-next-documentary-batch', priority='P1', lesson_id=None,
                       title='Preparar el siguiente lote documental revisable',
                       evidence=dict(current_occurrences=len(occurrences), proposed_target=occurrence_target,
                                     document_ids=sorted(d['id'] for d in pictography['documents']),
                                     training_allowed=False),
                       acceptance='Reutilizar pictography_pipeline y cachés públicas para un lote con URL, localizador y hash; validar colisiones y derechos, comparar contra el índice y conservar un candidato antes de publicar. La cantidad no sustituye evidencia ni revisión.')
        tasks.append(task(finding, 'technical', dict(pict_sources,
                                                   **{'docs/TRABAJO_AUTONOMO.md': sources['docs/TRABAJO_AUTONOMO.md']})))
    issue('pictography-training-rights', 'human', 'Resolver permisos antes de un uso nuevo',
          dict(rights=pictography['rights']),
          'Mantener training:false. Solo considerar otro uso con decisión identificada y evidencia de derechos por obra, edición, transcripción e imagen.')
    kinds = dict(sorted(Counter(row['kind'] for row in records.values()).items()))
    report = dict(schema_version=1, sources=sources, source_fingerprint=fingerprint(sources),
                  counts=dict(public_records=kinds, lessons=lesson_report['lessons'],
                              passages=lesson_report['examples'], target_senses=lesson_report['target_senses'],
                              pictography={key: len(pictography[key]) for key in
                                           ('documents', 'pages', 'zones', 'elements', 'occurrences')},
                              designations=len({e['designation'] for e in elements}),
                              lexical_links=sum(len(e.get('lexical_links', [])) for e in elements)),
                  proposed_lesson_target=lesson_target,
                  lessons_remaining_to_proposed_target=max(0, lesson_target-lesson_report['lessons']),
                  technical_progress=progress,
                  proposed_occurrence_target=occurrence_target,
                  occurrences_remaining_to_proposed_target=max(0, occurrence_target-len(occurrences)),
                  gaps=gaps, lesson_audit=lesson_report, lesson_review_queue=lesson_queue,
                  editorial_decisions=copy.deepcopy(decisions),
                  historical_editorial_decisions={key: copy.deepcopy(value) for key, value in decisions.items()
                                                 if key not in {f['id'] for f in lesson_report['findings']}},
                  limits=['Un campo vacío registra ausencia en el índice; no obliga a asociar cada palabra con una imagen.',
                          'Validación técnica no equivale a revisión lingüística, cotejo primario ni ensayo con personas.',
                          'Hashes de archivos locales, no verificación de las páginas remotas ni permiso de entrenamiento.'],
                  privacy=dict(private_database_opened=False, corpus_modified=False),
                  llm_calls=0, network_requests=0)
    report['diagnostic_fingerprint'] = fingerprint(report)
    return report, sorted(tasks, key=lambda t: (t['priority'], t['category'], t['id']))


def empty_state():
    return dict(schema_version=1, tasks={}, runs=[], history=[])


def validate_state(state):
    if (state.get('schema_version') != 1 or not isinstance(state.get('tasks'), dict)
            or not isinstance(state.get('runs'), list) or not isinstance(state.get('history'), list)):
        raise ValueError('Estado de iteración inválido; no se sobrescribe.')
    for rid, row in state['tasks'].items():
        if not isinstance(row, dict) or row.get('status') not in STATUSES:
            raise ValueError('Estado de tarea inválido: '+rid)
        for key in ('snapshots', 'history'):
            if not isinstance(row.get(key), list):
                raise ValueError('Historia de tarea inválida: '+rid)
    return state


def event(history, kind, **values):
    item = dict(kind=kind, **values)
    item['id'] = fingerprint(item)
    if not any(previous.get('id') == item['id'] for previous in history):
        history.append(item)


def reconcile(tasks, state, diagnostic_fingerprint, legacy_decisions=None):
    """Retain all notes/snapshots and reopen decisions bound to changed evidence."""
    result = copy.deepcopy(validate_state(state))
    current_ids = {t['id'] for t in tasks}
    for rid, row in result['tasks'].items():
        if rid not in current_ids and row.get('present', True):
            row['present'] = False
            event(row['history'], 'absent', diagnostic_fingerprint=diagnostic_fingerprint)
    for current in tasks:
        rid = current['id']
        if rid not in result['tasks']:
            row = dict(status='open', present=True, notes=[], snapshots=[], history=[])
            result['tasks'][rid] = row
            decision = (legacy_decisions or {}).get(rid)
            if decision:
                imported = copy.deepcopy(decision)
                # A matching legacy finding authorizes migration, not new human review.
                if imported.get('fingerprint') == current['finding_fingerprint']:
                    imported['fingerprint'] = current['fingerprint']
                imported['origin'] = 'editorial/lesson-decisions.json'
                imported['original_decision'] = copy.deepcopy(decision)
                imported['evidence_hashes'] = evidence_hashes(decision['evidence']) if decision.get('evidence') else {}
                imported['evidence_hashes_observed_at_import'] = True
                row['decision'] = imported
                event(row['history'], 'decision_imported', decision=imported)
        row = result['tasks'][rid]
        if not row.get('present', True):
            event(row['history'], 'reappeared', diagnostic_fingerprint=diagnostic_fingerprint)
        row['present'] = True
        if not any(s['fingerprint'] == current['fingerprint'] for s in row['snapshots']):
            row['snapshots'].append(copy.deepcopy(current))
            event(row['history'], 'observed', fingerprint=current['fingerprint'])
        row['current'] = copy.deepcopy(current)
        decision = row.get('decision')
        reasons = []
        if decision:
            if decision.get('status') not in STATUSES:
                raise ValueError('Decisión de tarea inválida: '+rid)
            if decision.get('fingerprint') != current['fingerprint']:
                reasons.append('finding_or_source_changed')
            hashes = evidence_hashes(decision['evidence']) if decision.get('evidence') else {}
            if hashes != decision.get('evidence_hashes', {}):
                reasons.append('decision_evidence_changed')
            if decision.get('status') == 'resolved' and (
                    not all(decision.get(key) for key in ('reviewer', 'date', 'evidence', 'resolution'))
                    or not hashes or any(value is None for value in hashes.values())):
                reasons.append('resolution_incomplete')
            row['status'] = 'open' if reasons else decision['status']
        else:
            row['status'] = 'open'
        row['decision_stale'] = bool(reasons)
        row['stale_reasons'] = reasons
        if reasons:
            event(row['history'], 'decision_stale', fingerprint=current['fingerprint'], reasons=reasons,
                  evidence_hashes=hashes)
    if not result['runs'] or result['runs'][-1] != diagnostic_fingerprint:
        result['runs'].append(diagnostic_fingerprint)
        event(result['history'], 'diagnostic', fingerprint=diagnostic_fingerprint)
    result['latest_diagnostic_fingerprint'] = diagnostic_fingerprint
    return result


def record_decision(state, decision):
    result = copy.deepcopy(validate_state(state))
    rid = decision.get('id')
    row = result['tasks'].get(rid)
    if not row or not row.get('present'):
        raise ValueError('La decisión necesita una tarea actual.')
    if decision.get('fingerprint') != row['current']['fingerprint']:
        raise ValueError('La decisión no corresponde al fingerprint actual.')
    if decision.get('status') not in STATUSES:
        raise ValueError('Estado de decisión inválido.')
    if not all(isinstance(decision.get(key), str) and decision[key].strip()
               for key in ('reviewer', 'date', 'resolution')):
        raise ValueError('La decisión requiere responsable, fecha y resolución explícitos.')
    date.fromisoformat(decision['date'])
    hashes = evidence_hashes(decision.get('evidence'))
    if any(value is None for value in hashes.values()):
        raise ValueError('La evidencia debe existir antes de registrar la decisión.')
    saved = copy.deepcopy(decision)
    saved['evidence_hashes'] = hashes
    row['decision'] = saved
    row.update(status=decision['status'], decision_stale=False, stale_reasons=[])
    event(row['history'], 'decision', decision=saved)
    return result


def queue_from_state(state):
    return [dict(row['current'], status=row['status'], decision_stale=row['decision_stale'],
                 stale_reasons=row['stale_reasons'], notes=copy.deepcopy(row.get('notes', [])))
            for row in sorted(state['tasks'].values(),
                              key=lambda r: (r['current']['priority'], r['current']['category'], r['current']['id']))
            if row.get('present')]


def render_markdown(report, queue):
    counts = report['counts']
    lines = ['# Diagnóstico de iteración de Amoxcalli', '',
             f"{counts['lessons']} lecturas · {counts['passages']} pasajes · "
             f"{counts['public_records'].get('sense', 0)} acepciones · {counts['public_records'].get('form', 0)} formas.", '',
             f"{counts['designations']} denominaciones · {counts['pictography']['elements']} elementos · "
             f"{counts['pictography']['occurrences']} apariciones · {counts['lexical_links']} vínculos léxicos declarados.", '',
             '## Datos ausentes y conexiones', '', '| Medida | Cantidad |', '|---|---:|']
    lines += [f'| {key} | {len(value)} |' for key, value in report['gaps'].items()]
    progress = report['technical_progress']
    lines += ['', '## Hitos técnicos calculados', '',
              f"Lecturas editoriales: {counts['lessons']} / {report['proposed_lesson_target']}; pendientes de ampliación: {report['lessons_remaining_to_proposed_target']}.",
              f"Apariciones documentales: {counts['pictography']['occurrences']} / {report['proposed_occurrence_target']}; pendientes: {report['occurrences_remaining_to_proposed_target']}.",
              'La preparación de lecturas no resuelve revisión especializada ni pruebas con personas.', '',
              '| Preparación | Estado | Evidencia actual |', '|---|---|---|']
    evaluation = progress['evaluation']
    for name in ('evaluation', 'retrieval', 'laboratory'):
        row = progress[name]
        evidence = (json.dumps(evaluation['counts'], ensure_ascii=False, sort_keys=True) if name == 'evaluation'
                    else str(row['measured_queries'])+' consultas medidas' if name == 'retrieval'
                    else ', '.join(row['measured_methods']) or 'Sin métodos medidos')
        lines.append('| '+name+' | '+('Preparación documentada' if row['ready'] else 'Pendiente o evidencia obsoleta')+' | '+evidence+' |')
    lines += ['', 'La reserva se cuenta aparte del desarrollo. Los benchmarks SFT históricos no completan estos hitos.', '',
              '## Cola retomable', '', '| Prioridad | Tipo | ID | Estado | Siguiente acción |', '|---|---|---|---|---|']
    clean = lambda value: str(value).replace('|', ' / ').replace('\n', ' ')
    for row in queue:
        lines.append('| ' + ' | '.join(clean(row[key]) for key in
                                     ('priority', 'category', 'id', 'status', 'acceptance')) + ' |')
    lines += ['', '## Obsolescencia', '',
              f"Diagnóstico: `{report['diagnostic_fingerprint']}`. Cambió respecto al último: {report['previous_result_obsolete']}.",
              f"Decisiones obsoletas: {sum(row['decision_stale'] for row in queue)}; se reabren y conservan su evidencia e historia.", '',
              '## Límites', ''] + ['- '+note for note in report['limits']]
    lines += ['', 'La base privada de Voces no se abre. No se modifica corpus, publica contenido, entrena, consulta un modelo ni accede a la red.', '',
              '## Fuentes locales', '', '| Archivo | SHA-256 |', '|---|---|']
    lines += [f'| {clean(key)} | {value or "ausente"} |' for key, value in report['sources'].items()]
    return '\n'.join(lines) + '\n'


def safe_destination(path):
    resolved = path.resolve()
    if resolved.is_relative_to(ROOT.resolve()) and not resolved.is_relative_to((ROOT / 'reports').resolve()):
        raise ValueError('Las salidas dentro del proyecto deben quedar en reports/.')
    if resolved.is_relative_to((ROOT / 'data').resolve()):
        raise ValueError('No se permite usar la base ni el directorio privado.')
    return resolved


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)+'\n', encoding='utf-8')
    temporary.replace(path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'reports/iterations/latest')
    parser.add_argument('--state', type=Path, default=ROOT / 'reports/iterations/state.json')
    parser.add_argument('--record-decision', type=Path, help='JSON explícito de decisión para una tarea actual.')
    parser.add_argument('--lesson-target', type=int, default=12,
                        help='Meta de lecturas editoriales; cero desactiva ampliación.')
    parser.add_argument('--occurrence-target', type=int, default=300,
                        help='Meta documental propuesta; cero desactiva la tarea de ampliación.')
    args = parser.parse_args(argv)
    output = safe_destination(args.output)
    state_path = safe_destination(args.state)
    if (state_path in {output / name for name in ('inventory.json', 'inventory.md', 'queue.json')}
            or output == state_path or output.is_relative_to(state_path)):
        raise ValueError('El estado y el informe necesitan archivos distintos.')
    if args.occurrence_target < 0 or args.lesson_target < 0:
        raise ValueError('La meta propuesta debe ser cero o positiva.')
    if args.record_decision:
        # Like report/state destinations, an input decision must stay outside private data.
        decision_input = safe_destination(args.record_decision)
        if decision_input.suffix != '.json':
            raise ValueError('La decisión debe ser un archivo JSON.')
    old = validate_state(json.loads(state_path.read_text(encoding='utf-8'))) if state_path.exists() else empty_state()
    sources = source_manifest()
    decision_path = ROOT / 'editorial/lesson-decisions.json'
    stored = json.loads(decision_path.read_text(encoding='utf-8')) if decision_path.exists() else dict(schema_version=1, decisions={})
    if stored.get('schema_version') != 1 or not isinstance(stored.get('decisions'), dict):
        raise ValueError('Decisiones editoriales inválidas; no se sobrescriben.')
    with tempfile.TemporaryDirectory(prefix='amoxcalli-iteration-') as directory:
        records = CorpusStore(Path(directory) / 'public.sqlite3').public_records()
        report, tasks = diagnose(records, Learning(Archive()), load_catalog(), sources, stored['decisions'], args.occurrence_target, args.lesson_target)
    if source_manifest() != sources:
        raise ValueError('Una fuente cambió durante el diagnóstico. Repetir sin escritores concurrentes.')
    state = reconcile(tasks, old, report['diagnostic_fingerprint'], stored['decisions'])
    if args.record_decision:
        state = record_decision(state, json.loads(decision_input.read_text(encoding='utf-8')))
    queue = queue_from_state(state)
    # Derive comparison from the persisted run sequence, making identical reruns byte-identical.
    report['previous_diagnostic_fingerprint'] = state['runs'][-2] if len(state['runs']) > 1 else None
    report['previous_result_obsolete'] = bool(report['previous_diagnostic_fingerprint'])
    report['tasks'] = dict(total=len(queue), statuses=dict(sorted(Counter(t['status'] for t in queue).items())),
                           categories=dict(sorted(Counter(t['category'] for t in queue).items())),
                           stale_decisions=sum(t['decision_stale'] for t in queue),
                           historical_tasks=sum(not t.get('present') for t in state['tasks'].values()))
    write_json(output / 'inventory.json', report)
    write_json(output / 'queue.json', dict(schema_version=1, diagnostic_fingerprint=report['diagnostic_fingerprint'], tasks=queue))
    (output / 'inventory.md').write_text(render_markdown(report, queue), encoding='utf-8')
    write_json(state_path, state)
    print(json.dumps(dict(counts=report['counts'], tasks=report['tasks'], source_fingerprint=report['source_fingerprint'],
                          llm_calls=0, network_requests=0), ensure_ascii=False, sort_keys=True))


if __name__ == '__main__':
    main()
