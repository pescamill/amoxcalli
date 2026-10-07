"""Traducción experimental y referencias recuperadas, sin red."""
import argparse,json,html,re
from pathlib import Path
from .runtime import load_model,translate
from .retrieval import full_index
from .review import local_review
ROOT=Path(__file__).resolve().parents[1]
GLYPHS={
 'xochitl':('Flor; elemento de Xochiacan','https://aztecglyphs.wired-humanities.org/content/xochitl-mdz10r'),
 'atl':('Agua; elemento de Ayotochco','https://aztecglyphs.wired-humanities.org/content/atl-mdz51r-0'),
 'calli':('Casa; elemento de Apancalecan','https://aztecglyphs.wired-humanities.org/content/calli-mdz13r')}
def render(result,path):
    body=[]
    for part in re.split(r'(\w+)',result['text']):
        safe=html.escape(part)
        if part.lower() in GLYPHS:
            label,url=GLYPHS[part.lower()];safe=f'<a href="{url}" title="{html.escape(label)}">{safe}</a>'
        body.append(safe)
    refs=''.join(f'<li><b>{html.escape(r["document"])}</b> — {html.escape(r["locator"])}<p>{html.escape(r["es"])}</p><p>{html.escape(r["nah"])}</p><a href="{html.escape(r["source_url"],quote=True)}">Catálogo del corpus</a></li>' for r in result['related_passages'])
    Path(path).write_text('<!doctype html><meta charset="utf-8"><html lang="es"><title>Náhuatl local</title><style>body{max-width:760px;margin:3rem auto;padding:1rem;font:18px/1.6 system-ui}a{color:#17604b}li{margin-bottom:2rem}</style><h1>Borrador experimental</h1><p>No revisado por un especialista. Los pasajes relacionados no verifican automáticamente la traducción.</p><p>'+''.join(body)+'</p><h2>Pasajes relacionados</h2><ol>'+refs+'</ol><p>Los enlaces en palabras coincidentes remiten a elementos del Códice Mendoza descritos por un catálogo secundario. No prueban equivalencia en esta oración. No se redistribuyen imágenes. Abrir fuentes externas requiere internet.</p></html>',encoding='utf-8')
def main():
    p=argparse.ArgumentParser();p.add_argument('text');p.add_argument('--base',default=str(ROOT/'models/base'));p.add_argument('--adapter');p.add_argument('--device',default='auto');p.add_argument('--rag',action='store_true');p.add_argument('--html');p.add_argument('--max-new-tokens',type=int,default=128);p.add_argument('--output');a=p.parse_args()
    import torch
    torch.set_num_threads(4)
    refs=full_index().search(a.text,3,variant='nci')
    model,tok,device=load_model(a.base,a.adapter,a.device)
    result=translate(model,tok,device,a.text,refs if a.rag else None,a.max_new_tokens);result.update(input=a.text,related_passages=refs,citation_status='related_not_translation_verified')
    result['review']=local_review(result)
    payload=json.dumps(result,ensure_ascii=False,indent=2);print(payload)
    if a.output:Path(a.output).write_text(payload,encoding='utf-8')
    if a.html:render(result,a.html)
if __name__=='__main__':main()
