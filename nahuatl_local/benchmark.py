"""Comparación reproducible de fragmentos reservados, con auditoría de solapamientos y varianza."""
import argparse,csv,hashlib,io,json,random,socket
from contextlib import contextmanager
from difflib import SequenceMatcher
from pathlib import Path
from .data import load_rows,canonical,work_group,passage_group
from .retrieval import Index,STOP
from .nahuatl_orthography import ORTHOGRAPHY_VERSION,STORAGE_RULE_IDS,COMPARISON_RULE_IDS
ROOT=Path(__file__).resolve().parents[1]
def overlap(row,train):
    for other in train:
        for field in ['es','nah']:
            a=canonical(row[field]).split();b=canonical(other[field]).split()
            if SequenceMatcher(None,a,b,autojunk=False).ratio()>=.65:return other['id']
    return None

def eligible(row):
    return 2<=len(canonical(row['es']).split())<=15 and len(canonical(row['nah']).split())<=25

def select_sample(rows,limit=None):
    """Selección determinista y agrupada por obra del conjunto reservado. Sin
    aleatoriedad: el orden es estable por grupo y por id de origen, para que el
    conjunto reservado sea reproducible byte a byte. Con límite, intercala un
    ejemplo por grupo y ronda para no sesgar hacia una sola obra."""
    rows=[r for r in rows if eligible(r)]
    groups={}
    for r in rows:groups.setdefault(work_group(r['document']),[]).append(r)
    for g in groups:groups[g].sort(key=lambda r:r['id'])
    ordered=sorted(groups)
    if limit is None:return [r for g in ordered for r in groups[g]]
    out=[];i={g:0 for g in ordered}
    while len(out)<limit and any(i[g]<len(groups[g]) for g in ordered):
        for g in ordered:
            if i[g]<len(groups[g]):out.append(groups[g][i[g]]);i[g]+=1
            if len(out)>=limit:break
    return out

def bootstrap_ci(items,statistic,clusters=None,n_resamples=1000,seed=2026,alpha=0.05):
    """IC por remuestreo de ``statistic`` sobre ``items``. Si ``clusters`` se da,
    remuestrea conglomerados enteros (mismo valor de grupo) para no subestimar la
    correlación intra-grupo; sin conglomerados es bootstrap i.i.d. Devuelve la
    estimación puntual, [lower, upper] y n."""
    if n_resamples<1:raise ValueError('n_resamples debe ser positivo')
    n=len(items)
    if clusters is not None and len(clusters)!=n:raise ValueError('Cada ejemplo necesita un conglomerado')
    clustered=clusters is not None
    empty=dict(n=n,estimate=None,lower=None,upper=None,clusters=None,n_resamples=n_resamples,seed=seed,alpha=alpha,method='bootstrap',degenerate=True,degeneracy_reason='empty_sample')
    if n==0:return empty
    rng=random.Random(seed)
    if clusters is None:clusters=list(range(n))
    groups={}
    for i,c in enumerate(clusters):groups.setdefault(c,[]).append(i)
    keys=list(groups)
    samples=[]
    for _ in range(n_resamples):
        chosen=[keys[rng.randrange(len(keys))] for _ in range(len(keys))]
        idx=[i for c in chosen for i in groups[c]]
        v=statistic([items[i] for i in idx]) if idx else None
        if v is not None:samples.append(v)
    if not samples:return empty
    samples.sort();k=len(samples)
    lower=samples[int(alpha/2*k)];upper=samples[max(0,int((1-alpha/2)*k)-1)]
    reason=('single_cluster' if clustered else 'single_example') if len(keys)==1 else 'zero_width_interval' if lower==upper else None
    return dict(n=n,estimate=statistic(items),lower=lower,upper=upper,clusters=len(keys),n_resamples=n_resamples,seed=seed,alpha=alpha,method='bootstrap',degenerate=reason is not None,degeneracy_reason=reason)

@contextmanager
def hermetic_network():
    """Bloquea las conexiones de red durante la evaluación y restaura al salir."""
    original_connect=socket.socket.connect;original_create=socket.create_connection
    def deny(*args,**kwargs):raise RuntimeError('Network connections disabled during evaluation')
    socket.socket.connect=deny;socket.create_connection=deny
    try:yield
    finally:socket.socket.connect=original_connect;socket.create_connection=original_create

REVIEW_HEADER=['example_id','source_text','candidate','source_id','semantic_fidelity_0_to_4','classical_fit_0_to_4','evidence_support_yes_no_unknown','modernization_risk_yes_no_unknown','citation_relation','glyph_relation','reviewer','notes']
def review_sheet(rows,predictions=None):
    """Ficha CSV de revisión humana del conjunto agrupado; las columnas de juicio
    quedan vacías para el especialista. Formato: templates/review_labels.csv."""
    pred={p['id']:p for p in (predictions or [])}
    buf=io.StringIO();w=csv.writer(buf);w.writerow(REVIEW_HEADER)
    for r in rows:
        w.writerow([r['id'],r['es'],pred.get(r['id'],{}).get('text',''),passage_group(r),'','','','','','','',''])
    return buf.getvalue()

def _cached_chrf(metric,predictions):
    """Reutiliza estadísticas de segmentos de SacreBLEU en los 1000 remuestreos.
    La agregación conserva chrF++ de corpus; no promedia scores por frase."""
    stats=metric._extract_corpus_statistics([r['text'] for r in predictions],[[r['reference'] for r in predictions]])
    by_id={r['id']:s for r,s in zip(predictions,stats)}
    def score(records):return metric._aggregate_and_compute([by_id[r['id']] for r in records]).score if records else None
    return score

def retrieval_benchmark(data,split='validation',limit=None,n_resamples=1000):
    """Baseline textual del primer pasaje BM25 de train, sin cargar un modelo.

    La consulta es el español reservado y el candidato es la transcripción
    náhuatl del pasaje de entrenamiento. No genera ni valida traducciones.
    """
    if split not in ('validation','test'):raise ValueError('La evaluación requiere validation o test')
    if limit is not None and limit<1:raise ValueError('--limit debe ser positivo')
    if n_resamples<1:raise ValueError('n_resamples debe ser positivo')
    from sacrebleu.metrics import CHRF
    data=Path(data);path=data/f'{split}.jsonl';train=data/'train.jsonl'
    heldout=load_rows(path);rows=select_sample(heldout,limit)
    if not rows:raise ValueError('No hay ejemplos elegibles')
    predictions=[]
    with hermetic_network():
        index=Index(train)
        for row in rows:
            refs=index.search(row['es'],2)
            candidate=refs[0]['nah'] if refs else ''
            predictions.append(dict(id=row['id'],source=row['es'],reference=row['nah'],document=row['document'],
                group=work_group(row['document']),passage=passage_group(row),overlap=overlap(row,index.rows),
                text=candidate,nearest=candidate,retrieval_ids=[r['id'] for r in refs],retrieved_passages=refs))
            print(row['id'],candidate[:90],flush=True)
    metric=CHRF(word_order=2);chrF=_cached_chrf(metric,predictions)
    clean=[r for r in predictions if r['overlap'] is None]
    def intervals(records):
        return dict(iid=bootstrap_ci(records,chrF,n_resamples=n_resamples),
                    clusters=bootstrap_ci(records,chrF,clusters=[r['group'] for r in records],n_resamples=n_resamples))
    normalization=dict(version=ORTHOGRAPHY_VERSION,storage_rules=list(STORAGE_RULE_IDS),comparison_rules=list(COMPARISON_RULE_IDS))
    manifest=data/'manifest.json';prepared=json.loads(manifest.read_text(encoding='utf-8')) if manifest.exists() else {}
    return dict(evaluation_mode='retrieval_only',generated_examples=0,split=split,n=len(rows),examples=len(rows),
        eligible_examples=sum(eligible(r) for r in heldout),selection_limit=limit,groups=sorted({r['group'] for r in predictions}),
        grouping_rule='Obra (work_group); los poemas/pasajes se representan por obra+locator porque Axolotl no distingue todos los poemas.',
        ids=[r['id'] for r in predictions],dataset_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        train_sha256=hashlib.sha256(train.read_bytes()).hexdigest(),train_rows=len(index.rows),
        train_groups=sorted({work_group(r['document']) for r in index.rows}),
        normalization=normalization,prepared_normalization=prepared.get('normalization'),
        prepared_normalization_matches_current=prepared.get('normalization')==normalization,
        prepared_manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest() if manifest.exists() else None,
        retrieval=dict(method='BM25',index_split='train',fields=['es','nah'],k=2,candidate='first_ranked_training_passage_nah',
            k1=1.5,b=.75,spanish_tokenization='lowercase_unicode_word_tokens',spanish_stopwords=sorted(STOP),
            nahuatl_tokenization='comparison_then_unicode_word_tokens',nahuatl_comparison_rules=list(COMPARISON_RULE_IDS)),
        overlap_audit=dict(threshold=.65,fields=['es','nah'],normalization='comparison',method='SequenceMatcher token ratio',
            flagged_examples=len(predictions)-len(clean)),
        chrF_plus_plus=chrF(predictions),chrF_plus_plus_ci=intervals(predictions),
        unflagged_examples=len(clean),filtered_examples=len(predictions)-len(clean),
        unflagged_chrF_plus_plus=chrF(clean),unflagged_chrF_plus_plus_ci=intervals(clean),
        retrieved_passage_chrF_plus_plus=chrF(clean),retrieval_coverage=sum(bool(r['retrieval_ids']) for r in predictions)/len(predictions),
        network_connections_blocked=True,metric_signature=str(metric.get_signature()),
        selection='Determinista e intercalada por obra con --limit; 2–15 palabras españolas normalizadas, <=25 náhuatl.',
        limitations='Baseline de recuperación, sin generación ni revisión lingüística. chrF++ mide similitud textual, no fidelidad semántica. '
            'Unflagged no implica independencia: la auditoría >=0.65 en cualquiera de las dos lenguas es una heurística. '
            'Los IC de obra pueden ser degenerados cuando queda una sola obra; no corrigen el sesgo de cobertura. '
            'La normalización, recuperación y muestra actuales difieren de los informes antiguos de 20 ejemplos de test; sus scores no son comparables.',
        predictions=predictions)

def write_report(report,rows,output):
    out=Path(output);out.parent.mkdir(parents=True,exist_ok=True)
    stem=out.stem.replace('-full','');review=out.with_name(stem+'.review.csv')
    report['review_sheet']=str(review)
    summary=dict(report);summary.pop('predictions')
    summary_path=out.with_name(stem+out.suffix) if stem!=out.stem else out.with_name(stem+'-summary'+out.suffix)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    summary_path.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    review.write_text(review_sheet(rows,report['predictions']),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)

def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('--adapter');p.add_argument('--rag',action='store_true');p.add_argument('--retrieval-only',action='store_true');p.add_argument('--split',choices=['validation','test'],default=None);p.add_argument('--limit',type=int,default=None);p.add_argument('--output',required=True);p.add_argument('--device',default='cpu');p.add_argument('--data',default=str(ROOT/'data/prepared'));p.add_argument('--base',default=str(ROOT/'models/base'));p.add_argument('--bootstrap-resamples',type=int,default=1000);a=p.parse_args(argv)
    a.split=a.split or ('validation' if a.retrieval_only else 'test')
    if a.limit is not None and a.limit<1:raise ValueError('--limit debe ser positivo')
    if a.bootstrap_resamples<1:raise ValueError('--bootstrap-resamples debe ser positivo')
    if a.retrieval_only:
        if a.adapter or a.rag:raise ValueError('--retrieval-only no usa --adapter ni --rag')
        report=retrieval_benchmark(a.data,a.split,a.limit,a.bootstrap_resamples)
        rows=select_sample(load_rows(Path(a.data)/f'{a.split}.jsonl'),a.limit)
        write_report(report,rows,a.output);return report
    import torch
    from sacrebleu.metrics import CHRF
    from .runtime import load_model,translate
    torch.set_num_threads(2)
    path=Path(a.data)/f'{a.split}.jsonl';rows=select_sample(load_rows(path),a.limit)
    if not rows:raise ValueError('No hay ejemplos elegibles')
    metric=CHRF(word_order=2)
    def chrF(records,key='text'):return metric.corpus_score([r[key] for r in records],[[r['reference'] for r in records]]).score if records else None
    with hermetic_network():
        model,tok,device=load_model(a.base,a.adapter,a.device);index=Index(Path(a.data)/'train.jsonl');predictions=[]
        for row in rows:
            refs=index.search(row['es'],2);value=translate(model,tok,device,row['es'],refs if a.rag else None,max_new_tokens=96)
            predictions.append(dict(id=row['id'],source=row['es'],reference=row['nah'],document=row['document'],group=work_group(row['document']),passage=passage_group(row),overlap=overlap(row,index.rows),nearest=refs[0]['nah'] if refs else '',**value));print(row['id'],value['text'][:90],flush=True)
    clean=[r for r in predictions if r['overlap'] is None]
    def repetition(text):
        tokens=canonical(text).split();grams=list(zip(tokens,tokens[1:],tokens[2:]));return 1-len(set(grams))/len(grams) if grams else 0
    groups=sorted({r['group'] for r in predictions})
    chrf_ci=dict(iid=bootstrap_ci(predictions,chrF,n_resamples=a.bootstrap_resamples),clusters=bootstrap_ci(predictions,chrF,clusters=[r['group'] for r in predictions],n_resamples=a.bootstrap_resamples))
    unflagged_ci=dict(iid=bootstrap_ci(clean,chrF,n_resamples=a.bootstrap_resamples),clusters=bootstrap_ci(clean,chrF,clusters=[r['group'] for r in clean],n_resamples=a.bootstrap_resamples))
    report=dict(adapter=a.adapter,rag=a.rag,split=a.split,n=len(rows),examples=len(rows),groups=groups,grouping_rule='Conjunto reservado agrupado por obra (work_group); el corpus Axolotl no distingue poemas dentro de las antologías, así que la hoja de revisión usa obra+locator como proxy de pasaje. IC por bootstrap i.i.d. y por conglomerados de obra, semilla fija 2026.',ids=[r['id'] for r in predictions],dataset_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),chrF_plus_plus=chrF(predictions),chrF_plus_plus_ci=chrf_ci,unflagged_examples=len(clean),unflagged_chrF_plus_plus=chrF(clean),unflagged_chrF_plus_plus_ci=unflagged_ci,retrieved_passage_chrF_plus_plus=chrF(clean,'nearest'),truncated=sum(r['truncated'] for r in predictions),repeated_trigram_fraction=sum(repetition(r['text']) for r in predictions)/len(predictions),mean_seconds=sum(r['seconds'] for r in predictions)/len(predictions),network_connections_blocked=True,metric_signature=str(metric.get_signature()),selection='Determinista y agrupada por obra; 2–15 palabras españolas normalizadas, <=25 náhuatl; solapamiento >=0.65 en cualquier idioma.',limitations='chrF++ es similitud textual, no exactitud. Unflagged no implica independencia; el IC refleja la varianza de la muestra, no el sesgo de cobertura ni la falta de revisión filológica.',predictions=predictions)
    write_report(report,rows,a.output)
if __name__=='__main__':main()
