"""QA DOM+HTTP reproducible, jsdom solo como dependencia de desarrollo."""
import os
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from nahuatl_local.corpus import CorpusStore
from nahuatl_local.platform import make_server
from nahuatl_local.documentary_retrieval import public_path
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("--documentary-display",action="store_true",help="Persistir evidencia de presentación solo tras pasar toda la suite.")
args=parser.parse_args()
with tempfile.TemporaryDirectory() as directory:
    httpd=make_server(CorpusStore(Path(directory)/'qa.sqlite3'),port=0)
    thread=threading.Thread(target=httpd.serve_forever,daemon=True);thread.start()
    try:
        environment=dict(os.environ,CORPUS_QA_ORIGIN=f'http://127.0.0.1:{httpd.server_address[1]}')
        evidence=Path(directory)/'documentary-display.json'
        if args.documentary_display:environment['LAB_DOCUMENTARY_DISPLAY_OUTPUT']=str(evidence)
        result=subprocess.run(['node',str(ROOT/'tests/platform_ui.cjs')],env=environment,timeout=60)
        if result.returncode==0 and args.documentary_display:
            destination=public_path(ROOT,'reports/documentary-laboratory-display-v1.json',writing=True)
            destination.write_bytes(evidence.read_bytes())
    finally:httpd.shutdown();httpd.server_close();thread.join()
    raise SystemExit(result.returncode)
