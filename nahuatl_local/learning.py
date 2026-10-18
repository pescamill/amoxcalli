"""Selección explícita para lectura; no infiere glosas ni corrige con un modelo."""
import copy
import hashlib
import json
import re
from .community import ROOT


class Learning:
    def __init__(self, archive, path=None):
        self.archive = archive
        self.data = json.loads((path or ROOT / 'corpus/learning-v1.json').read_text())
        if self.data.get('schema_version') != 1 or self.data.get('variant') != 'nci':
            raise ValueError('Ruta de aprendizaje inválida.')
        seen = set()
        for lesson in self.data['lessons']:
            if type(lesson.get('version', self.data['version'])) is not int or lesson.get('version', self.data['version']) < 1:
                raise ValueError('Versión de lección inválida.')
            if type(lesson.get('practice_version',lesson.get('version',self.data['version']))) is not int or lesson.get('practice_version',lesson.get('version',self.data['version']))<1:
                raise ValueError('Versión de práctica inválida.')
            if not lesson.get('examples'):
                raise ValueError('Una lectura necesita ejemplos.')
            if lesson['id'] in seen:
                raise ValueError('Lección duplicada.')
            seen.add(lesson['id'])
            for example in lesson['examples']:
                row = archive.get(example['archive_id'])
                digest = hashlib.sha256((row['nah'] + '\0' + row['es']).encode()).hexdigest()
                if row['iso'] != self.data['variant'] or digest != example['source_hash']:
                    raise ValueError('El ejemplo cambió o pertenece a otra ruta lingüística.')
                end = 0
                for annotation in example['annotations']:
                    if annotation.get('relation', 'full_word') not in ('full_word', 'observed_form', 'source_variant', 'thematic'):
                        raise ValueError('Relación de lectura inválida.')
                    start = row['nah'].find(annotation['quote'], end)
                    if annotation.get('relation') == 'full_word' and annotation['quote']:
                        match = re.compile(r'(?<!\w)' + re.escape(annotation['quote']) + r'(?!\w)').search(row['nah'], end)
                        if match is None and start >= 0:
                            raise ValueError('Una palabra completa no puede ser parte interna de otra forma.')
                        start = match.start() if match else -1
                    if start < 0 or not annotation['quote']:
                        raise ValueError('La anotación no corresponde al texto de la fuente.')
                    if annotation.get('relation')=='full_word' and ((start and (row['nah'][start-1].isalnum() or row['nah'][start-1]=='_')) or (start+len(annotation['quote'])<len(row['nah']) and (row['nah'][start+len(annotation['quote'])].isalnum() or row['nah'][start+len(annotation['quote'])]=='_'))):
                        raise ValueError('Una palabra completa no puede ser parte interna de otra forma.')
                    # Índices JS: la interfaz utiliza unidades UTF-16 para slice().
                    annotation['start'] = len(row['nah'][:start].encode('utf-16-le')) // 2
                    end = start + len(annotation['quote'])
                    annotation['end'] = len(row['nah'][:end].encode('utf-16-le')) // 2
                exercise = example['exercise']
                answer = exercise['answer']
                if (exercise['kind'] not in ('meaning', 'cloze') or type(answer) is not int
                        or not 0 <= answer < len(exercise['options'])
                        or len(set(exercise['options'])) != len(exercise['options'])):
                    raise ValueError('Clave de ejercicio inválida.')
                if exercise['kind'] == 'cloze' and (not exercise.get('blank') or exercise['blank'] not in row['nah']
                        or exercise['options'][answer] != exercise['blank']):
                    raise ValueError('La clave debe recuperar la forma exacta de la fuente.')
                words=example.get('explore_words',[])
                if not isinstance(words,list) or len(words)>12 or any(
                        not isinstance(word,str) or not word or len(word)>300 or word not in row['nah'] for word in words) or len(set(words))!=len(words):
                    raise ValueError('Las palabras para explorar deben conservar una forma del pasaje.')
                comprehension=example.get('comprehension')
                if comprehension is not None:
                    if not isinstance(comprehension,dict):raise ValueError('Pregunta de comprensión inválida.')
                    options=comprehension.get('options');key=comprehension.get('answer')
                    if (comprehension.get('kind')!='meaning' or not isinstance(options,list) or not 2<=len(options)<=5
                            or any(not isinstance(o,str) or not o.strip() for o in options) or len(set(options))!=len(options)
                            or type(key) is not int or not 0<=key<len(options)
                            or any(not isinstance(comprehension.get(k),str) or not comprehension[k].strip() for k in ('question','explanation'))
                            or options[key] not in row['es']):
                        raise ValueError('La comprensión necesita una respuesta citada de la traducción de origen.')

    def catalog(self, records):
        result = copy.deepcopy(self.data)
        visible = []
        if self.data['source_id'] in records:
            for lesson in result['lessons']:
                refs = set(lesson['sense_ids']) | {lesson['cover_glyph']}
                refs.update(a['sense_id'] for e in lesson['examples'] for a in e['annotations'])
                annotations=[a for e in lesson['examples'] for a in e['annotations']]
                refs.update(a['glyph_id'] for a in annotations if a.get('glyph_id'))
                if not refs.issubset(records):
                    continue
                cover=records[lesson['cover_glyph']]
                if cover['kind']!='glyph' or cover['sense_id'] not in lesson['sense_ids']:
                    raise ValueError('La portada necesita un glifo de una acepción objetivo.')
                if any(records[a['sense_id']]['kind'] != 'sense' or a.get('glyph_id') and (
                        records[a['glyph_id']]['kind'] != 'glyph' or records[a['glyph_id']]['sense_id'] != a['sense_id'])
                        for a in annotations):
                    raise ValueError('La referencia visual debe pertenecer a la acepción anotada.')
                for a in annotations:
                    if a.get('relation')=='full_word' and not any(r['kind']=='form' and r['sense_id']==a['sense_id'] and r['written'].casefold()==a['quote'].casefold() for r in records.values()):
                        raise ValueError('La palabra completa necesita una forma documentada de esa acepción.')
                for example in lesson['examples']:
                    example['passage'] = self.archive.get(example['archive_id'])
                visible.append(lesson)
        result['lessons'] = visible
        return result
