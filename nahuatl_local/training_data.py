"""Consulta de pares y propuestas; no entrena ni altera particiones."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
from .community import ROOT, Problem, now, text, identifier
from .corpus import normalize, safe_url
from .data import load_rows, canonical, work_group

LICENSES = ('CC0-1.0', 'CC-BY-4.0', 'CC-BY-SA-4.0', 'Public-Domain', 'MPL-2.0')
FIELDS = ('es','nah','document','locator','source_url','license','reviewer','iso')


class TrainingData:
    def __init__(self, root=ROOT):
        self.root = Path(root)
        self.datasets = {}
        ref = self.root / 'data/training-reference/continued-unseen'
        if (ref/'manifest.json').exists():
            manifest = json.loads((ref/'manifest.json').read_text())
            for split, expected in manifest['dataset_sha256'].items():
                if hashlib.sha256((ref/f'{split}.jsonl').read_bytes()).hexdigest() != expected:
                    raise ValueError('La referencia histórica cambió; no se puede atribuir a los pesos.')
            rows = load_rows(ref/'train.jsonl')
            seen_raw = (ref/'seen.json').read_bytes()
            if manifest.get('seen_sha256') and hashlib.sha256(seen_raw).hexdigest()!=manifest['seen_sha256']:
                raise ValueError('La lista de pares recorridos cambió; verificar la referencia histórica.')
            seen = json.loads(seen_raw)
            by_id = {r['id']:r for r in rows}
            if len(set(seen['ids'])) != manifest['seen_pairs'] or not set(seen['ids']) <= by_id.keys():
                raise ValueError('IDs de entrenamiento histórico inválidos.')
            self.datasets['seen'] = dict(label='Pares recorridos por el adaptador', rows=[by_id[i] for i in seen['ids']], note='400 pasos del piloto y 250 de continuación; orden y cursor del checkpoint. Archivos históricos verificados por SHA256.')
            self.datasets['historical'] = dict(label='Preparación histórica de entrenamiento',rows=rows,note='Incluye pares que no cabían en el formato de 192 tokens y otros aún no recorridos. No todos llegaron a los pesos.')
        for split,label in [('train','Entrenamiento actual'),('validation','Validación reservada'),('test','Prueba reservada')]:
            p = self.root / f'data/prepared/{split}.jsonl'
            if p.is_file():self.datasets[split] = dict(label=label,rows=load_rows(p),note='Preparación actual; sus hashes difieren de la corrida histórica. Validación y prueba no se añaden al entrenamiento.')
        self.heldout_works = {r['group'] for k,d in self.datasets.items() if k in ('validation','test') for r in d['rows']}
        self.existing = {canonical(r[f]) for d in self.datasets.values() for r in d['rows'] for f in ('es','nah')}

    def search(self, dataset='seen', query='', document='', offset=0, limit=20):
        if dataset not in self.datasets:raise Problem('Conjunto no disponible.',404)
        if not isinstance(query,str) or len(query)>300:raise Problem('Busca con hasta 300 caracteres.')
        try:offset,limit=int(offset),int(limit)
        except (ValueError,TypeError):raise Problem('Paginación inválida.')
        if offset<0 or not 1<=limit<=100:raise Problem('Paginación fuera de rango.')
        d=self.datasets[dataset];terms=normalize(query).split()
        rows=[r for r in d['rows'] if (not document or r['document']==document) and
              all(t in normalize(r['es']+' '+r['nah']) for t in terms)]
        return dict(dataset=dataset,note=d['note'],total=len(rows),offset=offset,limit=limit,results=rows[offset:offset+limit],
            datasets=[dict(id=k,label=v['label'],count=len(v['rows'])) for k,v in self.datasets.items()],
            documents=sorted({r['document'] for r in d['rows']}))


class PairProposals:
    def __init__(self, store, data):
        self.store,self.data=store,data
        with store.db() as db:
            db.execute('CREATE TABLE IF NOT EXISTS training_pair_proposals(id TEXT PRIMARY KEY, owner TEXT NOT NULL REFERENCES people(id), payload TEXT NOT NULL, fingerprint TEXT NOT NULL, status TEXT NOT NULL, created TEXT NOT NULL, review TEXT, UNIQUE(owner,fingerprint))')

    def propose(self, person, body):
        if any(body.get(k) is not True for k in ('authorship','review_consent','training_consent')):
            raise Problem('Confirma procedencia, revisión y permiso de entrenamiento.')
        if body.get('iso','nci')!='nci':raise Problem('Este entrenamiento es de náhuatl clásico; identifica otro conjunto para variantes actuales.')
        r={k:text(body.get(k,''),k,12000 if k in ('es','nah') else 500,True) for k in FIELDS if k not in ('reviewer','iso')}
        if r['license'] not in LICENSES:raise Problem('Licencia no admitida; requiere revisión de permisos.')
        r['source_url']=safe_url(r['source_url']);r.update(iso='nci',reviewer='')
        if work_group(r['document']) in self.data.heldout_works:raise Problem('Esta obra está reservada para evaluación; no añadir al entrenamiento.',409)
        if any(canonical(r[k]) in self.data.existing for k in ('es','nah')):raise Problem('El par coincide con datos existentes o reservados.',409)
        fingerprint=hashlib.sha256((canonical(r['es'])+'\0'+canonical(r['nah'])).encode()).hexdigest()
        with self.store.db() as db:
            old=db.execute('SELECT id,status FROM training_pair_proposals WHERE fingerprint=? AND status!=?',(fingerprint,'withdrawn')).fetchone()
            if old:
                if old['id'] in {p['id'] for p in self.mine(person)}:return dict(id=old['id'],status=old['status'],duplicate=True)
                raise Problem('Este par ya tiene una propuesta pendiente.',409)
            # Permite volver a presentar una propuesta propia retirada sin duplicar la clave.
            own=db.execute('SELECT id FROM training_pair_proposals WHERE owner=? AND fingerprint=?',(person['id'],fingerprint)).fetchone()
            rid=own['id'] if own else 'pair-'+identifier()
            db.execute('INSERT INTO training_pair_proposals VALUES(?,?,?,?,?,?,NULL) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload,status=excluded.status,created=excluded.created,review=NULL',
                       (rid,person['id'],json.dumps(r,ensure_ascii=False),fingerprint,'pending',now()))
        return dict(id=rid,status='pending',duplicate=False)

    def mine(self, person):
        with self.store.db() as db:rows=db.execute('SELECT * FROM training_pair_proposals WHERE owner=? ORDER BY created DESC',(person['id'],)).fetchall()
        return [dict(id=r['id'],status=r['status'],created=r['created'],pair=json.loads(r['payload']),review=json.loads(r['review']) if r['review'] else None) for r in rows]

    def withdraw(self,person,rid):
        with self.store.db() as db:
            if not db.execute('UPDATE training_pair_proposals SET status=? WHERE id=? AND owner=?',('withdrawn',rid,person['id'])).rowcount:raise Problem('Propuesta no encontrada.',404)

    def decide(self,rid,reviewer,reason,rights_checked=False,linguistic_checked=False):
        reviewer=text(reviewer,'Revisor',200,True);reason=text(reason,'Motivo',2000,True)
        if not rights_checked or not linguistic_checked:raise Problem('Revisa derechos y fidelidad lingüística antes de aceptar.')
        with self.store.db() as db:
            row=db.execute('SELECT * FROM training_pair_proposals WHERE id=? AND status=?',(rid,'pending')).fetchone()
            if not row:raise Problem('La propuesta no está pendiente.',409)
            r=json.loads(row['payload'])
            # Vuelve a verificar reservas y duplicados si cambió la preparación.
            if work_group(r['document']) in self.data.heldout_works or any(canonical(r[k]) in self.data.existing for k in ('es','nah')):
                raise Problem('El par coincide con la preparación o una obra reservada.',409)
            r['reviewer']=reviewer
            db.execute('UPDATE training_pair_proposals SET payload=?,status=?,review=? WHERE id=?',(json.dumps(r,ensure_ascii=False),'accepted',json.dumps(dict(reviewer=reviewer,reason=reason,created=now(),rights_checked=True,linguistic_checked=True)),rid))

    def export(self,person=None):
        with self.store.db() as db:
            rows=db.execute('SELECT payload FROM training_pair_proposals WHERE status=?'+(' AND owner=?' if person else ''),('accepted',person['id']) if person else ('accepted',)).fetchall()
        out=io.StringIO(newline='');writer=csv.DictWriter(out,fieldnames=FIELDS);writer.writeheader()
        for r in rows:writer.writerow(json.loads(r['payload']))
        return out.getvalue()


def main():
    from .corpus import CorpusStore
    p=argparse.ArgumentParser();p.add_argument('--db');sub=p.add_subparsers(dest='action',required=True)
    review=sub.add_parser('review');review.add_argument('id');review.add_argument('--reviewer',required=True);review.add_argument('--reason',required=True);review.add_argument('--rights-checked',action='store_true');review.add_argument('--linguistic-checked',action='store_true')
    export=sub.add_parser('export');export.add_argument('--output',required=True)
    a=p.parse_args();pairs=PairProposals(CorpusStore(a.db) if a.db else CorpusStore(),TrainingData())
    if a.action=='review':pairs.decide(a.id,a.reviewer,a.reason,a.rights_checked,a.linguistic_checked);print('Par aceptado; todavía no se ha preparado ni entrenado.')
    else:
        out=Path(a.output)
        if out.exists():raise ValueError('Usa un archivo nuevo.')
        out.write_text(pairs.export(),encoding='utf-8');print(out)

if __name__=='__main__':main()
