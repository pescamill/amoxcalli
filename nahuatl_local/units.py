"""Unidades cortas de gramática y lecturas nuevas: generadas desde el corpus, servidas como borrador.

Qué hace
--------
``generate`` propone, sin modelo ni red, a partir de tres piezas que ya existen:

* el **archivo** clásico (pasajes ``nci`` de Axolotl, con su traducción de origen);
* el **analizador** (``morphology``): segmentación, etiqueta y glosa de cada morfema;
* el **índice de términos** (``terms``): solo cuentan las grafías *seguras* del grupo de
  cada palabra (las inciertas —homógrafos, compuestos— no entran).

Cada **unidad** une vocabulario de las lecturas con una regla (absolutivo, posesivos,
locativos, sujeto y objeto, plural) y reúne cinco tipos de ejercicio —emparejar, armar
con fichas de morfemas, identificar el morfema, elegir la traducción de un pasaje breve
real y completar con distractores de la misma raíz— más una lectura breve real al cierre.
Las **lecturas nuevas** se eligen ordenando pasajes breves por cobertura de raíces y se
entregan como receta de ``lesson_builder`` (propuesta preparada, nunca aplicada).

Validez y revisión
------------------
``check`` vuelve a derivar cada respuesta correcta desde el pasaje (hash, forma
completa, traducción) y el análisis actual (segmentación, morfema, acepción, grafía
segura); lo que no pasa no se sirve. Todo es ``automatic_draft``: una unidad solo se
muestra como revisada si la cola editorial (``editorial/lesson-decisions.json``,
``lesson_audit.merge_decisions``) tiene una decisión resuelta, con revisor, fecha,
evidencia, resolución y la huella exacta de lo revisado. Las reglas y ayudas son
plantillas del proyecto, pendientes de revisión especializada como el analizador.

Uso::

    python3 -m nahuatl_local.units            # regenera unidades, receta, propuesta, cola e informe
    python3 -m nahuatl_local.units --check    # falla si algún archivo generado no está al día
"""
import argparse
import copy
import hashlib
import json
import re
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from threading import Lock

from .lesson_audit import fingerprint, merge_decisions
from .morphology import ANALYZER_VERSION, WORD
from .stems import ROOT, es_tokens
from .text import es_key, fold, loose_key

UNITS = ROOT / 'corpus' / 'units-v1.json'
LEARNING = ROOT / 'corpus' / 'learning-v1.json'
DECISIONS = ROOT / 'editorial' / 'lesson-decisions.json'
READINGS_ID = 'lecturas-generadas-001'
RECIPE = ROOT / 'configs' / (READINGS_ID + '.json')
PROPOSAL = ROOT / 'editorial' / (READINGS_ID + '.json')
QUEUE = ROOT / 'reports' / 'units-review-queue.json'
COVERAGE = ROOT / 'reports' / 'units-coverage.json'
MARKDOWN = ROOT / 'reports' / 'UNIDADES_COBERTURA.md'
GENERATOR_VERSION = 'units-gen-1'
SHORT = 12            # «pasaje breve»: palabras como las cuenta el analizador
READING_WORDS = 20    # pasajes de una lectura nueva (las lecturas actuales van de 1 a 87 palabras; mediana 10)
READINGS = 6          # lecturas nuevas por propuesta
DRAFT = 'Borrador automático: generado desde el archivo, el analizador y el índice de términos; pendiente de revisión.'

# Glosa breve de un morfema: la del analizador sin su aclaración entre paréntesis.
SHORT_GLOSS = {('ABS', k): 'absolutivo' for k in ('λ', 'λi', 'li', 'in')}
SHORT_GLOSS.update({('POSD', 'w'): 'poseído', ('POSD', 'wi'): 'poseído', ('LIG', 'ti'): None})
# Apoyo español de los verbos: la etiqueta («ver») no aparece conjugada en las traducciones.
# Tabla editorial breve, pendiente de revisión como las glosas del analizador.
SUPPORT_EXTRA = {'sense-itta': ('ver', 'veo', 'ves', 'vio', 'vió', 'vieron', 'verá', 'verán', 'veremos', 'vemos', 'ven',
                                'mira', 'miro', 'miró', 'miraron', 'contemplo', 'contempla', 'contemplaron', 'visto')}

# Una regla por unidad: qué morfemas enseña (posición, clave fonémica) y qué afijos admite junto a ellos.
RULES = [
    dict(id='absolutivo', title='La palabra sola: -tl, -tli, -li',
         objective='Reconocer el absolutivo de un sustantivo sin poseedor y separar la raíz.',
         focus={('ABS', 'λ'), ('ABS', 'λi'), ('ABS', 'li')}, allowed=set(),
         summary='Un sustantivo sin poseedor lleva una terminación llamada absolutivo: -tl tras vocal (xochi-tl), '
                 '-tli tras consonante (metz-tli) y -li cuando la raíz termina en l (cal-li).',
         points=['La raíz es lo que queda al quitar el absolutivo: xochi-, metz-, cal-.',
                 'Al poseer el sustantivo o añadirle otro sufijo, el absolutivo desaparece: cal-li → no-cal.']),
    dict(id='posesivos', title='Mi, tu, su, nuestro: no-, mo-, i-, to-',
         objective='Reconocer al poseedor por el prefijo y notar que el absolutivo cae.',
         focus={('POSS', 'no'), ('POSS', 'mo'), ('POSS', 'i'), ('POSS', 'to')}, allowed={('POSD', 'w'), ('POSD', 'wi')},
         summary='El poseedor va delante de la raíz: no- «mi», mo- «tu», i- «su», to- «nuestro». '
                 'La forma poseída pierde el absolutivo: cal-li «casa» → i-cal «su casa».',
         points=['Algunas raíces toman -uh al poseerse: xochi-tl → to-xochi-uh «nuestra flor».',
                 'El prefijo dice quién posee; la raíz, qué se posee.']),
    dict(id='locativos', title='Lugares: -co, -pan, -tlan, -icpac',
         objective='Reconocer un sufijo de lugar pegado a la raíz y leerlo como «en», «sobre» o «junto a».',
         focus={('REL', 'ko'), ('REL', 'pan'), ('REL', 'λan'), ('REL', 'kpak'), ('REL', 'ikpak'), ('REL', 'itik'), ('REL', 'nawak')},
         allowed={('LIG', 'ti'), ('POSS', 'no'), ('POSS', 'mo'), ('POSS', 'i'), ('POSS', 'to'), ('POSS', 'in')},
         summary='Los lugares se dicen con sufijos pegados a la raíz, sin absolutivo: cal-co «en la casa», '
                 'tlal-pan «sobre la tierra», te-tlan «junto a las piedras».',
         points=['-ticpac y -icpac significan «encima de»: tlal-ti-cpac «sobre la tierra».',
                 'La -ti- de tlal-ti-cpac es una ligadura entre la raíz y el sufijo.']),
    dict(id='sujeto-objeto', title='Quién ve qué: ni-, ti-, qui-',
         objective='Reconocer el sujeto (ni- «yo», ti- «tú / nosotros») y el objeto qui- / c- «lo, la» en un verbo.',
         focus={('SUBJ', 'ni'), ('SUBJ', 'ti'), ('SUBJ', 'n'), ('SUBJ', 't'), ('OBJ', 'ki'), ('OBJ', 'k')},
         allowed={('ANT', 'o'), ('T', ''), ('T', 's'), ('T', 'k'), ('T', 'ke'), ('T', 'ya'), ('T', 'ske')}, min_roots=1,
         short=20,  # los verbos de las lecturas casi no aparecen en pasajes de 12 palabras o menos
         summary='El verbo lleva delante quién hace la acción y a quién o qué: ni-qu-itta «yo lo veo», '
                 'ti-qu-itta «tú lo ves», qu-itta «él lo ve» (la tercera persona no lleva prefijo de sujeto).',
         points=['qui- se escribe qu- ante i y c- ante otras vocales: qu-itta, c-ana.',
                 'El tiempo va al final: qu-itta-z «lo verá», qu-itta-que «lo vieron».']),
    dict(id='plural', title='Más de uno: -meh, -tin',
         objective='Reconocer el plural de un sustantivo animado.',
         focus={('PL', 'me'), ('PL', 'tin'), ('PL', 'ke')}, allowed=set(),
         summary='Los sustantivos animados forman plural con -meh, -tin o -queh en lugar del absolutivo: '
                 'toto-tl «pájaro» → toto-meh «pájaros».',
         points=['Las cosas (calli, tetl) no suelen llevar plural.',
                 'Muchas grafías coloniales no escriben la h final: totome.']),
]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def passage_hash(row):
    return sha((row['nah'] + '\0' + row['es']).encode())


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def words(text):
    return WORD.findall(text)


def whole(form, text):
    """Posición de ``form`` como palabra completa en ``text`` (o -1)."""
    m = re.search(r'(?<![\w])' + re.escape(form) + r'(?![\w])', text)
    return m.start() if m else -1


def short_gloss(m):
    key = (m['slot'], m['key'])
    if key in SHORT_GLOSS:
        return SHORT_GLOSS[key]
    return (m['gloss'] or m['tag']).split(' (')[0]


def gloss_chain(occ):
    """Glosa por partes (morfema a morfema), no una traducción: «mi + casa»."""
    parts = []
    for m in occ['morphemes']:
        g = occ['label'] if m['role'] == 'stem' else short_gloss(m)
        if g:
            parts.append(g)
    return ' + '.join(parts)


def stable(items, salt):
    """Orden determinista que no coincide con el original (las opciones no van siempre primero)."""
    return sorted(items, key=lambda x: sha((salt + '\0' + json.dumps(x, ensure_ascii=False, sort_keys=True)).encode()))


class Corpus:
    """Ocurrencias de cada acepción en el archivo: grafía segura + análisis + apoyo en la traducción."""

    def __init__(self, terms, records):
        terms._build()
        self.terms, self.records = terms, records
        self.analyzer = terms.analyzer
        self.rows = terms.rows
        self._occ = {}
        self._lock = Lock()

    def label(self, sid):
        return self.records[sid]['label'].split(' / ')[0]

    def headword(self, sid):
        forms = [r for r in self.records.values() if r['kind'] == 'form' and r.get('sense_id') == sid]
        return (next((f for f in forms if f['id'].startswith('lex-')), forms[0] if forms else {})).get('written', '')

    def support_keys(self, sid):
        s = self.records[sid]
        keys = set()
        for label in [s.get('label', '')] + list(s.get('aliases', [])):
            for part in re.split(r'\s*/\s*', label):
                toks = [k for k, _ in es_tokens(part)]
                if len(toks) == 1:
                    keys.add(toks[0])
        keys.update(es_key(w) for w in SUPPORT_EXTRA.get(sid, ()))
        return keys

    def support(self, sid, es):
        """Palabra de la traducción que respalda la acepción, tal como está escrita (o None)."""
        keys = self.support_keys(sid)
        return next((surface for key, surface in es_tokens(es) if key in keys), None)

    def analysis(self, form, sid):
        a = self.analyzer.analyze(form, limit=1)
        if not a or a[0]['basis'] not in ('dictionary', 'dictionary_truncated'):
            return None
        if sid not in {d['sense_id'] for d in a[0]['dictionary']}:
            return None
        return a[0]

    def certain_keys(self, sid):
        """Grafías seguras del grupo. En un verbo también sus formas verbales: el índice las aparta como
        posibles homógrafos de un sustantivo, pero en una entrada verbal son su flexión esperada."""
        gid = self.terms.sense_group.get(sid)
        if not gid:
            return set()
        group = self.terms.group(gid)
        keys = set(group['_certain_keys'])
        if self.records[sid].get('pos') == 'verb':
            keys.update(v['key'] for v in group['spellings']['uncertain'] if v['reason'] == 'verb')
        return keys

    def occurrences(self, sid):
        """[ocurrencia] de la acepción: una por pasaje y grafía, en el orden del archivo."""
        with self._lock:
            if sid in self._occ:
                return self._occ[sid]
            out = []
            for key in sorted(self.certain_keys(sid)):
                for rid, w in self.terms.postings.get(key, []):
                    row = self.rows[rid]
                    if row['iso'] != 'nci' or whole(w, row['nah']) < 0:
                        continue
                    a = self.analysis(w, sid)
                    support = a and self.support(sid, row['es'])
                    if not support:
                        continue
                    morphemes = [dict(role=m['role'], slot=m['slot'], key=m['key'], surface=m['surface'], gloss=m['gloss'], tag=m['tag'])
                                 for m in a['morphemes'] if m['surface'] or m['role'] == 'stem']
                    out.append(dict(sense_id=sid, label=self.label(sid), archive_id=rid, form=w, segmentation=a['segmentation'],
                                    stem=a['stem'], morphemes=morphemes, support=support, words=len(words(row['nah'])),
                                    signature=tuple((m['slot'], m['key']) for m in morphemes if m['role'] != 'stem')))
            out.sort(key=lambda o: (self.rows[o['archive_id']]['line'], fold(o['form'])))
            self._occ[sid] = out
            return out

    def evidence(self, occ):
        row = self.rows[occ['archive_id']]
        return dict(archive_id=occ['archive_id'], source_hash=passage_hash(row), form=occ['form'], sense_id=occ['sense_id'],
                    segmentation=occ['segmentation'], support=occ['support'])


def reading_senses(learning):
    out = []
    for lesson in learning['lessons']:
        for sid in lesson['sense_ids'] + [a['sense_id'] for e in lesson['examples'] for a in e['annotations']]:
            if sid not in out:
                out.append(sid)
    return out


def used_passages(learning):
    return {e['archive_id'] for lesson in learning['lessons'] for e in lesson['examples']}


# ---------------------------------------------------------------------------
# Unidades
# ---------------------------------------------------------------------------
def matches(rule, occ):
    sig = set(occ['signature'])
    return bool(sig & rule['focus']) and sig <= rule['focus'] | rule['allowed'] and not occ['form'].isupper()


def focal(rule, occ):
    return [m for m in occ['morphemes'] if (m['slot'], m['key']) in rule['focus']]


def pick_targets(rule, occs, limit=6):
    short = rule.get('short', SHORT)
    """Formas distintas que cubren primero morfemas nuevos, luego raíces nuevas, luego frecuencia."""
    by_form = defaultdict(list)
    for o in occs:
        by_form[fold(o['form'])].append(o)
    pool = sorted(by_form.values(), key=lambda os: (-len(os), min(o['words'] for o in os), fold(os[0]['form'])))
    chosen, morphs, roots = [], set(), set()
    while pool and len(chosen) < limit:
        def gain(os):
            o = os[0]
            keys = {(m['slot'], m['key']) for m in focal(rule, o)}
            return (len(keys - morphs) > 0, o['sense_id'] not in roots, any(x['words'] <= short for x in os))
        best = max(pool, key=gain)
        pool.remove(best)
        chosen.append(sorted(best, key=lambda o: (o['form'][:1].isupper(), o['words'] > short, o['words'], self_line(o)))[0] | dict(attested=len(best)))
        morphs.update((m['slot'], m['key']) for m in focal(rule, best[0]))
        roots.add(best[0]['sense_id'])
    return chosen


def self_line(o):
    return int(o['archive_id'].split('-')[-1])


def build_unit(rule, corpus, senses, glosses):
    short = rule.get('short', SHORT)
    occs = [o for sid in senses for o in corpus.occurrences(sid) if matches(rule, o)]
    targets = pick_targets(rule, occs)
    if len(targets) < 4 or len({t['sense_id'] for t in targets}) < rule.get('min_roots', 2):
        return None, dict(id=rule['id'], reason='insufficient', forms=len(targets), roots=len({t['sense_id'] for t in targets}))
    uid = rule['id']
    exercises, used = [], set()

    def add(kind, **fields):
        exercises.append(dict(id=f'{uid}-{len(exercises) + 1}', kind=kind, **fields))

    def other_glosses(right):
        mine = sorted({g for g in (short_gloss(m) for t in targets for m in focal(rule, t)) if g and g != right})
        pool = mine + [g for g in glosses if g not in mine and g != right]
        return pool[:2]

    # 1. Emparejar forma y glosa por partes.
    pairs = targets[:4]
    add('match', prompt='Une cada forma del archivo con su glosa por partes.',
        pairs=[dict(form=t['form'], gloss=gloss_chain(t)) for t in pairs],
        evidence=[corpus.evidence(t) for t in pairs],
        explanation='Glosas del analizador, morfema a morfema; no son traducciones. Cada forma aparece en un pasaje real.')
    # 2–3. Identificar el morfema.
    for t in targets[:2]:
        m = focal(rule, t)[0]
        right = short_gloss(m)
        options = stable([right] + other_glosses(right), t['form'])
        piece = m['surface'] + '-' if m['role'] == 'prefix' else '-' + m['surface']
        add('identify', prompt=f'En «{t["form"]}», ¿qué indica «{piece}»?', form=t['form'], morpheme=dict(slot=m['slot'], key=m['key'], surface=m['surface']),
            options=options, answer=options.index(right), evidence=[corpus.evidence(t)],
            explanation=f'El analizador segmenta «{t["form"]}» como {t["segmentation"]}; «{piece}» se glosa «{m["gloss"]}».')
    # 4–5. Armar con fichas de morfemas.
    built = [t for t in targets[2:] + targets[:2] if len(t['morphemes']) >= 2][:2]
    for t in built:
        pieces = [m['surface'] for m in t['morphemes']]
        extra = next((m['surface'] for o in targets for m in focal(rule, o) if fold(m['surface']) not in {fold(p) for p in pieces}), None)
        tiles = stable(pieces + ([extra] if extra else []), t['form'] + ':tiles')
        answer, free = [], list(range(len(tiles)))
        for p in pieces:
            i = next(i for i in free if tiles[i] == p)
            free.remove(i)
            answer.append(i)
        add('build', prompt=f'Arma la forma que significa «{gloss_chain(t)}».', gloss=gloss_chain(t), tiles=tiles, answer=answer,
            form=t['form'], evidence=[corpus.evidence(t)],
            explanation=f'«{t["form"]}» aparece así en el archivo: {t["segmentation"]}.')
    # 6–7. Completar con distractores de la misma raíz.
    clozes = 0
    for t in sorted(occs, key=lambda o: (o['words'], self_line(o))):
        if clozes == 2:
            break
        row = corpus.rows[t['archive_id']]
        if t['words'] > short or t['archive_id'] in used or len(re.findall(r'(?<![\w])' + re.escape(t['form']) + r'(?![\w])', row['nah'])) != 1:
            continue
        siblings, seen = [], {fold(t['form'])}
        for o in corpus.occurrences(t['sense_id']):
            if o['signature'] != t['signature'] and fold(o['form']) not in seen and not o['form'].isupper():
                seen.add(fold(o['form']))
                siblings.append(o)
        siblings.sort(key=lambda o: (set(o['signature']) & rule['focus'] == set(), self_line(o)))
        if len(siblings) < 2 or any(fold(o['form']) == fold(t['form']) for o in siblings[:2]):
            continue
        options = stable([t['form']] + [o['form'] for o in siblings[:2]], t['archive_id'])
        used.add(t['archive_id'])
        clozes += 1
        add('cloze', prompt='Completa el pasaje con la forma que escribe el registro. La traducción del archivo te orienta.',
            archive_id=t['archive_id'], blank=t['form'], options=options, answer=options.index(t['form']),
            evidence=[corpus.evidence(t)] + [corpus.evidence(o) for o in siblings[:2]],
            explanation=f'El registro escribe «{t["form"]}» ({t["segmentation"]}). Las otras opciones comparten la raíz '
                        f'{t["stem"]} con otros afijos; también están en el archivo.')
    # 8–9. Elegir la traducción de un pasaje breve real.
    translations = 0
    for t in sorted(occs, key=lambda o: (o['words'], self_line(o))):
        if translations == 2:
            break
        row = corpus.rows[t['archive_id']]
        if t['words'] > short or t['archive_id'] in used or len(row['es']) > 160:
            continue
        others = []
        for o in corpus.occurrences(t['sense_id']) + [x for sid in senses for x in corpus.occurrences(sid)]:
            r = corpus.rows[o['archive_id']]
            if o['archive_id'] != t['archive_id'] and o['words'] <= short and fold(r['es']) != fold(row['es']) and len(r['es']) <= 160 \
                    and all(fold(r['es']) != fold(corpus.rows[x]['es']) for x in others):
                others.append(o['archive_id'])
            if len(others) == 2:
                break
        if len(others) < 2:
            continue
        ids = stable([t['archive_id']] + others, t['form'] + ':es')
        used.add(t['archive_id'])
        translations += 1
        add('translate', prompt='¿Qué dice este pasaje breve?', archive_id=t['archive_id'], option_ids=ids, answer=ids.index(t['archive_id']),
            focus_form=t['form'], evidence=[corpus.evidence(t)],
            explanation=f'Es la traducción del archivo para este registro. «{t["form"]}» = {gloss_chain(t)}.')
    # Lectura breve real al cierre: el pasaje breve no usado con más formas de la regla.
    per_passage = defaultdict(list)
    for o in occs:
        if o['words'] <= short and o['archive_id'] not in used:
            per_passage[o['archive_id']].append(o)
    if not per_passage or clozes < 1 or translations < 1:
        return None, dict(id=uid, reason='insufficient_passages', forms=len(targets), clozes=clozes, translations=translations)
    rid = min(per_passage, key=lambda r: (-len({fold(o['form']) for o in per_passage[r]}), corpus.rows[r]['line']))
    closing_forms = sorted({fold(o['form']): o for o in per_passage[rid]}.values(), key=lambda o: whole(o['form'], corpus.rows[rid]['nah']))
    closing = dict(archive_id=rid, forms=[dict(form=o['form'], segmentation=o['segmentation'], gloss=gloss_chain(o)) for o in closing_forms],
                   evidence=[corpus.evidence(o) for o in closing_forms])
    morphemes = Counter()
    examples = defaultdict(set)
    for t in targets:
        for m in focal(rule, t):
            morphemes[(m['slot'], m['key'])] += 1
            examples[(m['slot'], m['key'])].add(m['surface'].lower())
    roots = sorted({t['sense_id'] for t in targets}, key=senses.index)
    unit = dict(id=uid, version=1, practice_version=1, title=rule['title'], objective=rule['objective'],
                minutes=round(1.5 + 0.6 * len(exercises)),
                rule=dict(summary=rule['summary'], points=rule['points'],
                          morphemes=[dict(slot=s, key=k, surfaces=sorted(examples[(s, k)]),
                                          gloss=next(m['gloss'] for t in targets for m in focal(rule, t) if (m['slot'], m['key']) == (s, k)))
                                     for s, k in sorted(morphemes)]),
                sense_ids=roots, words=[dict(form=t['form'], segmentation=t['segmentation'], gloss=gloss_chain(t), sense_id=t['sense_id'],
                                             attested=t['attested']) for t in targets],
                exercises=exercises, closing=closing, review_status='automatic_draft')
    return unit, None


def build_units(corpus, learning):
    senses = [s for s in reading_senses(learning) if s in corpus.records]
    glosses = sorted({g for r in RULES for k in r['focus'] for g in [SHORT_GLOSS.get(k)] if g} |
                     {'mi', 'tu', 'su', 'nuestro', 'en', 'encima de', 'plural', 'yo', 'lo / la'})
    units, skipped = [], []
    for rule in RULES:
        unit, why = build_unit(rule, corpus, senses, glosses)
        (units if unit else skipped).append(unit or why)
    return units, skipped


# ---------------------------------------------------------------------------
# Validez automática
# ---------------------------------------------------------------------------
def check_evidence(corpus, ev, problems, where):
    row = corpus.rows.get(ev['archive_id'])
    if not row or row['iso'] != 'nci' or passage_hash(row) != ev['source_hash']:
        problems.append(f'{where}: el pasaje {ev["archive_id"]} cambió o no es clásico')
        return None
    if whole(ev['form'], row['nah']) < 0:
        problems.append(f'{where}: «{ev["form"]}» no está como palabra completa en {ev["archive_id"]}')
    a = corpus.analysis(ev['form'], ev['sense_id'])
    if not a or a['segmentation'] != ev['segmentation']:
        problems.append(f'{where}: el análisis de «{ev["form"]}» ya no es {ev["segmentation"]}')
    if loose_key(ev['form']) not in corpus.certain_keys(ev['sense_id']):
        problems.append(f'{where}: «{ev["form"]}» no es una grafía segura de {ev["sense_id"]}')
    if not ev['support'] or corpus.support(ev['sense_id'], row['es']) is None or ev['support'] not in row['es']:
        problems.append(f'{where}: la traducción de {ev["archive_id"]} no respalda {ev["sense_id"]}')
    return a


def check_exercise(corpus, ex, rule, problems):
    short = rule.get('short', SHORT)
    where = ex['id']
    analyses = [check_evidence(corpus, ev, problems, where) for ev in ex['evidence']]
    forms = {fold(ev['form']): a for ev, a in zip(ex['evidence'], analyses)}
    kind = ex['kind']
    if kind == 'match':
        if len(ex['pairs']) < 3 or len({fold(p['form']) for p in ex['pairs']}) != len(ex['pairs']) or len({p['gloss'] for p in ex['pairs']}) != len(ex['pairs']):
            problems.append(f'{where}: las parejas deben ser distintas')
        for p in ex['pairs']:
            a = forms.get(fold(p['form']))
            ev = next((e for e in ex['evidence'] if fold(e['form']) == fold(p['form'])), None)
            if not a or not ev or p['gloss'] != gloss_chain(dict(morphemes=[m for m in a['morphemes'] if m['surface'] or m['role'] == 'stem'],
                                                                   label=corpus.label(ev['sense_id']))):
                problems.append(f'{where}: la glosa de «{p["form"]}» no sale del análisis')
    elif kind == 'identify':
        a = forms.get(fold(ex['form']))
        m = a and next((m for m in a['morphemes'] if (m['slot'], m['key'], m['surface']) == (ex['morpheme']['slot'], ex['morpheme']['key'], ex['morpheme']['surface'])), None)
        if not m or (m['slot'], m['key']) not in rule['focus'] or ex['options'][ex['answer']] != short_gloss(m) or len(set(ex['options'])) != len(ex['options']):
            problems.append(f'{where}: la clave no es la glosa del morfema analizado')
    elif kind == 'build':
        a = forms.get(fold(ex['form']))
        pieces = [ex['tiles'][i] for i in ex['answer']]
        if not a or fold(''.join(pieces)) != fold(ex['form']) or pieces != [m['surface'] for m in a['morphemes'] if m['surface']] or len(set(ex['answer'])) != len(ex['answer']):
            problems.append(f'{where}: las fichas no reconstruyen la forma analizada')
        if not a or ex['gloss'] != gloss_chain(dict(morphemes=[m for m in a['morphemes'] if m['surface'] or m['role'] == 'stem'], label=corpus.label(ex['evidence'][0]['sense_id']))):
            problems.append(f'{where}: la consigna no sale del análisis')
    elif kind == 'cloze':
        row = corpus.rows.get(ex['archive_id'])
        if not row or ex['options'][ex['answer']] != ex['blank'] or ex['evidence'][0]['archive_id'] != ex['archive_id'] or ex['evidence'][0]['form'] != ex['blank'] \
                or len(re.findall(r'(?<![\w])' + re.escape(ex['blank']) + r'(?![\w])', row['nah'])) != 1 or len(words(row['nah'])) > short:
            problems.append(f'{where}: la clave debe ser la forma exacta del pasaje breve')
        sense = ex['evidence'][0]['sense_id']
        stems = {a['stem_key'] for a in analyses if a}
        if len(stems) != 1 or any(e['sense_id'] != sense for e in ex['evidence']) or len({fold(o) for o in ex['options']}) != 3 \
                or {fold(e['form']) for e in ex['evidence']} != {fold(o) for o in ex['options']}:
            problems.append(f'{where}: los distractores deben ser otras formas atestiguadas de la misma raíz')
    elif kind == 'translate':
        rows = [corpus.rows.get(i) for i in ex['option_ids']]
        if any(r is None or r['iso'] != 'nci' for r in rows) or ex['option_ids'][ex['answer']] != ex['archive_id'] \
                or ex['evidence'][0]['archive_id'] != ex['archive_id'] or len({fold(r['es']) for r in rows}) != len(rows) \
                or len(words(corpus.rows[ex['archive_id']]['nah'])) > short:
            problems.append(f'{where}: la respuesta debe ser la traducción de origen del pasaje breve')
    else:
        problems.append(f'{where}: tipo de ejercicio desconocido')


def check_unit(corpus, unit):
    """Lista de problemas de una unidad (vacía si cada clave está respaldada por pasaje y análisis)."""
    rule = next((r for r in RULES if r['id'] == unit['id']), None)
    problems = []
    if not rule:
        return [f'{unit["id"]}: regla desconocida']
    short = rule.get('short', SHORT)
    for ex in unit['exercises']:
        check_exercise(corpus, ex, rule, problems)
    for ev in unit['closing']['evidence']:
        check_evidence(corpus, ev, problems, unit['id'] + '-cierre')
    if len(words(corpus.rows.get(unit['closing']['archive_id'], {'nah': ''})['nah'])) > short:
        problems.append(unit['id'] + '-cierre: la lectura de cierre debe ser breve')
    if {e['kind'] for e in unit['exercises']} != {'match', 'identify', 'build', 'cloze', 'translate'}:
        problems.append(unit['id'] + ': faltan tipos de ejercicio')
    return problems


# ---------------------------------------------------------------------------
# Lecturas nuevas (recetas para lesson_builder)
# ---------------------------------------------------------------------------
def slug(text):
    return re.sub(r'[^a-z0-9]+', '-', fold(text)).strip('-')


def build_readings(corpus, learning, exclude):
    """Receta de ``READINGS`` lecturas nuevas: una palabra con glifo y cuatro pasajes breves por lectura."""
    records = corpus.records
    taught = set(reading_senses(learning))
    used = used_passages(learning) | exclude
    forms = defaultdict(set)
    for r in records.values():
        if r['kind'] == 'form':
            forms[r['sense_id']].add(r['written'].casefold())
    known = {fold(w) for ws in forms.values() for w in ws}
    glyphs = defaultdict(list)
    for r in records.values():
        if r['kind'] == 'glyph' and r.get('sense_id'):
            glyphs[r['sense_id']].append(r)

    def roots(row):
        """Acepciones del catálogo que el analizador encuentra en el pasaje (cobertura de raíces)."""
        out = set()
        for w in words(row['nah']):
            a = corpus.analyzer.analyze(w, limit=1)
            if a and a[0]['basis'] in ('dictionary', 'dictionary_truncated') and a[0]['class_'] not in ('particle', 'foreign'):
                out.update(d['sense_id'] for d in a[0]['dictionary'][:1])
        return out

    # Cada palabra con glifo y forma exacta del diccionario reúne sus pasajes breves aún no usados, ordenados por
    # cobertura de raíces (las ya enseñadas cuentan doble: el pasaje nuevo se lee con palabras conocidas).
    pools = []
    for sid, sense in sorted(records.items()):
        if sense['kind'] != 'sense' or sense.get('pos') != 'noun' or not glyphs[sid]:
            continue
        rows = []
        for o in corpus.occurrences(sid):
            row = corpus.rows[o['archive_id']]
            if o['words'] > READING_WORDS or o['archive_id'] in used or o['form'].casefold() not in forms[sid] or fold(o['form']) not in known:
                continue
            cover = roots(row)
            rows.append((-(len(cover & taught) * 2 + len(cover)), o['words'], row['line'], o, cover))
        rows.sort(key=lambda r: r[:3])
        if len({r[3]['archive_id'] for r in rows}) >= 4:
            pools.append((sid not in taught, len(rows), sid, rows))
    # Primero el vocabulario nuevo, luego las raíces con menos pasajes (para que todas alcancen cuatro).
    pools.sort(key=lambda p: (not p[0], p[1], p[2]))
    chosen, taken, candidates = [], set(), []
    for new_word, _, sid, rows in pools:
        picked, docs = [], Counter()
        for limit in (2, 4):
            for r in rows:
                rid = r[3]['archive_id']
                if len(picked) < 4 and rid not in taken and rid not in {p[3]['archive_id'] for p in picked} and docs[corpus.rows[rid]['document']] < limit:
                    picked.append(r)
                    docs[corpus.rows[rid]['document']] += 1
        candidates.append(dict(sense_id=sid, new_word=new_word, passages=len(rows), selected=len(picked)))
        if len(picked) == 4 and len(chosen) < READINGS:
            picked.sort(key=lambda r: r[:3])
            chosen.append((0, 0, sid, picked))
            taken.update(p[3]['archive_id'] for p in picked)
    lessons, ranking = [], []
    heads = {sid: corpus.headword(sid) for _, _, sid, _ in chosen}
    for n, (_, _, sid, picked) in enumerate(chosen):
        head, label = heads[sid].lower(), corpus.label(sid)
        cover = sorted(glyphs[sid], key=lambda g: (not g.get('image'), g['id']))[0]
        others = [heads[s] for s in sorted(heads) if s != sid and fold(heads[s]) != fold(head)]
        examples = []
        for i, (_, _, _, o, cov) in enumerate(picked):
            row = corpus.rows[o['archive_id']]
            annotations, last, target = [], -1, None
            for m in WORD.finditer(row['nah']):
                w = m.group(0)
                if m.start() < last:
                    continue
                if target is None and fold(w) == fold(o['form']):
                    target = w
                    annotations.append(dict(quote=w, relation='full_word', sense_id=sid,
                                            note=f'Palabra completa registrada en el diccionario: {head} «{label}». La traducción del registro '
                                                 f'dice «{o["support"]}». Ayuda generada automáticamente; pendiente de revisión.'))
                    last = m.end()
                    continue
                for tsid in sorted((taught & cov) - {sid}):
                    a = corpus.analysis(w, tsid)
                    if not a or a['class_'] in ('particle', 'foreign') or len(a['stem_key']) < 3 or loose_key(w) not in corpus.certain_keys(tsid):
                        continue
                    if w.casefold() in forms[tsid]:
                        annotations.append(dict(quote=w, relation='full_word', sense_id=tsid,
                                                note=f'Palabra completa registrada en el diccionario: {corpus.headword(tsid)} «{corpus.label(tsid)}». '
                                                     'Ayuda generada automáticamente; pendiente de revisión.'))
                    else:
                        annotations.append(dict(quote=w, relation='observed_form', sense_id=tsid,
                                                note=f'Forma del pasaje con la raíz de {corpus.headword(tsid)} «{corpus.label(tsid)}»; '
                                                     f'el analizador propone {a["segmentation"]}. Ayuda generada automáticamente; pendiente de revisión.'))
                    last = m.end()
                    break
            # Mismas mayúsculas que la palabra del hueco: la inicial no debe delatar la respuesta.
            case = (lambda d: d[:1].upper() + d[1:].lower()) if target[:1].isupper() else str.lower
            pool = [case(d) for d in others if fold(d) != fold(o['form'])]
            distractors = pool[i % max(1, len(pool) - 1):][:2]
            if len(distractors) < 2:
                distractors = pool[:2]
            wrong = [corpus.label(s) for s in sorted(heads) if s != sid and corpus.label(s) not in row['es']][:2]
            options = stable([o['support']] + wrong, o['archive_id'] + ':c')
            examples.append(dict(archive_id=o['archive_id'],
                                 context=f'Pasaje breve de {row["document"] or "obra no indicada"}, elegido automáticamente porque reúne '
                                         f'{head} con {len(cov)} raíces del diccionario. Contexto pendiente de revisión.',
                                 annotations=annotations, cloze=dict(blank=target, distractors=distractors),
                                 comprehension=dict(kind='meaning', question=f'¿Qué palabra de la traducción corresponde a «{o["form"]}»?',
                                                    options=options, answer=options.index(o['support']),
                                                    explanation=f'La traducción del archivo dice «{o["support"]}». Comprobación automática de procedencia; '
                                                                'la interpretación está pendiente de revisión.'),
                                 explore_words=[o['form']]))
            ranking.append(dict(lesson=f'gen-{slug(head)}', archive_id=o['archive_id'], words=o['words'], roots=sorted(cov), reading_roots=sorted(cov & taught)))
        lessons.append(dict(id=f'gen-{slug(head)}', title=f'Más pasajes con {head}' if sid in taught else f'Reconocer {head}',
                            objective=f'Leer {head} «{label}» en cuatro pasajes breves que aún no estaban en las lecturas; cada uno la reúne con otras palabras del diccionario.',
                            minutes=6, sense_ids=[sid], cover_glyph=cover['id'],
                            reading_tips=[f'Busca {head} como palabra completa; el diccionario la registra como «{label}».',
                                          'Las ayudas de esta lectura se generaron automáticamente desde el archivo y el analizador; están pendientes de revisión.'],
                            examples=examples))
    recipe = dict(schema_version=1, release_id=READINGS_ID, review_status='editorial_draft',
                  generated_by=dict(module='nahuatl_local.units', version=GENERATOR_VERSION, analyzer=ANALYZER_VERSION, llm_calls=0, network_requests=0),
                  note='Receta generada automáticamente: selección por cobertura de raíces y ayudas redactadas por plantilla. Solo se publica tras revisión.',
                  lessons=lessons, lesson_updates=[])
    return recipe, ranking, candidates


def annotations_has(annotations, relation):
    return any(a['relation'] == relation for a in annotations)


# ---------------------------------------------------------------------------
# Cola editorial y servicio
# ---------------------------------------------------------------------------
def findings(units, recipe):
    out = []

    def issue(fid, lesson_id, title, evidence, acceptance):
        f = dict(id=fid, priority='P1', lesson_id=lesson_id, title=title, evidence=evidence, acceptance=acceptance)
        f['fingerprint'] = fingerprint(f)
        out.append(f)
    for unit in units:
        issue(f'unit-{unit["id"]}-review', unit['id'], f'Revisar la unidad generada «{unit["title"]}»', unit,
              'Cotejar cada pasaje con su edición; revisar la regla, las glosas por partes, la segmentación de cada forma, los '
              'distractores y la lectura de cierre. Registrar revisor, fecha, evidencia y resolución con esta huella. '
              'La validación automática no sustituye esta revisión.')
    for lesson in recipe['lessons']:
        issue(f'generated-reading-{lesson["id"]}-review', lesson['id'], f'Revisar la lectura propuesta «{lesson["title"]}»', lesson,
              'Cotejar los cuatro pasajes, las ayudas redactadas por plantilla, el hueco, sus distractores y la comprensión. '
              'Si se acepta, publicarla con lesson_builder --apply sobre la propuesta; no editar el archivo generado a mano.')
    return out


def review_state(finding_list, decisions_path=DECISIONS):
    stored = json.loads(Path(decisions_path).read_text()) if Path(decisions_path).exists() else dict(schema_version=1, decisions={})
    if stored.get('schema_version') != 1 or not isinstance(stored.get('decisions'), dict):
        raise ValueError('Formato de decisiones inválido.')
    out = {}
    for item in merge_decisions(finding_list, stored['decisions']):
        d = item['decision']
        reviewed = item['status'] == 'resolved' and not item['review_stale']
        out[item['lesson_id']] = dict(status='reviewed' if reviewed else 'automatic_draft', task=item['id'], queue_status=item['status'],
                                      stale=item['review_stale'], reviewer=d.get('reviewer') if reviewed else None,
                                      date=d.get('date') if reviewed else None)
    return out


class Units:
    """Unidades servidas: validadas contra el análisis actual y con su estado en la cola editorial."""

    def __init__(self, terms, records_fn, path=UNITS, decisions=DECISIONS, recipe=RECIPE):
        self.terms, self.records_fn, self.path, self.decisions, self.recipe = terms, records_fn, Path(path), Path(decisions), Path(recipe)
        self._lock = Lock()
        self._corpus = None
        self._checked = None

    def corpus(self):
        with self._lock:
            if self._corpus is None:
                self._corpus = Corpus(self.terms, self.records_fn())
            return self._corpus

    def _validated(self):
        corpus = self.corpus()
        with self._lock:
            if self._checked is None:
                data = json.loads(self.path.read_text())
                if data.get('schema_version') != 1 or data.get('variant') != 'nci':
                    raise ValueError('Unidades inválidas.')
                units, report = [], []
                for unit in data['units']:
                    problems = check_unit(corpus, unit)
                    report.append(dict(id=unit['id'], exercises=len(unit['exercises']), problems=problems))
                    if not problems:
                        units.append(unit)
                self._checked = (data, units, report)
            return self._checked

    def catalog(self):
        data, units, report = self._validated()
        corpus = self.corpus()
        recipe = json.loads(self.recipe.read_text()) if self.recipe.exists() else dict(lessons=[])
        state = review_state(findings(data['units'], recipe), self.decisions)
        out = []
        for unit in units:
            u = copy.deepcopy(unit)
            u['review'] = state[u['id']]
            ids = {u['closing']['archive_id']} | {i for e in u['exercises'] for i in [e.get('archive_id')] + e.get('option_ids', []) if i}
            u['passages'] = {i: corpus.rows[i] for i in sorted(ids)}
            out.append(u)
        proposed = [dict(id=l['id'], title=l['title'], objective=l['objective'], review=state[l['id']],
                         passages=[corpus.rows[e['archive_id']] for e in l['examples']]) for l in recipe['lessons']]
        return dict(id=data['id'], version=data['version'], note=data['note'], generated_by=data['generated_by'], units=out,
                    proposed_readings=proposed, validation=dict(checked=len(report), served=len(units), report=report))

    def examples(self, sense_id, limit=3):
        """Ejemplos de concordancia para el repaso: formas distintas de la raíz en pasajes breves reales."""
        corpus = self.corpus()
        if sense_id not in corpus.records or corpus.records[sense_id]['kind'] != 'sense':
            raise KeyError(sense_id)
        occs = sorted(corpus.occurrences(sense_id), key=lambda o: (o['words'] > SHORT, o['form'].isupper(), o['words'], self_line(o)))
        out, signatures = [], set()
        for o in occs:
            if o['signature'] in signatures or o['words'] > SHORT * 2:
                continue
            signatures.add(o['signature'])
            row = corpus.rows[o['archive_id']]
            out.append(dict(archive_id=o['archive_id'], form=o['form'], segmentation=o['segmentation'], gloss=gloss_chain(o),
                            support=o['support'], nah=row['nah'], es=row['es'], document=row['document'], locator=row['locator'],
                            automatic=True))
            if len(out) == limit:
                break
        return dict(sense_id=sense_id, examples=out,
                    note='Concordancia automática: grafías seguras del índice de términos y glosa por partes del analizador; pendiente de revisión.')


# ---------------------------------------------------------------------------
# Generación, informe y comprobación
# ---------------------------------------------------------------------------
def coverage(units, skipped, recipe, ranking, candidates, learning, corpus, problems):
    senses = reading_senses(learning)
    taught_roots = sorted({s for u in units for s in u['sense_ids']})
    morphemes = sorted({(m['slot'], m['key']) for u in units for m in u['rule']['morphemes']})
    return dict(schema_version=1, generator=GENERATOR_VERSION, analyzer=ANALYZER_VERSION, llm_calls=0, network_requests=0,
                units=[dict(id=u['id'], title=u['title'], minutes=u['minutes'],
                            morphemes=[dict(slot=m['slot'], key=m['key'], surfaces=m['surfaces'], gloss=m['gloss']) for m in u['rule']['morphemes']],
                            roots=[dict(sense_id=s, headword=corpus.headword(s), label=corpus.label(s)) for s in u['sense_ids']],
                            forms=[w['form'] for w in u['words']], exercises=dict(Counter(e['kind'] for e in u['exercises'])),
                            passages=sorted({e['archive_id'] for x in u['exercises'] for e in x['evidence']} | {u['closing']['archive_id']}),
                            validity=dict(answers=len(u['exercises']) + 1, problems=problems.get(u['id'], [])))
                       for u in units],
                skipped=skipped,
                totals=dict(units=len(units), exercises=sum(len(u['exercises']) for u in units),
                            reading_roots=len(senses), reading_roots_in_units=len(set(taught_roots) & set(senses)),
                            roots_not_in_units=[s for s in senses if s not in taught_roots], morphemes=len(morphemes),
                            valid_answers=sum(len(u['exercises']) + 1 for u in units if not problems.get(u['id'])),
                            answers=sum(len(u['exercises']) + 1 for u in units)),
                readings=dict(release_id=recipe['release_id'], proposed=len(recipe['lessons']),
                              lessons_after_review=len(learning['lessons']) + len(recipe['lessons']),
                              lessons=[dict(id=l['id'], sense_id=l['sense_ids'][0], passages=[e['archive_id'] for e in l['examples']]) for l in recipe['lessons']],
                              passage_ranking=ranking, candidate_senses=candidates))


def markdown(cov):
    t = cov['totals']
    lines = ['# Unidades y lecturas generadas · cobertura y validez', '',
             f'Generador `{cov["generator"]}` · analizador `{cov["analyzer"]}` · sin modelo ni red. Todo es **borrador automático** '
             'hasta que la cola editorial registre revisor, fecha, evidencia y resolución.', '',
             f'**{t["units"]} unidades · {t["exercises"]} ejercicios · {t["valid_answers"]}/{t["answers"]} respuestas respaldadas** '
             f'(pasaje + análisis + grafía segura). Raíces de las lecturas presentes en unidades: {t["reading_roots_in_units"]}/{t["reading_roots"]}. '
             f'Morfemas enseñados: {t["morphemes"]}.', '',
             '| Unidad | Min | Morfemas | Raíces | Ejercicios | Pasajes |', '|---|---:|---|---|---|---:|']
    for u in cov['units']:
        lines.append(f"| {u['title']} | {u['minutes']} | {', '.join(m['gloss'].split(' (')[0] + ' (' + '/'.join(m['surfaces']) + ')' for m in u['morphemes'])} | "
                     f"{', '.join(r['headword'] for r in u['roots'])} | {', '.join(f'{k} {v}' for k, v in sorted(u['exercises'].items()))} | {len(u['passages'])} |")
    if cov['skipped']:
        lines += ['', '## Reglas sin material suficiente', '']
        lines += [f"- {s['id']}: {s['reason']} ({', '.join(f'{k} {v}' for k, v in s.items() if k not in ('id', 'reason'))})" for s in cov['skipped']]
    r = cov['readings']
    lines += ['', f'## Lecturas propuestas · {r["release_id"]}', '',
              f'{r["proposed"]} lecturas nuevas en la cola (de {r["lessons_after_review"] - r["proposed"]} a {r["lessons_after_review"]} si se aceptan). '
              'Pasajes ordenados por cobertura de raíces (las de las lecturas cuentan doble).', '',
              '| Lectura | Pasajes |', '|---|---|']
    lines += [f"| {l['id']} | {', '.join(l['passages'])} |" for l in r['lessons']]
    lines += ['', f'Sin cubrir por las unidades: {", ".join(t["roots_not_in_units"]) or "ninguna"}. '
              'Las glosas por partes vienen del analizador (pendiente de revisión especializada); no son traducciones.', '']
    return '\n'.join(lines)


def generate(terms=None, write=True):
    from .lesson_builder import build as build_readings_proposal
    from .lexicon import load_records
    from .terms import TermIndex
    records = load_records()
    corpus = Corpus(terms or TermIndex(), records)
    learning = json.loads(LEARNING.read_text())
    units, skipped = build_units(corpus, learning)
    problems = {u['id']: check_unit(corpus, u) for u in units}
    if any(problems.values()):
        raise ValueError('Unidad generada sin respaldo: ' + json.dumps(problems, ensure_ascii=False))
    exclude = {e['archive_id'] for u in units for x in u['exercises'] for e in x['evidence']} | {u['closing']['archive_id'] for u in units}
    recipe, ranking, candidates = build_readings(corpus, learning, exclude)
    data = dict(schema_version=1, id='unidades-v1', version=1, variant='nci', review_status='automatic_draft', note=DRAFT,
                generated_by=dict(module='nahuatl_local.units', version=GENERATOR_VERSION, analyzer=ANALYZER_VERSION, llm_calls=0, network_requests=0),
                units=units)
    queue = dict(schema_version=1, decisions=str(DECISIONS.relative_to(ROOT)), tasks=merge_decisions(findings(units, recipe),
                 json.loads(DECISIONS.read_text())['decisions'] if DECISIONS.exists() else {}))
    cov = coverage(units, skipped, recipe, ranking, candidates, learning, corpus, problems)
    files = {UNITS: encode(data), RECIPE: encode(recipe), QUEUE: encode(queue), COVERAGE: encode(cov), MARKDOWN: markdown(cov).encode()}
    with tempfile.TemporaryDirectory() as directory:
        # La propuesta de lecturas la valida y redacta lesson_builder (sin aplicar), igual que una receta a mano.
        tmp_recipe = Path(directory) / 'recipe.json'
        tmp_recipe.write_bytes(files[RECIPE])
        staging = ROOT / 'editorial' / f'.{READINGS_ID}-{sha(files[RECIPE])[:12]}.json'
        try:
            build_readings_proposal(tmp_recipe, staging)
            proof = json.loads(staging.read_text())
        finally:
            staging.unlink(missing_ok=True)
    proof['config_sha256'] = sha(files[RECIPE])
    files[PROPOSAL] = encode(proof)
    if write:
        for path, raw in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
    return files, cov


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--check', action='store_true', help='Falla si algún archivo generado no coincide con una generación nueva.')
    args = parser.parse_args(argv)
    files, cov = generate(write=not args.check)
    if args.check:
        stale = [str(p.relative_to(ROOT)) for p, raw in files.items() if not p.exists() or p.read_bytes() != raw]
        if stale:
            print('Generación desactualizada: ' + ', '.join(stale) + '. Ejecuta python3 -m nahuatl_local.units', file=sys.stderr)
            return 1
    print(json.dumps(cov['totals'] | dict(readings=cov['readings']['proposed']), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
