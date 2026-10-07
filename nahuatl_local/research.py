"""Archivo bilingüe local de Axolotl; conserva las filas y etiquetas originales."""
import csv,json
from collections import Counter
from threading import Lock
from .community import ROOT,Problem
from .retrieval import Index

LABELS={'nci':'Náhuatl clásico','azz':'Náhuatl de la Sierra de Puebla','nhm':'Náhuatl de Morelos','nhn':'Náhuatl central','nhw':'Náhuatl de la Huasteca occidental','nhe':'Náhuatl de la Huasteca oriental','unknown':'Variedad no indicada'}
class Archive:
    def __init__(self):
        self.config=json.loads((ROOT/'configs/sources.json').read_text())['corpus']
        self.path=ROOT/'corpus/axolotl/axolotl.csv'
        self.url=f"https://github.com/{self.config['repository']}/blob/{self.config['revision']}/{self.config['path']}"
        self.rows=[];self.index={};self._bm25=None;self._bm25_lock=Lock()
        with self.path.open(encoding='utf-8',newline='') as f:
            for line,fields in enumerate(csv.reader(f),1):
                if len(fields)<5:continue
                es,nah,variant,document,iso=fields[:5]
                if not es.strip() or not nah.strip():continue
                iso=iso or 'unknown'
                row=dict(id=f'axolotl-{line:05d}',line=line,es=es,nah=nah,variant=variant,iso=iso,document=document,
                    variant_label=LABELS.get(iso,variant),period='historical' if iso=='nci' else 'unknown' if iso=='unknown' else 'modern',
                    locator=f'Axolotl, registro CSV {line}; página de la edición primaria pendiente',
                    source_url=self.url,verification='Alineación de origen; sin cotejo propio',rights_note=self.config['rights_note'])
                self.rows.append(row);self.index[row['id']]=row
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

    def search(self,query='',variant='',document='',period='',offset=0,limit=20):
        if not isinstance(query,str) or len(query)>300:raise Problem('Busca con hasta 300 caracteres.')
        try:offset=int(offset);limit=int(limit)
        except (TypeError,ValueError):raise Problem('Paginación inválida.')
        if offset<0 or not 1<=limit<=100:raise Problem('Paginación fuera de rango.')
        candidates=self._ranked(query,variant) if query.strip() else self.rows
        rows=[r for r in candidates if (not variant or r['iso']==variant) and
              (not document or r['document']==('' if document=='__unknown__' else document)) and (not period or r['period']==period)]
        return dict(total=len(rows),offset=offset,limit=limit,results=rows[offset:offset+limit])

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
