"""Aviso de versión nueva: una consulta anónima a GitHub, como mucho una vez al día.

Solo se pide el número de la última versión publicada; no se envía nada del usuario.
Sin internet, la consulta falla en silencio y la aplicación sigue igual.
Se desactiva con `serve --no-update-check` o AMOXCALLI_NO_UPDATE_CHECK=1.
"""
import json
import os
import re
import threading
import time
import urllib.request
from pathlib import Path

from . import __version__
from .community import ROOT

LATEST = 'https://api.github.com/repos/pescamill/amoxcalli/releases/latest'
DOWNLOAD = 'https://github.com/pescamill/amoxcalli/releases/latest'
CACHE = ROOT / 'data/derived/update-check.json'
DAY = 24 * 3600


def parse(tag):
    """'v0.1.2' → (0, 1, 2); None si no es una versión."""
    m = re.fullmatch(r'v?(\d+)\.(\d+)\.(\d+)', (tag or '').strip())
    return tuple(int(x) for x in m.groups()) if m else None


def disabled():
    return os.environ.get('AMOXCALLI_NO_UPDATE_CHECK', '').strip() not in ('', '0')


class Updates:
    def __init__(self, current=__version__, cache=CACHE, fetch=None, git=None):
        self.current = current
        self.cache = Path(cache)
        self.fetch = fetch or self._fetch
        # Instalado con git clone: se actualiza con git pull, no con el .zip.
        self.git = (ROOT / '.git').exists() if git is None else git
        self.latest = None
        self.notes = ''

    def _fetch(self):
        req = urllib.request.Request(LATEST, headers={'Accept': 'application/vnd.github+json',
                                                      'User-Agent': f'Amoxcalli/{__version__}'})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.load(r)
        return dict(tag=data.get('tag_name', ''), notes=(data.get('body') or '')[:2000])

    def check(self, now=None):
        """Usa el resultado guardado si tiene menos de un día; si no, pregunta a GitHub."""
        now = time.time() if now is None else now
        try:
            saved = json.loads(self.cache.read_text())
            fresh = now - saved.get('checked', 0) < DAY
        except (OSError, ValueError):
            saved, fresh = {}, False
        if not fresh:
            try:
                saved = dict(self.fetch(), checked=now)
                self.cache.parent.mkdir(parents=True, exist_ok=True)
                self.cache.write_text(json.dumps(saved, ensure_ascii=False))
            except Exception:
                pass  # sin red o GitHub no responde: se queda lo último que se supo
        self.latest, self.notes = saved.get('tag'), saved.get('notes', '')
        return self.status()

    def start(self):
        def run():
            s = self.check()
            if s['available']:
                print(f"Hay una versión nueva de Amoxcalli: {s['latest']} (tienes {s['current']}). {DOWNLOAD}", flush=True)
        threading.Thread(target=run, daemon=True, name='update-check').start()

    def status(self):
        new, old = parse(self.latest), parse(self.current)
        available = bool(new and old and new > old)
        out = dict(current=self.current, available=available)
        if available:
            out.update(latest=self.latest.lstrip('v'), notes=self.notes, url=DOWNLOAD,
                       how='git' if self.git else 'zip')
        return out
