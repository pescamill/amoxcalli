"""Prepare immutable spelling-match candidates from public data, never apply links."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import tempfile
import unicodedata

from .community import ROOT
from .corpus import CorpusStore
from .documentary_retrieval import BUNDLES, public_records
from .editorial_pipeline import encoded
from .lesson_review_packet import safe_path
from .pictography import load_catalog, validate

CONTEXT_LIMIT = 3
NOTICE = 'Coincidencia de escritura; no prueba equivalencia de sentido ni lectura de toda la imagen.'
IMPLEMENTATION = ('nahuatl_local/lexical_link_review.py', 'nahuatl_local/corpus.py',
                  'nahuatl_local/community.py', 'nahuatl_local/documentary_retrieval.py',
                  'nahuatl_local/pictography.py', 'nahuatl_local/lesson_review_packet.py',
                  'nahuatl_local/editorial_pipeline.py', 'docs/CANDIDATOS_CONEXIONES_LEXICAS.md')
MEMBERS = {'candidates.json', 'candidates.md'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def fingerprint(value):
    return sha(encoded(value))


def match_key(value):
    return unicodedata.normalize('NFC', value).casefold().strip()


def source_snapshot():
    # Preflight every fixed path before the temporary store may open it.
    paths = ['corpus/' + name for name in BUNDLES]
    paths += ['corpus/editorial-releases.json', 'corpus/pictography/catalog.json',
              'nahuatl_local/community_web/catalog.json', *IMPLEMENTATION]
    for name in paths:
        safe_path(name)
    release_path = safe_path('corpus/editorial-releases.json')
    releases = json.loads(release_path.read_bytes())
    if releases.get('schema_version') != 1 or not isinstance(releases.get('releases'), list):
        raise ValueError('Registro de publicaciones inválido.')
    seen = set()
    for row in releases['releases']:
        rid = row.get('id', '')
        if (not re.fullmatch(r'[a-z0-9][a-z0-9-]{1,79}', rid) or rid in seen
                or row.get('bundle') != f'editorial-{rid}.json'):
            raise ValueError('Publicación fuera del contrato público.')
        name = 'corpus/' + row['bundle']
        safe_path(name)
        paths.append(name)
        seen.add(rid)
    raw = {name: safe_path(name).read_bytes() for name in sorted(set(paths))}
    for row in releases['releases']:
        if sha(raw['corpus/' + row['bundle']]) != row.get('sha256'):
            raise ValueError('Publicación editorial obsoleta.')
    # These files are references only. No CSV, battery/reserve, DB, image or URL is opened.
    origins = {}
    for name in paths:
        if name.startswith('corpus/') and name != 'corpus/pictography/catalog.json':
            for row in json.loads(raw[name]).get('records', []):
                origins.setdefault(row['id'], []).append(dict(path=name, file_sha256=sha(raw[name]),
                                                             row_sha256=fingerprint(row), row=copy.deepcopy(row)))
    return {name: sha(value) for name, value in raw.items()}, origins


def blank_review():
    return dict(status='pending', reviewer='', date='', decision='', evidence=[], notes='')


def build_candidates(records, catalog, sources, origins):
    """Pure selection: no homonym merging, inference, fuzzy match or accent removal."""
    validate(catalog)
    records = public_records({rid: row for rid, row in records.items() if not row.get('withdrawn')})
    forms = [r for r in records.values() if r['kind'] == 'form' and r.get('sense_id') in records
             and records[r['sense_id']]['kind'] == 'sense']
    by_spelling = {}
    for form in forms:
        if form.get('written'):
            by_spelling.setdefault(match_key(form['written']), []).append(form)
    pages = {row['id']: row for row in catalog['pages']}
    docs = {row['id']: row for row in catalog['documents']}
    zones = {row['id']: row for row in catalog['zones']}
    occurrences = {}
    for row in sorted(catalog['occurrences'], key=lambda r: r['id']):
        for component in row['components']:
            occurrences.setdefault(component['element_id'], []).append(row)
    candidates = []
    matched = excluded = 0
    def snapshot(row):
        # A public current row must not republish a private/withdrawn original,
        # or an older version whose evidence depends on a now-hidden record.
        public_origins = []
        for origin in origins.get(row['id'], []):
            original = origin['row']
            if (not original.get('withdrawn') and original.get('rights', {}).get('public') is True
                    and row['id'] in public_records({**records, row['id']: original})):
                public_origins.append(copy.deepcopy(origin))
        return dict(record=copy.deepcopy(row), public_row_sha256=fingerprint(row),
                    source_rows=public_origins)
    for element in sorted(catalog['elements'], key=lambda r: r['id']):
        linked = {row['sense_id'] for row in element.get('lexical_links', [])}
        for form in sorted(by_spelling.get(match_key(element['designation']), []), key=lambda r: r['id']):
            matched += 1
            if form['sense_id'] in linked:
                excluded += 1
                continue
            sense = records[form['sense_id']]
            evidence_sources = set()
            for row in (form, sense):
                if row.get('primary_source_id'):
                    evidence_sources.add(row['primary_source_id'])
                for evidence in row.get('evidence', []):
                    evidence_sources.update(evidence[k] for k in ('source_id', 'via_source_id') if evidence.get(k))
            contexts = []
            # A component can appear more than once in a row: count each appearance once.
            found = {row['id']: row for row in occurrences.get(element['id'], [])}
            for row in list(found.values())[:CONTEXT_LIMIT]:
                page = pages[row['page_id']]
                contexts.append(dict(occurrence=copy.deepcopy(row), occurrence_row_sha256=fingerprint(row),
                                     page=copy.deepcopy(page), page_row_sha256=fingerprint(page),
                                     zone=copy.deepcopy(zones.get(row.get('zone_id'))),
                                     catalogued_values=[copy.deepcopy(c['values']) for c in row['components']
                                                        if c['element_id'] == element['id']]))
            ids = dict(element_id=element['id'], form_id=form['id'], sense_id=sense['id'])
            candidate = dict(id='designation-form-' + fingerprint(ids), **ids,
                             match=dict(method='exact_original' if element['designation'] == form['written']
                                        else 'NFC_casefold_strip', key=match_key(form['written']),
                                        accent_removal=False, notice=NOTICE),
                             element=copy.deepcopy(element), element_row_sha256=fingerprint(element),
                             catalog_rights=copy.deepcopy(catalog['rights']),
                             document=copy.deepcopy(docs[element['document_id']]),
                             form=snapshot(form), sense=snapshot(sense),
                             sources=[snapshot(records[rid]) for rid in sorted(evidence_sources)
                                      if rid in records and records[rid]['kind'] == 'source'],
                             contexts=dict(total=len(found), shown=len(contexts), omitted=len(found)-len(contexts),
                                           limit=CONTEXT_LIMIT, selection='ID ascending; not semantic representativeness',
                                           occurrences=contexts), human_review=blank_review())
            candidate['fingerprint'] = fingerprint(candidate)
            candidates.append(candidate)
    counts = dict(elements=len(catalog['elements']),
                  elements_without_registered_links=sum(not e.get('lexical_links') for e in catalog['elements']),
                  registered_links=sum(len(e.get('lexical_links', [])) for e in catalog['elements']),
                  public_forms=len(forms), matched_form_pairs=matched, excluded_existing_sense_pairs=excluded,
                  candidates=len(candidates), candidate_elements=len({c['element_id'] for c in candidates}),
                  candidate_senses=len({c['sense_id'] for c in candidates}))
    return dict(schema_version=1, kind='lexical_link_review_candidates', source_hashes=copy.deepcopy(sources),
                source_fingerprint=fingerprint(sources), counts=counts,
                matching='Exact original or NFC + casefold + strip; no accent removal, morphology or fuzzy matching.',
                notice=NOTICE, human_review='pending',
                scope=dict(public_temporary_store=True, private_database_opened=False, corpus_modified=False,
                           links_applied=0, network_requests=0, image_downloads=0, model_calls=0,
                           training=False, reserve_used=False), candidates=candidates)


def build():
    sources, origins = source_snapshot()
    # Always pass an explicit temporary filename; never instantiate the default Voces DB.
    with tempfile.TemporaryDirectory(prefix='amoxcalli-lexical-link-review-') as directory:
        records = CorpusStore(Path(directory) / 'public.sqlite3').public_records()
    report = build_candidates(records, load_catalog(safe_path('corpus/pictography/catalog.json')), sources, origins)
    current, _ = source_snapshot()
    if current != sources:
        raise ValueError('Una fuente cambió durante la preparación.')
    return report


def literal(value):
    # HTML escaping + numeric pipes/newlines keep original labels safe in Markdown tables.
    import html
    return html.escape(str(value)).replace('|', '&#124;').replace('\n', '&#10;').replace('\r', '&#13;')


def render(report):
    lines = ['# Candidatos de conexión léxica', '', NOTICE, '',
             'Revisión humana: **pendiente**. No se aplican vínculos ni permisos nuevos.', '',
             f"{report['counts']['candidates']} pares candidatos; {report['counts']['candidate_elements']} elementos; "
             f"{report['counts']['excluded_existing_sense_pairs']} pares excluidos por acepción ya vinculada.", '',
             'Comparación: escritura original exacta o NFC + casefold + espacios exteriores. Se conservan acentos y originales.', '',
             'Los contextos son hasta tres apariciones por ID; no son una muestra semántica. El JSON conserva filas completas, '
             'variantes, estados, condiciones de uso, fuentes y hashes. Las URLs son referencias; no se consultaron.', '']
    for c in report['candidates']:
        e, f, s = c['element'], c['form']['record'], c['sense']['record']
        lines += [f"## {literal(e['designation'])} ↔ {literal(f['written'])}", '',
                  f"ID: `{c['id']}`. Método: `{c['match']['method']}`. Estado: **pending**.", '',
                  f"Elemento: `{e['id']}` · código {literal(e['code'])} · {literal(c['document']['title'])}.",
                  'Significados catalogados: ' + literal(json.dumps(e.get('meanings', []), ensure_ascii=False)) + '.',
                  f"Forma: `{f['id']}` · acepción: `{s['id']}` · {literal(f.get('variant_label', ''))}.",
                  'Glosa conservada: ' + literal(s.get('definition', '')) + '.', '',
                  'Fuente del elemento: ' + literal(e['url']),
                  'Condiciones del catálogo: ' + literal(c['catalog_rights']['note']),
                  'Condiciones de la forma: ' + literal(f['rights'].get('note', '')), '']
        for row in c['sources']:
            source = row['record']
            lines.append(f"Fuente léxica: `{source['id']}` · {literal(source.get('label', ''))} · {literal(source.get('url', ''))}.")
        for ev in f.get('evidence', []):
            lines.append(f"Localizador léxico: {literal(ev.get('locator', ''))} · estado `{ev.get('status', '')}`.")
        lines += ['', f"Contextos: {c['contexts']['shown']} de {c['contexts']['total']}; omitidos: {c['contexts']['omitted']}."]
        for ctx in c['contexts']['occurrences']:
            occurrence = ctx['occurrence']
            lines.append(f"- `{occurrence['id']}` · {literal(ctx['page']['locator'])} · lectura catalogada: "
                         f"{literal(occurrence['reading'])} · valores del componente: "
                         f"{literal(json.dumps(ctx['catalogued_values'], ensure_ascii=False))} · {literal(occurrence['url'])}")
        lines += ['', 'Revisor: ____ · fecha: ____ · decisión y evidencia: ____ · notas: ____', '',
                  f"Fingerprint del candidato: `{c['fingerprint']}`.", '']
    lines += ['## Fuentes y alcance', '', 'Las decisiones deben anotarse en un archivo aparte; este paquete es inmutable.', '']
    lines += [f'- `{path}` · SHA-256 `{value}`' for path, value in sorted(report['source_hashes'].items())]
    return '\n'.join(lines) + '\n'


def output_path(path):
    path = safe_path(path, output=True)
    parts = path.relative_to(ROOT).parts
    if len(parts) < 3 or parts[:2] != ('reports', 'lexical-link-review'):
        raise ValueError('Usa una carpeta nueva bajo reports/lexical-link-review/.')
    # Reject every existing member symlink before reading any package or source.
    if path.exists():
        if not path.is_dir() or {p.name for p in path.iterdir()} != MEMBERS:
            raise ValueError('El paquete existente tiene miembros distintos; no se sobrescriben notas.')
        for name in MEMBERS:
            member = safe_path(path / name)
            if not member.is_file():
                raise ValueError('Miembro inválido; no se sobrescriben notas.')
    return path


def prepare(path, check=False):
    output = output_path(path)
    if check and not output.exists():
        raise ValueError('Falta el paquete de candidatos.')
    report = build()
    files = {'candidates.json': encoded(report), 'candidates.md': render(report).encode('utf-8')}
    if output.exists():
        if any((output / name).read_bytes() != raw for name, raw in files.items()):
            raise ValueError('Paquete editado o fuentes obsoletas; usa una salida nueva. No se sobrescriben notas.')
        return 'valid' if check else 'unchanged', report['counts']
    output.mkdir(parents=True)
    for name, raw in files.items():
        with safe_path(output / name).open('xb') as handle:
            handle.write(raw)
    return 'prepared', report['counts']


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--check', action='store_true', help='Reconstruir fuentes, IDs y relaciones sin escribir.')
    args = parser.parse_args(argv)
    state, counts = prepare(args.output, args.check)
    print(json.dumps(dict(state=state, counts=counts, links_applied=0, network_requests=0, model_calls=0)))


if __name__ == '__main__':
    main()
