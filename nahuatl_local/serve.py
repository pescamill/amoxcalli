"""Consulta local, borradores y fichas de revisión sin API externa."""
import argparse,json
from pathlib import Path
from http.server import BaseHTTPRequestHandler,HTTPServer
from .retrieval import full_index
from .data import canonical
from .review import local_review,request_bundle
ROOT=Path(__file__).resolve().parents[1]
PAGE='''<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Náhuatl local</title><style>body{max-width:820px;margin:35px auto;padding:20px;background:#f6f2e9;color:#213c31;font:18px/1.55 system-ui}textarea{width:95%;padding:14px;font:inherit}button{padding:12px;background:#23533f;color:white;border:0;border-radius:8px;margin:12px 8px 12px 0;cursor:pointer}article{padding:20px;margin:16px 0;background:white;border-radius:12px}a{color:#23533f}small{display:block}label{display:block}</style><h1>Náhuatl local</h1><p>Pasajes históricos y borradores experimentales. Las coincidencias documentales y la generación se muestran por separado.</p><textarea id="text" rows="3" placeholder="Escribe en español"></textarea><label><input type="checkbox" id="draft">Generar un borrador local</label><button id="go">Consultar</button><button id="export" hidden>Exportar ficha de revisión</button><p id="status"></p><div id="results"></div><script>
const $=id=>document.getElementById(id);let bundle=null;function el(tag,text){let n=document.createElement(tag);n.textContent=text;return n}
$('go').onclick=async()=>{$('go').disabled=true;$('export').hidden=true;$('status').textContent='Procesando localmente…';$('results').replaceChildren();try{let r=await fetch('/query',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:$('text').value,draft:$('draft').checked})});let d=await r.json();if(!r.ok)throw Error(d.error);$('status').textContent=d.status;if(d.generated){let a=el('article','');a.append(el('h2','Borrador: requiere revisión'),el('p',d.generated.text),el('small',d.generated.review.reason));$('results').append(a);bundle=d.review_request;$('export').hidden=false}for(let hit of d.passages){let a=el('article','');a.append(el('h2',hit.document),el('p',hit.es),el('p',hit.nah),el('small',hit.locator));let link=el('a','Catálogo del corpus');link.href=hit.source_url;link.target='_blank';link.rel='noopener';a.append(link);$('results').append(a)}}catch(e){$('status').textContent=e.message}finally{$('go').disabled=false}};
$('export').onclick=()=>{let url=URL.createObjectURL(new Blob([JSON.stringify(bundle,null,2)],{type:'application/json'}));let a=el('a','');a.href=url;a.download='revision.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)};
</script><small>La ficha se exporta localmente para revisión humana.</small></html>'''
def main():
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8765);p.add_argument('--adapter',default=str(ROOT/'outputs/classical-v2/best'));p.add_argument('--device',default='auto');a=p.parse_args();index=full_index();loaded=None
    class Handler(BaseHTTPRequestHandler):
        def reply(self,status,value):
            self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.end_headers();self.wfile.write(json.dumps(value,ensure_ascii=False).encode())
        def do_GET(self):
            if self.path!='/':return self.reply(404,{'error':'No encontrado'})
            self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers();self.wfile.write(PAGE.encode())
        def do_POST(self):
            nonlocal loaded
            hosts={f'127.0.0.1:{a.port}',f'localhost:{a.port}'}
            if self.headers.get('Host') not in hosts or self.headers.get('Origin') not in {None,*('http://'+h for h in hosts)}:return self.reply(403,{'error':'Origen no permitido'})
            if self.path!='/query':return self.reply(404,{'error':'No encontrado'})
            try:
                size=int(self.headers.get('Content-Length',0))
                if not 0<size<10000:raise ValueError('Tamaño de solicitud inválido')
                req=json.loads(self.rfile.read(size));text=req.get('text','')
                if not isinstance(text,str) or not 0<len(text.strip())<=1000:raise ValueError('Escribe de 1 a 1000 caracteres')
                exact=[r for r in index.rows if canonical(r['es'])==canonical(text)];refs=exact or index.search(text,3,variant='nci')
                result=dict(passages=refs,status='Coincidencia en el corpus; edición y alineación requieren revisión.' if exact else 'Pasajes relacionados; no certifican la traducción.')
                if req.get('draft'):
                    if loaded is None:
                        import torch
                        from .runtime import load_model
                        torch.set_num_threads(4);loaded=load_model(ROOT/'models/base',a.adapter,a.device)
                    from .runtime import translate
                    generated=translate(*loaded,text,max_new_tokens=96);generated.update(input=text,related_passages=refs);generated['review']=local_review(generated);result.update(generated=generated,review_request=request_bundle(generated))
                self.reply(200,result)
            except (ValueError,FileNotFoundError) as e:self.reply(400,{'error':str(e)})
            except Exception:self.reply(500,{'error':'No se pudo ejecutar el modelo; revisa instalación, pesos y memoria.'})
    server=HTTPServer(('127.0.0.1',a.port),Handler);print(f'Abre http://127.0.0.1:{a.port}',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:server.server_close()
if __name__=='__main__':main()
