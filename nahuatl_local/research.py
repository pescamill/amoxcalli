"""Archivo bilingüe local de Axolotl; conserva las filas y etiquetas originales."""
import json
from collections import Counter
from threading import Lock
from .community import ROOT,Problem
from .passages import AXOLOTL,LABELS,load,source
from .retrieval import Index

class Archive:
    def __init__(self):
        self.config=source(ROOT)
        self.path=ROOT/AXOLOTL
        self.url=self.config['url']
        self.rows=load(ROOT);self.index={r['id']:r for r in self.rows};self._bm25=None;self._bm25_lock=Lock()
        variants=Counter(r['iso'] for r in self.rows);works=Counter(r['document'] for r in self.rows)
        self.summary=dict(total=len(self.rows),works=sum(bool(k) for k in works),citation=self.config['citation'],source_url=self.url,revision=self.config['revision'],
            variants=[dict(id=k,label=LABELS.get(k,k),count=n) for k,n in variants.most_common()],
            documents=[dict(id=k or '__unknown__',label=k or 'Obra no indicada',count=n) for k,n in sorted(works.items())])

    def get(self,rid):
        if rid not in self.index:raise Problem('Pasaje no encontrado.',404)
        return dict(self.index[rid])

    def _ranked(self,query,variant=''):
        # El archivo completo es para consulta, separado del índice train-only
        # del benchmark. La comparación no altera las transcripciones de rows.
        if self._bm25 is None:
            with self._bm25_lock:
                if self._bm25 is None:self._bm25=Index(rows=self.rows)
        return self._bm25.search(query,k=len(self.rows),variant=variant or None)

    def search(self,query='',variant='',document='',period='',offset=0,limit=20,terms=None):
        """Pasajes de una consulta. Con ``terms`` (``terms.TermIndex``), una palabra que la búsqueda única
        resuelve a un grupo devuelve los pasajes de todas sus grafías seguras; si no, BM25 sobre ambas lenguas."""
        if not isinstance(query,str) or len(query)>300:raise Problem('Busca con hasta 300 caracteres.')
        try:offset=int(offset);limit=int(limit)
        except (TypeError,ValueError):raise Problem('Paginación inválida.')
        if offset<0 or not 1<=limit<=100:raise Problem('Paginación fuera de rango.')
        resolved=terms.resolve(query) if terms is not None and query.strip() else None
        if resolved:
            group,word=resolved;candidates=[self.index[rid] for rid in terms.passage_ids(group['id'],first=word)]
        else:
            group=None;candidates=self._ranked(query,variant) if query.strip() else self.rows
        rows=[r for r in candidates if (not variant or r['iso']==variant) and
              (not document or r['document']==('' if document=='__unknown__' else document)) and (not period or r['period']==period)]
        return dict(total=len(rows),offset=offset,limit=limit,results=rows[offset:offset+limit],term=group,
                    method='term_group' if group else 'bm25' if query.strip() else 'all')

    def context(self,query):
        if not query.strip():return []
        return [r for r in self._ranked(query,'nci') if len(r['es'])+len(r['nah'])<=600][:2]

    def task(self,store,mode,person,after=''):
        prefix='axolotl-'+mode+'-'
        with store.db() as db:done={r[0] for r in db.execute('SELECT task FROM contributions WHERE owner=? AND kind=?',(person['id'],mode))}
        tasks=[r for r in self.rows if prefix+str(r['line']).zfill(5) not in done]
        if not tasks:return dict(task=None,remaining=0)
        try:last=int(after[len(prefix):]) if after.startswith(prefix) else 0
        except ValueError:last=0
        r=next((r for r in tasks if r['line']>last),tasks[0]);tid=prefix+str(r['line']).zfill(5)
        task=dict(id=tid,kind=mode,text=r['nah'] if mode=='recognize' else r['es'],
            source=dict(label=f"{r['document']} · {r['variant_label']} · {r['locator']}",url=self.url,
                        rights=self.config['rights_note'],split='collection',archive_id=r['id'],original_variant=r['iso']))
        with store.db() as db:db.execute('INSERT OR IGNORE INTO tasks VALUES(?,?,?)',(tid,mode,json.dumps(task,ensure_ascii=False)))
        return dict(task=task,remaining=len(tasks))
