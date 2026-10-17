"""Evaluación reproducible sobre obras reservadas; nunca usar como entrenamiento."""
import argparse,json
from pathlib import Path
from .runtime import load_model,translate
from nahuatl_local.data import load_rows,work_group,passage_group
from .benchmark import select_sample,bootstrap_ci,hermetic_network,review_sheet
ROOT=Path(__file__).resolve().parents[2]
def main():
    p=argparse.ArgumentParser();p.add_argument('--adapter');p.add_argument('--limit',type=int,default=None);p.add_argument('--device',default='auto');p.add_argument('--output',default='experiments/llm/reports/llm-evaluation.json');a=p.parse_args()
    if a.limit is not None and a.limit<1:raise ValueError('--limit debe ser positivo')
    import torch
    from sacrebleu.metrics import CHRF
    torch.set_num_threads(4)
    rows=select_sample(load_rows(ROOT/'data/prepared/test.jsonl'),a.limit)
    if not rows:raise ValueError('No hay ejemplos elegibles')
    metric=CHRF(word_order=2)
    def chrF(records):return metric.corpus_score([r['text'] for r in records],[[r['reference'] for r in records]]).score if records else None
    with hermetic_network():
        model,tok,dev=load_model(ROOT/'models/base',a.adapter,a.device)
        predictions=[]
        for row in rows:
            result=translate(model,tok,dev,row['es']);predictions.append(dict(id=row['id'],reference=row['nah'],group=work_group(row['document']),passage=passage_group(row),**result));print(row['id'],flush=True)
    ci=dict(iid=bootstrap_ci(predictions,chrF),clusters=bootstrap_ci(predictions,chrF,clusters=[r['group'] for r in predictions]))
    report=dict(adapter=a.adapter,n=len(rows),examples=len(rows),groups=sorted({r['group'] for r in predictions}),grouping_rule='Conjunto reservado agrupado por obra (work_group); IC por bootstrap i.i.d. y por conglomerados de obra, semilla fija.',chrF_plus_plus=chrF(predictions),chrF_plus_plus_ci=ci,metric_signature=str(metric.get_signature()),predictions=predictions,warning='Métrica textual; no demuestra corrección gramatical ni histórica. Comparar base y adaptador con el mismo límite.')
    Path(a.output).write_text(json.dumps(report,ensure_ascii=False,indent=2));Path(a.output).with_suffix('.review.csv').write_text(review_sheet(rows,predictions),encoding='utf-8')
if __name__=='__main__':main()
