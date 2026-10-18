"""Extracción determinista GDN/Molina 2: sin LLM, OCR o actualización de fichas."""
import argparse
from collections import Counter
from datetime import datetime
import hashlib
import html
import json
from pathlib import Path
import re
import ssl
import time
from urllib.parse import urlencode
from urllib.request import urlopen
from zoneinfo import ZoneInfo
from .community import ROOT
from .text import fold

FIELDS=('pk','paleografia','grafiaNormalizada','traduccion','fuente')
STRING=r"'((?:\\.|[^'\\])*)'"
ROW=re.compile(r'\{\s*'+r'\s*,\s*'.join(k+r'\s*:\s*'+STRING for k in FIELDS)+r'\s*,?\s*\}',re.S)


def js_string(value):
    def unescape(m):
        token=m.group(1)
        if token[0] in 'ux':return chr(int(token[1:],16))
        table={"'":"'",'"':'"','\\':'\\','n':'\n','r':'\r','t':'\t','/':'/'}
        if token not in table:raise ValueError('Escape JavaScript desconocido; no modificar el texto.')
        return table[token]
    return html.unescape(re.sub(r'\\(u[0-9a-fA-F]{4}|x[0-9a-fA-F]{2}|.)',unescape,value))


def parse_page(raw):
    document=raw.decode('utf-8') if isinstance(raw,bytes) else raw
    match=re.search(r'var\s+mydata\s*=\s*\[(.*?)\]\s*;',document,re.S)
    if not match:raise ValueError('Cambió el formato GDN: no se encontró mydata. No se importa.')
    body=match.group(1)
    if ROW.sub('',body).strip(' ,\r\n\t'):raise ValueError('Datos GDN no reconocidos; detener extracción sin evaluarlos.')
    return [dict(zip(FIELDS,map(js_string,m.groups()))) for m in ROW.finditer(body)]


def bundle_from_pages(pages,excluded=(),limit=600):
    records=[];seen=set();pks=set();rejected=Counter();excluded=set(excluded)
    for raw,url in pages:
        for e in parse_page(raw):
            if e['pk'] in pks:continue
            pks.add(e['pk'])
            written,gloss,head=e['paleografia'],e['traduccion'],e['grafiaNormalizada']
            if not re.fullmatch(r'\d+',e['pk']) or e['fuente']!='1571 Molina 2':rejected['other_source']+=1;continue
            if not head.isalpha() or '+' in head or not written or not gloss:rejected['compound_or_generated_entry']+=1;continue
            if not written.isalpha():rejected['entry_with_prefix_or_punctuation']+=1;continue
            if '\ufffd' in written+gloss or len(written)>300 or len(gloss)>300:rejected['format_or_length']+=1;continue
            if re.match(r'^(idem|id[eé]m|lo mesmo)',gloss,re.I):rejected['cross_reference']+=1;continue
            key=(fold(head),fold(gloss))
            if fold(head) in excluded or key in seen:rejected['already_catalogued']+=1;continue
            if len(records)//2>=limit:rejected['batch_limit']+=1;continue
            seen.add(key);pk=e['pk'];sid='sense-gdn-m2-'+pk;entry='https://gdn.iib.unam.mx/contexto/'+pk
            rights=dict(public=True,training=False,note='Referencia y transcripción breve de entrada histórica de Molina (1571), vía GDN, UNAM. Conservar atribución; derechos de la edición digital no auditados para entrenamiento.')
            common=dict(verification='catalog_checked',rights=rights,import_status='automatic_transcription')
            records.append(dict(**common,id=sid,kind='sense',label=gloss,definition=gloss,pos='other',aliases=[],notes='Traducción histórica de la fuente, sin modernizar ni separar acepciones automáticamente.'))
            records.append(dict(**common,id='lex-gdn-m2-'+pk,kind='form',label=written,written=written,sense_id=sid,
                catalog_normalized=head,period='historical',variant='nci',variant_label='Náhuatl clásico',
                orthography='Paleografía de la entrada GDN/Molina 2, conservada. La grafía normalizada del catálogo se guarda por separado.',
                variation_kind='historical',url=entry,
                evidence=[dict(source_id='src-molina',via_source_id='src-gdn',locator=f'Molina 2 (1571); entrada GDN {pk}. Folio primario pendiente de cotejo.',status='catalog_checked')],
                source_entry=dict(id=pk,collection='Molina_2',query_url=url,sha256=hashlib.sha256(raw).hexdigest()),
                notes='Extraído por parser determinista del catálogo. Sin cotejo primario, revisión lingüística ni asociación glífica automática.'))
    return dict(schema_version=1,records=records),dict(entries=len(records)//2,source_records=len(pks),rejected=dict(rejected),llm_calls=0)


def harvest(cache,letters='acehimnopqtxyz',per_letter=100):
    cache=Path(cache);cache.mkdir(parents=True,exist_ok=True)
    context=ssl.create_default_context()
    try:
        import certifi
        context=ssl.create_default_context(cafile=certifi.where())
    except ImportError:pass
    pages=[]
    for letter in letters:
        if not letter.isalpha() or len(letter)!=1:raise ValueError('Prefijos inválidos.')
        url='https://gdn.iib.unam.mx/termino/search?'+urlencode(dict(action='search',queryBuscarEn='nahuatlGrafiaNormalizada',queryCreiterio=letter,**{'queryEnDiccionarios[]':'Molina_2'},queryPartePalabra='inicio',queryLimiteRegistros=per_letter))
        file=cache/f'molina2-{letter}-{per_letter}.html'
        if file.exists():raw=file.read_bytes()
        else:
            with urlopen(url,context=context,timeout=30) as response:
                if response.geturl().split('/')[2]!='gdn.iib.unam.mx':raise ValueError('Redirección fuera de la fuente.')
                raw=response.read(5_000_001)
            if len(raw)>5_000_000:raise ValueError('Respuesta demasiado grande.')
            parse_page(raw);file.write_bytes(raw);time.sleep(1)
        pages.append((raw,url))
    return pages


def main():
    p=argparse.ArgumentParser();p.add_argument('--cache',default='data/dictionary-cache');p.add_argument('--letters',default='acehimnopqtxyz');p.add_argument('--per-letter',type=int,choices=(50,100,500,1000,1500),default=100);p.add_argument('--limit',type=int,default=600);p.add_argument('--output',default='corpus/gdn-lexicon-v6.json');p.add_argument('--report',default='reports/dictionary-import-v6.json');a=p.parse_args()
    if not 1<=a.limit<=4000:raise ValueError('Límite 1–4000 entradas por lote.')
    excluded=set()
    for name in ('seed.json','glyph-lexicon-v5.json'):
        excluded.update(fold(r['written']) for r in json.loads((ROOT/'corpus'/name).read_text())['records'] if r['kind']=='form')
    pages=harvest(a.cache,a.letters,a.per_letter);bundle,report=bundle_from_pages(pages,excluded,a.limit)
    if not bundle['records']:raise ValueError('No hay entradas seguras para incorporar.')
    report.update(date=str(datetime.now(ZoneInfo('America/Mexico_City')).date()),source='GDN / Molina_2',pages=[dict(url=url,sha256=hashlib.sha256(raw).hexdigest()) for raw,url in pages])
    # Valida todo el lote en una base temporal antes de publicar el JSON.
    import tempfile
    from .corpus import CorpusStore
    with tempfile.TemporaryDirectory() as d:
        store=CorpusStore(Path(d)/'validation.sqlite3');merged={**store.records(),**{r['id']:r for r in bundle['records']}}
        for r in bundle['records']:store.validate(r,merged)
    Path(a.output).write_text(json.dumps(bundle,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    Path(a.report).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
