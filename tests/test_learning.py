import copy
import json
from pathlib import Path
import tempfile
import unittest
from nahuatl_local.community import ROOT, Problem
from nahuatl_local.corpus import CorpusStore
from nahuatl_local.learning import Learning
from nahuatl_local.research import Archive


class LearningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = Archive()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'corpus.sqlite3'
        self.store = CorpusStore(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def load_changed(self, change):
        data=json.loads((ROOT/'corpus/learning-v1.json').read_text())
        change(data)
        path=Path(self.tmp.name)/'lessons.json';path.write_text(json.dumps(data))
        return Learning(self.archive,path)

    def test_selected_passages_preserve_original_and_only_classical(self):
        data=Learning(self.archive).catalog(self.store.public_records())
        self.assertEqual(len(data['lessons']),12)
        ids=[]
        for lesson in data['lessons']:
            for e in lesson['examples']:
                ids.append(e['archive_id'])
                self.assertEqual(e['passage'],self.archive.get(e['archive_id']))
                self.assertEqual(e['passage']['iso'],'nci')
                for a in e['annotations']:
                    raw=e['passage']['nah'].encode('utf-16-le')
                    self.assertEqual(raw[a['start']*2:a['end']*2].decode('utf-16-le'),a['quote'])
        self.assertEqual(len(set(ids)),48)
        self.assertEqual(data['review_status'],'editorial_draft')

    def test_changed_source_mixed_variant_bad_span_and_answer_fail_closed(self):
        changes=[lambda d:d['lessons'][0]['examples'][0].update(source_hash='obsolete'),
                 lambda d:d['lessons'][0]['examples'][0]['annotations'][0].update(quote='not in source'),
                 lambda d:d['lessons'][0]['examples'][0]['exercise'].update(answer=999),
                 lambda d:d['lessons'][0]['examples'][0]['exercise'].update(kind='free_model'),
                 lambda d:d.update(variant='azz')]
        for change in changes:
            with self.subTest(change=change),self.assertRaises(ValueError):self.load_changed(change)

    def test_complete_word_search_skips_earlier_internal_occurrence(self):
        learning=Learning(self.archive)
        lesson=next(l for l in learning.data['lessons'] if l['id']=='fuego-viento')
        example=lesson['examples'][0]
        row=self.archive.get(example['archive_id'])
        annotation=example['annotations'][0]
        self.assertEqual(row['id'],'axolotl-05345')
        self.assertIn('tletlalito',row['nah'])
        self.assertGreater(annotation['start'],row['nah'].index('tletlalito'))
        raw=row['nah'].encode('utf-16-le')
        self.assertEqual(raw[annotation['start']*2:annotation['end']*2].decode('utf-16-le'),'tletl')
        # A preceding thematic annotation may end inside the first word. Searching
        # the original string retains its left boundary and finds the later word.
        def change(data):
            e=next(l for l in data['lessons'] if l['id']=='fuego-viento')['examples'][0]
            e['annotations'].insert(0,dict(quote='tle',sense_id='sense-tletl',relation='thematic',note='Synthetic boundary test.'))
        changed=self.load_changed(change)
        e=next(l for l in changed.data['lessons'] if l['id']=='fuego-viento')['examples'][0]
        self.assertEqual(e['annotations'][1]['start'],annotation['start'])

    def test_new_readings_preserve_every_existing_lesson_and_comprehension(self):
        before=json.loads((ROOT/'reports/learning-before-lecturas-003-2026-10-07/learning-v1.json').read_text())
        current=json.loads((ROOT/'corpus/learning-v1.json').read_text())
        self.assertEqual(current['lessons'][:len(before['lessons'])],before['lessons'])
        self.assertEqual([l['id'] for l in current['lessons'][6:]],
                         ['casas-relatos','animales-relatos','piedra-lena','arboles-cerros','fuego-viento','sol-luna'])
        for lesson in current['lessons'][6:]:
            self.assertEqual(lesson['version'],1)
            self.assertEqual(len(lesson['examples']),4)
            for example in lesson['examples']:
                q=example['comprehension'];row=self.archive.get(example['archive_id'])
                self.assertIn(q['options'][q['answer']],row['es'])

    def test_private_or_withdrawn_dependency_hides_lesson(self):
        learning=Learning(self.archive)
        records=self.store.public_records()
        records.pop('sense-xochitl')
        self.assertNotIn('flor',{l['id'] for l in learning.catalog(records)['lessons']})
        records.pop('src-axolotl')
        self.assertEqual(learning.catalog(records)['lessons'],[])

    def test_dictionary_expands_with_cited_images_without_training_grants(self):
        bundle=json.loads((ROOT/'corpus/glyph-lexicon-v5.json').read_text())
        senses=[r for r in bundle['records'] if r['kind']=='sense']
        self.assertEqual(len(senses),12)
        for sense in senses:
            glyph=next(g for g in bundle['records'] if g['kind']=='glyph' and g['sense_id']==sense['id'])
            self.assertTrue(glyph['image'].startswith('https://aztecglyphs.wired-humanities.org/'))
            self.assertTrue(glyph['manuscript_url'].startswith('https://digital.bodleian.ox.ac.uk/'))
            self.assertEqual(glyph['evidence'][0]['status'],'catalog_checked')
            self.assertEqual(glyph['glyph_status'],'proposed')
            self.assertFalse(glyph['rights']['training'])
        self.assertEqual(self.store.records()['glyph-tletl-mdz13r']['glyph_type'],'iconography')
        self.assertEqual(CorpusStore(self.path).records(),self.store.records())

    def test_image_migration_preserves_local_image_credit_and_context(self):
        r=self.store.records()['glyph-metztli-osu14v']
        r.update(image='https://example.org/local-image.png',image_credit='Crédito de la edición local',context='Contexto editado localmente',expected_version=r['version'])
        self.store.import_bundle(dict(schema_version=1,records=[r]),'QA','Edición local')
        with self.store.db() as db:db.execute("DELETE FROM corpus_meta WHERE key='glyph-source-images-v5'")
        after=CorpusStore(self.path).records()[r['id']]
        for field in ('image','image_credit','context'):self.assertEqual(after[field],r[field])
        self.assertEqual(after['version'],r['version']+1)

    def test_provenance_link_and_glyph_type_validation(self):
        recs=self.store.records()
        for field,value in [('manuscript_url','javascript:alert(1)'),('glyph_type','automatic_translation')]:
            r=copy.deepcopy(recs['glyph-tetl-mdz48r']);r[field]=value
            with self.assertRaises(Problem):self.store.validate(r,recs)

    def test_cloze_rejects_wrong_source_form_and_glyph_rejects_wrong_meaning(self):
        with self.assertRaises(ValueError):
            self.load_changed(lambda d:d['lessons'][0]['examples'][1]['exercise'].update(answer=0))
        with self.assertRaises(ValueError):
            self.load_changed(lambda d:d['lessons'][0]['examples'][0]['annotations'][0].update(relation='inferred_translation'))
        learning=self.load_changed(lambda d:d['lessons'][0]['examples'][0]['annotations'][0].update(glyph_id='glyph-xochitl'))
        with self.assertRaises(ValueError):learning.catalog(self.store.public_records())
        records=self.store.public_records();records.pop('glyph-cacahuaxochitl-mh885v')
        self.assertNotIn('flor',{l['id'] for l in Learning(self.archive).catalog(records)['lessons']})

    def test_complete_words_require_matching_forms_and_preserve_practice_editions(self):
        learning=self.load_changed(lambda d:d['lessons'][0]['examples'][0]['annotations'][1].update(sense_id='sense-atl',glyph_id='glyph-atl'))
        with self.assertRaisesRegex(ValueError,'forma documentada'):learning.catalog(self.store.public_records())
        with self.assertRaisesRegex(ValueError,'Versión de práctica'):
            self.load_changed(lambda d:d['lessons'][1].update(practice_version=0))
        with self.assertRaisesRegex(ValueError,'parte interna'):
            self.load_changed(lambda d:d['lessons'][0]['examples'][2]['annotations'][0].update(quote='xochitl',sense_id='sense-xochitl'))

    def test_context_questions_quote_the_original_translation_and_keep_recognition(self):
        before=json.loads((ROOT/'reports/learning-before-reading-context-2026-10-07/learning-v1.json').read_text())
        current=Learning(self.archive).data
        for old,new in zip(before['lessons'],current['lessons']):
            self.assertEqual([(e['archive_id'],e['source_hash'],e['exercise']) for e in old['examples']],
                             [(e['archive_id'],e['source_hash'],e['exercise']) for e in new['examples']])
        aves=next(l for l in current['lessons'] if l['id']=='aves')
        self.assertEqual((aves['version'],aves['practice_version']),(2,1))
        for example in aves['examples']:
            question=example['comprehension'];row=self.archive.get(example['archive_id'])
            self.assertIn(question['options'][question['answer']],row['es'])
            self.assertTrue(all(word in row['nah'] for word in example['explore_words']))
        changes=[lambda e:e['comprehension'].update(answer=True),
                 lambda e:e['comprehension'].update(options=['Una traducción inventada.','Otra invención.']),
                 lambda e:e.update(explore_words=['palabra ausente']),
                 lambda e:e.update(explore_words=[{}]),
                 lambda e:e.update(comprehension=[])]
        for change in changes:
            with self.subTest(change=change),self.assertRaises(ValueError):
                self.load_changed(lambda d:change(next(l for l in d['lessons'] if l['id']=='aves')['examples'][0]))

    def test_flor_update_is_append_only_preserves_passages_and_other_lessons(self):
        original=json.loads((ROOT/'reports/learning-audit-before-flor-v2/learning-v1.json').read_text())
        current=Learning(self.archive).data
        self.assertEqual(current['lessons'][0]['version'],2)
        for old,new in zip(original['lessons'],current['lessons']):
            self.assertEqual([(e['archive_id'],e['source_hash']) for e in old['examples']],
                             [(e['archive_id'],e['source_hash']) for e in new['examples']])
        # Remove computed display offsets before comparing the unedited lessons.
        for lesson in current['lessons']:
            for example in lesson['examples']:
                for a in example['annotations']:a.pop('start');a.pop('end')
        snapshot=json.loads((ROOT/'reports/learning-before-expansion-2026-09-30/learning-v1.json').read_text())
        self.assertEqual(snapshot['lessons'][1:],original['lessons'][1:])
        for old,new in zip(snapshot['lessons'],current['lessons']):
            self.assertEqual([e['exercise'] for e in old['examples']],[e['exercise'] for e in new['examples']])
        self.assertEqual(current['lessons'][1]['practice_version'],1)
        bundle=json.loads((ROOT/'corpus/flor-lexicon-v8.json').read_text())
        self.assertEqual(len(bundle['records']),5)
        self.assertTrue(all(not r['rights']['training'] for r in bundle['records']))
        form=self.store.records()['lex-cuicatl']
        self.assertEqual((form['written'],form['catalog_normalized'],form['historical_gloss']),('Cuicatl','cuicatl','canto, o cancion.'))
        r=self.store.records()['lex-cacahuaxochitl'];r.update(notes='Edición local conservada',expected_version=r['version'])
        self.store.import_bundle(dict(schema_version=1,records=[r]),'QA','Prueba de conservación')
        with self.store.db() as db:db.execute("DELETE FROM corpus_meta WHERE key LIKE 'flor-v8-%'")
        self.assertEqual(CorpusStore(self.path).records()[r['id']]['notes'],'Edición local conservada')
