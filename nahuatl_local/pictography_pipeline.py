"""Extract bounded Tlachia pages without a model; preserve labels and exceptions."""
import argparse
import hashlib
import json
import ssl
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import urlopen
from .pictography import ROOT, source_url, validate, require

VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}


class Node:
    def __init__(self, tag='', attrs=()):
        self.tag, self.attrs, self.children = tag, dict(attrs), []

    def text(self):
        return ' '.join(''.join(c.text() if isinstance(c, Node) else c for c in self.children).split())

    def walk(self, skip_articles=False):
        for child in self.children:
            if isinstance(child, Node):
                if skip_articles and child.tag == 'article': continue
                yield child
                yield from child.walk(skip_articles)


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node(); self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs); self.stack[-1].children.append(node)
        if tag not in VOID: self.stack.append(node)

    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]; break

    def handle_data(self, value): self.stack[-1].children.append(value)


def fields(article):
    out = {}
    for node in article.walk(skip_articles=True):
        if node.tag == 'p' and ':' in node.text():
            key, value = node.text().split(':', 1)
            if value.strip(): out.setdefault(key.strip(), []).append(value.strip())
    return out


def first_image(article):
    return next((source_url(n.attrs['src'], True) for n in article.walk(skip_articles=True)
                 if n.tag == 'img' and '/archivos/' in n.attrs.get('src', '')), None)


def heading(article, tag):
    return next((n.text() for n in article.walk(skip_articles=True) if n.tag == tag), '')


def parse_page(raw, page, document, lexical_links):
    parser = PageParser(); parser.feed(raw.decode('utf-8'))
    articles = [n for n in parser.root.walk() if n.tag == 'article']
    prefix = page['locator']
    output = {'pages': [], 'zones': [], 'elements': [], 'occurrences': [], 'exceptions': []}
    page_row = dict(id=document['id']+':'+prefix, document_id=document['id'], locator=prefix,
                    url=page['url'], source_hash=hashlib.sha256(raw).hexdigest())
    current_zone = None; found_page = False; elements = {}
    for article in articles:
        cls = article.attrs.get('class', '').split()
        if 'lamina' in cls:
            title = heading(article, 'h3')
            if title == 'Lámina - '+prefix:
                found_page = True; page_row['image'] = first_image(article)
        elif 'zona' in cls:
            title = heading(article, 'h3')
            if not title.startswith('Zona - '+prefix): continue
            code = title.removeprefix('Zona - ')
            current_zone = document['id']+':'+code
            output['zones'].append(dict(id=current_zone, page_id=page_row['id'], code=code, image=first_image(article)))
        elif 'glifo' in cls or 'personaje' in cls:
            kind = 'glyph' if 'glifo' in cls else 'personage'
            title = heading(article, 'h3'); marker = 'Glifo - ' if kind == 'glyph' else 'Personaje - '
            require(title.startswith(marker+prefix), 'Cambió el formato o se mezclaron láminas: '+title)
            code = title.removeprefix(marker); data = fields(article)
            reading = data.get('Lectura', [])
            if len(reading) != 1:
                output['exceptions'].append(dict(code=code, reason='Lectura ausente o múltiple; requiere revisión.'))
                continue
            occurrence = dict(id=document['id']+':'+code, page_id=page_row['id'], zone_id=current_zone,
                              code=code, kind=kind, reading=reading[0], verification='catalog_checked',
                              url=page['url'], image=first_image(article), citations=data.get('Cita', []),
                              morphology=data.get('Morfología', []), segmentation=data.get('Descomposicion', []),
                              unexpressed=data.get('Parte no expresada', []), components=[])
            # Only nested element records belong to this occurrence. GDN paragraphs are ignored.
            for child in article.walk():
                if child.tag != 'article' or 'elemento' not in child.attrs.get('class', '').split(): continue
                designation = heading(child, 'h4').removeprefix('Elemento: ').strip()
                code_url = next((n.text() for n in child.walk(skip_articles=True)
                                 if n.tag == 'p' and n.text().startswith('https://tlachia.iib.unam.mx/elemento/')), '')
                element_code = code_url.rsplit('/', 1)[-1]
                require(designation and code_url and element_code, 'Elemento sin denominación o código en '+code)
                source_url(code_url)
                eid = document['id']+':element:'+element_code
                ef = fields(child)
                element = dict(id=eid, document_id=document['id'], code=element_code, designation=designation,
                               designation_status='catalog_label', meanings=ef.get('Sentido', []),
                               image=first_image(child), url=page['url'], lexical_links=[])
                for relation in lexical_links:
                    if relation['designation'] == designation:
                        element['lexical_links'].append({k: relation[k] for k in ('sense_id', 'relation', 'note')})
                if eid in elements:
                    require(elements[eid] == element, 'Denominaciones contradictorias para '+eid)
                elements[eid] = element
                occurrence['components'].append(dict(element_id=eid, values=ef.get('Valor fonético', [])))
            output['occurrences'].append(occurrence)
    require(found_page and output['occurrences'], 'No se reconoció la lámina o sus fichas; no se publica una extracción vacía.')
    output['pages'].append(page_row); output['elements'] = list(elements.values())
    return output


def write_new(path, data):
    path = Path(path); value = json.dumps(data, ensure_ascii=False, indent=2)+'\n'
    if path.exists():
        require(path.read_text() == value, 'La salida cambió: utiliza un nombre de lote nuevo.')
        return 'unchanged'
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as f: f.write(value)
    return 'created'


def prepare(recipe_path, cache, fetch=False):
    recipe = json.loads(Path(recipe_path).read_text()); cache = Path(cache)
    require(len(recipe['pages']) <= 10, 'Máximo diez láminas por lote.')
    docs = {d['id']: d for d in recipe['documents']}
    data = dict(schema_version=1, release_id=recipe['id'], attribution=recipe['attribution'],
                rights=recipe['rights'], documents=recipe['documents'], pages=[], zones=[], elements=[], occurrences=[])
    exceptions = []; element_map = {}
    for page in recipe['pages']:
        source_url(page['url'])
        require(Path(page['cache_file']).name == page['cache_file'], 'Nombre de caché inválido.')
        path = cache/page['cache_file']
        if not path.exists() and fetch:
            try:
                import certifi
                context = ssl.create_default_context(cafile=certifi.where())
            except ImportError: context = ssl.create_default_context()
            raw = urlopen(page['url'], timeout=25, context=context).read(2_000_001)
            require(len(raw) <= 2_000_000, 'Página demasiado grande.')
            cache.mkdir(parents=True, exist_ok=True)
            with path.open('xb') as f: f.write(raw)
        require(path.is_file(), 'Falta la página cacheada: '+str(path)+'; usa --fetch.')
        raw = path.read_bytes()
        require(len(raw) <= 2_000_000, 'Caché demasiado grande.')
        parsed = parse_page(raw, page, docs[page['document_id']], recipe.get('lexical_links', []))
        for key in ('pages', 'zones', 'occurrences'): data[key].extend(parsed[key])
        for element in parsed['elements']:
            existing = element_map.get(element['id'])
            # The element index is document-scoped; evidence URL may differ by page.
            require(not existing or {k:v for k,v in existing.items() if k != 'url'} ==
                    {k:v for k,v in element.items() if k != 'url'}, 'Conflicto entre láminas: '+element['id'])
            element_map.setdefault(element['id'], element)
        exceptions.extend(parsed['exceptions'])
    data['elements'] = list(element_map.values())
    require(len(data['occurrences']) <= 100, 'Máximo cien apariciones por lote.')
    validate(data)
    return data, dict(release_id=recipe['id'], exceptions=exceptions,
                      counts={k:len(data[k]) for k in ('documents','pages','zones','elements','occurrences')},
                      scope='Extracción literal de catálogo; no cotejo del manuscrito ni revisión lingüística.')


def publish(candidate, destination):
    candidate = validate(candidate); path = Path(destination)
    if not path.exists(): return write_new(path, candidate)
    old = validate(json.loads(path.read_text()))
    merged = json.loads(json.dumps(old))
    for key in ('documents','pages','zones','elements','occurrences'):
        existing = {r['id']:r for r in old[key]}
        for row in candidate[key]:
            previous = existing.get(row['id'])
            # Elements are document-scoped: another page can cite the same record.
            # Preserve the original row (URL and notes included); only its evidence
            # page URL may differ in the candidate. All semantic fields must match.
            equal = previous == row
            if previous is not None and key == 'elements':
                equal = ({k:v for k,v in previous.items() if k != 'url'} ==
                         {k:v for k,v in row.items() if k != 'url'})
            require(previous is None or equal, 'No se reemplaza una ficha existente: '+row['id'])
            if row['id'] not in existing: merged[key].append(row)
    if merged == old: return 'unchanged'
    merged['release_id'] = candidate['release_id']; validate(merged)
    # A backup includes only the public index; never the community database.
    backup = path.with_name(path.stem+'-before-'+candidate['release_id']+path.suffix)
    write_new(backup, old)
    temp = path.with_suffix('.tmp')
    require(not temp.exists(), 'Hay una publicación pendiente; conserva el archivo temporal.')
    with temp.open('x', encoding='utf-8') as f: json.dump(merged, f, ensure_ascii=False, indent=2); f.write('\n')
    temp.replace(path)
    return 'added'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--recipe', type=Path, required=True)
    parser.add_argument('--cache', type=Path, default=ROOT/'data/pictography-cache')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--fetch', action='store_true')
    parser.add_argument('--publish', type=Path, help='Incorporación aditiva; rechaza sustituciones de IDs.')
    args = parser.parse_args()
    data, report = prepare(args.recipe, args.cache, args.fetch)
    write_new(args.output.with_name(args.output.stem+'-report.json'), report)
    report['candidate'] = write_new(args.output, data)
    if args.publish: report['publication'] = publish(data, args.publish)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__': main()
