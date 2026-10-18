"""QA de retorno a pasajes públicos, con HTTP y almacenamiento sintéticos."""
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
parser.add_argument('--baseline', action='store_true')
args = parser.parse_args()
with tempfile.TemporaryDirectory() as directory:
    httpd = make_server(CorpusStore(Path(directory) / 'qa.sqlite3'), port=0)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        prewarm(f'http://127.0.0.1:{httpd.server_address[1]}')
        environment = dict(os.environ, CORPUS_QA_ORIGIN=f'http://127.0.0.1:{httpd.server_address[1]}')
        if args.baseline:
            environment['READING_CONTINUITY_BASELINE'] = '1'
        result = subprocess.run(['node', str(ROOT / 'tests/reading_continuity.cjs')], env=environment, timeout=60)
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join()
    raise SystemExit(result.returncode)
