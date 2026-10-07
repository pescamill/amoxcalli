"""Importa pares revisados y conserva validación/prueba intactas."""
import argparse,csv,hashlib,json,shutil
from pathlib import Path
from .data import canonical,load_rows,work_group
REQUIRED=['es','nah','document','locator','source_url','license','reviewer','iso']
def import_reviewed(source,base,output):
    source,base,output=map(Path,(source,base,output))
    if output.exists():raise ValueError('Usa un directorio nuevo')
    train=load_rows(base/'train.jsonl');held=[r for s in ['validation','test'] for r in load_rows(base/f'{s}.jsonl')];works={r['group'] for r in held};seen_es={canonical(r['es']) for r in train+held};seen_nah={canonical(r['nah']) for r in train+held};accepted=[];rejected=[]
    with source.open(encoding='utf-8-sig',newline='') as file:
        reader=csv.DictReader(file)
        if not set(REQUIRED)<=set(reader.fieldnames or []):raise ValueError('Faltan columnas obligatorias')
        for line,r in enumerate(reader,2):
            reason=None
            if any(not r.get(k,'').strip() for k in REQUIRED):reason='campo vacío'
            elif r['iso']!='nci':reason='no clásico'
            elif r['license'] not in ['CC0-1.0','CC-BY-4.0','CC-BY-SA-4.0','Public-Domain','MPL-2.0']:reason='revisar licencia'
            elif work_group(r['document']) in works:reason='obra reservada'
            elif canonical(r['es']) in seen_es or canonical(r['nah']) in seen_nah:reason='duplicado o frase reservada'
            elif not r['source_url'].startswith(('https://','http://')):reason='URL inválida'
            if reason:rejected.append(dict(line=line,reason=reason));continue
            seen_es.add(canonical(r['es']));seen_nah.add(canonical(r['nah']));identifier=hashlib.sha256((r['es']+'\0'+r['nah']).encode()).hexdigest()[:16]
            accepted.append(dict(id='reviewed-'+identifier,es=r['es'],nah=r['nah'],document=r['document'],group=work_group(r['document']),variant='Classical Nahuatl',iso='nci',source_url=r['source_url'],locator=r['locator'],declared_license=r['license'],reviewer=r['reviewer'],linguistic_review='user_declared_not_independently_verified'))
    if not accepted:raise ValueError('No se aceptaron pares: '+json.dumps(rejected,ensure_ascii=False))
    output.mkdir(parents=True)
    for split in ['validation','test']:shutil.copyfile(base/f'{split}.jsonl',output/f'{split}.jsonl')
    (output/'train.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in train+accepted),encoding='utf-8')
    manifest=json.loads((base/'manifest.json').read_text());manifest['curation']=dict(accepted=len(accepted),rejected=rejected,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest());manifest['splits']['train']=dict(rows=len(train+accepted),groups=sorted({r['group'] for r in train+accepted}));manifest['retained']=len(train+accepted+held);(output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));return manifest['curation']
def main():
    p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('--base',default='data/prepared');p.add_argument('--output',default='data/curated');a=p.parse_args();print(json.dumps(import_reviewed(a.source,a.base,a.output),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
