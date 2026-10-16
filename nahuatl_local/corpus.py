"""Corpus de investigación: entidades enlazadas, propuestas y revisión explícita.

Comparte SQLite y perfiles con Voces. No necesita un modelo ni servicios externos.
"""
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlparse
from .community import Store, Problem, ROOT, now, text, choice, identifier
from . import lexicon
from .lexicon import releases as editorial_releases  # noqa: F401 (nombre público; las pruebas lo sustituyen)

KINDS = ('source', 'sense', 'form', 'text', 'glyph', 'note')
PERIODS = ('historical', 'modern', 'unknown')


def safe_url(value):
    value = text(value, 'Enlace', 2000)
    parsed = urlparse(value)
    if value and (parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password):
        raise Problem('El enlace debe ser HTTP o HTTPS, sin credenciales.')
    return value


def digest(record):
    return hashlib.sha256(json.dumps(record, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


class CorpusStore(Store):
    def __init__(self, path=None, root=None):
        super().__init__(path) if path is not None else super().__init__()
        with self.db() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS corpus_records(
              id TEXT PRIMARY KEY, kind TEXT NOT NULL, payload TEXT NOT NULL,
              origin TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1, updated TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS corpus_links(
              owner TEXT NOT NULL REFERENCES corpus_records(id),
              target TEXT NOT NULL REFERENCES corpus_records(id), relation TEXT NOT NULL,
              PRIMARY KEY(owner,target,relation));
            CREATE TABLE IF NOT EXISTS corpus_proposals(
              id TEXT PRIMARY KEY, owner TEXT NOT NULL REFERENCES people(id),
              payload TEXT NOT NULL, status TEXT NOT NULL, created TEXT NOT NULL,
              review TEXT, record_id TEXT, fingerprint TEXT NOT NULL,
              UNIQUE(owner,fingerprint));
            CREATE TABLE IF NOT EXISTS corpus_history(
              id INTEGER PRIMARY KEY, record_id TEXT NOT NULL, version INTEGER NOT NULL,
              payload TEXT NOT NULL, reviewer TEXT NOT NULL, reason TEXT NOT NULL, created TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS corpus_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
            ''')
        # Los paquetes y su orden viven en ``lexicon.STEPS``; los marcadores de migración
        # ya registrados hacen que cada paso se aplique una sola vez por base.
        release_list = editorial_releases() if root is None else editorial_releases(Path(root) / lexicon.RELEASES)
        for step, bundle in lexicon.steps(root or ROOT, release_list):
            if step.action == 'images':
                self.backfill_glyph_images(bundle)
            elif step.action == 'source_images':
                self.backfill_source_images(bundle)
            else:
                self.import_bundle(bundle, step.reviewer, step.reason, seed=step.action == 'seed',
                                   migration_key=None if step.action == 'seed' else step.marker)

    def records(self, db=None):
        if db is None:
            with self.db() as conn:
                return self.records(conn)
        return {r['id']: dict(json.loads(r['payload']), version=r['version'])
                for r in db.execute('SELECT * FROM corpus_records ORDER BY id')}

    def validate(self, record, all_records):
        if not isinstance(record, dict):
            raise Problem('Cada registro debe ser un objeto.')
        r = json.loads(json.dumps(record, ensure_ascii=False))
        r.pop('version', None)
        rid = text(r.get('id', ''), 'Identificador', 120, True)
        if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9._:-]*', rid):
            raise Problem('Identificador inválido.')
        kind = choice(r.get('kind'), KINDS, 'tipo de registro')
        text(r.get('label', ''), 'Título', 300, True)
        choice(r.get('verification'), ['inherited', 'catalog_checked', 'reviewed'], 'estado de verificación')
        rights = r.get('rights', {})
        if not isinstance(rights, dict) or not isinstance(rights.get('public'), bool) or not isinstance(rights.get('training'), bool):
            raise Problem('Declara por separado consulta pública y entrenamiento.')
        text(rights.get('note', ''), 'Nota de derechos', 2000, True)
        if rights['training']:
            text(rights.get('basis', ''), 'Fundamento del permiso de entrenamiento', 2000, True)
        if 'url' in r:
            safe_url(r['url'])
        refs = []

        def ref(key, expected, required=True):
            target = r.get(key)
            if not target and not required:
                return
            if not isinstance(target, str) or target not in all_records or all_records[target].get('kind') not in expected:
                raise Problem(f'{key}: referencia inexistente o de tipo incorrecto.')
            refs.append((target, key))

        evidence = r.get('evidence', [])
        if not isinstance(evidence, list):
            raise Problem('Las evidencias deben formar una lista.')
        for e in evidence:
            if not isinstance(e, dict):
                raise Problem('Evidencia inválida.')
            for key in ('source_id', 'via_source_id'):
                if key == 'via_source_id' and not e.get(key):
                    continue
                target = e.get(key)
                if target not in all_records or all_records[target].get('kind') != 'source':
                    raise Problem('La evidencia necesita una fuente registrada.')
                refs.append((target, key))
            text(e.get('locator', ''), 'Página, folio o entrada', 500, True)
            choice(e.get('status'), ['inherited', 'catalog_checked', 'primary_checked'], 'comprobación de evidencia')
            if e['status'] == 'primary_checked':
                if all_records[e['source_id']].get('source_type') != 'primary':
                    raise Problem('Una comprobación primaria debe citar una fuente primaria.')
                text(e.get('checked_by', ''), 'Responsable de cotejo', 200, True)
                text(e.get('checked_at', ''), 'Fecha de cotejo', 50, True)
                text(e.get('note', ''), 'Nota de cotejo', 2000, True)
        if kind == 'source':
            choice(r.get('source_type'), ['primary', 'edition', 'research', 'catalog', 'community'], 'tipo de fuente')
            for key in ('institution', 'author', 'date', 'language', 'description'):
                text(r.get(key, ''), key, 3000, True)
            ref('primary_source_id', ['source'], False)
            if r.get('primary_source_id') and all_records[r['primary_source_id']].get('source_type') != 'primary':
                raise Problem('La edición debe enlazar una fuente primaria.')
        elif kind == 'sense':
            text(r.get('definition', ''), 'Acepción en español', 2000, True)
            choice(r.get('pos'), ['noun', 'verb', 'other'], 'categoría gramatical')
            if not isinstance(r.get('aliases', []), list) or not all(isinstance(x, str) for x in r.get('aliases', [])):
                raise Problem('Los alias deben ser textos.')
        else:
            if not evidence:
                raise Problem('Este registro requiere al menos una fuente y un localizador.')
            if kind in ('form', 'glyph'):
                ref('sense_id', ['sense'])
            if kind in ('form', 'text'):
                choice(r.get('period'), PERIODS, 'época')
                text(r.get('variant', ''), 'Variante o variedad histórica', 200, True)
                text(r.get('orthography', ''), 'Convención de escritura', 300, True)
            if kind == 'form':
                text(r.get('written', ''), 'Forma documentada', 300, True)
                choice(r.get('variation_kind'), ['historical', 'dialectal', 'orthographic', 'unspecified'], 'relación de variación')
            if kind == 'text':
                text(r.get('nah', ''), 'Transcripción', 16000)
                text(r.get('es', ''), 'Traducción', 16000)
                choice(r.get('text_status'), ['transcribed', 'pointer'], 'tipo de texto')
                if r['text_status'] == 'transcribed' and not r.get('nah', '').strip():
                    raise Problem('Falta la transcripción en náhuatl.')
                for target in r.get('sense_ids', []):
                    if target not in all_records or all_records[target].get('kind') != 'sense':
                        raise Problem('Acepción del texto no encontrada.')
                    refs.append((target, 'sense_id'))
            if kind == 'glyph':
                association = r.get('association')
                if association is not None:
                    if not isinstance(association, dict):
                        raise Problem('La asociación glífica debe ser un objeto.')
                    choice(association.get('type'), ['related_meaning', 'definition_reference', 'passage_reference'], 'relación visual')
                    text(association.get('note', ''), 'Alcance de la asociación', 3000, True)
                    safe_url(text(association.get('evidence_url', ''), 'Enlace de la asociación', 2000, True))
                    for key, expected in [('reference_form_id', 'form'), ('reference_glyph_id', 'glyph')]:
                        target = association.get(key)
                        if key == 'reference_glyph_id' and not target:
                            continue
                        if target not in all_records or all_records[target].get('kind') != expected or target == rid:
                            raise Problem('Referencia de asociación inexistente o de tipo incorrecto.')
                        if expected == 'form' and all_records[target].get('sense_id') != r['sense_id']:
                            raise Problem('La forma de evidencia debe pertenecer a esta acepción.')
                        refs.append((target, key))
                    if association['type'] == 'definition_reference':
                        text(association.get('definition_quote', ''), 'Definición citada', 2000, True)
                    if association['type'] == 'passage_reference':
                        passage = association.get('passage', {})
                        if not isinstance(passage, dict) or passage.get('iso') != 'nci':
                            raise Problem('La comparación requiere un pasaje clásico identificado.')
                        for field in ('id', 'nah', 'es', 'document', 'sha256'):
                            text(passage.get(field, ''), 'Pasaje: '+field, 3000, True)
                choice(r.get('glyph_status'), ['proposed', 'documented_context'], 'estado del glifo')
                text(r.get('context', ''), 'Contexto de uso glífico', 3000, True)
                text(r.get('reading', ''), 'Lectura propuesta', 300, True)
                if 'glyph_type' in r:
                    choice(r['glyph_type'], ['element', 'simplex', 'compound', 'iconography', 'unspecified'], 'tipo de imagen de fuente')
                if 'manuscript_url' in r:
                    safe_url(r['manuscript_url'])
                if 'image' in r:
                    safe_url(r['image'])
                    text(r.get('image_credit', ''), 'Crédito de imagen', 500, True)
                if not any(all_records[e['source_id']].get('source_type') == 'primary' for e in evidence):
                    raise Problem('El glifo debe identificar el códice o documento primario.')
                if r['glyph_status'] == 'documented_context' and not any(e['status'] == 'primary_checked' for e in evidence):
                    raise Problem('Documentar el contexto requiere cotejo primario explícito.')
        if len(json.dumps(r, ensure_ascii=False)) > 30000:
            raise Problem('Registro demasiado grande.')
        return r, refs

    def _write(self, db, record, links, origin, reviewer, reason):
        current = db.execute('SELECT version FROM corpus_records WHERE id=?', (record['id'],)).fetchone()
        version = current['version'] + 1 if current else 1
        payload = json.dumps(record, ensure_ascii=False)
        db.execute('INSERT INTO corpus_records VALUES(?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET '
                   'kind=excluded.kind,payload=excluded.payload,version=excluded.version,updated=excluded.updated',
                   (record['id'], record['kind'], payload, origin, version, now()))
        db.execute('DELETE FROM corpus_links WHERE owner=?', (record['id'],))
        for target, relation in set(links):
            db.execute('INSERT INTO corpus_links VALUES(?,?,?)', (record['id'], target, relation))
        db.execute('INSERT INTO corpus_history(record_id,version,payload,reviewer,reason,created) VALUES(?,?,?,?,?,?)',
                   (record['id'], version, payload, reviewer, reason, now()))

    def import_bundle(self, bundle, reviewer, reason, seed=False, migration_key=None):
        text(reviewer, 'Revisor', 200, True); text(reason, 'Motivo', 2000, True)
        if not isinstance(bundle, dict) or bundle.get('schema_version') != 1 or not isinstance(bundle.get('records'), list):
            raise Problem('Formato requerido: schema_version=1 y records=[…].')
        records = bundle['records']
        if len(records) > 10000:
            raise Problem('Importa como máximo 10000 registros por lote.')
        ids = [r.get('id') for r in records if isinstance(r, dict)]
        if len(ids) != len(records) or len(set(ids)) != len(ids):
            raise Problem('Registros o identificadores duplicados en el lote.')
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            marker = 'seed-v1' if seed else migration_key
            if marker and db.execute('SELECT 1 FROM corpus_meta WHERE key=?', (marker,)).fetchone():
                return 0
            existing = self.records(db)
            if migration_key:
                # Una actualización de referencias nunca sustituye una edición local.
                records = [r for r in records if r['id'] not in existing]
            merged = {**existing, **{r['id']: r for r in records}}
            # Revalida también los registros dependientes de cualquier cambio.
            checked = {rid: self.validate(r, merged) for rid, r in merged.items() if not r.get('withdrawn')}
            for r in records:
                old = existing.get(r['id'])
                if old:
                    if r.get('expected_version') != old['version']:
                        raise Problem(f"{r['id']}: incluye expected_version={old['version']} para editar.", 409)
                    if r['kind'] != old['kind']:
                        raise Problem('No se puede cambiar el tipo de un registro.')
                origin = db.execute('SELECT origin FROM corpus_records WHERE id=?', (r['id'],)).fetchone()
                if origin and origin['origin'].startswith('proposal:'):
                    raise Problem('Las aportaciones se corrigen mediante otra propuesta; conserva su permiso y retiro.')
            # Inserta primero entidades para satisfacer claves foráneas en cualquier orden de lote.
            for r in records:
                clean = checked[r['id']][0]; clean.pop('expected_version', None)
                db.execute('INSERT OR IGNORE INTO corpus_records VALUES(?,?,?,?,?,?)',
                           (r['id'], r['kind'], json.dumps(clean), 'seed' if seed else 'import', 0, now()))
            for r in records:
                clean, links = checked[r['id']]; clean.pop('expected_version', None)
                self._write(db, clean, links, 'seed' if seed else 'import', reviewer, reason)
            if marker:
                db.execute('INSERT INTO corpus_meta VALUES(?,?)', (marker, now()))
        return len(records)

    def backfill_glyph_images(self, bundle):
        # Añade solo image/image_credit a glifos ya presentes; no sustituye ediciones locales.
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute("SELECT 1 FROM corpus_meta WHERE key='glyph-images-v4'").fetchone():
                return 0
            existing = self.records(db)
            changed = 0
            for entry in bundle['records']:
                rid = entry.get('id')
                image = entry.get('image')
                current = existing.get(rid)
                if not current or not image or current.get('image'):
                    continue
                merged = {**current, 'image': image, 'image_credit': entry.get('image_credit', '')}
                clean, links = self.validate(merged, existing)
                origin = db.execute('SELECT origin FROM corpus_records WHERE id=?', (rid,)).fetchone()['origin']
                self._write(db, clean, links, origin, 'Migración de imágenes glíficas',
                            'Imagen enlazada desde su ficha externa')
                changed += 1
            db.execute("INSERT INTO corpus_meta VALUES('glyph-images-v4',?)", (now(),))
        return changed

    def backfill_source_images(self, bundle):
        """Completa campos ausentes sin sustituir imágenes, textos o ediciones locales."""
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute("SELECT 1 FROM corpus_meta WHERE key='glyph-source-images-v5'").fetchone():
                return 0
            existing = self.records(db)
            changed = 0
            for entry in bundle['records']:
                current = existing.get(entry['id'])
                if not current or current.get('withdrawn') or current['kind'] != 'glyph':
                    continue
                additions = {k: entry[k] for k in ('glyph_type', 'manuscript_url') if k in entry and k not in current}
                # Imagen y crédito son una pareja; nunca atribuye una imagen local con un crédito externo.
                if not current.get('image'):
                    additions.update(image=entry['image'], image_credit=entry['image_credit'])
                if not additions:
                    continue
                clean, links = self.validate({**current, **additions}, existing)
                origin = db.execute('SELECT origin FROM corpus_records WHERE id=?', (entry['id'],)).fetchone()['origin']
                self._write(db, clean, links, origin, 'Consulta editorial de catálogos',
                            'Imagen y procedencia tomadas de la ficha existente; cotejo primario pendiente')
                changed += 1
            db.execute("INSERT INTO corpus_meta VALUES('glyph-source-images-v5',?)", (now(),))
        return changed

    def public_records(self):
        # Un dato dependiente de otro retirado/privado deja de publicarse también.
        return lexicon.public_closure(self.records())

    def catalog_data(self):
        rows = list(self.public_records().values())
        rules_path=ROOT/'corpus/glyph-link-rules-v7.json'
        featured=json.loads(rules_path.read_text())['featured_sense_ids'] if rules_path.is_file() else []
        return dict(schema_version=1, records=rows, count=len(rows),
                    dictionary_featured_ids=featured,
                    variants=self.catalog['variants'],
                    note='Corpus inicial de referencias. La ausencia de una forma o glifo no demuestra que no exista.')

    def propose(self, person, body):
        kind = choice(body.get('kind'), ['form','text','glyph'], 'aportación')
        if body.get('review_consent') is not True or body.get('authorship') is not True:
            raise Problem('Confirma la revisión y que puedes compartir esta aportación.')
        public = body.get('public_consent') is True
        training = body.get('training_consent') is True
        records = self.public_records()
        rid = 'aporte-' + identifier()
        source_id = text(body.get('source_id',''), 'Fuente', 120, True)
        if source_id not in records or records[source_id]['kind'] != 'source':
            raise Problem('Selecciona una fuente del catálogo.')
        locator = text(body.get('locator',''), 'Página, folio o sesión', 500, True)
        period = choice(body.get('period'), PERIODS, 'época')
        if period == 'modern':
            variant = person['variant_key']
            variant_label = person['variant_label']
        else:
            variant = 'nci' if period == 'historical' else 'unknown'
            variant_label = 'Náhuatl histórico; propuesta por revisar' if period == 'historical' else 'Por identificar'
        archive_id=body.get('archive_id')
        if archive_id:
            if kind!='text':raise Problem('El cotejo de un pasaje debe ser textual.')
            from .research import Archive
            original=Archive().get(archive_id)
            period=original['period'];variant=original['iso'];variant_label=original['variant_label']
            source_id='src-axolotl';locator=original['locator']
        r = dict(id=rid,kind=kind,label=text(body.get('label',''), 'Título',300,True),
                 period=period,variant=variant,variant_label=variant_label,
                 orthography=text(body.get('orthography','Sin normalizar'), 'Escritura',300,True),
                 verification='inherited',evidence=[dict(source_id=source_id,locator=locator,status='inherited')],
                 rights=dict(public=public,training=training,note='Permisos explícitos de la persona aportante; revisar derechos de la fuente.',
                             basis='Consentimiento corpus-1: uso en entrenamiento del proyecto; sin permiso de redistribución del corpus.' if training else ''),
                 notes=text(body.get('notes',''), 'Notas',3000),
                 contributor_group=hashlib.sha256(person['id'].encode()).hexdigest()[:20])
        if kind == 'form':
            r.update(sense_id=body.get('sense_id'),written=text(body.get('written',''), 'Forma',300,True),
                     variation_kind=choice(body.get('variation_kind'), ['historical','dialectal','orthographic','unspecified'], 'tipo de variación'))
        elif kind == 'text':
            r.update(nah=text(body.get('nah',''), 'Texto náhuatl',12000,True),es=text(body.get('es',''), 'Traducción',12000),
                     text_status='transcribed',sense_ids=[body['sense_id']] if body.get('sense_id') else [])
        else:
            r.update(sense_id=body.get('sense_id'),glyph_status='proposed',
                     reading=text(body.get('reading',''), 'Lectura',300,True),
                     context=text(body.get('context',''), 'Contexto',3000,True),url=safe_url(body.get('url','')))
        if archive_id:r['archive_id']=archive_id
        clean,_ = self.validate(r, {**records,rid:r})
        fingerprint = digest({k:v for k,v in clean.items() if k != 'id'})
        payload = dict(record=clean,profile_snapshot={k:person[k] for k in ('variant_key','variant_label','own_name')},
                       consent=dict(version='corpus-1',review=True,authorship=True,public=public,training=training))
        with self.db() as db:
            old=db.execute('SELECT id,status FROM corpus_proposals WHERE owner=? AND fingerprint=?', (person['id'],fingerprint)).fetchone()
            if old:
                return dict(id=old['id'],status=old['status'],duplicate=True)
            db.execute('INSERT INTO corpus_proposals VALUES(?,?,?,?,?,?,?,?)',
                       (rid,person['id'],json.dumps(payload,ensure_ascii=False),'pending',now(),None,None,fingerprint))
        return dict(id=rid,status='pending',duplicate=False)

    def proposals(self, person=None):
        with self.db() as db:
            rows=db.execute('SELECT * FROM corpus_proposals'+(' WHERE owner=?' if person else '')+' ORDER BY created DESC',
                            (person['id'],) if person else ()).fetchall()
        return [dict(id=r['id'],status=r['status'],created=r['created'],payload=json.loads(r['payload']),
                     review=json.loads(r['review']) if r['review'] else None) for r in rows]

    def decide(self, proposal_id, decision, reviewer, reason, primary_checked=False, rights_checked=False):
        choice(decision,['accepted','rejected'],'decisión')
        text(reviewer,'Revisor',200,True);text(reason,'Justificación',3000,True)
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT * FROM corpus_proposals WHERE id=?',(proposal_id,)).fetchone()
            if not row or row['status'] != 'pending':
                raise Problem('La propuesta no está pendiente.',409)
            payload=json.loads(row['payload']);r=payload['record']
            review=dict(reviewer=reviewer,reason=reason,created=now(),rights_checked=rights_checked,primary_checked=primary_checked)
            if decision=='accepted':
                if not rights_checked:
                    raise Problem('La aceptación requiere revisar derechos de la fuente y permisos del aporte.')
                if r.get('period') == 'modern' and r.get('variant') == 'unknown':
                    raise Problem('Identifica la variante antes de aceptar; retira y vuelve a aportar.')
                if primary_checked:
                    for e in r['evidence']:
                        e.update(status='primary_checked',checked_by=reviewer,checked_at=now(),note=reason)
                    if r['kind']=='glyph':
                        r['glyph_status']='documented_context'
                r['verification']='reviewed';r['review']=review
                clean,links=self.validate(r,{**self.records(db),r['id']:r})
                self._write(db,clean,links,'proposal:'+proposal_id,reviewer,reason)
            db.execute('UPDATE corpus_proposals SET status=?,review=?,record_id=? WHERE id=?',
                       (decision,json.dumps(review),r['id'] if decision=='accepted' else None,proposal_id))

    def withdraw_proposal(self, person, proposal_id):
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT * FROM corpus_proposals WHERE id=? AND owner=?',(proposal_id,person['id'])).fetchone()
            if not row:
                raise Problem('Aportación no encontrada.',404)
            if row['record_id']:
                record=self.records(db).get(row['record_id'])
                if record:
                    tombstone=dict(id=record['id'],kind=record['kind'],label='Aportación retirada',withdrawn=True,
                                   rights=dict(public=False,training=False,note='Retirada por su autor.'),verification='inherited')
                    db.execute('UPDATE corpus_records SET payload=?,updated=? WHERE id=?',(json.dumps(tombstone),now(),record['id']))
                    db.execute('DELETE FROM corpus_links WHERE owner=?',(record['id'],))
                    db.execute('DELETE FROM corpus_history WHERE record_id=?',(record['id'],))
            db.execute("UPDATE corpus_proposals SET status='withdrawn',payload='{}',review=NULL WHERE id=?",(proposal_id,))

    def export_data(self, purpose='research', period=''):
        choice(purpose,['research','training'],'uso de exportación')
        records=self.public_records() if purpose=='research' else self.records()
        if purpose=='training':
            eligible=[]
            for r in records.values():
                if r.get('kind') not in ('form','text') or r.get('withdrawn') or not r['rights']['training'] or r.get('verification')!='reviewed':
                    continue
                if period and r.get('period')!=period:
                    continue
                source_ids={e[k] for e in r.get('evidence',[]) for k in ('source_id','via_source_id') if e.get(k)}
                sources=[records.get(sid,{}) for sid in sorted(source_ids)]
                if not sources or not all(s.get('rights',{}).get('training') and not s.get('withdrawn') for s in sources):
                    continue
                if r.get('period')=='unknown' or r.get('variant')=='unknown':
                    continue
                # Los pares requieren traducción; las formas, una acepción autorizada.
                if r['kind']=='text' and (r.get('text_status')!='transcribed' or not r.get('es')):
                    continue
                sense=records.get(r.get('sense_id'),{})
                if r['kind']=='form' and (sense.get('withdrawn') or not sense.get('rights',{}).get('training')):
                    continue
                if r.get('period')=='historical' and not any(e['status']=='primary_checked' for e in r['evidence']):
                    continue
                eligible.append(dict(r,split='unassigned',group=r['evidence'][0]['source_id'],
                                     source_records=sources,es=r.get('es') if r['kind']=='text' else sense['label'],
                                     nah=r.get('nah') if r['kind']=='text' else r['written']))
            return dict(schema_version=1,purpose=purpose,records=eligible,redistribution=False,
                        note='Uso de entrenamiento del proyecto; separar por obra y hablante antes de entrenar. No se incorpora automáticamente.')
        return dict(schema_version=1,purpose=purpose,records=list(records.values()),
                    note='Exportación para investigación local; conserva los derechos por registro. No concede redistribución ni entrenamiento.')
