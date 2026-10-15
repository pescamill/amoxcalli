"""Preparación sin dependencias: variantes explícitas y separación por obra."""
import argparse, collections, hashlib, json, random, statistics
from pathlib import Path
from .nahuatl_orthography import storage, comparison, ORTHOGRAPHY_VERSION, STORAGE_RULE_IDS, COMPARISON_RULE_IDS
from .passages import AXOLOTL, passage_id, records as axolotl_records
ROOT=Path(__file__).resolve().parents[1]
LENGTH_RATIO_TAU=2.5
LENGTH_RATIO_UNIT='words'
OVERFLOW_TOKEN_LIMIT=192

def canonical(text):
    # Delega en la normalización de comparación; conserva el nombre para los llamadores existentes.
    return comparison(text)
def work_group(title):
    if 'Libro las ocho relaciones' in title:return 'Chimalpahin: las ocho relaciones'
    return title

def passage_group(row):
    # Clave de poema/pasaje para agrupar evaluación y revisión. El corpus
    # Axolotl no trae identificador de poema; se usa obra (work_group) más la
    # fila de origen (locator) como proxy de pasaje. Una agrupación por poema
    # real exige metadatos de edición que el corpus no aporta.
    return '{} :: {}'.format(work_group(row.get('document','')), row.get('locator',''))

def default_corpus_path():
    """Prefiere el corpus versionado; cae al descargado por download.py."""
    committed=ROOT/AXOLOTL
    downloaded=ROOT/'data/raw'/Path(AXOLOTL).name
    if committed.exists():return committed
    if downloaded.exists():return downloaded
    raise FileNotFoundError(
        f'No se encontró el corpus en {committed} ni en {downloaded}. '
        'Ejecuta: python -m nahuatl_local.download --only corpus')

def _token_length_stats(tokenizer_dir,records):
    from transformers import AutoTokenizer
    tokenizer=AutoTokenizer.from_pretrained(str(tokenizer_dir),local_files_only=True,trust_remote_code=False)
    def field_stats(field):
        lengths=sorted(len(tokenizer(row[field],add_special_tokens=False)['input_ids']) for row in records)
        n=len(lengths);total_tokens=sum(lengths);total_chars=sum(len(row[field]) for row in records)
        return {'rows':n,
                'mean':round(total_tokens/n,3) if n else 0.0,
                'median':statistics.median(lengths) if n else 0,
                'p95':lengths[int(n*0.95)] if n else 0,
                'tokens_per_char':round(total_tokens/total_chars,4) if total_chars else 0.0,
                'overflow_at_'+str(OVERFLOW_TOKEN_LIMIT):sum(1 for length in lengths if length>OVERFLOW_TOKEN_LIMIT)}
    return {'es':field_stats('es'),'nah':field_stats('nah'),
            'tokenizer':str(Path(tokenizer_dir)),'overflow_limit':OVERFLOW_TOKEN_LIMIT}

def prepare(raw,output,seed=42,tokenizer_dir=None):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    records=[];rejected=collections.Counter();seen_es=set();seen_nah=set()
    # Formato de entrenamiento congelado (manifiestos y referencias lo fijan): sale de los
    # registros crudos del único lector del CSV, no del modelo de pasaje de la aplicación.
    for line,row in axolotl_records(raw):
        if len(row)<5:rejected['schema']+=1;continue
        es,nah,variant,document,iso=row[:5]
        if variant!='Classical Nahuatl' or iso!='nci':rejected['other_or_unknown_variant']+=1;continue
        es,nah=es.strip(),nah.strip()
        if not es or not nah or not document.strip():rejected['empty']+=1;continue
        if '\ufffd' in es+nah:rejected['encoding']+=1;continue
        es_words,nah_words=len(es.split()),len(nah.split())
        if not 2<=es_words<=100 or not 2<=nah_words<=100:rejected['length']+=1;continue
        if max(es_words,nah_words)/max(1,min(es_words,nah_words))>LENGTH_RATIO_TAU:rejected['length_ratio']+=1;continue
        es,nah=storage(es),storage(nah)
        if comparison(es)==comparison(nah):rejected['identical_languages']+=1;continue
        e,n=comparison(es),comparison(nah)
        if e in seen_es or n in seen_nah:rejected['duplicate_source_or_target']+=1;continue
        seen_es.add(e);seen_nah.add(n)
        records.append({'id':passage_id(line),'es':es,'nah':nah,'variant':variant,'iso':'nci','document':document,'group':work_group(document),'locator':f'axolotl.csv, fila {line} (sin página de edición disponible)','source_url':'https://www.axolotl-corpus.mx/','declared_license':'MPL-2.0 (repositorio distribuidor)','linguistic_review':'upstream_alignment_not_independently_reviewed'})
    groups=sorted({r['group'] for r in records});random.Random(seed).shuffle(groups)
    if len(groups)<3:raise ValueError('Se requieren al menos tres obras para separar entrenamiento, validación y prueba.')
    n=max(1,round(len(groups)*0.15));test=set(groups[:n]);valid=set(groups[n:2*n]);train=set(groups[2*n:])
    buckets={'train':[],'validation':[],'test':[]}
    for r in records:buckets['test' if r['group'] in test else 'validation' if r['group'] in valid else 'train'].append(r)
    for split,rows in buckets.items():
        (output/f'{split}.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')
    token_length=None;token_length_note=None
    if tokenizer_dir is not None:
        tokenizer_path=Path(tokenizer_dir)
        if (tokenizer_path/'tokenizer_config.json').exists() or (tokenizer_path/'vocab.json').exists():
            token_length=_token_length_stats(tokenizer_path,records)
        else:
            token_length_note='El directorio de tokenizador no se resolvió: '+str(tokenizer_path)
    else:
        token_length_note='Estadísticas de tokens omitidas: prepare() se ejecutó sin tokenizer_dir.'
    report={'seed':seed,'raw_sha256':hashlib.sha256(Path(raw).read_bytes()).hexdigest(),'retained':len(records),'rejected':dict(rejected),'splits':{k:{'rows':len(v),'groups':sorted({r['group'] for r in v})} for k,v in buckets.items()},
            'normalization':{'version':ORTHOGRAPHY_VERSION,'storage_rules':list(STORAGE_RULE_IDS),'comparison_rules':list(COMPARISON_RULE_IDS)},
            'length_ratio':{'tau':LENGTH_RATIO_TAU,'unit':LENGTH_RATIO_UNIT},
            'token_length':token_length,
            'limits':['Las etiquetas de variante y alineaciones proceden de Elotl; falta revisión filológica propia.','Deduplicación por comparación normalizada (ç→tz, v→u, sin marcas); no elimina todas las paráfrasis o traducciones compartidas entre antologías.','La división por obra no demuestra generalización entre géneros.','El texto persistido está normalizado en modo storage ('+ORTHOGRAPHY_VERSION+'); las métricas chrF++ previas no son comparables.']}
    if token_length_note is not None:report['token_length_note']=token_length_note
    (output/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report

def load_rows(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]
def main():
    p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,default=None);p.add_argument('--output',type=Path,default=ROOT/'data/prepared');p.add_argument('--tokenizer-dir',type=Path,default=None);a=p.parse_args()
    raw=a.raw or default_corpus_path()
    print(json.dumps(prepare(raw,a.output,tokenizer_dir=a.tokenizer_dir),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
