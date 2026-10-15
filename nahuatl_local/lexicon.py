"""Diccionario: una sola fuente de verdad y un esquema de entrada léxica.

Fuentes, en orden
-----------------
``STEPS`` es la única lista de paquetes léxicos versionados (``corpus/*.json``),
con la forma en que cada uno entra en la base: importación aditiva (una
actualización nunca sustituye una edición local) o relleno de campos ausentes.
Les siguen las publicaciones editoriales registradas en
``corpus/editorial-releases.json`` (``releases``). Los paquetes no se editan:
son la evidencia que citan las evaluaciones, por archivo y hash.

Catálogo canónico
-----------------
``corpus/lexicon-catalog.json`` se **genera** (``python -m nahuatl_local.lexicon``)
aplicando ``STEPS`` a una base vacía con el mismo código que usa el servidor
(``CorpusStore``) y guardando sus registros públicos. Lleva el hash de cada
paquete de entrada; ``load`` rechaza un catálogo obsoleto. Así:

* el servidor lee ``CorpusStore.public_records()``: el catálogo más las ediciones
  locales y las aportaciones aceptadas de Voces de esa instalación;
* el analizador, Preguntar y las evaluaciones leen ``load_records()``: el catálogo
  sin datos locales (reproducible y sin abrir bases privadas);
* una prueba comprueba que una base nueva publica exactamente el catálogo.

Esquema de entrada léxica (``entries``)
---------------------------------------
Los registros (``sense``, ``form``, ``glyph``…) siguen siendo la unidad que se
guarda, edita, cita y propone. Una **entrada** los agrupa por lema: las formas
cuya clave fonémica coincide (``text.phonemic_key``; *quauitl*/*cuahuitl*,
*iuan*/*ihuan*) y las acepciones a las que pertenecen forman una entrada::

    id, lemma, key, loose_key       lema mostrado y sus claves de consulta
    senses, forms, glyphs           registros completos, sin modificar
    spellings                       todas las grafías escritas y normalizadas
    sources                         fuentes citadas por cualquier evidencia
    rights                          public / training (training solo si todo lo permite)
    review                          estado más bajo, transcripción automática, cotejo primario
"""
import argparse
import hashlib
import json
import re
import sqlite3
import tempfile
from collections import Counter, namedtuple
from contextlib import closing
from pathlib import Path

from .text import fold, key_of, loose_key, readable

ROOT = Path(__file__).resolve().parents[1]
CATALOG = 'corpus/lexicon-catalog.json'
RELEASES = 'corpus/editorial-releases.json'
SCHEMA = 'amoxcalli-lexicon-1'

# action: «seed» (solo en una base vacía), «import» (añade registros nuevos),
# «images» / «source_images» (rellenan campos ausentes de glifos existentes).
# Un marcador que termina en «-» recibe los 16 primeros dígitos del hash del paquete.
Step = namedtuple('Step', 'path action marker reviewer reason optional')
STEPS = (
    Step('corpus/seed.json', 'seed', 'seed-v1', 'Migración inicial', 'Integración Scriptorium + Voces', False),
    Step('corpus/glyph-links-v2.json', 'import', 'glyph-links-v2', 'Actualización del catálogo',
         'Vínculos glíficos consultados', False),
    Step('corpus/archive-source-v3.json', 'import', 'archive-source-v3', 'Integración del archivo',
         'Fuente de los pasajes consultables', False),
    Step('corpus/glyph-images-v4.json', 'images', 'glyph-images-v4', 'Migración de imágenes glíficas',
         'Imagen enlazada desde su ficha externa', False),
    Step('corpus/glyph-lexicon-v5.json', 'import', 'glyph-lexicon-v5', 'Consulta editorial de catálogos',
         'Lemas y asociaciones glíficas con fuentes ya registradas; sin cotejo primario', False),
    Step('corpus/glyph-source-images-v5.json', 'source_images', 'glyph-source-images-v5', 'Consulta editorial de catálogos',
         'Imagen y procedencia tomadas de la ficha existente; cotejo primario pendiente', False),
    Step('corpus/gdn-lexicon-v6.json', 'import', 'gdn-v6-', 'Extracción automática de GDN',
         'Paleografía y traducción de catálogo conservadas; revisión lingüística pendiente', True),
    Step('corpus/glyph-associations-v7.json', 'import', 'glyph-v7-', 'Script de referencias visuales',
         'Enlaces documentales y contextuales explícitos; sin atribuir lectura completa', True),
    Step('corpus/flor-lexicon-v8.json', 'import', 'flor-v8-', 'Consulta editorial de flor',
         'Entradas léxicas seleccionadas y alcance nominal explícito; cotejo primario pendiente', True),
)
BUNDLE_PATHS = tuple(step.path for step in STEPS)


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


# ---------------------------------------------------------------------------
# Fuentes
# ---------------------------------------------------------------------------
def releases(manifest=None, root=ROOT):
    """Publicaciones editoriales registradas, validadas: [(registro, paquete)].

    Cada paquete debe llamarse ``editorial-<id>.json`` y conservar el hash
    registrado; un cambio exige una publicación nueva."""
    from .community import text
    path = Path(manifest) if manifest is not None else Path(root) / RELEASES
    if not path.exists():
        return []
    data = json.loads(path.read_text())
    if data.get('schema_version') != 1 or not isinstance(data.get('releases'), list):
        raise ValueError('Registro de publicaciones editoriales inválido.')
    seen, result = set(), []
    for release in data['releases']:
        rid, filename = release.get('id', ''), release.get('bundle', '')
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]{1,79}', rid) or rid in seen or filename != f'editorial-{rid}.json':
            raise ValueError('Identificador o archivo de publicación inválido.')
        raw = (path.parent / filename).read_bytes()
        if sha256(raw) != release.get('sha256'):
            raise ValueError('La publicación editorial cambió sin una versión nueva.')
        text(release.get('reviewer', ''), 'Responsable', 200, True)
        text(release.get('reason', ''), 'Alcance de publicación', 2000, True)
        seen.add(rid)
        result.append((release, json.loads(raw)))
    return result


def steps(root=ROOT, release_list=None):
    """Pasos de migración en orden, con su paquete leído: [(Step, paquete)].

    ``release_list`` permite al llamador inyectar sus publicaciones (pruebas)."""
    root = Path(root)
    out = []
    for step in STEPS:
        path = root / step.path
        if step.optional and not path.is_file():
            continue
        raw = path.read_bytes()
        marker = step.marker + sha256(raw)[:16] if step.marker.endswith('-') else step.marker
        out.append((step._replace(marker=marker), json.loads(raw.decode('utf-8'))))
    for release, bundle in (releases(root=root) if release_list is None else release_list):
        out.append((Step('corpus/' + release['bundle'], 'import',
                         'editorial-release-' + release['id'] + '-' + release['sha256'][:16],
                         release['reviewer'], release['reason'], False), bundle))
    return out


def input_paths(root=ROOT):
    """Rutas relativas de todos los paquetes que alimentan el catálogo."""
    return [step.path for step, _ in steps(root)]


def source_rows(documents, apply_patches=False):
    """Filas tal como están en los paquetes, para citar archivo y hash.

    ``documents``: [(ruta, contenido)] en el orden de ``input_paths``. Devuelve
    (filas, orígenes): la última fila completa de cada ID y el archivo que la
    contiene. Las filas sin ``kind`` son rellenos; con ``apply_patches`` se
    superponen en su posición a la fila vigente. No aplica la fusión de la base
    (para eso está el catálogo)."""
    rows, origins = {}, {}
    for path, data in documents:
        for row in data.get('records', []):
            if 'kind' in row:
                rows[row['id']] = row
                origins[row['id']] = path
            elif apply_patches:
                if row['id'] not in rows:
                    raise ValueError('Parche público sin registro previo.')
                rows[row['id']] = dict(rows[row['id']], **row)
    return rows, origins


def public_closure(records):
    """Registros públicos cuyas dependencias también son públicas.

    Un dato que depende de otro retirado o privado (acepción, fuente, evidencia,
    asociación) deja de publicarse. Única implementación del cierre público."""
    visible = {rid: r for rid, r in records.items() if r.get('rights', {}).get('public') is True}
    while True:
        hidden = set()
        for rid, r in visible.items():
            deps = [r[k] for k in ('sense_id', 'primary_source_id') if r.get(k)] + list(r.get('sense_ids', []))
            deps += [e[k] for e in r.get('evidence', []) for k in ('source_id', 'via_source_id') if e.get(k)]
            association = r.get('association') or {}
            deps += [association[k] for k in ('reference_form_id', 'reference_glyph_id') if association.get(k)]
            if any(d not in visible for d in deps):
                hidden.add(rid)
        if not hidden:
            return visible
        visible = {rid: r for rid, r in visible.items() if rid not in hidden}


# ---------------------------------------------------------------------------
# Entradas léxicas
# ---------------------------------------------------------------------------
REVIEW_ORDER = ('inherited', 'catalog_checked', 'reviewed')


def form_key(form):
    """Clave de lema de una forma: fonémica de su forma normalizada de catálogo o escrita."""
    return key_of(form.get('catalog_normalized') or form.get('written') or '')


def entries(records):
    """Agrupa acepciones, formas y glifos públicos por lema (ver el docstring del módulo)."""
    senses = {rid: r for rid, r in records.items() if r.get('kind') == 'sense'}
    parent = {sid: sid for sid in senses}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    forms_by_sense, owner_of_key = {}, {}
    for r in sorted(records.values(), key=lambda r: r['id']):
        if r.get('kind') != 'form' or r.get('sense_id') not in senses:
            continue
        forms_by_sense.setdefault(r['sense_id'], []).append(r)
        k = form_key(r)
        if not k:
            continue
        if k in owner_of_key:
            a, b = find(owner_of_key[k]), find(r['sense_id'])
            if a != b:
                parent[max(a, b)] = min(a, b)
        else:
            owner_of_key[k] = r['sense_id']
    groups = {}
    for sid in sorted(senses):
        groups.setdefault(find(sid), []).append(sid)
    glyphs_by_sense = {}
    for r in sorted(records.values(), key=lambda r: r['id']):
        if r.get('kind') == 'glyph' and r.get('sense_id') in senses:
            glyphs_by_sense.setdefault(r['sense_id'], []).append(r)
    out, used = [], Counter()
    for root_id in sorted(groups):
        sense_ids = groups[root_id]
        forms = [f for sid in sense_ids for f in forms_by_sense.get(sid, [])]
        glyphs = [g for sid in sense_ids for g in glyphs_by_sense.get(sid, [])]
        written = Counter(f.get('catalog_normalized') or f['written'] for f in forms)
        lemma = sorted(written, key=lambda w: (-written[w], fold(w), w))[0] if written else senses[root_id]['label']
        key = Counter(form_key(f) for f in forms).most_common(1)[0][0] if forms else ''
        members = [senses[s] for s in sense_ids] + forms + glyphs
        base = 'lemma-' + (readable(key) if key else root_id)
        used[base] += 1
        eid = base if used[base] == 1 else base + '-' + hashlib.sha256(root_id.encode()).hexdigest()[:6]
        statuses = [m.get('verification') for m in members if m.get('verification') in REVIEW_ORDER]
        out.append(dict(
            id=eid, lemma=lemma, key=readable(key) if key else '', loose_key=loose_key(lemma),
            senses=[senses[s] for s in sense_ids], forms=forms, glyphs=glyphs,
            spellings=sorted({s for f in forms for s in (f.get('written'), f.get('catalog_normalized')) if s},
                             key=lambda s: (fold(s), s)),
            sources=sorted({e[k] for m in members for e in m.get('evidence', [])
                            for k in ('source_id', 'via_source_id') if e.get(k)}),
            rights=dict(public=all(m.get('rights', {}).get('public') is True for m in members),
                        training=all(m.get('rights', {}).get('training') is True for m in [senses[s] for s in sense_ids] + forms)),
            review=dict(status=min(statuses, key=REVIEW_ORDER.index) if statuses else 'inherited',
                        automatic=any(m.get('import_status') == 'automatic_transcription' for m in members),
                        primary_checked=any(e.get('status') == 'primary_checked' for m in members for e in m.get('evidence', [])))))
    return out


# ---------------------------------------------------------------------------
# Catálogo canónico
# ---------------------------------------------------------------------------
def build(root=ROOT):
    """Catálogo canónico: los registros públicos de una base nueva, agrupados en entradas."""
    from .corpus import CorpusStore
    with tempfile.TemporaryDirectory(prefix='amoxcalli-lexicon-') as directory:
        store = CorpusStore(Path(directory) / 'catalog.sqlite3', root=root)
        records = {rid: {k: v for k, v in r.items() if k != 'version'} for rid, r in store.public_records().items()}
    grouped = entries(records)
    in_entries = {m['id'] for e in grouped for m in e['senses'] + e['forms'] + e['glyphs']}
    rest = [records[rid] for rid in sorted(records) if rid not in in_entries]
    inputs = {p: sha256((Path(root) / p).read_bytes()) for p in input_paths(root)}
    return dict(schema=SCHEMA, generated_by='python -m nahuatl_local.lexicon', inputs=inputs,
                counts=dict(entries=len(grouped), records=len(records), **dict(sorted(Counter(r['kind'] for r in records.values()).items()))),
                note='Generado; no editar a mano. Las correcciones entran como paquete nuevo o como propuesta revisada.',
                entries=grouped, sources=[r for r in rest if r['kind'] == 'source'],
                other=[r for r in rest if r['kind'] != 'source'])


def encode(catalog):
    return json.dumps(catalog, ensure_ascii=False, indent=1, sort_keys=False) + '\n'


def load(root=ROOT):
    """Catálogo canónico validado contra los hashes de sus paquetes de entrada."""
    root = Path(root)
    catalog = json.loads((root / CATALOG).read_text(encoding='utf-8'))
    if catalog.get('schema') != SCHEMA:
        raise ValueError('Esquema de catálogo léxico desconocido.')
    current = {p: sha256((root / p).read_bytes()) for p in input_paths(root)}
    if catalog.get('inputs') != current:
        raise ValueError('Catálogo léxico obsoleto: regenéralo con `python -m nahuatl_local.lexicon`.')
    return catalog


def records_of(catalog):
    """Registros planos {id: registro} del catálogo (entradas, fuentes y demás)."""
    rows = [m for e in catalog['entries'] for m in e['senses'] + e['forms'] + e['glyphs']]
    rows += catalog['sources'] + catalog['other']
    return {r['id']: r for r in sorted(rows, key=lambda r: r['id'])}


def load_records(root=ROOT):
    """Registros públicos del catálogo canónico: lo que leen analizador y evaluaciones."""
    return records_of(load(root))


# ---------------------------------------------------------------------------
# Migración de una base local sobre el catálogo
# ---------------------------------------------------------------------------
def snapshot(db):
    """Contenido completo de cada tabla de una base SQLite abierta."""
    return {row[0]: [tuple(r) for r in db.execute('SELECT * FROM "' + row[0] + '"').fetchall()]
            for row in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()}


def divergence(store, root=ROOT):
    """IDs en que una base local difiere del catálogo: ediciones, registros propios y ocultos."""
    catalog = load_records(root)
    public = {rid: {k: v for k, v in r.items() if k != 'version'} for rid, r in store.public_records().items()}
    return dict(edited=sorted(rid for rid in public if rid in catalog and public[rid] != catalog[rid]),
                local_only=sorted(set(public) - set(catalog)),
                hidden=sorted(set(catalog) - set(public)))


def migrate(db_path, root=ROOT, backup_dir=None):
    """Superpone una base de Voces al catálogo canónico sin perder nada.

    1. Respalda la base (``data/backups/voces-before-lexicon-catalog-v1.sqlite3``).
    2. La abre con ``CorpusStore``: aplica pasos pendientes de ``STEPS`` (solo añaden).
    3. Registra en ``corpus_meta`` el catálogo sobre el que queda la base.
    4. Comprueba que cada fila previa sigue intacta: en tablas ``corpus_*`` las filas
       anteriores siguen presentes; las demás tablas (perfiles, aportaciones, audio)
       son idénticas. Si algo falla, se detiene y conserva el respaldo."""
    from .corpus import CorpusStore
    from .community import now
    db_path = Path(db_path)
    backup_dir = Path(backup_dir) if backup_dir is not None else Path(root) / 'data/backups'
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / 'voces-before-lexicon-catalog-v1.sqlite3'
    if not backup.exists():
        with closing(sqlite3.connect(db_path)) as src, closing(sqlite3.connect(backup)) as dest:
            src.backup(dest)
        backup.chmod(0o600)
    with closing(sqlite3.connect(backup)) as db:
        before = snapshot(db)
    store = CorpusStore(db_path, root=None if Path(root) == ROOT else root)
    marker = 'lexicon-catalog-' + sha256((Path(root) / CATALOG).read_bytes())[:16]
    with store.db() as db:
        db.execute('INSERT OR IGNORE INTO corpus_meta VALUES(?,?)', (marker, now()))
        after = snapshot(db)
    preserved = {table: set(rows).issubset(set(after.get(table, []))) if table.startswith('corpus_')
                 else rows == after.get(table, []) for table, rows in before.items()}
    if not all(preserved.values()):
        raise RuntimeError('La comprobación de preservación falló; se conserva el respaldo ' + str(backup))
    changes = divergence(store, root)
    return dict(schema_version=1, backup=str(backup), marker=marker, tables_preserved=preserved,
                records_before=len(before.get('corpus_records', [])), records_after=len(after.get('corpus_records', [])),
                proposals=len(after.get('corpus_proposals', [])), people=len(after.get('people', [])),
                edited=len(changes['edited']), local_only=len(changes['local_only']), hidden=len(changes['hidden']))


def main(argv=None):
    parser = argparse.ArgumentParser(description='Genera o comprueba corpus/lexicon-catalog.json; migra una base local.')
    parser.add_argument('--check', action='store_true', help='Falla si el catálogo no coincide con los paquetes.')
    parser.add_argument('--migrate', type=Path, metavar='DB',
                        help='Respalda la base de Voces indicada, la superpone al catálogo y comprueba la preservación.')
    args = parser.parse_args(argv)
    if args.migrate:
        print(json.dumps(migrate(args.migrate), ensure_ascii=False, indent=2))
        return
    catalog = build()
    path = ROOT / CATALOG
    if args.check:
        if not path.is_file() or path.read_text(encoding='utf-8') != encode(catalog):
            raise SystemExit('El catálogo léxico no coincide con los paquetes; ejecuta python -m nahuatl_local.lexicon')
    else:
        path.write_text(encode(catalog), encoding='utf-8')
    print(json.dumps(catalog['counts'], ensure_ascii=False))


if __name__ == '__main__':
    main()
