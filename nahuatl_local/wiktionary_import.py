"""Lote léxico de Wiktionary (CC BY-SA 4.0): náhuatl clásico desde wiktextract/kaikki.org.

Determinista, sin LLM ni OCR. La receta (``editorial/wiktionary-nci-v12.json``)
fija la URL y el SHA-256 de cada extracto; ``--fetch`` descarga solo lo que falta
en ``data/wiktionary-cache/`` y consulta la API de Wikimedia para la revisión de
cada página vigente en la fecha del volcado. Repetir sin red produce los mismos bytes.

Qué entra
---------
* Un lema por página y sección gramatical, con sus acepciones (idioma marcado en
  ``gloss_language``), formas flexionadas y grafías alternativas, URL de la revisión
  y licencia por registro (``rights``: CC BY-SA 4.0, atribución, ``training=false``).
* Estado «extracción automática» (``import_status``) y verificación ``inherited``.

Qué no entra
------------
* Lemas cuya clave fonémica ya tiene una forma en el catálogo (Molina/GDN o curada):
  no se crean duplicados ni se toca el registro existente; el informe los lista.
* Entradas que solo remiten a otra (formas flexionadas, grafías alternativas): se
  añaden como formas del lema si este entra en el lote; si no, se descartan.
* Locuciones con espacios, afijos, entradas sin glosa y reconstrucciones no atestiguadas.
* Préstamos del español y nombres extranjeros: los marca la página o contienen letras ajenas a la
  ortografía clásica (b, d, f, g, j, r, v, ñ, ũ). Se parecen a palabras españolas y confunden la
  detección del idioma de una consulta.

Antes de escribir, el lote se importa en una base temporal sobre el catálogo actual
y se comprueba que todos los registros previos quedan idénticos (preservación).
"""
import argparse
import hashlib
import json
import re
import ssl
import tempfile
import time
from collections import Counter
from pathlib import Path
from urllib.parse import quote, urlencode
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from .text import key_of, strip_marks

ROOT = Path(__file__).resolve().parents[1]
RECIPE = ROOT / 'editorial' / 'wiktionary-nci-v12.json'
CACHE = ROOT / 'data' / 'wiktionary-cache'
USER_AGENT = 'Amoxcalli-local/0.1 (offline learning platform; one-time revision lookup)'
FORM_OF = {'form-of', 'alt-of'}
POS = {'noun': 'noun', 'name': 'noun', 'verb': 'verb'}
SKIP_POS = {'prefix', 'suffix', 'infix', 'affix', 'interfix', 'circumfix', 'character', 'symbol', 'punct', 'phrase'}
SKIP_FORM_TAGS = {'table-tags', 'inflection-template', 'class'}
MAX_FORMS = 40
# Letras ajenas a la ortografía clásica: solo aparecen en préstamos y nombres extranjeros
# (abril, caballo, Peru, Madrid, España, Perũ).
FOREIGN_LETTERS = set('bdfgjrvñũ')
LOAN_MARKS = ('NCI:Palabras provenientes del español', 'Classical Nahuatl terms borrowed from Spanish')
LOAN_ETYMOLOGY = re.compile(r'(Del español|Borrowed from Spanish|From Spanish)\b')
CITATION_MARK = re.compile(r'\^\([^)]*\)')


def _context():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        # Python.org en macOS no trae certificados: usa los del sistema si existen (TLS verificado igualmente).
        system = Path('/etc/ssl/cert.pem')
        return ssl.create_default_context(cafile=str(system)) if system.is_file() else ssl.create_default_context()


def _get(url, limit=20_000_000, attempts=6):
    request = Request(url, headers={'User-Agent': USER_AGENT})
    for attempt in range(attempts):
        try:
            raw = urlopen(request, timeout=60, context=_context()).read(limit + 1)
            break
        except HTTPError as error:
            # Wikimedia limita la frecuencia: espera lo que indica Retry-After y reintenta.
            if error.code not in (429, 503) or attempt == attempts - 1:
                raise
            time.sleep(max(int(error.headers.get('Retry-After') or 0), 5 * 2 ** attempt))
    if len(raw) > limit:
        raise ValueError('Respuesta demasiado grande: ' + url)
    return raw


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


# ---------------------------------------------------------------------------
# Caché: extractos y revisiones
# ---------------------------------------------------------------------------
def extract_rows(extract, cache=CACHE, fetch=False):
    """Filas JSON del extracto, comprobando el SHA-256 de la receta."""
    path = Path(cache) / extract['file']
    if not path.is_file():
        if not fetch:
            raise SystemExit(f'Falta {path}; usa --fetch.')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(_get(extract['url']))
    raw = path.read_bytes()
    if sha256(raw) != extract['sha256']:
        raise SystemExit(f'{path}: el extracto cambió (SHA-256 distinto). Registra un lote nuevo con su hash.')
    return [json.loads(line) for line in raw.decode('utf-8').splitlines() if line.strip()]


def revisions(wiki, titles, dump, cache=CACHE, fetch=False, pause=1.0):
    """Revisión de cada página vigente en la fecha del volcado: {título: {revid, timestamp}}.

    Primero la última revisión de cada página (50 títulos por consulta); si es
    posterior al volcado, la última anterior a él (una consulta por título)."""
    path = Path(cache) / f'revisions-{wiki}.json'
    known = json.loads(path.read_text(encoding='utf-8')) if path.is_file() else {}
    cutoff = dump + 'T23:59:59Z'
    api = f'https://{wiki}/w/api.php?'

    def save():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(dict(sorted(known.items())), ensure_ascii=False, indent=0) + '\n', encoding='utf-8')

    missing = sorted(t for t in titles if t not in known)
    if missing and not fetch:
        raise SystemExit(f'Faltan {len(missing)} revisiones de {wiki} en {path}; usa --fetch.')
    for i in range(0, len(missing), 50):
        chunk = missing[i:i + 50]
        data = json.loads(_get(api + urlencode(dict(action='query', format='json', formatversion=2, prop='revisions',
                                                       rvprop='ids|timestamp', titles='|'.join(chunk)))))
        names = {n['to']: n['from'] for n in data['query'].get('normalized', [])}
        for page in data['query']['pages']:
            title = names.get(page['title'], page['title'])
            rev = (page.get('revisions') or [{}])[0]
            known[title] = dict(revid=rev.get('revid'), timestamp=rev.get('timestamp'), latest=True)
        save()
        time.sleep(pause)
    save()
    later = sorted(t for t in titles if known[t].get('latest') and (known[t]['timestamp'] or '') > cutoff)
    if later and not fetch:
        raise SystemExit(f'Faltan {len(later)} revisiones anteriores al volcado de {wiki}; usa --fetch.')
    for n, title in enumerate(later, 1):
        data = json.loads(_get(api + urlencode(dict(action='query', format='json', formatversion=2, prop='revisions',
                                                       rvprop='ids|timestamp', rvlimit=1, rvdir='older',
                                                       rvstart=cutoff, titles=title))))
        rev = (data['query']['pages'][0].get('revisions') or [{}])[0]
        known[title] = dict(revid=rev.get('revid'), timestamp=rev.get('timestamp'), latest=False)
        if n % 20 == 0:
            save()
        time.sleep(pause)
    save()
    return {t: known[t] for t in titles}


# ---------------------------------------------------------------------------
# Selección y registros
# ---------------------------------------------------------------------------
def _glosses(row):
    out = []
    for s in row.get('senses', []):
        tags = set(s.get('tags', []))
        if not s.get('glosses') or tags & FORM_OF or s.get('form_of') or s.get('alt_of'):
            continue
        # Las marcas de mantenimiento de la wiki («^([cita requerida])») no son parte de la acepción.
        gloss = ' '.join(CITATION_MARK.sub('', ' — '.join(g.strip() for g in s['glosses'] if g.strip())).split())
        if gloss and gloss not in out:
            out.append(gloss)
    return out


def _targets(row):
    """Lemas a los que remite una entrada que solo es forma de otra: [(lema, tipo, etiquetas)]."""
    out = []
    for s in row.get('senses', []):
        tags = s.get('tags', [])
        for key, kind in (('alt_of', 'alternative'), ('form_of', 'inflection')):
            for t in s.get(key) or []:
                if t.get('word'):
                    out.append((t['word'], kind, [x for x in tags if x not in FORM_OF]))
    return out


def _slug(word):
    return re.sub(r'[^a-z0-9]+', '-', strip_marks(word).casefold()).strip('-')[:40] or 'x'


def _rid(prefix, extract, word, *parts):
    h = hashlib.sha256('\x1f'.join([extract['id'], word, *map(str, parts)]).encode()).hexdigest()[:8]
    return f'{prefix}-wikt-{extract["gloss_language"]}-{_slug(word)}-{h}'


def _page_url(extract, title, revid=None):
    base = f'https://{extract["wiki"]}/'
    if revid:
        return base + 'w/index.php?' + urlencode(dict(title=title, oldid=revid))
    return base + 'wiki/' + quote(title, safe='')


def _spanish_loan(row):
    """Préstamo del español según la propia página (categoría o etimología)."""
    categories = {c.get('name') if isinstance(c, dict) else c for c in row.get('categories', [])}
    etymology = ' '.join(row.get('etymology_texts') or [row.get('etymology_text') or ''])
    return bool(categories & set(LOAN_MARKS)) or bool(LOAN_ETYMOLOGY.match(etymology.strip()))


def _reconstruction(row):
    return (row.get('original_title') or '').startswith('Reconstruction:')


def _usable(word):
    return (bool(word) and ' ' not in word.strip() and not set(word.casefold()) & FOREIGN_LETTERS
            and re.fullmatch(r"[^\W\d_]+(?:['’][^\W\d_]+)*", word) is not None)


def select(recipe, rows_by_extract, catalog_keys):
    """Elige lemas nuevos y sus remisiones. Devuelve (lemas, remisiones, informe).

    ``lemas``: [(extracto, fila)] en orden; una clave fonémica entra desde un
    solo extracto (prioridad de la receta: español antes que inglés)."""
    report = Counter()
    duplicates, chosen = {}, {}
    extracts = sorted(recipe['extracts'], key=lambda e: e['priority'])
    for extract in extracts:
        for row in rows_by_extract[extract['id']]:
            word = row.get('word', '')
            if _reconstruction(row):
                report['reconstrucción_no_atestiguada'] += 1
                continue
            if row.get('lang_code') != 'nci':
                report['otra_lengua'] += 1
                continue
            if word and ' ' not in word and set(word.casefold()) & FOREIGN_LETTERS or _spanish_loan(row):
                report['préstamo_del_español_o_nombre_extranjero'] += 1
                continue
            if not _usable(word):
                report['locución_o_grafía_no_alfabética'] += 1
                continue
            if row.get('pos') in SKIP_POS:
                report['afijo_o_locución'] += 1
                continue
            if not _glosses(row):
                report['solo_remite_a_otra_entrada' if _targets(row) else 'sin_glosa'] += 1
                continue
            k = key_of(word)
            if k in catalog_keys:
                report['ya_en_el_catálogo'] += 1
                duplicates.setdefault(k, dict(word=word, extract=extract['id'], catalog=catalog_keys[k]))
                continue
            owner = chosen.get(k)
            if owner and owner[0]['id'] != extract['id']:
                report['ya_en_otro_extracto'] += 1
                continue
            if owner and owner[1] != word:
                report['otra_grafía_misma_clave'] += 1
                continue
            chosen.setdefault(k, (extract, word))
            report['lema_incorporado'] += 1
    lemmas = [(e, r) for e in extracts for r in rows_by_extract[e['id']]
              if _usable(r.get('word', '')) and not _reconstruction(r) and not _spanish_loan(r)
              and r.get('pos') not in SKIP_POS and _glosses(r)
              and chosen.get(key_of(r['word'])) == (e, r['word'])]
    by_word = {(e['id'], r['word']) for e, r in lemmas}
    referrals = []
    for extract in extracts:
        for row in rows_by_extract[extract['id']]:
            if _glosses(row) or not _usable(row.get('word', '')) or _reconstruction(row):
                continue
            for target, kind, tags in _targets(row):
                if kind == 'alternative' and key_of(row['word']) in catalog_keys:
                    report['grafía_alternativa_ya_en_el_catálogo'] += 1
                elif (extract['id'], target) in by_word:
                    referrals.append((extract, row, target, kind, tags))
                    report['remisión_añadida_como_forma'] += 1
    return lemmas, referrals, dict(counts=dict(sorted(report.items())),
                                   duplicates=[duplicates[k] for k in sorted(duplicates)])


def _rights(extract, title, revid):
    lang = 'Wikcionario en español' if extract['gloss_language'] == 'es' else 'Wiktionary en inglés'
    return dict(public=True, training=False, license='CC BY-SA 4.0',
                license_url='https://creativecommons.org/licenses/by-sa/4.0/', share_alike=True,
                attribution=f'Colaboradores de {lang}, «{title}», revisión {revid} (enlace en «url»)',
                note=f'{lang}, CC BY-SA 4.0: se redistribuye con atribución y la misma licencia (no MIT). Sin entrenamiento.')


def records_for(recipe, lemmas, referrals, revs):
    """Registros del lote: fuentes, una acepción y una forma por lema y sección, formas remitidas."""
    out = [dict(s) for s in recipe['sources']]
    lemma_form, seen = {}, Counter()
    for extract, row in lemmas:
        title, pos = row['word'], row.get('pos', '')
        seen[extract['id'], title, pos] += 1
        n = seen[extract['id'], title, pos]
        rev = revs[extract['wiki']].get(title) or {}
        revid = rev.get('revid')
        if not revid:
            raise SystemExit(f'Sin revisión para {extract["wiki"]} «{title}»; no se publica sin procedencia.')
        url = _page_url(extract, title, revid)
        glosses = _glosses(row)
        language = 'español' if extract['gloss_language'] == 'es' else 'inglés'
        definition = ' '.join(f'{i}. {g}' for i, g in enumerate(glosses, 1)) if len(glosses) > 1 else glosses[0]
        sid = _rid('sense', extract, title, pos, n)
        fid = _rid('lex', extract, title, pos, n)
        common = dict(verification='inherited', rights=_rights(extract, title, revid), import_status='automatic_transcription',
                      import_source='wiktionary')
        evidence = [dict(source_id=extract['source_id'], status='inherited',
                         locator=f'{extract["section"]}, «{title}» ({pos}), revisión {revid} '
                                 f'({rev.get("timestamp", "")[:10]}), vigente en el volcado del {extract["dump"]}')]
        out.append(dict(common, id=sid, kind='sense', label=glosses[0][:300], definition=definition[:2000],
                        pos=POS.get(pos, 'other'), wiktionary_pos=pos, gloss_language=extract['gloss_language'],
                        aliases=[], url=url, evidence=evidence,
                        notes=f'Acepciones en {language}, tal como en la página; sin cotejo ni revisión especializada.'))
        forms = []
        for f in row.get('forms', []):
            tags = [t for t in f.get('tags', []) if t not in SKIP_FORM_TAGS]
            value = (f.get('form') or '').strip()
            if value and value != title and tags and not set(f.get('tags', [])) & SKIP_FORM_TAGS and value != '-':
                forms.append(dict(form=value, tags=tags))
        canonical = [f['form'] for f in forms if f['tags'] == ['canonical']]
        form = dict(common, id=fid, kind='form', label=title, written=title, sense_id=sid, period='historical',
                    variant='nci', variant_label='Náhuatl clásico', orthography=extract['orthography'],
                    variation_kind='unspecified', url=url, evidence=evidence,
                    inflections=[f for f in forms if f['tags'] != ['canonical']][:MAX_FORMS],
                    source_entry=dict(wiki=extract['wiki'], title=title, revid=revid, timestamp=rev.get('timestamp'),
                                      extract=extract['id'], dump=extract['dump']),
                    notes='Título de la página; parser determinista sobre wiktextract.')
        if canonical:
            form['wiktionary_canonical'] = canonical[0]
        out += [form]
        lemma_form.setdefault((extract['id'], title), form)
    for extract, row, target, kind, tags in referrals:
        lemma = lemma_form[extract['id'], target]
        title = row['word']
        rev = revs[extract['wiki']].get(title) or {}
        if kind == 'inflection':
            entry = dict(form=title, tags=tags + ['wiktionary-form-of'])
            if entry not in lemma['inflections']:
                lemma['inflections'].append(entry)
            continue
        if key_of(title) == key_of(target) and title.casefold() == target.casefold():
            continue
        if not rev.get('revid'):
            raise SystemExit(f'Sin revisión para {extract["wiki"]} «{title}»; no se publica sin procedencia.')
        fid = _rid('lex', extract, title, 'alt', target)
        if any(r['id'] == fid for r in out):
            continue
        url = _page_url(extract, title, rev['revid'])
        out.append(dict(lemma, id=fid, label=title, written=title, variation_kind='orthographic', url=url,
                        rights=_rights(extract, title, rev['revid']), inflections=[],
                        evidence=[dict(source_id=extract['source_id'], status='inherited',
                                       locator=f'{extract["section"]}, «{title}», grafía alternativa de «{target}», '
                                               f'revisión {rev["revid"]}, vigente en el volcado del {extract["dump"]}')],
                        source_entry=dict(lemma['source_entry'], title=title, revid=rev['revid'], timestamp=rev.get('timestamp')),
                        notes=f'Grafía alternativa registrada en Wiktionary para «{target}».'))
        out[-1].pop('wiktionary_canonical', None)
    return out


# ---------------------------------------------------------------------------
# Comprobación de preservación y escritura
# ---------------------------------------------------------------------------
def preservation(bundle, marker, root=ROOT):
    """Importa el lote en una base temporal sobre el catálogo y compara lo previo."""
    from .corpus import CorpusStore
    with tempfile.TemporaryDirectory(prefix='amoxcalli-wiktionary-') as directory:
        store = CorpusStore(Path(directory) / 'check.sqlite3', root=root)
        before = {rid: {k: v for k, v in r.items() if k != 'version'} for rid, r in store.records().items()}
        added = store.import_bundle(bundle, 'Extracción automática de Wiktionary', 'Comprobación de preservación',
                                    migration_key=marker)
        after = {rid: {k: v for k, v in r.items() if k != 'version'} for rid, r in store.records().items()}
    changed = sorted(rid for rid in before if after.get(rid) != before[rid])
    if changed:
        raise SystemExit('La comprobación de preservación falló: ' + ', '.join(changed[:10]))
    return dict(records_before=len(before), records_after=len(after), added=added, previous_records_unchanged=True)


def build(recipe_path=RECIPE, cache=CACHE, fetch=False, root=ROOT):
    from . import lexicon
    recipe = json.loads(Path(recipe_path).read_text(encoding='utf-8'))
    rows = {e['id']: extract_rows(e, cache, fetch) for e in recipe['extracts']}
    # Deduplicación contra el catálogo sin este lote (Molina/GDN, curadas y publicaciones).
    output = Path(root) / recipe['output']
    previous = [s for s in lexicon.steps(root) if s[0].path != recipe['output']]
    catalog_keys = {}
    for step, bundle in previous:
        for r in bundle.get('records', []):
            if r.get('kind') == 'form':
                k = key_of(r.get('catalog_normalized') or r.get('written') or '')
                if k:
                    catalog_keys.setdefault(k, r['id'])
    lemmas, referrals, selection = select(recipe, rows, catalog_keys)
    revs = {}
    for e in recipe['extracts']:
        titles = {r['word'] for ex, r in lemmas if ex['wiki'] == e['wiki']}
        titles |= {row['word'] for ex, row, _, kind, _ in referrals if ex['wiki'] == e['wiki']}
        revs.setdefault(e['wiki'], {})
        revs[e['wiki']].update(revisions(e['wiki'], sorted(titles), e['dump'], cache, fetch))
    # Sin revisión localizable no hay procedencia: la entrada no se publica.
    has_rev = lambda ex, title: bool((revs[ex['wiki']].get(title) or {}).get('revid'))
    missing = sorted({r['word'] for ex, r in lemmas if not has_rev(ex, r['word'])})
    lemmas = [(ex, r) for ex, r in lemmas if has_rev(ex, r['word'])]
    kept = {(ex['id'], r['word']) for ex, r in lemmas}
    referrals = [x for x in referrals if has_rev(x[0], x[1]['word']) and (x[0]['id'], x[2]) in kept]
    if missing:
        selection['counts']['sin_revisión_localizable'] = len(missing)
    records = records_for(recipe, lemmas, referrals, revs)
    bundle = dict(schema_version=1, release_id=recipe['id'], license=recipe['license'],
                  attribution='Colaboradores de Wikcionario y de Wiktionary. Cada registro enlaza la revisión de su página. '
                              'Extracción: wiktextract (Tatu Ylonen), publicada en kaikki.org.',
                  share_alike='Este lote es una adaptación de Wiktionary y se distribuye bajo CC BY-SA 4.0, no bajo la licencia MIT '
                              'del código. Quien lo redistribuya o modifique debe conservar la atribución y la misma licencia.',
                  records=records)
    kinds = Counter(r['kind'] for r in records)
    by_lang = Counter(r['gloss_language'] for r in records if r['kind'] == 'sense')
    later = sum(1 for wiki in revs for v in revs[wiki].values() if not v.get('latest'))
    report = dict(schema_version=1, release_id=recipe['id'], generated_by='python -m nahuatl_local.wiktionary_import',
                  consulted=recipe['consulted'], output=recipe['output'],
                  extracts=[{k: e[k] for k in ('id', 'url', 'sha256', 'wiki', 'dump', 'extracted')} for e in recipe['extracts']],
                  counts=dict(records=len(records), **dict(sorted(kinds.items())),
                              senses_by_gloss_language=dict(sorted(by_lang.items())),
                              revisions_before_dump_lookup=later),
                  selection=selection['counts'], duplicates_skipped=len(selection['duplicates']),
                  duplicates=selection['duplicates'], llm_calls=0,
                  scope='Extracción automática: sin cotejo primario ni revisión lingüística. rights.training=false en todos los registros.')
    return bundle, report


def encode(data):
    """Cabecera legible y un registro por línea: diffs por registro, tamaño contenido."""
    head = {k: v for k, v in data.items() if k != 'records'}
    body = ',\n'.join(json.dumps(r, ensure_ascii=False) for r in data.get('records', []))
    return json.dumps(head, ensure_ascii=False, indent=1)[:-2] + ',\n "records": [\n' + body + '\n ]\n}\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--recipe', type=Path, default=RECIPE)
    parser.add_argument('--cache', type=Path, default=CACHE)
    parser.add_argument('--fetch', action='store_true', help='Descarga extractos y revisiones ausentes de la caché.')
    parser.add_argument('--check', action='store_true', help='Falla si el lote distribuido no coincide con la caché.')
    args = parser.parse_args(argv)
    bundle, report = build(args.recipe, args.cache, args.fetch)
    from . import lexicon
    marker = next((s.marker for s in lexicon.STEPS if s.path == report['output']), 'wiktionary-check-')
    path, report_path = ROOT / report['output'], ROOT / json.loads(args.recipe.read_text())['report']
    if args.check:
        if not path.is_file() or path.read_text(encoding='utf-8') != encode(bundle):
            raise SystemExit('El lote de Wiktionary no coincide con la caché y la receta.')
        print(json.dumps(report['counts'], ensure_ascii=False))
        return
    if path.is_file() and path.read_text(encoding='utf-8') != encode(bundle):
        raise SystemExit(f'{path} ya existe con otro contenido: los lotes publicados no se reescriben; usa un ID nuevo.')
    if not path.is_file():
        report['preservation'] = preservation(bundle, marker + 'check')
        path.write_text(encode(bundle), encoding='utf-8')
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(dict(report['counts'], selection=report['selection'],
                          preservation=report.get('preservation', 'unchanged')), ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
