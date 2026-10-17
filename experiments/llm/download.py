"""Único módulo que descarga recursos. No se importa al entrenar ni inferir."""
import argparse, certifi, hashlib, json, ssl, urllib.request
from pathlib import Path
from nahuatl_local.passages import AXOLOTL
ROOT=Path(__file__).resolve().parents[2]
SSL_CONTEXT=ssl.create_default_context(cafile=certifi.where())
def fetch(url,path):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        print(f"Ya existe: {path.name}",flush=True)
    else:
        temp=path.with_suffix(path.suffix+'.part')
        request=urllib.request.Request(url,headers={'User-Agent':'NahuatlLocal/0.1 (research)'})
        with urllib.request.urlopen(request,timeout=90,context=SSL_CONTEXT) as response,temp.open('wb') as out:
            while chunk:=response.read(1024*1024):out.write(chunk)
        temp.replace(path)
        print(f"Descargado: {path.name} ({path.stat().st_size:,} bytes)",flush=True)
    digest=hashlib.file_digest(path.open('rb'),'sha256').hexdigest()
    return {'path':str(path.relative_to(ROOT)),'sha256':digest,'url':url,'bytes':path.stat().st_size}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--only',choices=['corpus','model','all'],default='all');a=p.parse_args()
    config=json.loads((ROOT/'configs/sources.json').read_text());records=[]
    if a.only in ['corpus','all']:
        s=config['corpus'];base=f"https://raw.githubusercontent.com/{s['repository']}/{s['revision']}/"
        records.append(fetch(base+s['path'],ROOT/'data/raw'/Path(AXOLOTL).name))
        records.append(fetch(base+'LICENSE',ROOT/'data/raw/UPSTREAM-LICENSE'))
    if a.only in ['model','all']:
        s=config['model'];base=f"https://huggingface.co/{s['repository']}/resolve/{s['revision']}/"
        for name in s['files']:records.append(fetch(base+name,ROOT/'models/base'/name))
    dest=ROOT/f"experiments/llm/reports/download-{a.only}.json";dest.parent.mkdir(exist_ok=True)
    dest.write_text(json.dumps(records,indent=2,ensure_ascii=False)+'\n')
if __name__=='__main__':main()
