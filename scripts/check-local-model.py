"""Prueba real de generación HTTP. Requiere ejecutar antes scripts/amoxcalli.sh setup."""
import json,sys,tempfile,threading,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from nahuatl_local.corpus import CorpusStore
from nahuatl_local.platform import make_server
with tempfile.TemporaryDirectory() as d:
    server=make_server(CorpusStore(Path(d)/'voces.sqlite3'),port=0)
    worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
    url=f'http://127.0.0.1:{server.server_address[1]}'
    try:
        status=json.load(urllib.request.urlopen(url+'/api/system'))
        if not status['model']['ready']:raise SystemExit('Modelo incompleto: ejecuta bash scripts/amoxcalli.sh setup')
        value='La casa y la flor.';start=time.monotonic()
        request=urllib.request.Request(url+'/api/compose',data=json.dumps({'text':value}).encode(),headers={'Content-Type':'application/json','Origin':url})
        result=json.load(urllib.request.urlopen(request,timeout=300))
        assert result['method']=='local_model'
        assert all(r['iso']=='nci' for r in result['context_passages'])
        report=dict(input=value,elapsed_seconds=round(time.monotonic()-start,2),model=status['model'],result=result,note='Comprobación de integración; no es validación lingüística.')
        (ROOT/'reports/webapp-model-smoke.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
        print(json.dumps(dict(output=result['segments'],seconds=report['elapsed_seconds'],context=len(result['context_passages'])),ensure_ascii=False),flush=True)
    finally:server.shutdown();server.server_close();worker.join()
