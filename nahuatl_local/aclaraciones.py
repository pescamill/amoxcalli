"""Aclaraciones: una sola forma de decir «esto no cuadra» desde cualquier pasaje, palabra o ficha.

Quien aclara elige qué pasa (un toque) y, si quiere, escribe una frase, propone algo y dice cómo lo sabe.
El contexto (ID, texto mostrado, ruta, versión) lo pone la aplicación. Se guarda en esta computadora y
solo sale si la persona decide compartirla. Nada se corrige solo: una persona coteja con la fuente.

Del lado del proyecto, `triage` lee una aclaración compartida (issue de GitHub o archivo), comprueba que el
ID exista, la etiqueta y muestra el registro actual junto a lo propuesto.
"""
import argparse
import json
import re
import secrets
import sys
import threading
import time
from pathlib import Path

from . import __version__
from .community import Problem, ROOT

STORE = ROOT / 'data/community/aclaraciones.jsonl'
SCHEMA = 'amoxcalli.aclaracion/1'
MARK = '<!-- amoxcalli:aclaracion -->'
# Qué pasa: cada categoría dice qué campo del registro mira la revisión y con qué etiqueta llega.
CATEGORIES = {
    'traduccion': dict(label='La traducción no corresponde', field='es', tag='traducción'),
    'analisis': dict(label='La división o el análisis de la palabra', field='analysis', tag='análisis'),
    'grafia': dict(label='Una palabra está mal escrita', field='nah', tag='grafía'),
    'fuente': dict(label='La obra, la página o la fuente no coincide', field='source', tag='fuente'),
    'uso': dict(label='En mi variante o comunidad se dice distinto', field='variant', tag='uso actual'),
    'duda': dict(label='No lo entiendo: tengo una duda', field=None, tag='duda'),
}
# Cómo lo sabe: no da más o menos valor, orienta quién debe revisar.
BASES = {
    'fuente': 'Lo leí en una fuente (obra y página)',
    'hablante': 'Hablo una variante actual',
    'estudio': 'Estudio o enseño náhuatl clásico',
    'intuicion': 'No estoy seguro; me llamó la atención',
}
LIMITS = dict(target=120, note=1000, proposal=600, citation=300, variant=120, nah=600, es=600, route=200)


def _text(value, key):
    value = ' '.join(str(value or '').split())
    if len(value) > LIMITS[key]:
        raise Problem(f'El campo «{key}» es demasiado largo (máximo {LIMITS[key]} caracteres).')
    return value


def clean(data):
    """Lo que se guarda: campos conocidos, recortados y validados. Nunca datos personales."""
    if not isinstance(data, dict):
        raise Problem('La aclaración debe ser un objeto.')
    category = data.get('category')
    if category not in CATEGORIES:
        raise Problem('Elige qué pasa.')
    target = _text(data.get('target'), 'target')
    if not re.fullmatch(r'[\w.:#-]{1,120}', target):
        raise Problem('Falta el pasaje o la ficha.')
    basis = data.get('basis') or 'intuicion'
    if basis not in BASES:
        raise Problem('«Cómo lo sabes» no es válido.')
    context = data.get('context') if isinstance(data.get('context'), dict) else {}
    return dict(schema=SCHEMA, target=target, category=category, basis=basis,
                note=_text(data.get('note'), 'note'), proposal=_text(data.get('proposal'), 'proposal'),
                citation=_text(data.get('citation'), 'citation'),
                variant=_text(data.get('variant'), 'variant') if basis == 'hablante' else '',
                context=dict(nah=_text(context.get('nah'), 'nah'), es=_text(context.get('es'), 'es'),
                             route=_text(context.get('route'), 'route'), version=__version__))


class Store:
    """Las aclaraciones de esta instalación, una por línea (JSONL), legibles y fáciles de respaldar."""

    def __init__(self, path=STORE):
        self.path = Path(path)
        self._lock = threading.Lock()

    def all(self):
        try:
            lines = self.path.read_text(encoding='utf-8').splitlines()
        except OSError:
            return []
        return [json.loads(line) for line in lines if line.strip()]

    def add(self, data):
        item = dict(clean(data), id='ac-' + secrets.token_hex(4), created=time.strftime('%Y-%m-%dT%H:%M:%S'))
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open('a', encoding='utf-8') as f:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        return item

    def remove(self, aid):
        with self._lock:
            items = self.all()
            kept = [i for i in items if i['id'] != aid]
            if len(kept) == len(items):
                raise Problem('Aclaración no encontrada.', 404)
            self.path.write_text(''.join(json.dumps(i, ensure_ascii=False) + '\n' for i in kept), encoding='utf-8')
        return dict(ok=True)


def routes(router, store):
    router.add('GET', '/api/aclaraciones', lambda r: r.reply(dict(items=store.all(), categories=CATEGORIES, bases=BASES)))
    router.add('POST', '/api/aclaraciones', lambda r: r.reply(store.add(r.body()), 201))
    router.add('DELETE', '/api/aclaraciones/', lambda r: r.reply(store.remove(r.tail)), prefix=True)


# ---------- del lado del proyecto ----------

def extract(text):
    """Las aclaraciones dentro de un issue (bloque ```json tras la marca) o de un archivo descargado."""
    text = text.strip()
    if text.startswith(('{', '[')):
        value = json.loads(text)
        items = value.get('items', [value]) if isinstance(value, dict) else value
    else:
        items = [json.loads(m) for m in re.findall(re.escape(MARK) + r'\s*```json\s*(\{.*?\})\s*```', text, re.S)]
    return [clean(i) for i in items]


def lookup(target):
    """El registro actual con ese ID: pasaje del archivo, entrada del diccionario o ficha de dios/calendario."""
    from .research import Archive
    archive = Archive()
    if target in archive.index:
        r = archive.index[target]
        return dict(kind='pasaje', nah=r.get('nah'), es=r.get('es'), source=r.get('document') or 'Obra no indicada')
    from .corpus import CorpusStore
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        records = CorpusStore(Path(d) / 'lookup.sqlite3').public_records()
    if target in records:
        r = records[target]
        return dict(kind=r.get('kind'), nah=r.get('written') or '', es=' · '.join(x for x in (r.get('label'), r.get('definition')) if x),
                    source=', '.join(e.get('source_id', '') for e in r.get('evidence', [])))
    try:
        from .entities import Entities
        e = Entities().get(target)
        return dict(kind='ficha', nah=e.get('name'), es=e.get('kind_label'), source='Fichas de dioses y calendario')
    except Exception:
        return None


def _cell(text):
    return str(text or '').replace('|', '\\|')[:400]


def triage(item, current):
    """Etiquetas y comentario para quien revisa: lo propuesto junto al registro actual."""
    cat = CATEGORIES[item['category']]
    labels = ['aclaración', cat['tag']] + ([] if current else ['id-no-encontrado'])
    if item['basis'] == 'hablante':
        labels.append('variante-actual')
    rows = [f"**{cat['label']}** · `{item['target']}` · {BASES[item['basis']]}"
            + (f" ({item['variant']})" if item['variant'] else '')]
    if current:
        rows += ['', '| | Registro actual | Lo que se vio en la app |', '|---|---|---|',
                 f"| Náhuatl | {_cell(current.get('nah'))} | {_cell(item['context']['nah'])} |",
                 f"| Español | {_cell(current.get('es'))} | {_cell(item['context']['es'])} |",
                 f"| Fuente | {_cell(current.get('source'))} | |"]
        if current.get('nah') and item['context']['nah'] and current['nah'] not in item['context']['nah']:
            rows.append('\n> El texto que vio la persona ya no coincide con el registro: quizá se corrigió después.')
    else:
        rows.append('\n> No se encontró ese ID en el corpus actual.')
    if item['proposal']:
        rows += ['', f"**Propone:** {item['proposal']}"]
    if item['citation']:
        rows += [f"**Cita:** {item['citation']}"]
    rows += ['', 'Siguiente paso: cotejar con la fuente. Si se confirma, corregir el registro y cerrar con el commit; '
                 'si es de una variante actual, pedir revisión de hablantes de esa variante.']
    return dict(labels=labels, comment='\n'.join(rows))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    t = sub.add_parser('triage', help='Lee aclaraciones (issue o .json) y escribe etiquetas y comentario en JSON.')
    t.add_argument('path', help='Archivo con el cuerpo del issue o el .json descargado; «-» para la entrada estándar.')
    args = p.parse_args()
    text = sys.stdin.read() if args.path == '-' else Path(args.path).read_text(encoding='utf-8')
    try:
        items = extract(text)
    except (Problem, ValueError) as error:
        print(json.dumps(dict(items=[], error=str(error)), ensure_ascii=False))
        return
    print(json.dumps(dict(items=[dict(item, **triage(item, lookup(item['target']))) for item in items]),
                     ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
