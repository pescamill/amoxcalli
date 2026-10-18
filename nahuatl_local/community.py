"""Voces: almacén de aportaciones de texto y voz, sus rutas HTTP y la administración por consola.

La aplicación (platform.py) sirve Voces en /aportar; este módulo no tiene servidor propio.
"""
import argparse
import contextlib
import hashlib
import json
import secrets
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = Path(__file__).with_name('community_web')
DEFAULT_DB = ROOT / 'data/community/voces.sqlite3'
MAX_AUDIO = 8 * 1024 * 1024
CONSENT_VERSION = 'voces-1'


class Problem(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def text(value, name, limit=4000, required=False):
    if not isinstance(value, str):
        raise Problem(f'{name}: se esperaba texto.')
    value = value.strip()
    try:
        value.encode('utf-8')
    except UnicodeEncodeError:
        raise Problem(f'{name}: el texto contiene un carácter inválido.') from None
    if len(value) > limit or (required and not value):
        raise Problem(f'{name}: completa el campo (máximo {limit} caracteres).')
    return value


def choice(value, allowed, name):
    if value not in allowed:
        raise Problem(f'Elige una opción de {name}.')
    return value


def identifier():
    return uuid.uuid4().hex


class Store:
    def __init__(self, path=DEFAULT_DB):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.catalog = json.loads((ASSETS / 'catalog.json').read_text())
        with self.db() as db:
            db.executescript('''
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS people(id TEXT PRIMARY KEY, session_hash TEXT UNIQUE NOT NULL,
              profile TEXT NOT NULL, created TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS tasks(id TEXT PRIMARY KEY, kind TEXT NOT NULL, payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS audio(id TEXT PRIMARY KEY, owner TEXT NOT NULL REFERENCES people(id),
              mime TEXT NOT NULL, body BLOB NOT NULL, created TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS contributions(id TEXT PRIMARY KEY, owner TEXT NOT NULL REFERENCES people(id),
              task TEXT NOT NULL REFERENCES tasks(id), kind TEXT NOT NULL, variant TEXT NOT NULL,
              payload TEXT NOT NULL, audio_id TEXT UNIQUE REFERENCES audio(id), created TEXT NOT NULL,
              status TEXT NOT NULL DEFAULT 'pending', curation TEXT, UNIQUE(owner, task));
            CREATE TABLE IF NOT EXISTS reviews(id TEXT PRIMARY KEY, owner TEXT NOT NULL REFERENCES people(id),
              contribution TEXT NOT NULL REFERENCES contributions(id), payload TEXT NOT NULL,
              created TEXT NOT NULL, UNIQUE(owner, contribution));
            CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, event TEXT NOT NULL,
              record TEXT NOT NULL, detail TEXT NOT NULL, created TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS contribution_queue ON contributions(variant,kind,status);
            ''')
            for task in self.catalog['tasks']:
                db.execute('INSERT OR IGNORE INTO tasks VALUES(?,?,?)',
                           (task['id'], task['kind'], json.dumps(task, ensure_ascii=False)))
        with contextlib.suppress(OSError):
            self.path.chmod(0o600)

    @contextlib.contextmanager
    def db(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            with db:
                yield db
        finally:
            db.close()

    def person(self, token):
        if not token:
            return None
        with self.db() as db:
            row = db.execute('SELECT * FROM people WHERE session_hash=?',
                             (hashlib.sha256(token.encode()).hexdigest(),)).fetchone()
        return dict(id=row['id'], **json.loads(row['profile'])) if row else None

    def save_profile(self, body, person=None):
        if body.get('participation_consent') is not True:
            raise Problem('Confirma que eres mayor de edad y aceptas guardar tus aportaciones en este proyecto.')
        variants = {v['id']: v['label'] for v in self.catalog['variants']}
        variant = choice(body.get('variant_id'), set(variants) | {'custom', 'unknown'}, 'variante')
        own_name = text(body.get('own_name', ''), 'Nombre de tu lengua', 100)
        if variant == 'custom' and not own_name:
            raise Problem('Escribe cómo llamas a tu variante.')
        key = 'custom:' + own_name.casefold() if variant == 'custom' else variant
        profile = dict(alias=text(body.get('alias', ''), 'Seudónimo', 40, True), variant_id=variant,
                       variant_key=key, variant_label=variants.get(variant, own_name or 'Por identificar'),
                       own_name=own_name, community=text(body.get('community', ''), 'Comunidad', 120),
                       experience=choice(body.get('experience'), ['childhood', 'learned', 'learning'], 'experiencia'),
                       historical=choice(body.get('historical'), ['none', 'some', 'study'], 'textos históricos'),
                       participation_consent=True, consent_version=CONSENT_VERSION)
        token = None
        with self.db() as db:
            if person:
                person_id = person['id']
                db.execute('UPDATE people SET profile=? WHERE id=?', (json.dumps(profile), person_id))
            else:
                token, person_id = secrets.token_urlsafe(32), identifier()
                db.execute('INSERT INTO people VALUES(?,?,?,?)',
                           (person_id, hashlib.sha256(token.encode()).hexdigest(), json.dumps(profile), now()))
        return dict(id=person_id, **profile), token

    def bootstrap(self, person):
        with self.db() as db:
            total = db.execute("SELECT count(*) FROM contributions WHERE status!='withdrawn'").fetchone()[0]
            if person:
                records = db.execute("SELECT * FROM contributions WHERE owner=? AND status!='withdrawn'", (person['id'],)).fetchall()
                reviews = db.execute('SELECT created FROM reviews WHERE owner=?', (person['id'],)).fetchall()
            else:
                records, reviews = [], []
        accepted = sum(r['status'] == 'accepted' for r in records)
        today = now()[:10]
        daily = sum(r['created'].startswith(today) for r in [*records, *reviews])
        points = len(records) * 10 + len(reviews) * 5 + accepted * 10
        return dict(profile=person, variants=self.catalog['variants'], variant_source=self.catalog['variant_source'],
                    stats=dict(contributions=len(records), reviews=len(reviews), accepted=accepted,
                               points=points, today=daily, goal=5, community_total=total),
                    consent_version=CONSENT_VERSION)

    def task(self, mode, person, after=''):
        choice(mode, ['recognize', 'translate', 'listen', 'review'], 'misión')
        with self.db() as db:
            if mode in ('recognize', 'translate'):
                rows = db.execute('SELECT * FROM tasks WHERE kind=? AND id NOT IN '
                                  '(SELECT task FROM contributions WHERE owner=?) ORDER BY id',
                                  (mode, person['id'])).fetchall()
                tasks = [json.loads(r['payload']) for r in rows]
            else:
                rows = db.execute("SELECT c.*,t.payload AS source FROM contributions c JOIN tasks t ON t.id=c.task "
                                  "WHERE c.owner!=? AND c.variant=? AND c.kind='translate' "
                                  "AND c.status NOT IN ('withdrawn','rejected') AND c.id NOT IN "
                                  "(SELECT contribution FROM reviews WHERE owner=?) ORDER BY c.created",
                                  (person['id'], person['variant_key'], person['id'])).fetchall()
                tasks = []
                for r in rows:
                    payload, source = json.loads(r['payload']), json.loads(r['source'])
                    if (mode == 'listen' and not r['audio_id']) or (mode == 'review' and not payload['text']):
                        continue
                    tasks.append(dict(id=r['id'], kind=mode, text=payload['text'], source_text=source['text'],
                                      audio_id=r['audio_id'], variant_label=payload['profile']['variant_label'],
                                      source={'label': 'Aportación de una persona participante', 'url': ''}))
        if not tasks:
            return dict(task=None, remaining=0)
        offset = next((i + 1 for i, t in enumerate(tasks) if t['id'] == after), 0) % len(tasks)
        return dict(task=tasks[offset], remaining=len(tasks))

    def save_audio(self, person, mime, body):
        if not body or len(body) > MAX_AUDIO:
            raise Problem('El audio debe tener contenido y pesar hasta 8 MB.', 413)
        mime = mime.split(';')[0].strip()
        valid = ((mime in ('audio/webm', 'video/webm') and body[:4] == b'\x1aE\xdf\xa3') or
                 (mime == 'audio/ogg' and body[:4] == b'OggS') or
                 (mime in ('audio/wav', 'audio/x-wav') and body[:4] == b'RIFF' and body[8:12] == b'WAVE') or
                 (mime in ('audio/mp4', 'audio/x-m4a') and body[4:8] == b'ftyp'))
        if not valid:
            raise Problem('Formato de audio no admitido. Usa WebM, Ogg, WAV o M4A.')
        audio_id = identifier()
        with self.db() as db:
            count = db.execute('SELECT count(*) FROM audio WHERE owner=? AND id NOT IN '
                               '(SELECT audio_id FROM contributions WHERE audio_id IS NOT NULL)', (person['id'],)).fetchone()[0]
            if count >= 5:
                raise Problem('Hay grabaciones sin enviar. Borra una antes de subir otra.', 429)
            db.execute('INSERT INTO audio VALUES(?,?,?,?,?)', (audio_id, person['id'], mime, body, now()))
        return audio_id

    def get_audio(self, audio_id, person):
        with self.db() as db:
            row = db.execute('SELECT * FROM audio WHERE id=?', (audio_id,)).fetchone()
            if not row:
                raise Problem('Audio no disponible.', 404)
            allowed = row['owner'] == person['id']
            if not allowed:
                allowed = db.execute("SELECT 1 FROM contributions WHERE audio_id=? AND variant=? "
                                     "AND kind='translate' AND status NOT IN ('withdrawn','rejected')",
                                     (audio_id, person['variant_key'])).fetchone() is not None
            if not allowed:
                raise Problem('Este audio no pertenece a tu cola de revisión.', 403)
            return row['mime'], row['body']

    def delete_unused_audio(self, audio_id, person):
        with self.db() as db:
            db.execute('DELETE FROM audio WHERE id=? AND owner=? AND id NOT IN '
                       '(SELECT audio_id FROM contributions WHERE audio_id IS NOT NULL)', (audio_id, person['id']))

    def contribute(self, person, body):
        if body.get('review_consent') is not True or body.get('rights_confirm') is not True:
            raise Problem('Confirma la autoría y el permiso de revisión antes de enviar.')
        with self.db() as db:
            task = db.execute('SELECT * FROM tasks WHERE id=?', (text(body.get('task_id', ''), 'Misión', 100, True),)).fetchone()
            if not task:
                raise Problem('Misión no disponible.', 404)
            answer = text(body.get('text', ''), 'Respuesta')
            audio_id = body.get('audio_id') or None
            if audio_id is not None:
                audio_id = text(audio_id, 'Grabación', 100, True)
                if not db.execute('SELECT 1 FROM audio WHERE id=? AND owner=?', (audio_id, person['id'])).fetchone():
                    raise Problem('Grabación no disponible.', 403)
            payload = dict(text=answer, profile={k: v for k, v in person.items() if k != 'id'},
                           consent_version=CONSENT_VERSION, review_consent=True, rights_confirm=True,
                           train_text=body.get('train_text') is True, train_audio=body.get('train_audio') is True,
                           public_redistribution=False)
            if task['kind'] == 'recognize':
                if audio_id:
                    raise Problem('La misión de lectura usa texto; graba en la misión de escritura y voz.')
                payload.update(recognition=choice(body.get('recognition'), ['yes','partly','no','unreadable'], 'comprensión'),
                               perceived=choice(body.get('perceived'), ['own','other','historical','unsure'], 'impresión'),
                               certainty=choice(body.get('certainty'), ['sure','somewhat','unsure'], 'seguridad'))
            elif not answer and not audio_id:
                raise Problem('Escribe o graba tu propuesta.')
            contribution_id = identifier()
            try:
                db.execute('INSERT INTO contributions(id,owner,task,kind,variant,payload,audio_id,created) VALUES(?,?,?,?,?,?,?,?)',
                           (contribution_id, person['id'], task['id'], task['kind'], person['variant_key'],
                            json.dumps(payload, ensure_ascii=False), audio_id, now()))
            except sqlite3.IntegrityError:
                raise Problem('Esta misión o grabación ya se envió. No se sumaron puntos otra vez.', 409) from None
        return dict(id=contribution_id, points=10, status='pending')

    def review(self, person, body):
        target = text(body.get('contribution_id', ''), 'Aportación', 100, True)
        verdict = choice(body.get('verdict'), ['matches','partial','different','unsure'], 'revisión')
        if body.get('review_consent') is not True:
            raise Problem('Autoriza guardar esta revisión.')
        payload = dict(verdict=verdict, correction=text(body.get('correction', ''), 'Sugerencia'),
                       transcript=text(body.get('transcript', ''), 'Transcripción'),
                       profile={k: v for k, v in person.items() if k != 'id'},
                       train_text=body.get('train_text') is True, consent_version=CONSENT_VERSION,
                       review_consent=True, public_redistribution=False)
        with self.db() as db:
            row = db.execute('SELECT * FROM contributions WHERE id=?', (target,)).fetchone()
            if not row or row['owner'] == person['id'] or row['variant'] != person['variant_key'] or row['kind'] != 'translate' or row['status'] in ('withdrawn','rejected'):
                raise Problem('Esta aportación no está disponible para tu revisión.', 403)
            try:
                review_id = identifier()
                db.execute('INSERT INTO reviews VALUES(?,?,?,?,?)', (review_id, person['id'], target, json.dumps(payload, ensure_ascii=False), now()))
            except sqlite3.IntegrityError:
                raise Problem('Ya revisaste esta aportación.', 409) from None
        return dict(id=review_id, points=5)

    def mine(self, person):
        with self.db() as db:
            contributions = db.execute('SELECT c.*,t.payload AS source,(SELECT count(*) FROM reviews WHERE contribution=c.id) AS reviews '
                                       'FROM contributions c JOIN tasks t ON t.id=c.task WHERE owner=? ORDER BY created DESC,c.rowid DESC', (person['id'],)).fetchall()
            reviews = db.execute('SELECT * FROM reviews WHERE owner=? ORDER BY created DESC,rowid DESC', (person['id'],)).fetchall()
        return dict(contributions=[dict(id=r['id'], kind=r['kind'], status=r['status'], created=r['created'],
                                        source=json.loads(r['source']), answer=json.loads(r['payload']),
                                        audio_id=r['audio_id'], reviews=r['reviews']) for r in contributions],
                    reviews=[dict(id=r['id'], contribution_id=r['contribution'], created=r['created'], answer=json.loads(r['payload'])) for r in reviews])

    def withdraw(self, person, record_id, review=False):
        with self.db() as db:
            if review:
                row = db.execute('SELECT * FROM reviews WHERE id=? AND owner=?', (record_id, person['id'])).fetchone()
                if not row:
                    raise Problem('Revisión no disponible.', 404)
                db.execute('DELETE FROM reviews WHERE id=?', (record_id,))
                # Una decisión que citó esta revisión vuelve a pendiente para evitar exportarla tras el retiro.
                db.execute("UPDATE contributions SET status='pending',curation=NULL WHERE id=? AND status='accepted'", (row['contribution'],))
                db.execute("UPDATE audit SET detail='{}' WHERE record=?", (row['contribution'],))
            else:
                row = db.execute('SELECT * FROM contributions WHERE id=? AND owner=?', (record_id, person['id'])).fetchone()
                if not row:
                    raise Problem('Aportación no disponible.', 404)
                db.execute('DELETE FROM reviews WHERE contribution=?', (record_id,))
                db.execute("UPDATE contributions SET status='withdrawn',payload='{}',audio_id=NULL,curation=NULL WHERE id=?", (record_id,))
                if row['audio_id']:
                    db.execute('DELETE FROM audio WHERE id=?', (row['audio_id'],))
                db.execute("UPDATE audit SET detail='{}' WHERE record=?", (record_id,))
            db.execute('INSERT INTO audit(event,record,detail,created) VALUES(?,?,?,?)', ('withdraw_review' if review else 'withdraw', record_id, '{}', now()))

    def curate(self, record_id, decision, reviewer, language, evidence, final_text='', source_url='', locator=''):
        choice(decision, ['accepted','rejected'], 'decisión')
        choice(language, ['modern','nci'], 'lengua de destino')
        reviewer, evidence = text(reviewer, 'Revisor', 200, True), text(evidence, 'Justificación', 4000, True)
        with self.db() as db:
            row = db.execute('SELECT * FROM contributions WHERE id=?', (record_id,)).fetchone()
            if not row or row['status'] == 'withdrawn' or row['kind'] != 'translate':
                raise Problem('Solo se pueden aprobar propuestas de traducción vigentes.')
            payload = json.loads(row['payload'])
            final_text = text(final_text or payload['text'], 'Texto revisado', 4000)
            if decision == 'accepted':
                if not final_text:
                    raise Problem('Transcribe y revisa el audio antes de aprobar; utiliza --text.')
                if row['variant'] == 'unknown' and language == 'modern':
                    raise Problem('La variante debe estar identificada antes de exportar.')
                if language == 'nci' and (not source_url.startswith(('https://','http://')) or not locator.strip()):
                    raise Problem('La clasificación clásica requiere --source-url y --locator de la evidencia histórica revisada.')
            value = dict(reviewer=reviewer, evidence=evidence, language=language, text=final_text,
                         source_url=source_url, locator=locator, at=now(), verification='organizer_declared')
            db.execute('UPDATE contributions SET status=?,curation=? WHERE id=?', (decision, json.dumps(value, ensure_ascii=False), record_id))
            db.execute('INSERT INTO audit(event,record,detail,created) VALUES(?,?,?,?)', ('curate', record_id, json.dumps(value), now()))

    def export(self, output, language, include_audio=False):
        choice(language, ['modern','nci'], 'destino de exportación')
        output = Path(output)
        if output.exists() or output.with_suffix('.manifest.json').exists():
            raise Problem('Elige un archivo nuevo; las exportaciones anteriores no se sobrescriben.')
        records, audio_payloads = [], []
        with self.db() as db:
            rows = db.execute("SELECT c.*,t.payload AS source FROM contributions c JOIN tasks t ON t.id=c.task WHERE c.status='accepted' AND c.kind='translate'").fetchall()
            for row in rows:
                payload, curated, source = json.loads(row['payload']), json.loads(row['curation']), json.loads(row['source'])
                if curated['language'] != language or not payload['train_text']:
                    continue
                item = dict(id='community-'+row['id'], es=source['text'], nah=curated['text'],
                            variant=payload['profile']['variant_label'] if language == 'modern' else 'Classical Nahuatl',
                            iso='nci' if language == 'nci' else None, contributor_variant=row['variant'],
                            source_task=row['task'], group='community-prompt:'+str(source.get('source', {}).get('group', row['task'])),
                            speaker_group='speaker-'+hashlib.sha256(row['owner'].encode()).hexdigest()[:16],
                            split='unassigned', curation=curated, consent_version=payload['consent_version'],
                            permission='project_training_only', public_redistribution=False,
                            audio_id=None)
                if include_audio and payload['train_audio'] and row['audio_id']:
                    audio = db.execute('SELECT * FROM audio WHERE id=?', (row['audio_id'],)).fetchone()
                    if audio:
                        ext = {'audio/ogg':'.ogg','audio/wav':'.wav','audio/x-wav':'.wav','audio/mp4':'.m4a','audio/x-m4a':'.m4a'}.get(audio['mime'], '.webm')
                        item['audio_id'] = audio['id']
                        item['audio_file'] = output.stem+'-audio/'+audio['id']+ext
                        item['audio_sha256'] = hashlib.sha256(audio['body']).hexdigest()
                        audio_payloads.append((item['audio_file'], audio['body']))
                records.append(item)
        if not records:
            raise Problem('No hay pares aprobados con permiso de entrenamiento para ese destino.')
        output.parent.mkdir(parents=True, exist_ok=True)
        for relative, body in audio_payloads:
            path = output.parent / relative
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(body)
        with output.open('x', encoding='utf-8') as f:
            for item in records:
                f.write(json.dumps(item, ensure_ascii=False)+'\n')
        manifest = dict(created=now(), language=language, pairs=len(records), audios=len(audio_payloads),
                        sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                        source_ids=[r['id'] for r in records],
                        warning='Material de preparación: separar por hablante y familia de estímulo, auditar solapamientos y derechos antes de entrenar o redistribuir.')
        output.with_suffix('.manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
        return manifest

    def export_observations(self, output):
        """Opiniones consentidas, separadas de pares de traducción aprobados."""
        output = Path(output)
        if output.exists():
            raise Problem('Elige un archivo nuevo.')
        records = []
        with self.db() as db:
            rows = db.execute("SELECT c.*,t.payload AS source FROM contributions c JOIN tasks t ON t.id=c.task WHERE c.status!='withdrawn' AND c.kind='recognize'").fetchall()
            for row in rows:
                p = json.loads(row['payload'])
                if not p['train_text']:
                    continue
                records.append(dict(id=row['id'], kind='recognition_observation', text=json.loads(row['source'])['text'],
                                    task_id=row['task'], variant=row['variant'],
                                    speaker_group='speaker-'+hashlib.sha256(row['owner'].encode()).hexdigest()[:16],
                                    recognition=p['recognition'], perceived=p['perceived'], certainty=p['certainty'],
                                    explanation=p['text'], historical_experience_self_reported=p['profile']['historical'],
                                    expert_verified=False, consent_version=p['consent_version'],
                                    permission='project_training_only', public_redistribution=False))
            for row in db.execute("SELECT r.*,c.payload AS original,c.status,c.variant FROM reviews r JOIN contributions c ON c.id=r.contribution WHERE c.status!='withdrawn'"):
                p, original = json.loads(row['payload']), json.loads(row['original'])
                if not p['train_text'] or not original['train_text']:
                    continue
                records.append(dict(id=row['id'], kind='peer_observation', contribution_id=row['contribution'],
                                    original_text=original['text'], variant=row['variant'],
                                    speaker_group='speaker-'+hashlib.sha256(row['owner'].encode()).hexdigest()[:16],
                                    verdict=p['verdict'], correction=p['correction'], transcript=p['transcript'],
                                    expert_verified=False, consent_version=p['consent_version'],
                                    permission='project_training_only', public_redistribution=False))
        if not records:
            raise Problem('No hay observaciones con permiso de entrenamiento.')
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open('x', encoding='utf-8') as f:
            for item in records:
                f.write(json.dumps(item, ensure_ascii=False)+'\n')
        return dict(observations=len(records), warning='Opiniones de participantes; no equivalen a traducciones correctas ni clasificaciones históricas verificadas.')

    def import_tasks(self, path):
        rows = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
        with self.db() as db:
            for task in rows:
                text(task.get('id', ''), 'Identificador', 100, True)
                choice(task.get('kind'), ['recognize','translate'], 'tipo de misión')
                text(task.get('text', ''), 'Texto', 4000, True)
                source = task.get('source', {})
                text(source.get('label', ''), 'Fuente', 300, True)
                text(source.get('rights', ''), 'Permiso de uso', 1000, True)
                if source.get('url') and not source['url'].startswith(('https://','http://')):
                    raise Problem('URL de fuente inválida.')
                if source.get('split') in ('test','validation'):
                    raise Problem('No importes la evaluación reservada como misiones de entrenamiento.')
                db.execute('INSERT INTO tasks VALUES(?,?,?)', (task['id'], task['kind'], json.dumps(task, ensure_ascii=False)))
        return len(rows)


def routes(router, store):
    """Rutas HTTP de Voces; platform.py las monta en la aplicación única (con /api/task y la página /aportar)."""
    def bootstrap(request):
        return request.reply(store.bootstrap(request.get_person()))

    def mine(request):
        return request.reply(store.mine(request.get_person(True)))

    def audio(request):
        mime, body = store.get_audio(request.tail, request.get_person(True))
        return request.reply(body, mime=mime)

    def profile(request):
        profile, token = store.save_profile(request.body(), request.get_person())
        secure = '; Secure' if request.headers.get('Origin', '').startswith('https://') else ''
        cookie = f'voces_session={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=7776000{secure}' if token else None
        return request.reply(profile, cookie=cookie)

    def save_audio(request):
        person = request.get_person(True)
        return request.reply({'id': store.save_audio(person, request.headers.get('Content-Type', ''), request.body(raw=True))}, 201)

    def contribute(request):
        person = request.get_person(True)
        return request.reply(store.contribute(person, request.body()), 201)

    def review(request):
        person = request.get_person(True)
        return request.reply(store.review(person, request.body()), 201)

    def delete_audio(request):
        store.delete_unused_audio(request.tail, request.get_person(True))
        return request.reply({'ok': True})

    def withdraw(request):
        store.withdraw(request.get_person(True), request.tail)
        return request.reply({'ok': True})

    def withdraw_review(request):
        store.withdraw(request.get_person(True), request.tail, review=True)
        return request.reply({'ok': True})

    router.add('GET', '/api/bootstrap', bootstrap)
    router.add('GET', '/api/mine', mine)
    router.add('GET', '/api/audio/', audio, prefix=True)
    router.add('POST', '/api/profile', profile)
    router.add('POST', '/api/audio', save_audio)
    router.add('POST', '/api/contributions', contribute)
    router.add('POST', '/api/reviews', review)
    router.add('DELETE', '/api/audio/', delete_audio, prefix=True)
    router.add('DELETE', '/api/contributions/', withdraw, prefix=True)
    router.add('DELETE', '/api/reviews/', withdraw_review, prefix=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, default=DEFAULT_DB)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('queue')
    imp = commands.add_parser('import-tasks'); imp.add_argument('path')
    curate = commands.add_parser('curate'); curate.add_argument('id'); curate.add_argument('--decision',choices=['accepted','rejected'],required=True); curate.add_argument('--reviewer',required=True); curate.add_argument('--language',choices=['modern','nci'],required=True); curate.add_argument('--evidence',required=True); curate.add_argument('--text',default=''); curate.add_argument('--source-url',default=''); curate.add_argument('--locator',default='')
    export = commands.add_parser('export'); export.add_argument('--output',required=True); export.add_argument('--language',choices=['modern','nci'],required=True); export.add_argument('--include-audio',action='store_true')
    observations = commands.add_parser('export-observations'); observations.add_argument('--output',required=True)
    args = parser.parse_args(); store = Store(args.db)
    try:
        if args.command == 'queue':
            with store.db() as db:
                for row in db.execute("SELECT c.*,t.payload AS task_payload FROM contributions c JOIN tasks t ON t.id=c.task WHERE c.status!='withdrawn'"):
                    item = dict(row);item['payload']=json.loads(item['payload']);item['task_payload']=json.loads(item['task_payload']);item['reviews']=[dict(r) for r in db.execute('SELECT id,payload FROM reviews WHERE contribution=?',(row['id'],))];print(json.dumps(item,ensure_ascii=False))
        elif args.command == 'import-tasks': print('Misiones importadas:',store.import_tasks(args.path))
        elif args.command == 'curate':
            store.curate(args.id,args.decision,args.reviewer,args.language,args.evidence,args.text,args.source_url,args.locator);print('Decisión guardada.')
        elif args.command == 'export': print(json.dumps(store.export(args.output,args.language,args.include_audio),ensure_ascii=False,indent=2))
        elif args.command == 'export-observations': print(json.dumps(store.export_observations(args.output),ensure_ascii=False,indent=2))
    except (Problem,sqlite3.IntegrityError,ValueError) as error:
        parser.exit(1,str(error)+'\n')


if __name__ == '__main__':
    main()
