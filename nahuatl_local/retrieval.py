"""Recuperación local BM25 sobre ambas lenguas, con filtro por variante.

El índice queda separado del split SFT: ``Index(path)`` indexa únicamente el
archivo indicado — ``benchmark.py`` y ``test_pipeline.py`` pasan ``train.jsonl``
para que la auditoría de solapamiento (``benchmark.overlap``, umbral 0.65)
compare contra un conjunto reservado limpio y el pasaje recuperado nunca sea
una fila del split de evaluación. ``full_index()`` construye un índice de
búsqueda sobre el corpus completo (todas las variantes) sin tocar los splits;
no participa en la métrica del benchmark. El llamador decide qué filas entran,
de modo que la contaminación se evita por construcción, no por convención.

Cada lengua se indexa por separado con su propio ``df`` y longitud media, para
que la fórmula BM25 sea correcta por campo; la puntuación de una consulta suma
las aportaciones de ``es`` y ``nah``. ``search`` acepta ``variant`` (filtro por
``iso``, p. ej. 'nci') y ``field`` (una sola lengua, p. ej. 'nah').

El campo ``nah`` usa la normalización ortográfica de comparación para hacer
coincidir equivalencias seguras (ç/tz, v/u y marcas diacríticas). Se aplica solo
a los tokens del índice y de la consulta; los pasajes y su procedencia conservan
el texto original. El campo ``es`` conserva su tokenización española.
"""
import math,re
from collections import Counter
from .data import load_rows
from .nahuatl_orthography import comparison
STOP=set('el la los las un una de del en a y que por con para se su es al lo'.split())
def tokens(text,stop=STOP):return [w for w in re.findall(r'\w+',text.lower()) if w not in stop]
def nah_tokens(text):return tokens(comparison(text),())
class Index:
    def __init__(self,path=None,rows=None):
        self.rows=load_rows(path) if rows is None else list(rows)
        self.es=[Counter(tokens(r['es'])) for r in self.rows]
        self.nah=[Counter(nah_tokens(r['nah'])) for r in self.rows]
        self.stats={f:(Counter(w for d in docs for w in d),sum(sum(d.values()) for d in docs)/max(len(docs),1))
                    for f,docs in (('es',self.es),('nah',self.nah))}
    def search(self,query,k=3,variant=None,field=None):
        if field not in (None,'es','nah'):
            raise ValueError('field debe ser "es", "nah" o None')
        if isinstance(k,bool) or not isinstance(k,int) or k<0:
            raise ValueError('k debe ser un entero no negativo')
        fields=['es','nah'] if field is None else [field]
        query_tokens={f:set(tokens(query) if f=='es' else nah_tokens(query)) for f in fields}
        n=len(self.rows)
        scores=[]
        for row,es,nah in zip(self.rows,self.es,self.nah):
            if variant and row.get('iso')!=variant:continue
            score=0.0
            for f in fields:
                doc=es if f=='es' else nah;df,avg=self.stats[f];length=sum(doc.values())
                for word in query_tokens[f]:
                    tf=doc[word]
                    if tf:score+=math.log(1+(n-df[word]+.5)/(df[word]+.5))*tf*2.5/(tf+1.5*(.25+.75*length/max(avg,1)))
            if score:scores.append(dict(row,retrieval_score=round(score,4)))
        return sorted(scores,key=lambda r:r['retrieval_score'],reverse=True)[:k]
def full_index():
    from .research import Archive
    return Index(rows=Archive().rows)
