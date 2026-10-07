"""QA visual en Chromium; dependencias de desarrollo Playwright y navegador local."""
import os,subprocess,sys,tempfile,threading
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from nahuatl_local.corpus import CorpusStore
from nahuatl_local.platform import make_server
with tempfile.TemporaryDirectory() as d:
    server=make_server(CorpusStore(Path(d)/'qa.sqlite3'),port=0)
    worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
    try:
        result=subprocess.run(['node',str(ROOT/'tests/webapp_browser.cjs')],env=dict(os.environ,CORPUS_QA_ORIGIN=f'http://127.0.0.1:{server.server_address[1]}'),cwd=ROOT,timeout=90)
    finally:server.shutdown();server.server_close();worker.join()
    raise SystemExit(result.returncode)
