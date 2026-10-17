"""QA DOM+HTTP reproducible, jsdom solo como dependencia de desarrollo.

Verifica la presentación; no escribe evidencias ni hashes en reports/.
"""
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import threading
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from nahuatl_local.corpus import CorpusStore
from nahuatl_local.platform import make_server
from qa_prewarm import prewarm
with tempfile.TemporaryDirectory() as directory:
    httpd=make_server(CorpusStore(Path(directory)/'qa.sqlite3'),port=0)
    thread=threading.Thread(target=httpd.serve_forever,daemon=True);thread.start()
    try:
        origin=f'http://127.0.0.1:{httpd.server_address[1]}'
        # Precalienta en el mismo proceso lo que se construye perezosamente (resumen del Laboratorio,
        # índices de evidencia y de análisis): en un clon limpio puede tardar más que las esperas del DOM.
        prewarm(origin)
        environment=dict(os.environ,CORPUS_QA_ORIGIN=origin)
        result=subprocess.run(['node',str(ROOT/'tests/platform_ui.cjs')],env=environment,timeout=120)
    finally:httpd.shutdown();httpd.server_close();thread.join()
    raise SystemExit(result.returncode)
