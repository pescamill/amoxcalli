"""Construye Amoxcalli para el teléfono: la misma aplicación como archivos estáticos, con su Python (Pyodide)
corriendo dentro del navegador. Sin servidor y, después de la primera visita, sin internet.

    python3 scripts/build_movil.py                 → sitio/app/ (se publica con la página de presentación)
    python3 scripts/build_movil.py --salida X      → otra carpeta

Solo empaqueta archivos del repositorio (git ls-files, sin los ignorados) y los datos derivados que se calculan aquí mismo: nunca
aportaciones, perfiles, aclaraciones ni la base local de quien construye.
"""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
PYODIDE = '0.29.5'
CDN = f'https://cdn.jsdelivr.net/pyodide/v{PYODIDE}/full/'
CORE = ['pyodide.js', 'pyodide.asm.js', 'pyodide.asm.wasm', 'python_stdlib.zip', 'pyodide-lock.json']
# Lo que la aplicación lee al correr (medido con un registro de aperturas sobre todas las rutas).
RUNTIME = ('nahuatl_local/', 'corpus/', 'editorial/', 'configs/', 'docs/', 'CONTRIBUTING.md')
DERIVED = ('data/derived/stem-counts.json', 'data/derived/gloss-hints.json')
TEXT = ('.html', '.js', '.css', '.webmanifest')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--salida', type=Path, default=ROOT / 'sitio' / 'app')
    ap.add_argument('--interno', type=Path, help=argparse.SUPPRESS)
    args = ap.parse_args()
    if args.interno:
        return export_pages(args.interno)
    out = args.salida.resolve()
    with tempfile.TemporaryDirectory(prefix='amoxcalli-movil-') as tmp:
        copy = Path(tmp) / 'amoxcalli'
        tracked = subprocess.run(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard', '--', *RUNTIME], cwd=ROOT, check=True,
                                 capture_output=True).stdout.decode().split('\0')
        for rel in filter(None, tracked):
            (copy / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / rel, copy / rel)
        if out.exists():
            shutil.rmtree(out)
        out.mkdir(parents=True)
        # En una copia limpia: prepara el análisis (data/derived/) y exporta las páginas con el mismo manejador.
        subprocess.run([sys.executable, str(Path(__file__).resolve()), '--interno', str(out)], cwd=copy, check=True)
        with zipfile.ZipFile(out / 'amoxcalli.zip', 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
            for rel in sorted(filter(None, tracked)) + list(DERIVED):
                if rel.startswith('nahuatl_local/movil_web/'):
                    continue  # el arranque del navegador va como archivos estáticos
                bundle.write(copy / rel, rel)
    fetch_pyodide(out / 'pyodide')
    for name in ('puente.js', 'worker.js', 'aportar.html'):
        shutil.copy2(ROOT / 'nahuatl_local' / 'movil_web' / name, out / name)
    write_service_worker(out)
    total = sum(p.stat().st_size for p in out.rglob('*') if p.is_file())
    print(f'listo: {out} ({total / 1e6:.1f} MB)')


def export_pages(out):
    """Corre dentro de la copia limpia: cada página y archivo sale del mismo manejador que usa el servidor."""
    sys.path.insert(0, str(Path.cwd()))
    from nahuatl_local.movil import App
    from nahuatl_local.platform import STATIC
    app = App()
    for stage in app.warm_stages():
        stage()
    paths = ['/', *[p for p in STATIC.aliases if p != '/']]
    paths += ['/' + f.name for f in sorted(STATIC.directory.iterdir())
              if STATIC.find('/' + f.name) and f.name not in ('index.html', 'sw.js', 'offline.html', 'offline.css')]
    paths.append('/archive.csv')
    files = {}
    for path in paths:
        status, _, body = app.request('GET', path)
        if status != 200:
            raise SystemExit(f'{path}: {status}')
        files['index.html' if path == '/' else path[1:]] = body
    targets = sorted({name.split('/')[0] + ('/' if '/' in name else '') for name in files} | {'api/', '#', 'sw.js'}, key=len, reverse=True)
    pattern = re.compile(r'(?<=[\'"`])/(?=(?:' + '|'.join(map(re.escape, targets)) + r'))')
    for name, body in files.items():
        target = out / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if not name.endswith(TEXT):
            target.write_bytes(body)
            continue
        text = body.decode()
        # Rutas absolutas → relativas: la app vive en una subcarpeta (pescamill.github.io/amoxcalli/app/).
        text = re.sub(r'(?<=[\'"`])/aportar/?(?=[\'"`])', 'aportar.html', text)
        text = pattern.sub('./', text)
        if name == 'index.html':
            text = text.replace('<head>', '<head><script src="puente.js"></script>', 1)
        if name == 'install.js':
            text = _replace(text, 'El servidor debe estar encendido para consultar y guardar aportaciones.',
                            'Funciona sin internet: lo que guardes se queda en este dispositivo.')
        if name == 'manifest.webmanifest':
            manifest = json.loads(text)
            manifest.update(id='./', start_url='./', scope='./')
            manifest['shortcuts'] = [s for s in manifest.get('shortcuts', []) if 'aportar' not in s['url']]
            text = json.dumps(manifest, ensure_ascii=False, indent=2)
        target.write_text(text)


def _replace(text, old, new):
    if old not in text:
        raise SystemExit(f'No se encontró el texto a reemplazar: {old!r}')
    return text.replace(old, new)


def fetch_pyodide(folder):
    """Pyodide servido desde la misma página (sin CDN al usarla): núcleo y el paquete sqlite3, verificado."""
    folder.mkdir(parents=True, exist_ok=True)
    for name in CORE:
        (folder / name).write_bytes(_download(CDN + name))
    lock = json.loads((folder / 'pyodide-lock.json').read_text())
    package = lock['packages']['sqlite3']
    wheel = _download(CDN + package['file_name'])
    if hashlib.sha256(wheel).hexdigest() != package['sha256']:
        raise SystemExit('sqlite3 de Pyodide no coincide con su huella: no se publica.')
    (folder / package['file_name']).write_bytes(wheel)


def _download(url):
    from nahuatl_local.wiktionary_import import _context  # TLS verificado también con Python.org en macOS
    with urllib.request.urlopen(url, timeout=120, context=_context()) as response:
        return response.read()


def write_service_worker(out):
    files = sorted(str(p.relative_to(out)) for p in out.rglob('*') if p.is_file())
    version = hashlib.sha256(b''.join(hashlib.sha256((out / f).read_bytes()).digest() for f in files)).hexdigest()[:12]
    template = (ROOT / 'nahuatl_local' / 'movil_web' / 'sw.js').read_text()
    # El corpus original en CSV (5 MB) solo se descarga a petición: no ocupa espacio sin conexión.
    listing = json.dumps(['./'] + [f for f in files if f not in ('index.html', 'archive.csv')])
    (out / 'sw.js').write_text(template.replace('__VERSION__', version).replace('__FILES__', listing))


if __name__ == '__main__':
    main()
