"""Prueba DOM/HTTP de Voces (/aportar) en la aplicación única. Requiere Node >=18 y jsdom 26.1.0 para QA."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from nahuatl_local.corpus import CorpusStore
from nahuatl_local.platform import make_server

with tempfile.TemporaryDirectory() as directory:
    httpd = make_server(CorpusStore(Path(directory) / 'qa.sqlite3'), port=0)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        env = dict(os.environ, VOCES_QA_ORIGIN='http://127.0.0.1:' + str(httpd.server_address[1]))
        result = subprocess.run(['node', str(ROOT / 'tests/community_ui.cjs')], env=env, timeout=45)
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join()
    raise SystemExit(result.returncode)
