"""Archivo paralelo Axolotl: único lector del CSV y modelo de pasaje.

``corpus/axolotl/axolotl.csv`` no tiene encabezado. Cada registro trae cinco
columnas (``COLUMNS``) y su identificador es el índice del registro CSV, base 1
(``axolotl-00001``). Un registro puede ocupar varias líneas físicas si un campo
lleva saltos de línea; por eso se cuenta el registro, no la línea.

Tres niveles, todos sobre el mismo análisis:

* ``parse`` / ``records``: registros crudos ``(número, campos)``, sin filtrar.
  Los usan quienes citan o hashean el original (evaluación documental,
  preparación de entrenamiento).
* ``passage``: el **modelo de pasaje** que comparten la aplicación, el
  analizador y las evaluaciones: id, náhuatl, español, variedad, obra,
  localizador y derechos. Conserva el texto tal cual; nada se normaliza aquí.
* ``load``: todos los pasajes utilizables (cinco campos, náhuatl y español no
  vacíos), en el orden del archivo.
"""
import csv
import io
import json
from pathlib import Path
from threading import Lock

ROOT = Path(__file__).resolve().parents[1]
AXOLOTL = 'corpus/axolotl/axolotl.csv'
COLUMNS = ('es', 'nah', 'variant', 'document', 'iso')
LABELS = {'nci': 'Náhuatl clásico', 'azz': 'Náhuatl de la Sierra de Puebla', 'nhm': 'Náhuatl de Morelos',
          'nhn': 'Náhuatl central', 'nhw': 'Náhuatl de la Huasteca occidental',
          'nhe': 'Náhuatl de la Huasteca oriental', 'unknown': 'Variedad no indicada'}
VERIFICATION = 'Alineación de origen; sin cotejo propio'

_CACHE = {}
_LOCK = Lock()


def passage_id(number):
    return f'axolotl-{number:05d}'


def parse(text):
    """Registros ``(número, campos)`` de un texto CSV de Axolotl. Único ``csv.reader`` del archivo."""
    return [(number, fields) for number, fields in enumerate(csv.reader(io.StringIO(text, newline='')), 1)]


def records(path=None, root=ROOT):
    """Registros crudos del archivo (por omisión, el versionado en ``corpus/``).

    Se memorizan por ruta, tamaño y fecha de modificación; cada llamada devuelve
    listas nuevas, de modo que modificar el resultado no altera la caché."""
    path = Path(path) if path is not None else Path(root) / AXOLOTL
    stat = path.stat()
    key = (str(path.resolve()), stat.st_size, stat.st_mtime_ns)
    with _LOCK:
        if key not in _CACHE:
            _CACHE.clear()
            _CACHE[key] = tuple((n, tuple(f)) for n, f in parse(path.read_bytes().decode('utf-8')))
        cached = _CACHE[key]
    return [(n, list(f)) for n, f in cached]


def original(fields):
    """Campos originales por nombre de columna, sin tocar (para citar)."""
    return dict(zip(COLUMNS, fields))


def source(root=ROOT):
    """Procedencia y derechos declarados del archivo (``configs/sources.json``)."""
    path = Path(root) / 'configs/sources.json'
    config = json.loads(path.read_text(encoding='utf-8'))['corpus'] if path.is_file() else {}
    url = (f"https://github.com/{config['repository']}/blob/{config['revision']}/{config['path']}"
           if config.get('repository') else '')
    return dict(config, url=url)


def passage(number, fields, origin=None):
    """Modelo de pasaje, o ``None`` si el registro no es utilizable.

    Claves: ``id``, ``line`` (número de registro), ``nah``, ``es``, ``variant`` e ``iso``
    (variedad declarada; ``unknown`` si falta), ``variant_label``, ``period``,
    ``document`` (obra), ``locator``, ``source_url``, ``rights_note`` y ``verification``."""
    if len(fields) < 5:
        return None
    es, nah, variant, document, iso = fields[:5]
    if not es.strip() or not nah.strip():
        return None
    origin = origin or {}
    iso = iso or 'unknown'
    return dict(id=passage_id(number), line=number, es=es, nah=nah, variant=variant, iso=iso, document=document,
                variant_label=LABELS.get(iso, variant),
                period='historical' if iso == 'nci' else 'unknown' if iso == 'unknown' else 'modern',
                locator=f'Axolotl, registro CSV {number}; página de la edición primaria pendiente',
                source_url=origin.get('url', ''), rights_note=origin.get('rights_note', ''),
                verification=VERIFICATION)


def load(root=ROOT, path=None):
    """Todos los pasajes utilizables, en el orden del archivo."""
    origin = source(root)
    rows = (passage(n, f, origin) for n, f in records(path, root))
    return [r for r in rows if r is not None]
