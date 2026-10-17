"""Fichas documentales de Preguntar: campos públicos con su procedencia, sin ranking propio.

Una ficha es un registro (forma, acepción, pasaje del archivo o elemento/aparición de Tlachia)
con sus campos literales, la fila y el archivo de origen (SHA256) y su URL. Preguntar pide las
fichas de una consulta: los IDs que contiene y los grupos de término que el índice de términos
reconoce. No hay índice invertido ni puntuación aparte (antes: ``DocumentaryIndex``, retirado
el 16 oct 2026). Solo biblioteca estándar; sin claves de evaluación ni entradas de modelo.
"""
import copy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlparse

from .community import ROOT
from . import lexicon, passages
from .morphology import WORD
from .text import fold, loose_key

CONFIG = dict(version='cards-v1', maximum_query_characters=1000, maximum_groups=8, limit=40,
              selection='IDs literales de la consulta; grupos de término del índice único (una palabra) '
                        'o palabras del diccionario mencionadas en una pregunta', model_calls=0)
NOTE = ('Campos registrados. Conserva originales y acepciones; no produce una traducción '
        'nueva ni decide qué acepción corresponde fuera de contexto. Cotejo primario y revisión lingüística pendientes.')
IDENTIFIER = re.compile(r'[\w]+(?:[:.-][\w]+)*')
# Palabras funcionales del español que también son grafías del diccionario (a, y, o, e…): en una
# pregunta no cuentan como mención, salvo escritas como alternativa explícita («o / o», «titi / y»).
FUNCTION_WORDS = set('a al ante cada con de del e el en es la las lo los o para por que qué se sin su sus un una y'.split())
SPANISH_ACCENT = re.compile('[áéíóú]', re.I)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def public_path(root, relative, writing=False):
    root = Path(root).absolute()
    relative = Path(relative)
    if relative.is_absolute() or '..' in relative.parts or not relative.parts or relative.parts[0] not in ('corpus', 'configs', 'docs', 'reports', 'nahuatl_local', 'tests'):
        raise ValueError('Solo se admiten rutas públicas explícitas del proyecto.')
    path = root / relative
    for part in (path, *path.parents):
        if part.is_symlink():
            raise ValueError('La ruta pública no puede atravesar enlaces simbólicos.')
        if part == root:
            break
    if writing and relative.parts[0] != 'reports':
        raise ValueError('El informe solo se escribe bajo reports/.')
    return path


def safe_url(value):
    if not isinstance(value, str):
        return ''
    return _safe_url(value)


@lru_cache(maxsize=65536)
def _safe_url(value):
    # Pocas URLs distintas se repiten en cientos de miles de campos: se valida cada una una vez.
    try:
        u = urlparse(value)
        return value if u.scheme in ('https', 'http') and u.hostname and not u.username and not u.password else ''
    except ValueError:
        return ''


def public_records(records):
    """Defensive public closure; the live store remains the authority for withdrawals."""
    return copy.deepcopy(lexicon.public_closure(records))


class PublicSources:
    """Explicit distributed public files, including the WHOLE CSV, without a DB."""
    def __init__(self, root=ROOT):
        self.root = Path(root)
        self.hashes = {}
        self.origins = {}
        self.rows = {}
        self.tables = {}
        def read(path):
            raw = public_path(self.root, path).read_bytes()
            self.hashes[path] = hashlib.sha256(raw).hexdigest()
            return raw
        read(lexicon.RELEASES)
        paths = list(lexicon.BUNDLE_PATHS)
        for release, _ in lexicon.releases(public_path(self.root, lexicon.RELEASES)):
            paths.append('corpus/' + release['bundle'])
        # Backfills affect live rows, but do not rewrite the original row.
        self.rows, self.origins = lexicon.source_rows([(path, json.loads(read(path))) for path in paths])
        self.catalog = json.loads(read('corpus/pictography/catalog.json'))
        from .pictography import validate
        validate(self.catalog)
        for table in ('documents', 'pages', 'zones', 'elements', 'occurrences'):
            self.tables[table] = {r['id']: r for r in self.catalog[table]}
        config = json.loads(read('configs/sources.json'))['corpus']
        self.archive_url = safe_url(f"https://github.com/{config['repository']}/blob/{config['revision']}/{config['path']}")
        self.archive = {}
        self.csv_rows = {}
        origin = dict(url=self.archive_url, rights_note=config['rights_note'])
        for line, row in passages.parse(read(passages.AXOLOTL).decode('utf-8')):
            item = passages.passage(line, row, origin)
            if item is not None:
                # Las citas usan los campos originales (``csv_rows``); ``archive`` es el modelo común.
                self.csv_rows[item['id']] = row
                self.archive[item['id']] = item

    def field(self, table, rid, key, value, url=''):
        if table == 'csv':
            path, row = passages.AXOLOTL, self.csv_rows[rid]
        elif table == 'records':
            path, row = self.origins.get(rid), self.rows.get(rid)
            if row is None or key not in row or row[key] != value:
                # Publicly edited live fields have a distinct evidence namespace.
                return dict(path=None, table='public_records', record_id=rid, field=key,
                            value=copy.deepcopy(value), url=safe_url(url), row_sha256=None, file_sha256=None)
        else:
            path, row = 'corpus/pictography/catalog.json', self.tables[table][rid]
            if row.get(key) != value:
                return dict(path=None, table='public_catalog', record_id=rid, field=key, value=copy.deepcopy(value),
                            url=safe_url(url), row_sha256=None, file_sha256=None)
        return dict(path=path, table=table, record_id=rid, field=key, value=copy.deepcopy(value),
                    url=safe_url(url), row_sha256=self._row_digest(row), file_sha256=self.hashes[path])

    def _row_digest(self, row):
        # Una fila aporta ~15 campos: su hash se calcula una vez por objeto fila (no se modifican en sitio).
        cache = self.__dict__.setdefault('_row_digests', {})
        found = cache.get(id(row))
        if found is None or found[0] is not row:
            found = cache[id(row)] = (row, digest(row))
        return found[1]

    def citation_valid(self, field):
        """Verify literals, complete rows/files and the documented URL, never follow a URL."""
        try:
            table, rid, key = field['table'], field['record_id'], field['field']
            if table == 'csv':
                row = self.csv_rows[rid]
                value = passages.original(row)[key]
                valid_urls = {self.archive_url}
            elif table == 'records':
                row = self.rows[rid]
                value = row[key]
                valid_urls = {safe_url(row.get('url', ''))}
                if row['kind'] == 'sense':
                    valid_urls |= {safe_url(f.get('url', '')) for f in self.rows.values() if f.get('sense_id') == rid}
                for e in row.get('evidence', []):
                    valid_urls |= {safe_url(self.rows.get(e.get(k), {}).get('url', '')) for k in ('source_id', 'via_source_id')}
            else:
                row = self.tables[table][rid]
                value = row[key]
                valid_urls = {safe_url(row.get('url', ''))}
                if row.get('page_id'):
                    valid_urls.add(safe_url(self.tables['pages'][row['page_id']]['url']))
            expected = self.field(table, rid, key, value, field.get('url', ''))
            return field == expected and field.get('url') in valid_urls and bool(field.get('url'))
        except (KeyError, TypeError, ValueError):
            return False


class Cards:
    """Fichas de los registros públicos, del archivo y del catálogo de Tlachia, por clave ``tipo:id``."""
    def __init__(self, records, sources=None):
        self.sources = sources or PublicSources()
        self.records = public_records(records)
        self.entries = {}
        self.identifiers = {}
        for rid, row in sorted(self.records.items()):
            associated = self.records.get(row.get('sense_id'))
            members = [row] + ([associated] if associated else [])
            urls = [safe_url(row.get('url', ''))]
            source_ids = sorted({e[k] for r in members for e in r.get('evidence', [])
                                 for k in ('source_id', 'via_source_id') if e.get(k) in self.records})
            urls += [safe_url(self.records[s].get('url', '')) for s in source_ids]
            url = next((u for u in urls if u), '')
            fields = [self.sources.field('records', r['id'], key, value, url)
                      for r in members for key, value in r.items() if key != 'version']
            self._add(rid, row['kind'], fields, source_ids, urls,
                      dict(label=row.get('written') or row.get('label', rid), records=members))
        for rid, row in self.sources.archive.items():
            original = passages.original(self.sources.csv_rows[rid])
            fields = [self.sources.field('csv', rid, key, original[key], self.sources.archive_url)
                      for key in ('nah', 'es', 'document', 'iso', 'variant')]
            self._add(rid, 'passage', fields, ['src-axolotl'], [self.sources.archive_url],
                      dict(label=row['document'], passage=row))
        for table, rows in self.sources.tables.items():
            for rid, original in rows.items():
                row = copy.deepcopy(original)
                if 'lexical_links' in row:
                    row['lexical_links'] = [link for link in row['lexical_links']
                                            if link.get('sense_id') in self.records and self.records[link['sense_id']]['kind'] == 'sense']
                url = row.get('url') or self.sources.tables['pages'].get(row.get('page_id'), {}).get('url', '')
                fields = [self.sources.field(table, rid, key, value, url) for key, value in row.items()]
                self._add(rid, table, fields, ['pictography:' + row.get('document_id', row.get('page_id', rid))],
                          [url], dict(label=row.get('designation') or row.get('reading') or row.get('title') or rid,
                                      documentary_record=row))

    def _add(self, rid, kind, fields, source_ids, urls, content):
        key = kind + ':' + rid
        self.entries[key] = dict(id=rid, kind=kind, fields=fields, source_ids=source_ids,
                                 urls=sorted({u for u in map(safe_url, urls) if u}), **content)
        self.identifiers[fold(rid)] = key

    def card(self, key, match):
        """Copia de la ficha ``tipo:id`` con su motivo; una forma añade la comparación original/normalización."""
        card = copy.deepcopy(self.entries[key])
        card.update(match=[match])
        if card['kind'] == 'form':
            form = card['records'][0]
            card['comparison'] = dict(written=form['written'], catalog_normalized=form.get('catalog_normalized'),
                equal_literal=form['written'] == form.get('catalog_normalized') if 'catalog_normalized' in form else None,
                sense_id=form['sense_id'])
        return card

    def term_keys(self, group):
        """Fichas de un grupo de término: formas (con su acepción), acepciones sin forma y glifos."""
        keys = [('sense', s['id']) for s in group['senses'] if not any(f['sense_id'] == s['id'] for f in group['forms'])]
        keys += [('form', f['id']) for f in group['forms']] + [('glyph', g['id']) for g in group['glyphs'] if g['source'] == 'dictionary']
        keys += [('elements' if g['source'] == 'tlachia_element' else 'occurrences', g['id'])
                 for g in group['glyphs'] if g['source'] != 'dictionary']
        return [kind + ':' + rid for kind, rid in keys]

    def lookup(self, query, terms):
        """Fichas de una consulta de Preguntar: IDs literales, luego los grupos de término.

        Una palabra sola usa el grupo principal de la búsqueda única (``terms.resolve``) y sus cinco
        primeros pasajes. En una
        pregunta más larga, cada palabra del diccionario mencionada (grafía exacta por clave laxa,
        sin palabras funcionales del español ni palabras con acento español) aporta sus grupos."""
        if not isinstance(query, str) or len(query) > CONFIG['maximum_query_characters']:
            raise ValueError('Consulta con hasta 1000 caracteres.')
        text = query.strip()
        found = {}
        spans = []
        for m in IDENTIFIER.finditer(fold(text)):
            key = self.identifiers.get(m.group(0))
            if key:
                found.setdefault(key, 'identifier')
            if key or (re.search(r'[:.-]', m.group(0)) and re.search(r'\d', m.group(0))):
                # Un ID (conocido o retirado) no se lee como palabras: «lex-gdn-m2-147139» no menciona «lex».
                spans.append(m.span())
        groups, passage_ids = [], []
        resolved = terms.resolve(text) if text and not spans else None
        if resolved:
            groups.append(resolved[0])
            # Como en Archivo: los primeros pasajes del grupo, con la grafía consultada primero.
            passage_ids = terms.passage_ids(resolved[0]['id'], first=resolved[1])[:5]
        else:
            explicit = set()
            if '/' in text:
                # «ca / auh»: cada lado de la barra es una grafía pedida (la palabra contigua a la barra).
                for left, right in re.findall(r'([^\W\d_]+)\s*/\s*([^\W\d_]+)', text):
                    explicit.update({left.casefold(), right.casefold()})
            seen = set()
            for m in WORD.finditer(text):
                w = m.group(0)
                if any(a <= m.start() < b for a, b in spans):
                    continue
                if w.casefold() not in explicit and fold(w) in FUNCTION_WORDS:
                    continue
                for gid in terms.spelling_owner_of(w):
                    # «náhuatl», «México»: el acento español solo cuenta si la entrada lo escribe así.
                    if gid in seen or len(seen) >= CONFIG['maximum_groups']:
                        continue
                    group = terms.summary(gid)
                    if SPANISH_ACCENT.search(w) and w.casefold() not in {a['form'].casefold() for a in group['spellings']['attested']}:
                        continue
                    seen.add(gid)
                    groups.append(group)
        for group in groups:
            for key in self.term_keys(group) + ['passage:' + rid for rid in passage_ids]:
                if key in self.entries:
                    found.setdefault(key, 'term_group')
        keys = list(found)
        hits = [self.card(key, found[key]) for key in keys[:CONFIG['limit']]]
        return dict(method='documentary_cards', query=query, results=hits, total=len(keys),
                    limit=CONFIG['limit'], truncated=len(keys) > CONFIG['limit'], abstained=not hits,
                    source_ids=sorted({s for hit in hits for s in hit['source_ids']}),
                    status='matches' if hits else 'no_documented_match', note=NOTE,
                    absence='No hay fichas registradas para esta consulta; no demuestra ausencia en la lengua.' if not hits else None,
                    term=groups[0] if groups else None, groups=[g['id'] for g in groups],
                    scope='local_documentary_fields_only', model_used=False)
