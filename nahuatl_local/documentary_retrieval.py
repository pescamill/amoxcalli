"""Public documentary lookup, stdlib only. No evaluation keys or model inputs.

The fixed v1 ranking matches IDs, complete catalog labels and inverted tokens.
It returns evidence-bearing fields, never generates translations or readings.
"""
from collections import defaultdict
import copy
import hashlib
import json
import math
from pathlib import Path
import re
from urllib.parse import urlparse

from .community import ROOT
from . import lexicon, passages
from .text import fold, tokens

CONFIG = dict(version='documentary-lookup-v1', limit=20, exact_label_score=100,
              exact_id_score=1000, token_min_overlap=2, maximum_query_characters=1000,
              matching='casefold / accent-insensitive whole tokens; originals unchanged',
              tie_break='score descending, type, literal ID', model_calls=0)
NOTE = ('Consulta de campos registrados. Conserva originales y acepciones; no produce una traducción '
        'nueva ni decide qué acepción corresponde fuera de contexto. Cotejo primario y revisión lingüística pendientes.')
STOPWORDS = set('a al ambos cada con conserva de del el en es escritura ficha fichas glosa histórica id la las '
                'lo los normalización original para por que qué registra registro se sin su sus todas traducción '
                'un una y acompaña catalogada cita coinciden compara corresponde identifica náhuatl española '
                'conservada declarado declarada variedad'.split())


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
                    url=safe_url(url), row_sha256=digest(row), file_sha256=self.hashes[path])

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


class DocumentaryIndex:
    """Constructor accepts public sources and rows only; search accepts a string only."""
    def __init__(self, records, sources=None):
        self.sources = sources or PublicSources()
        self.records = public_records(records)
        self.entries = {}
        self.labels = defaultdict(set)
        self.postings = defaultdict(set)
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
            labels = [row.get(k, '') for k in ('written', 'catalog_normalized', 'label')] + row.get('aliases', [])
            if associated:
                labels += [associated.get('label', '')] + associated.get('aliases', [])
            searchable = labels + [associated.get('definition', '') if associated else '', row.get('definition', ''), row.get('nah', ''), row.get('es', '')]
            self._add(rid, row['kind'], labels, searchable, fields, source_ids, urls,
                      dict(label=row.get('written') or row.get('label', rid), records=members))
        for rid, row in self.sources.archive.items():
            original = passages.original(self.sources.csv_rows[rid])
            fields = [self.sources.field('csv', rid, key, original[key], self.sources.archive_url)
                      for key in ('nah', 'es', 'document', 'iso', 'variant')]
            self._add(rid, 'passage', [], [row['nah'], row['es'], row['document']], fields,
                      ['src-axolotl'], [self.sources.archive_url], dict(label=row['document'], passage=row))
        for table, rows in self.sources.tables.items():
            for rid, original in rows.items():
                row = copy.deepcopy(original)
                if 'lexical_links' in row:
                    row['lexical_links'] = [link for link in row['lexical_links']
                                            if link.get('sense_id') in self.records and self.records[link['sense_id']]['kind'] == 'sense']
                url = row.get('url') or self.sources.tables['pages'].get(row.get('page_id'), {}).get('url', '')
                fields = [self.sources.field(table, rid, key, value, url) for key, value in row.items()]
                labels = [row.get(k, '') for k in ('designation', 'reading', 'code', 'title', 'locator')]
                self._add(rid, table, labels, labels, fields, ['pictography:' + row.get('document_id', row.get('page_id', rid))],
                          [url], dict(label=row.get('designation') or row.get('reading') or row.get('title') or rid,
                                      documentary_record=row))

    def _add(self, rid, kind, labels, searchable, fields, source_ids, urls, content):
        key = kind + ':' + rid
        self.entries[key] = dict(id=rid, kind=kind, fields=fields, source_ids=source_ids,
                                 urls=sorted({u for u in map(safe_url, urls) if u}), **content)
        self.identifiers[fold(rid)] = key
        for label in labels:
            phrase = tuple(tokens(label))
            if phrase:
                self.labels[phrase].add(key)
        for token in set(tokens(' '.join(str(s) for s in searchable if s))):
            self.postings[token].add(key)

    def search(self, query):
        if not isinstance(query, str) or len(query) > CONFIG['maximum_query_characters']:
            raise ValueError('Consulta con hasta 1000 caracteres.')
        q = fold(query.strip())
        if not q:
            return self._response(query, [], 0)
        words = tokens(q)
        scores = defaultdict(float)
        reasons = defaultdict(set)
        # Identifier boundaries include punctuation used inside catalog IDs.
        for identifier in re.findall(r'[\w]+(?:[:.-][\w]+)*', q):
            key = self.identifiers.get(identifier)
            if key:
                scores[key] += CONFIG['exact_id_score']
                reasons[key].add('identifier')
        maximum = min(12, len(words))
        for start in range(len(words)):
            for size in range(1, maximum + 1):
                phrase = tuple(words[start:start + size])
                if len(phrase) != size:
                    break
                # Functional words in a sentence are not reliable lexical requests;
                # the same word alone can always be looked up.
                if size == 1 and phrase[0] in STOPWORDS and len(words) > 1:
                    continue
                for key in self.labels.get(phrase, ()):
                    scores[key] = max(scores[key], CONFIG['exact_label_score'] + size)
                    reasons[key].add('catalog_label')
        useful = set(words) - STOPWORDS
        overlaps = defaultdict(set)
        for token in useful:
            for key in self.postings.get(token, ()):
                overlaps[key].add(token)
        for key, overlap in overlaps.items():
            if len(overlap) >= min(CONFIG['token_min_overlap'], len(useful)) and useful:
                scores[key] += sum(math.log(1 + len(self.entries) / len(self.postings[t])) for t in overlap) / len(useful)
                reasons[key].add('tokens')
        ranked = sorted(scores, key=lambda k: (-scores[k], self.entries[k]['kind'], self.entries[k]['id']))
        # A sense bundled with a retrieved form need not be repeated as a separate hit.
        bundled = {r['id'] for key in ranked if self.entries[key]['kind'] == 'form'
                   for r in self.entries[key].get('records', []) if r['kind'] == 'sense'}
        ranked = [key for key in ranked if not (self.entries[key]['kind'] == 'sense' and self.entries[key]['id'] in bundled)]
        hits = []
        for key in ranked[:CONFIG['limit']]:
            result = copy.deepcopy(self.entries[key])
            result.update(score=round(scores[key], 6), match=sorted(reasons[key]))
            if result['kind'] == 'form':
                form = result['records'][0]
                result['comparison'] = dict(written=form['written'], catalog_normalized=form.get('catalog_normalized'),
                    equal_literal=form['written'] == form.get('catalog_normalized') if 'catalog_normalized' in form else None,
                    sense_id=form['sense_id'])
            hits.append(result)
        return self._response(query, hits, len(ranked))

    def _response(self, query, hits, total):
        return dict(method='public_documentary_retrieval', query=query, results=hits, total=total,
                    limit=CONFIG['limit'], truncated=total > CONFIG['limit'], abstained=not hits,
                    source_ids=sorted({s for hit in hits for s in hit['source_ids']}),
                    status='matches' if hits else 'no_documented_match', note=NOTE,
                    absence='No hay coincidencias registradas para esta consulta; no demuestra ausencia en la lengua.' if not hits else None,
                    scope='local_documentary_fields_only', model_used=False)
