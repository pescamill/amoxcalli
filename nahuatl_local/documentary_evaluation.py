"""Batería documental v1: claves literales, grupos antes de split, cero modelos/red.

The recipe is deliberately fixed and validated by reconstruction. Changing its
selection or reference contract requires a new recipe, not accepting arbitrary
reference strings. No input under data/ is enumerated or opened.
"""
import argparse
from collections import Counter, defaultdict
import copy
import csv
import hashlib
import json
from pathlib import Path
import unicodedata

from .community import ROOT

RECIPE = 'documentary-fields-v1'
BUNDLES = (
    'corpus/seed.json', 'corpus/glyph-links-v2.json', 'corpus/archive-source-v3.json',
    'corpus/glyph-images-v4.json', 'corpus/glyph-lexicon-v5.json',
    'corpus/glyph-source-images-v5.json', 'corpus/gdn-lexicon-v6.json',
    'corpus/glyph-associations-v7.json', 'corpus/flor-lexicon-v8.json',
)
FIXED = ('corpus/editorial-releases.json', 'corpus/learning-v1.json',
         'corpus/pictography/catalog.json', 'corpus/axolotl/axolotl.csv',
         'configs/sources.json', 'nahuatl_local/documentary_evaluation.py', 'docs/EVALUACION_DOCUMENTAL.md')
UNCERTAINTY = 'Referencia literal del índice local; cotejo primario y juicio lingüístico pendientes.'


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n'


def normalized(value):
    """Conservative split-only comparison; originals and references stay intact."""
    return ' '.join(''.join(c for c in unicodedata.normalize('NFD', value.casefold())
                           if unicodedata.category(c) != 'Mn').split())


def public_path(root, relative):
    p = Path(relative)
    if p.is_absolute() or '..' in p.parts or not p.parts or p.parts[0] not in ('corpus', 'configs', 'nahuatl_local', 'docs', 'reports'):
        raise ValueError('Entrada fuera de la lista pública explícita.')
    candidate = root / p
    for part in (candidate, *candidate.parents):
        if part.is_symlink():
            raise ValueError('Una entrada pública no puede ser un enlace simbólico.')
        if part == root:
            break
    return candidate


def inputs(root=ROOT):
    root = Path(root)
    files = list(BUNDLES) + list(FIXED)
    manifest = json.loads(public_path(root, 'corpus/editorial-releases.json').read_text())
    for release in manifest['releases']:
        filename = 'corpus/' + release['bundle']
        if filename != 'corpus/editorial-' + release['id'] + '.json':
            raise ValueError('Publicación editorial inválida.')
        raw = public_path(root, filename).read_bytes()
        if hashlib.sha256(raw).hexdigest() != release['sha256']:
            raise ValueError('Publicación editorial obsoleta.')
        files.append(filename)
    hashes = {p: hashlib.sha256(public_path(root, p).read_bytes()).hexdigest() for p in sorted(set(files))}
    docs = {p: json.loads(public_path(root, p).read_text(encoding='utf-8')) for p in files if p.endswith('.json')}
    records, origins = {}, {}
    for path in list(BUNDLES) + [p for p in files if p.startswith('corpus/editorial-') and p != 'corpus/editorial-releases.json']:
        for r in docs[path].get('records', []):
            # Match admitted migration order; a reference cites the actual file
            # holding the final row, never a fabricated merged transcription.
            if 'kind' not in r:
                # Image backfill bundles contain patches, not replacement rows.
                # They do not supply lexical/source reference fields.
                if r['id'] not in records:
                    raise ValueError('Parche público sin registro previo.')
                records[r['id']] = dict(records[r['id']], **r)
            else:
                records[r['id']] = r
                origins[r['id']] = path
    records = public_dependency_filter(records)
    origins = {rid: path for rid, path in origins.items() if rid in records}
    ids = {e['archive_id'] for lesson in docs['corpus/learning-v1.json']['lessons'] for e in lesson['examples']}
    passages = {}
    # Axolotl has no header. The ID is the original 1-based CSV row index.
    with public_path(root, 'corpus/axolotl/axolotl.csv').open(encoding='utf-8', newline='') as f:
        for line, row in enumerate(csv.reader(f), 1):
            rid = f'axolotl-{line:05d}'
            if rid in ids:
                if len(row) < 5:
                    raise ValueError('Pasaje sin campos originales.')
                passages[rid] = row
    if set(passages) != ids:
        raise ValueError('Falta un pasaje publicado.')
    return dict(root=root, hashes=hashes, docs=docs, records=records, origins=origins, passages=passages)


def public_dependency_filter(records):
    """Apply the public dependency closure without opening any persistent store.

    A later private version hides the earlier public row. Source, sense and
    association dependencies use the same contract as CorpusStore.validate.
    Only the public keys retained here may enter split families or references.
    """
    visible = {rid: row for rid, row in records.items() if row.get('rights', {}).get('public') is True}
    while True:
        hidden = set()
        for rid, row in visible.items():
            dependencies = [row[k] for k in ('sense_id', 'primary_source_id') if row.get(k)]
            dependencies += row.get('sense_ids', [])
            dependencies += [e[k] for e in row.get('evidence', []) for k in ('source_id', 'via_source_id') if e.get(k)]
            association = row.get('association') or {}
            dependencies += [association[k] for k in ('reference_form_id', 'reference_glyph_id') if association.get(k)]
            if any(target not in visible for target in dependencies):
                hidden.add(rid)
        if not hidden:
            return visible
        visible = {rid: row for rid, row in visible.items() if rid not in hidden}


def partition_families(nodes):
    """Connected components from evidenced resources, not arbitrary group labels.

    A resource is a typed [reason, literal identifier] pair. All nodes sharing
    one are joined; the manifest records those pairs for independent inspection.
    """
    parent = {n['id']: n['id'] for n in nodes}
    if len(parent) != len(nodes):
        raise ValueError('ID de entidad duplicado.')

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    owners = {}
    for node in sorted(nodes, key=lambda n: n['id']):
        for kind, key in node['resources']:
            token = (kind, key)
            if token in owners:
                a, b = find(node['id']), find(owners[token])
                parent[max(a, b)] = min(a, b)
            else:
                owners[token] = node['id']
    groups = defaultdict(list)
    for node in nodes:
        groups[find(node['id'])].append(node)
    result, membership = [], {}
    for members in groups.values():
        member_ids = sorted(n['id'] for n in members)
        gid = 'family-' + digest(member_ids)[:20]
        for mid in member_ids:
            membership[mid] = gid
        resources = sorted({(kind, key) for n in members for kind, key in n['resources']})
        result.append(dict(id=gid, member_ids=member_ids, resources=[list(r) for r in resources]))
    return sorted(result, key=lambda g: g['id']), membership


def families(data):
    nodes = []
    for rid, r in sorted(data['records'].items()):
        if r['kind'] not in ('form', 'sense'):
            continue
        resources = [('lexical_id', rid)]
        if r['kind'] == 'form':
            resources.append(('lexical_id', r['sense_id']))
            for key in ('written', 'catalog_normalized'):
                if r.get(key):
                    resources.append(('lexical_spelling', normalized(r[key])))
            for alias in r.get('aliases', []):
                resources.append(('lexical_spelling', normalized(alias)))
            entry = r.get('source_entry', {})
            extraction = r.get('extraction', {})
            if entry.get('id') or extraction.get('entry_id'):
                resources.append(('catalog_entry', 'GDN:' + str(entry.get('id') or extraction['entry_id'])))
        nodes.append(dict(id='lex:' + rid, resources=resources))
    for rid, row in sorted(data['passages'].items()):
        # Whole works are reserved, a stronger boundary than duplicate passages.
        nodes.append(dict(id='passage:' + rid, resources=[('passage_id', rid),
                     ('passage_work', row[3]), ('passage_original', normalized(row[1]))]))
    catalog = data['docs']['corpus/pictography/catalog.json']
    pages = {p['id']: p for p in catalog['pages']}
    for table in ('documents', 'pages', 'zones', 'elements', 'occurrences'):
        for row in catalog[table]:
            resources = [('visual_id', row['id'])]
            if table == 'documents':
                doc = row['id']
            elif table in ('pages', 'elements'):
                doc = row['document_id']
            else:
                doc = pages[row['page_id']]['document_id']
            resources.append(('visual_document', doc))
            if row.get('page_id'):
                resources.append(('visual_id', row['page_id']))
            if row.get('zone_id'):
                resources.append(('visual_id', row['zone_id']))
            for component in row.get('components', []):
                resources.append(('visual_id', component['element_id']))
            if row.get('image'):
                resources.append(('image_url', row['image']))
            nodes.append(dict(id='visual:' + table + ':' + row['id'], resources=resources))
    return partition_families(nodes)


def field(data, path, table, rid, key):
    if table == 'csv':
        row = data['passages'][rid]
        value = row[{'es': 0, 'nah': 1, 'variant': 2, 'document': 3, 'iso': 4}[key]]
    else:
        row = next(r for r in data['docs'][path][table] if r['id'] == rid)
        value = row[key]
    return dict(path=path, table=table, record_id=rid, field=key,
                value=copy.deepcopy(value), row_sha256=digest(row), file_sha256=data['hashes'][path])


def record_field(data, rid, key):
    return field(data, data['origins'][rid], 'records', rid, key)


def permission(data, refs, visual):
    rights = []
    for ref in refs:
        if ref['table'] == 'records':
            r = next(r for r in data['docs'][ref['path']]['records'] if r['id'] == ref['record_id'])
            item = dict(path=ref['path'], record_id=r['id'], original_rights=copy.deepcopy(r['rights']))
            if item not in rights:
                rights.append(item)
    if visual:
        rights.append(dict(path='corpus/pictography/catalog.json',
                           original_rights=copy.deepcopy(data['docs']['corpus/pictography/catalog.json']['rights'])))
    if any(r['table'] == 'csv' for r in refs):
        rights.append(dict(path='configs/sources.json',
                           original_rights_note=data['docs']['configs/sources.json']['corpus']['rights_note']))
    return dict(local_documentary_fields='authorized_local_scope',
                basis='Instrucción humana del ciclo 005: preparar y validar consultas de los campos públicos ya distribuidos para consulta local.',
                source_conditions=rights, evaluation=False, training=False,
                image_model_input=False, image_copy=False, external_send=False,
                image_evaluation_status='pending_rights_and_execution' if visual else 'not_applicable',
                limits='Este alcance operativo local no concede una licencia nueva, redistribución, entrenamiento ni procesamiento de imágenes por un modelo.')


def query(data, membership, ids, suffix, modality, split, task, question, refs, source_ids, urls, responsibility, interpretation):
    groups = sorted({membership[mid] for mid in ids})
    if len(groups) != 1:
        raise ValueError('La consulta cruza familias; reformular antes del split.')
    # IDs refer to documented entities and task, unaffected by row ordering.
    rid = 'doc-' + modality + '-' + suffix + '-' + digest(ids)[:16]
    return dict(id=rid, group_id=groups[0], entity_ids=ids, modality=modality, split=split,
                task=task, question=question,
                reference=dict(fields=refs, source_ids=sorted(set(source_ids)), urls=sorted(set(urls)),
                               attributed_responsibility=responsibility, interpretation=interpretation),
                reference_authority='documentary', review_status='source_derived_not_human_validated',
                uncertainty=UNCERTAINTY, rights=permission(data, refs, modality == 'visual'),
                source_hashes={r['path']: data['hashes'][r['path']] for r in refs})


def build(root=ROOT):
    data = inputs(root)
    group_rows, membership = families(data)
    records = data['records']
    catalog = data['docs']['corpus/pictography/catalog.json']
    forms = sorted((r for r in records.values() if r['kind'] == 'form'), key=lambda r: r['id'])
    form_groups = defaultdict(list)
    for form in forms:
        form_groups[membership['lex:' + form['id']]].append(form)
    # Do not use pictographic designations to teach/choose lexical references
    # across the manuscript reserve. A shared label is not a linguistic merger.
    pict_labels = {normalized(e['designation']) for e in catalog['elements']}
    eligible = []
    excluded = []
    for gid, fs in sorted(form_groups.items()):
        if any(normalized(f.get(k, '')) in pict_labels for f in fs for k in ('written', 'catalog_normalized')):
            excluded.append(gid)
            continue
        if all(data['origins'][f['id']] in ('corpus/gdn-lexicon-v6.json', 'corpus/editorial-batch-007-v9.json')
               and f.get('catalog_normalized') and f.get('url') and f['verification'] == 'catalog_checked'
               and f['sense_id'] in records for f in fs):
            eligible.append((gid, fs))
    # Reserve by family hash before selecting task references, never by scores.
    lexical_reserve = [(g, fs) for g, fs in eligible if int(digest(g)[:8], 16) % 5 == 0][:12]
    reserved_ids = {g for g, _ in lexical_reserve}
    development = [(g, fs) for g, fs in eligible if g not in reserved_ids]
    # Include all ambiguous groups first, then spread singletons by spelling.
    ambiguous = sorted((item for item in development if len(item[1]) > 1), key=lambda item: item[0])
    initials = defaultdict(list)
    for item in sorted(development, key=lambda item: (normalized(item[1][0]['written']), item[0])):
        if len(item[1]) == 1:
            initials[normalized(item[1][0]['written'])[:1]].append(item)
    development = ambiguous
    while any(initials.values()):
        for initial in sorted(initials):
            if initials[initial]:
                development.append(initials[initial].pop(0))
    selected = [('development', g, fs) for g, fs in development[:44]] + [('reserve', g, fs) for g, fs in lexical_reserve]
    queries = []
    for split, gid, fs in selected:
        label = ' / '.join(f['written'] for f in fs)
        refs = []
        source_ids, urls = [], []
        for f in fs:
            refs += [record_field(data, f['id'], k) for k in ('written', 'catalog_normalized', 'sense_id', 'evidence')]
            refs.append(record_field(data, f['sense_id'], 'definition'))
            source_ids += [e[k] for e in f['evidence'] for k in ('source_id', 'via_source_id') if e.get(k)]
            urls.append(f['url'])
        owners = sorted({records[s]['author'] for s in source_ids if s in records})
        ids = ['lex:' + f['id'] for f in fs]
        queries.append(query(data, membership, ids, 'gloss', 'textual', split, 'lexical',
                       f'¿Qué glosa histórica registra la ficha de {label}? Conserva todas las acepciones registradas y cita sus entradas.',
                       refs, source_ids, urls, owners,
                       'Glosa literal de las fichas; no traducción nueva ni elección de una acepción fuera de contexto.'))
        queries.append(query(data, membership, ids, 'spelling', 'textual', split, 'comparison',
                       f'Compara la escritura original y la normalización catalogada de {label}. ¿Coinciden y qué ID de acepción corresponde a cada ficha?',
                       refs, source_ids, urls, owners,
                       'Comparar los campos written y catalog_normalized sin sustituir la paleografía; conservar IDs de todas las acepciones.'))
    # Whole document reservation prevents versions/parallel passages crossing.
    works = sorted({row[3] for row in data['passages'].values()})
    reserve_works = works[-2:]
    config = data['docs']['configs/sources.json']['corpus']
    archive_url = f"https://github.com/{config['repository']}/blob/{config['revision']}/{config['path']}"
    for rid, row in sorted(data['passages'].items()):
        split = 'reserve' if row[3] in reserve_works else 'development'
        refs = [field(data, 'corpus/axolotl/axolotl.csv', 'csv', rid, k) for k in ('nah', 'es', 'document', 'iso')]
        queries.append(query(data, membership, ['passage:' + rid], 'parallel', 'textual', split, 'comparison',
                       f'En {row[3]}, registro {rid}, ¿qué original náhuatl acompaña a la traducción española conservada? Cita ambos sin corregirlos e identifica la variedad declarada.',
                       refs, ['src-axolotl'], [archive_url], [config['citation']],
                       'Alineación heredada del CSV, no traducción producida por un modelo; folio primario pendiente.'))
    pages = {p['id']: p for p in catalog['pages']}
    documents = {d['id']: d for d in catalog['documents']}
    elements = {e['id']: e for e in catalog['elements']}
    # Six distinct observation needs; select by documentary availability, not
    # model performance. Manuscript reserve is fixed before these choices.
    tasks = [('designation-reading', 14), ('component-value', 12), ('citation', 8),
             ('segmentation', 8), ('unexpressed', 4), ('link-absence', 8)]
    for split in ('development', 'reserve'):
        for suffix, count in tasks:
            candidates = []
            for o in sorted(catalog['occurrences'], key=lambda r: r['id']):
                docid = pages[o['page_id']]['document_id']
                if (docid == 'telleriano') != (split == 'development'):
                    continue
                if suffix in ('designation-reading', 'component-value', 'link-absence') and not o['components']:
                    continue
                if suffix == 'component-value' and not any(c['values'] for c in o['components']):
                    continue
                if suffix == 'citation' and not o['citations']:
                    continue
                if suffix == 'segmentation' and not o['segmentation']:
                    continue
                if suffix == 'unexpressed' and not o['unexpressed']:
                    continue
                if suffix == 'link-absence' and not any(not elements[c['element_id']]['lexical_links'] for c in o['components']):
                    continue
                candidates.append(o)
            # Spread over pages using stable round robin, including omissions.
            by_page = defaultdict(list)
            for o in candidates:
                by_page[o['page_id']].append(o)
            spread = []
            while any(by_page.values()):
                for pid in sorted(by_page):
                    if by_page[pid]:
                        spread.append(by_page[pid].pop(0))
            limit = count if split == 'development' else max(1, count // 3)
            for o in spread[:limit]:
                p = pages[o['page_id']]
                doc = documents[p['document_id']]
                refs = [field(data, 'corpus/pictography/catalog.json', 'occurrences', o['id'], k)
                        for k in ('code', 'page_id', 'reading', 'image')]
                refs += [field(data, 'corpus/pictography/catalog.json', 'pages', p['id'], k)
                         for k in ('image', 'source_hash', 'locator')]
                if suffix in ('designation-reading', 'component-value', 'link-absence'):
                    refs.append(field(data, 'corpus/pictography/catalog.json', 'occurrences', o['id'], 'components'))
                    for component in o['components']:
                        e = elements[component['element_id']]
                        refs += [field(data, 'corpus/pictography/catalog.json', 'elements', e['id'], k)
                                 for k in ('designation', 'designation_status', 'lexical_links')]
                else:
                    refs.append(field(data, 'corpus/pictography/catalog.json', 'occurrences', o['id'],
                                      {'citation': 'citations', 'segmentation': 'segmentation', 'unexpressed': 'unexpressed'}[suffix]))
                prompts = {
                    'designation-reading': '¿Qué denominaciones tienen sus elementos y qué lectura consigna la aparición? Mantén separados esos campos.',
                    'component-value': '¿Qué valor consigna cada componente? Distingue denominación y valor contextual y registra valores vacíos.',
                    'citation': '¿Qué citas consigna la ficha? Contrástalas con la lectura del conjunto sin reconstruir una lectura nueva.',
                    'segmentation': '¿Qué segmentación conserva la ficha? Copia sus marcas de duda sin convertirlas en análisis validado.',
                    'unexpressed': '¿Qué elementos declara como no expresados? Contrasta ese campo con la lectura catalogada.',
                    'link-absence': '¿Qué componentes carecen de vínculo léxico explícito? Identifica sus denominaciones; una lista vacía no prueba ausencia en la lengua.',
                }
                queries.append(query(data, membership, ['visual:occurrences:' + o['id']], suffix, 'visual', split, 'observation',
                               f'Consulta documental de {doc["title"]}, lámina {p["locator"]}, código {o["code"]}. {prompts[suffix]}',
                               refs, ['src-tlachia', doc['id']], [o['url'], o['image'], p['image']], [doc['attribution']],
                               'Observación de campos del catálogo con URL de imagen de referencia; imagen no descargada ni procesada.'))
    queries.sort(key=lambda q: q['id'])
    partition = []
    for group in group_rows:
        splits = sorted({q['split'] for q in queries if q['group_id'] == group['id']})
        partition.append(dict(group, split=splits[0] if len(splits) == 1 else 'unused' if not splits else 'overlap'))
    return dict(schema_version=1, recipe=RECIPE, reference_kind='literal_public_documentary_fields',
                scope=dict(prepared=True, retrieval_executed=False, visual_model_executed=False,
                           human_validation=False, training=False, evaluation=False,
                           image_model_input=False, image_copy=False, external_send=False),
                source_hashes=data['hashes'], queries=queries, partition=partition,
                split_policy=dict(lexical='Familias por acepción, entrada y escritura; 1/5 por hash antes de selección; 12 familias de reserva.',
                                  passages='Obras completas: las dos últimas por título ordenado se reservan; duplicados originales se agrupan.',
                                  visual='Telleriano desarrollo; Calpan y MH-Tianquiztenco reserva; manuscrito/lámina/zonas/componentes/URLs compartidos forman familias.',
                                  reserve_works=reserve_works, excluded_lexical_pictographic_families=excluded,
                                  linguistic_scope='Agrupación contra fuga documental, sin fusionar fuentes ni sentidos. Denominaciones compartidas entre manuscritos siguen presentes; no se mide generalización a conceptos desconocidos.'),
                limits=['Consultas parametrizadas a campos publicados; no preguntas de comprensión humana.',
                        'Reserva pequeña fijada por evidencia; no calibrada con resultados ni usada para elegir cambios.',
                        'Hashes locales y hashes de extracción heredados; no verificación remota actual ni licencia nueva.',
                        'URLs de imágenes únicamente: evaluación VLM pendiente de derechos y ejecución.'])


def overlap_report(battery):
    """Check actual referenced IDs/images and all family resources across splits."""
    sets = {split: defaultdict(set) for split in ('development', 'reserve')}
    groups = {g['id']: g for g in battery.get('partition', [])}
    for q in battery.get('queries', []):
        split = q['split']
        sets[split]['groups'].add(q['group_id'])
        sets[split]['entities'].update(q['entity_ids'])
        for ref in q['reference']['fields']:
            sets[split]['referenced_records'].add((ref['path'], ref['table'], ref['record_id']))
            if ref['field'] == 'image':
                sets[split]['images'].add(ref['value'])
        for resource in groups[q['group_id']]['resources']:
            sets[split]['family_resources'].add(tuple(resource))
    return {key: sorted(sets['development'][key] & sets['reserve'][key])
            for key in ('groups', 'entities', 'referenced_records', 'images', 'family_resources')}


def validate(battery, root=ROOT):
    """Reject stale/tampered keys, permission escalation and fake grouping.

    Reconstruction is part of the contract, not a claim of semantic correctness.
    This v1 accepts only its documented selection recipe, not arbitrary fixtures.
    """
    expected = build(root)
    errors = []
    if not isinstance(battery, dict):
        errors.append('battery_not_object')
        battery = {}
    for key in expected:
        if battery.get(key) != expected[key]:
            errors.append('mismatch:' + key)
    if set(battery) != set(expected):
        errors.append('unexpected_or_missing_top_level_fields')
    try:
        overlaps = overlap_report(battery)
        if any(overlaps.values()):
            errors.append('split_overlap')
    except (KeyError, TypeError, ValueError):
        overlaps = {}
        errors.append('invalid_partition_or_reference')
    queries = battery.get('queries', [])
    counts = {split: {modality: sum(isinstance(q, dict) and q.get('split') == split and q.get('modality') == modality for q in queries)
                      for modality in ('textual', 'visual')} for split in ('development', 'reserve')} if isinstance(queries, list) else {}
    if not counts or counts['development']['textual'] < 100 or counts['development']['visual'] < 50 or not all(counts['reserve'].values()):
        errors.append('insufficient_documentary_queries')
    return dict(schema_version=1, validator=RECIPE, valid=not errors, errors=errors,
                evaluation_sha256=digest(battery), source_hashes=expected['source_hashes'], counts=counts,
                overlaps=overlaps, task_counts=dict(sorted(Counter(q['task'] for q in queries if isinstance(q, dict) and 'task' in q).items())),
                scope=expected['scope'], reference_validation='Exact reconstruction from original public fields, row/file hashes, attribution and evidenced families.',
                model_calls=0, network_requests=0, image_downloads=0)


def load_development(path=None, modality=None, root=ROOT):
    """No split argument: the adjustment helper can never return reserve keys."""
    root = Path(root)
    path = Path(path) if path is not None else root / 'configs/documentary-evaluation-v1.json'
    if not path.is_absolute():
        path = root / path
    if path != root / 'configs/documentary-evaluation-v1.json':
        raise ValueError('El helper solo admite la batería pública fija; no abre rutas privadas o alternativas.')
    path = public_path(root, 'configs/documentary-evaluation-v1.json')
    battery = json.loads(path.read_text(encoding='utf-8'))
    report = validate(battery, root)
    if not report['valid']:
        raise ValueError('Batería obsoleta o inválida: ' + ', '.join(report['errors']))
    if modality not in (None, 'textual', 'visual'):
        raise ValueError('Modalidad inválida.')
    return copy.deepcopy([q for q in battery['queries'] if q['split'] == 'development' and (modality is None or q['modality'] == modality)])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Validar sin escribir.')
    args = parser.parse_args(argv)
    path = public_path(ROOT, 'configs/documentary-evaluation-v1.json')
    battery = json.loads(path.read_text(encoding='utf-8')) if args.check else build()
    report = validate(battery)
    if not report['valid']:
        raise ValueError(', '.join(report['errors']))
    if not args.check:
        output = public_path(ROOT, 'reports/documentary-evaluation-validation-v1.json')
        if path.exists() and path.read_text(encoding='utf-8') != encoded(battery):
            old = path.read_bytes()
            backup = public_path(ROOT, 'reports/documentary-evaluation-backups/' + hashlib.sha256(old).hexdigest() + '.json')
            backup.parent.mkdir(parents=True, exist_ok=True)
            if backup.exists() and backup.read_bytes() != old:
                raise ValueError('Respaldo previo inconsistente; no se sobrescribe.')
            backup.write_bytes(old)
        path.write_text(encoded(battery), encoding='utf-8')
        output = public_path(ROOT, 'reports/documentary-evaluation-validation-v1.json')
        output.write_text(encoded(report), encoding='utf-8')
    print(encoded({k: report[k] for k in ('valid', 'counts', 'task_counts', 'overlaps', 'evaluation_sha256')}), end='')


if __name__ == '__main__':
    main()
