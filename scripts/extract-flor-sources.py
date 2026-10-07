"""Reproduce the flor GDN evidence from cache; use --fetch to retrieve missing pages."""
import argparse,sys
from urllib.request import urlopen
from urllib.parse import urlencode
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json,ssl,hashlib,certifi,re

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
cache=Path(__file__).resolve().parents[1]/'data/editorial-cache/flor-v1'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--fetch',action='store_true',help='Fetch missing cache files from GDN; default is offline.')
args=parser.parse_args()
from nahuatl_local.dictionary_import import parse_page
cache.mkdir(parents=True,exist_ok=True)
def get(term):
 url='https://gdn.iib.unam.mx/termino/search?'+urlencode(dict(action='search',queryBuscarEn='nahuatlGrafiaNormalizada',queryCreiterio=term,**{'queryEnDiccionarios[]':'Molina_2'},queryPartePalabra='inicio',queryLimiteRegistros=50))
 file=cache/(term+'-molina2.html')
 if not file.exists():
  if not args.fetch:raise FileNotFoundError('Missing cache: '+str(file)+'; use --fetch to retrieve it.')
  with urlopen(url,context=ssl.create_default_context(cafile=certifi.where()),timeout=25) as r:raw=r.read(5000000)
  file.write_bytes(raw)
 raw=file.read_bytes()
 try:rows=parse_page(raw)
 except ValueError:
  if b'mydata' in raw or not re.search(rb'<article class="terminos">\s*No se han encontrado registros\s*</article>',raw):raise
  rows=[]
 return dict(query=term,url=url,sha256=hashlib.sha256(raw).hexdigest(),entries=rows)
with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(get,['cuicatl','cacahuaxochitl','cacauaxochitl','itta']))
(cache.parents[2]/'editorial/flor-source-extract.json').write_text(json.dumps(dict(schema_version=1,queries=results,llm_calls=0),ensure_ascii=False,indent=2)+'\n')
for r in results:print(json.dumps(dict(query=r['query'],entries=r['entries'][:5],total=len(r['entries'])),ensure_ascii=False))
