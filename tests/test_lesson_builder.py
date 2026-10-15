import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from nahuatl_local.community import ROOT
from nahuatl_local.editorial_pipeline import encoded
from nahuatl_local.lesson_builder import build
from nahuatl_local.learning import Learning
from nahuatl_local.research import Archive


class LessonBuilderTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=ROOT/'editorial',prefix='lesson-test-')
        self.root=Path(self.tmp.name);self.output=self.root/'proposal.json'
        self.base=ROOT/'tests/fixtures/learning/before-expansion-2026-09-30.json'
        self.config=ROOT/'configs/learning-expansion-2026-09-30.json'

    def tearDown(self):self.tmp.cleanup()

    def test_batch_preserves_sources_keys_and_generates_exact_cloze_options(self):
        originals={p:p.read_bytes() for p in (self.base,ROOT/'corpus/axolotl/axolotl.csv')}
        result=build(self.config,self.output,self.base)
        self.assertEqual((result['added_lessons'],result['added_examples']),(3,12))
        before=self.output.read_bytes();build(self.config,self.output,self.base);self.assertEqual(self.output.read_bytes(),before)
        data=json.loads(before)['learning'];old=json.loads(self.base.read_text())
        for a,b in zip(old['lessons'],data['lessons']):
            self.assertEqual([(e['archive_id'],e['source_hash'],e['exercise']) for e in a['examples']],[(e['archive_id'],e['source_hash'],e['exercise']) for e in b['examples']])
        self.assertEqual(data['lessons'][1]['practice_version'],1)
        self.assertEqual(data['lessons'][2]['examples'][1]['annotations'][0]['relation'],'thematic')
        path=self.root/'learning.json';path.write_bytes(encoded(data));validated=Learning(Archive(),path)
        self.assertEqual(len(validated.data['lessons']),6)
        self.assertEqual(originals,{p:p.read_bytes() for p in originals})
        for lesson in data['lessons'][3:]:
            for e in lesson['examples']:
                ex=e['exercise'];self.assertEqual(ex['options'][ex['answer']],ex['blank'])

    def test_second_expansion_keeps_all_six_existing_lessons_intact(self):
        base=ROOT/'tests/fixtures/learning/before-lecturas-003-2026-10-07.json'
        config=ROOT/'configs/learning-expansion-2026-10-07.json'
        sentinel=self.root/'private-sentinel.sqlite3';sentinel.write_bytes(b'Synthetic private state; never opened by builder')
        before=sentinel.read_bytes()
        result=build(config,self.output,base)
        data=json.loads(self.output.read_text())['learning']
        self.assertEqual((result['added_lessons'],result['added_examples']),(6,24))
        self.assertEqual(data['lessons'][:6],json.loads(base.read_text())['lessons'])
        self.assertEqual(data,json.loads((ROOT/'corpus/learning-v1.json').read_text()))
        self.assertEqual(sentinel.read_bytes(),before)

    def test_duplicate_passages_unknown_forms_and_wrong_visual_dependencies_fail(self):
        recipes=json.loads(self.config.read_text())
        changes=[lambda c:c['lessons'][0].update(cover_glyph='glyph-xochitl'),lambda c:c['lessons'][0]['examples'][0].update(archive_id='axolotl-05338'),lambda c:c['lessons'][0]['examples'][0]['cloze'].update(distractors=['not_a_dictionary_form','xochitl']),lambda c:c['lessons'][0]['examples'][0]['annotations'][0].update(glyph_id='glyph-xochitl'),lambda c:c['lessons'][0]['examples'][0]['annotations'][0].update(sense_id='sense-xochitl')]
        for change in changes:
            altered=copy.deepcopy(recipes);change(altered);path=self.root/'recipes.json';path.write_bytes(encoded(altered))
            with self.assertRaises(ValueError):build(path,self.output,self.base)
            self.assertFalse(self.output.exists())

    def test_apply_is_reversible_and_repeat_does_not_reset_practice(self):
        base=self.root/'corpus/learning-v1.json';base.parent.mkdir();base.write_bytes(self.base.read_bytes())
        output=self.root/'editorial/proposal.json'
        with patch('nahuatl_local.lesson_builder.ROOT',self.root):
            self.assertEqual(build(self.config,output,base,apply=True)['state'],'published')
            before=base.read_bytes();self.assertEqual(build(self.config,output,base,apply=True)['state'],'already_published')
            self.assertEqual(base.read_bytes(),before)
        backup=self.root/'reports/learning-before-lecturas-002/learning-v1.json'
        self.assertEqual(backup.read_bytes(),self.base.read_bytes())
        self.assertEqual(json.loads(before)['lessons'][0]['version'],2)
        self.assertEqual(json.loads(before)['lessons'][1]['practice_version'],1)

    def test_context_recipe_adds_source_backed_questions_without_replacing_old_keys(self):
        base=ROOT/'tests/fixtures/learning/before-reading-context-2026-10-07.json'
        config=ROOT/'configs/reading-context-2026-10-07.json'
        result=build(config,self.output,base)
        self.assertEqual(result['added_examples'],0)
        self.assertEqual(result['clarified_lessons'],['aves'])
        data=json.loads(self.output.read_text())['learning']
        self.assertEqual(data,json.loads((ROOT/'tests/fixtures/learning/before-lecturas-003-2026-10-07.json').read_text()))
        recipes=json.loads(config.read_text())
        recipes['lesson_updates'][0]['example_updates'][0]['exercise']={}
        altered=self.root/'altered.json';altered.write_bytes(encoded(recipes))
        with self.assertRaises(ValueError):build(altered,self.root/'bad.json',base)


if __name__=='__main__':unittest.main()
