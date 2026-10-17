"""QA de Dioses y calendario: fichas, búsqueda por grafía, calendario, lecturas y unidad, con HTTP sintético."""
import argparse
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

parser = argparse.ArgumentParser(description=__doc__)
parser.parse_args()
with tempfile.TemporaryDirectory() as directory:
    httpd = make_server(CorpusStore(Path(directory) / 'qa.sqlite3'), port=0)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        origin = f'http://127.0.0.1:{httpd.server_address[1]}'
        prewarm(origin)
        environment = dict(os.environ, CORPUS_QA_ORIGIN=origin)
        result = subprocess.run(['node', str(ROOT / 'tests/gods_ui.cjs')], env=environment, timeout=120)
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join()
    raise SystemExit(result.returncode)
