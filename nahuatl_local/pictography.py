"""Public documentary index, separate from lexical senses and personal data."""
import json
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / 'corpus/pictography/catalog.json'
SOURCE_HOST = 'tlachia.iib.unam.mx'
TOPICS = {'01': 'Cuerpo humano', '02': 'Fauna', '03': 'Flora', '04': 'Cosmos',
          '05': 'Artefactos', '06': 'Numerales', '07': 'Formas', '08': 'Colores',
          '09': 'Indeterminados'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def source_url(value, image=False):
    parsed = urlparse(value)
    require(parsed.scheme == 'https' and parsed.hostname == SOURCE_HOST
            and not parsed.username and not parsed.password, 'Enlace documental no permitido.')
    if image:
        require(parsed.path.startswith('/archivos/') and '/imagenes/' in parsed.path,
                'La imagen debe proceder del catálogo documental.')
    return value


def validate(data):
    require(data.get('schema_version') == 1, 'Versión pictográfica desconocida.')
    require(data.get('rights', {}).get('training') is False, 'Este índice no autoriza entrenamiento.')
    require(data.get('rights', {}).get('note'), 'Faltan condiciones de consulta.')
    for key in ('documents', 'pages', 'zones', 'elements', 'occurrences'):
        require(isinstance(data.get(key), list), 'Falta la colección ' + key)
        ids = [row.get('id') for row in data[key]]
        require(all(isinstance(rid, str) and re.fullmatch(r'[A-Za-z0-9._:-]+', rid)
                    for rid in ids) and len(ids) == len(set(ids)), 'IDs inválidos o duplicados en ' + key)
    docs = {d['id']: d for d in data['documents']}
    pages = {p['id']: p for p in data['pages']}
    zones = {z['id']: z for z in data['zones']}
    elements = {e['id']: e for e in data['elements']}
    for d in docs.values():
        require(d.get('title') and d.get('attribution') and d.get('scope'), 'Documento sin alcance o atribución.')
        source_url(d['url'])
    for p in pages.values():
        require(p.get('document_id') in docs and p.get('locator'), 'Lámina sin documento o localizador.')
        require(re.fullmatch(r'[a-f0-9]{64}', p.get('source_hash', '')), 'Hash documental inválido.')
        source_url(p['url'])
        if p.get('image'): source_url(p['image'], True)
    for z in zones.values():
        require(z.get('page_id') in pages and z.get('code'), 'Zona sin lámina o código.')
        if z.get('image'): source_url(z['image'], True)
    for e in elements.values():
        require(e.get('document_id') in docs and e.get('designation') and e.get('code'), 'Elemento incompleto.')
        require(e.get('designation_status') == 'catalog_label', 'No se debe inferir certeza de una denominación.')
        source_url(e['url'])
        if e.get('image'): source_url(e['image'], True)
        require(isinstance(e.get('lexical_links', []), list), 'Vínculos léxicos inválidos.')
        for relation in e.get('lexical_links', []):
            require(relation.get('relation') == 'designation' and relation.get('sense_id')
                    and relation.get('note'), 'El enlace léxico necesita un alcance explícito.')
    for o in data['occurrences']:
        require(o.get('page_id') in pages and o.get('kind') in ('glyph', 'personage'), 'Aparición sin lámina o tipo.')
        require(o.get('code') and o.get('reading') and o.get('verification') == 'catalog_checked', 'Aparición sin lectura atribuida.')
        source_url(o['url'])
        if o.get('image'): source_url(o['image'], True)
        if o.get('zone_id'):
            require(o['zone_id'] in zones and zones[o['zone_id']]['page_id'] == o['page_id'], 'Zona de otra lámina.')
        require(isinstance(o.get('components'), list) and isinstance(o.get('citations'), list), 'Análisis incompleto.')
        for c in o['components']:
            require(c.get('element_id') in elements, 'Componente sin elemento.')
            require(elements[c['element_id']]['document_id'] == pages[o['page_id']]['document_id'], 'Elemento de otro documento.')
            require(isinstance(c.get('values'), list) and all(isinstance(v, str) and v for v in c['values']), 'Valores inválidos.')
    return data


def load_catalog(path=CATALOG):
    return validate(json.loads(Path(path).read_text(encoding='utf-8')))


def public_catalog(records, path=CATALOG):
    data = load_catalog(path)
    # Resolve links only against current PUBLIC lexical records. Nothing is inferred.
    available = {rid for rid, row in records.items() if row['kind'] == 'sense'}
    for element in data['elements']:
        element['lexical_links'] = [r for r in element.get('lexical_links', []) if r['sense_id'] in available]
        element['topic'] = TOPICS.get(element['code'][:2], 'Sin clasificación temática')
    data['summary'] = {'documents': len(data['documents']), 'pages': len(data['pages']),
                       'zones': len(data['zones']), 'elements': len(data['elements']),
                       'glyphs': sum(o['kind'] == 'glyph' for o in data['occurrences']),
                       'personages': sum(o['kind'] == 'personage' for o in data['occurrences']),
                       'components': sum(len(o['components']) for o in data['occurrences'])}
    return data
