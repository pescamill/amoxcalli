import copy
from collections import Counter
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from nahuatl_local.community import ROOT, Problem
from nahuatl_local.editorial_pipeline import assemble as pipeline_assemble, encoded, lexical_priorities, prepare as pipeline_prepare, source_pages


BASELINE=ROOT/'reports/editorial-pipeline/batch-007/catalog-baseline.json'
LESSONS=ROOT/'tests/fixtures/learning/before-expansion-2026-09-30.json'


def prepare(*args,**kwargs):
    kwargs.setdefault('catalog_path',BASELINE)
    return pipeline_prepare(*args,**kwargs)


def assemble(*args,**kwargs):
    kwargs.setdefault('catalog_path',BASELINE)
    kwargs.setdefault('lessons_path',LESSONS)
    return pipeline_assemble(*args,**kwargs)


class EditorialPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(dir=ROOT/'reports',prefix='pipeline-test-')
        cls.batch=Path(cls.tmp.name)/'batch'
        cls.config=Path(cls.tmp.name)/'config.json';cls.config.write_bytes(encoded(dict(schema_version=1,gdn_prefixes=list('acehimnopqtxyz'),per_prefix=100,lexical_limit=50,concordance_limit=100)));cls.lessons=LESSONS
        cls.summary=prepare(cls.config,cls.lessons,cls.batch)

    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()

    def setUp(self):
        self.tmpout=tempfile.TemporaryDirectory(dir=ROOT/'editorial',prefix='pipeline-test-')
        self.output=Path(self.tmpout.name)/'reviewed.json'
        self.decisions=Path(self.tmpout.name)/'decisions.json'
        self.group=json.loads((self.batch/'review-groups.json').read_text())['groups'][0]
        self.accept=dict(status='accepted',fingerprint=self.group['fingerprint'],reviewer='Synthetic QA, not a linguistic review',date='2026-09-30',evidence=['Synthetic acceptance for mechanism only'],resolution='Test-only contextual comparison; no teaching release or training.')

    def tearDown(self):self.tmpout.cleanup()

    def decision(self,groups=None,items=None):
        self.decisions.write_bytes(encoded(dict(schema_version=1,groups=groups or {},items=items or {})))

    def test_repeat_is_identical_and_does_not_touch_sources_or_live_catalogue(self):
        private_fixture=Path(self.tmpout.name)/'private-sentinel.sqlite3'
        private_fixture.write_bytes(b'Synthetic private state; no live database dependency')
        paths=[self.lessons,ROOT/'corpus/axolotl/axolotl.csv',ROOT/'editorial/lesson-decisions.json',private_fixture]
        before={p:p.read_bytes() for p in paths if p.exists()}
        self.assertEqual(prepare(self.config,self.lessons,self.batch)['state'],'unchanged')
        self.assertEqual(before,{p:p.read_bytes() for p in before})
        self.assertEqual((self.summary['llm_calls'],self.summary['network_requests']),(0,0))
        self.assertEqual(self.summary['lessons'],3)
        concordance=json.loads((self.batch/'concordances.json').read_text())
        self.assertEqual(len(concordance['candidates']),100)
        for c in concordance['candidates']:
            self.assertFalse(c['rights_training'])
            self.assertEqual(c['status'],'candidate')
            self.assertNotIn('definition',c)
            self.assertTrue(all('heldout' in e for e in c['evidence']))
        next_source=json.loads((self.batch/'next-source-config.json').read_text())
        self.assertLessEqual(len(next_source['gdn_prefixes']),8)

    def test_group_acceptance_assembles_without_import_or_training(self):
        self.decision({self.group['id']:self.accept})
        result=assemble(self.batch,self.decisions,self.output)
        self.assertFalse(result['imported']);self.assertFalse(result['training'])
        baseline={r['id'] for r in json.loads((self.batch/'catalog-baseline.json').read_text())['records']}
        bundle=json.loads(self.output.read_text())
        self.assertTrue(bundle['records'])
        for r in bundle['records']:
            self.assertNotIn(r['id'],baseline)
            self.assertFalse(r['rights']['training'])
            self.assertEqual(r['glyph_status'],'proposed')
        with self.assertRaises(FileExistsError):assemble(self.batch,self.decisions,self.output)

    def test_stale_or_incomplete_acceptance_and_item_exceptions_fail_closed(self):
        bad=copy.deepcopy(self.accept);bad['fingerprint']='obsolete'
        self.decision({self.group['id']:bad})
        with self.assertRaises(ValueError):assemble(self.batch,self.decisions,self.output)
        bad=copy.deepcopy(self.accept);bad['evidence']=[]
        self.decision({self.group['id']:bad})
        with self.assertRaises(ValueError):assemble(self.batch,self.decisions,self.output)
        iid,digest=next(iter(self.group['item_fingerprints'].items()))
        self.decision({self.group['id']:self.accept},{iid:dict(status='rejected',fingerprint=digest)})
        with self.assertRaisesRegex(ValueError,'No hay candidatos'):assemble(self.batch,self.decisions,self.output)
        self.assertFalse(self.output.exists())

    def test_edited_batch_or_changed_catalogue_is_rejected(self):
        changed=Path(self.tmpout.name)/'batch';shutil.copytree(self.batch,changed)
        (changed/'draft-bundle.json').write_text('{}')
        self.decision({self.group['id']:self.accept})
        with self.assertRaisesRegex(ValueError,'modificado'):assemble(changed,self.decisions,self.output)
        baseline=json.loads((self.batch/'catalog-baseline.json').read_text());baseline['records'][0]['notes']='Changed catalogue snapshot'
        catalog=Path(self.tmpout.name)/'catalog.json';catalog.write_bytes(encoded(baseline))
        with self.assertRaisesRegex(ValueError,'cambiaron'):assemble(self.batch,self.decisions,self.output,catalog_path=catalog)

    def test_missing_cache_empty_results_and_changed_source_format_are_distinct(self):
        with tempfile.TemporaryDirectory() as directory,patch('nahuatl_local.editorial_pipeline.ROOT',Path(directory)):
            config=dict(gdn_prefixes=['x'],per_prefix=100)
            pages,metadata,requests=source_pages(config)
            self.assertEqual(pages,[]);self.assertEqual(metadata[0]['state'],'missing_cache');self.assertEqual(requests,0)
            cache=Path(directory)/'data/dictionary-cache';cache.mkdir(parents=True)
            file=cache/'molina2-x-100.html';file.write_text('<article class="terminos">\n No se han encontrado registros</article>')
            self.assertEqual(source_pages(config)[1][0]['records'],0)
            file.write_text('var mydata = [unexpected]; <article class="terminos">No se han encontrado registros</article>')
            with self.assertRaises(ValueError):source_pages(config)
            file.write_text('Unexpected server response')
            with self.assertRaises(ValueError):source_pages(config)

    def test_existing_output_and_protected_paths_are_never_overwritten(self):
        marker=self.batch/'README.md';before=marker.read_bytes()
        different=Path(self.tmpout.name)/'config.json';config=json.loads(self.config.read_text());config['concordance_limit']=10;different.write_bytes(encoded(config))
        with self.assertRaises(ValueError):prepare(different,self.lessons,self.batch)
        self.assertEqual(marker.read_bytes(),before)
        with self.assertRaises(ValueError):prepare(self.config,self.lessons,ROOT/'corpus')

    def test_catalog_normalized_head_does_not_replace_written_form_for_priority(self):
        forms={'synthetic-one':dict(written='NIqa',catalog_normalized='qa'),'synthetic-two':dict(written='other',catalog_normalized='other')}
        items=lexical_priorities(forms,Counter(qa=1000,other=2),{'qa'})
        self.assertEqual(items[0]['sense_id'],'synthetic-two')
        candidate=items[1]
        self.assertEqual(candidate['exact_corpus_occurrences'],0)
        self.assertEqual(candidate['catalog_head_occurrences'],1000)
        self.assertFalse(candidate['in_current_lessons'])
        self.assertTrue(candidate['catalog_head_differs'])

    def test_batch_group_dependencies_and_fetch_receipt_do_not_break_repeatability(self):
        raw=b"var mydata = [{pk:'9999999',paleografia:'syntheticqa',grafiaNormalizada:'syntheticqa',traduccion:'flor',fuente:'1571 Molina 2'}];"
        pages=([(raw,'https://gdn.iib.unam.mx/termino/search')],[dict(state='cached',records=1)],1)
        batch=Path(self.tmp.name)/'synthetic-batch'
        with patch('nahuatl_local.editorial_pipeline.source_pages',return_value=pages):prepare(self.config,self.lessons,batch)
        with patch('nahuatl_local.editorial_pipeline.source_pages',return_value=(pages[0],pages[1],0)):
            self.assertEqual(prepare(self.config,self.lessons,batch)['state'],'unchanged')
        groups=json.loads((batch/'review-groups.json').read_text())['groups']
        accepted={g['id']:dict(self.accept,fingerprint=g['fingerprint']) for g in groups}
        visual=next(g for g in groups if g['kind']=='contextual_visual')
        self.decision({visual['id']:accepted[visual['id']]})
        with self.assertRaises(Problem):assemble(batch,self.decisions,self.output)
        self.decision(accepted)
        self.assertEqual(assemble(batch,self.decisions,self.output)['records'],4)


if __name__=='__main__':unittest.main()
