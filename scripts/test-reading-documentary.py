"""QA de continuidad: del pasaje a las fichas de Preguntar y de vuelta, sin geometría simulada."""
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
from qa_prewarm import prewarm

with tempfile.TemporaryDirectory() as directory:
    httpd = make_server(CorpusStore(Path(directory) / 'qa.sqlite3'), port=0)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        prewarm(f'http://127.0.0.1:{httpd.server_address[1]}')
        environment = dict(os.environ, CORPUS_QA_ORIGIN=f'http://127.0.0.1:{httpd.server_address[1]}')
        result = subprocess.run(['node', str(ROOT / 'tests/reading_documentary_continuity.cjs')], env=environment, timeout=60)
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join()
    raise SystemExit(result.returncode)
