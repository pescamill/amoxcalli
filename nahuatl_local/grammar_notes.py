"""Notas gramaticales breves con cita de una gramática histórica de dominio público.

``corpus/grammar-notes-carochi-v1.json`` reúne notas redactadas por el proyecto a
partir del facsímil de Carochi (1645), con libro, capítulo y folio. Las usan las
unidades de lectura (absolutivo, posesivos, prefijos de sujeto y objeto, plurales,
locativos). ``load`` valida el archivo; ``for_unit`` devuelve las notas de una unidad.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = 'corpus/grammar-notes-carochi-v1.json'
SCHEMA = 'amoxcalli-grammar-notes-1'
UNITS = ('absolutivo', 'posesivos', 'prefijos de sujeto', 'prefijos de objeto', 'plurales', 'locativos')


def load(root=ROOT):
    data = json.loads((Path(root) / PATH).read_text(encoding='utf-8'))
    if data.get('schema') != SCHEMA:
        raise ValueError('Esquema de notas gramaticales desconocido.')
    source, rights = data['source'], data['rights']
    if not source['facsimile']['url'].startswith('https://') or 'Dominio público' not in source['rights']:
        raise ValueError('La fuente necesita un facsímil enlazado y su condición de dominio público.')
    if rights.get('training') is not False or not rights.get('note'):
        raise ValueError('Declara los derechos de las notas; el entrenamiento queda excluido.')
    seen = set()
    for note in data['notes']:
        citation = note.get('citation') or {}
        if not all(citation.get(k) for k in ('book', 'chapter', 'folios')) or 'f. ' not in citation['folios']:
            raise ValueError(f'{note.get("id")}: cada nota cita libro, capítulo y folio.')
        if not note.get('summary') or len(note['summary']) > 900 or not note.get('units'):
            raise ValueError(f'{note.get("id")}: nota vacía, demasiado larga o sin unidad.')
        if note['id'] in seen:
            raise ValueError('Identificador de nota duplicado.')
        seen.add(note['id'])
    return data


def for_unit(unit, root=ROOT):
    """Notas de una unidad, con la fuente para citarla."""
    data = load(root)
    return [dict(note, source=data['source']['label'] + ' (' + data['source']['date'] + ')',
                 facsimile=data['source']['facsimile']['url'])
            for note in data['notes'] if unit in note['units']]
