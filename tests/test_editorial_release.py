import copy
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from nahuatl_local.community import ROOT
from nahuatl_local.corpus import CorpusStore, editorial_releases
from nahuatl_local.editorial_pipeline import assemble, encoded, sha
from nahuatl_local.editorial_release import publish, run, snapshot, verify


class EditorialReleaseTests(unittest.TestCase):
    def setUp(self):
        self.batch=ROOT/'reports/editorial-pipeline/batch-007'
        self.pages=pages=json.loads((self.batch/'sources.json').read_text())['pages']
        if not all((ROOT/'data/dictionary-cache'/f"molina2-{page['prefix']}-500.html").is_file() for page in pages):
            # Páginas GDN/Molina cacheadas localmente; no se distribuyen con el repositorio.
            self.skipTest('Falta la caché local data/dictionary-cache/ del lote 007.')
        self.tmp=tempfile.TemporaryDirectory(dir=ROOT/'editorial',prefix='release-test-')
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.baseline=self.batch/'catalog-baseline.json'
        self.check=self.root/'source-check.json';self.bundle=self.root/'accepted.json'
        # Reproduce this historical batch independently of later distributed releases.
        self.releases_patch=patch('nahuatl_local.corpus.editorial_releases',return_value=[])
        self.releases_patch.start()
        self.addCleanup(self.releases_patch.stop)
        self.db=self.root/'private.sqlite3';self.store=CorpusStore(self.db)
        for name in ('corpus/axolotl/axolotl.csv','corpus/glyph-link-rules-v7.json','corpus/learning-v1.json'):
            dest=self.root/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name if name!='corpus/learning-v1.json' else ROOT/'tests/fixtures/learning/before-expansion-2026-09-30.json',dest)

        for page in pages:
            dest=self.root/'data/dictionary-cache'/f"molina2-{page['prefix']}-500.html"
            dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/'data/dictionary-cache'/dest.name,dest)

    def accepted(self):
        verify(self.batch,self.check,date='2026-09-30')
        assemble(self.batch,self.check,self.bundle,catalog_path=self.baseline,lessons_path=ROOT/'tests/fixtures/learning/before-expansion-2026-09-30.json')

    def apply(self,rid='test-batch'):
        with patch('nahuatl_local.editorial_release.ROOT',self.root):
            return publish(self.batch,self.bundle,rid,self.db)

    def test_literal_source_check_accepts_only_limited_scope_and_repeats(self):
        result=verify(self.batch,self.check,date='2026-09-30')
        self.assertEqual(result['states'],dict(accepted=89))
        self.assertEqual(verify(self.batch,self.check)['state'],'unchanged')
        report=json.loads(self.check.read_text())
        self.assertFalse(report['primary_review']);self.assertFalse(report['linguistic_certification'])
        self.assertEqual((report['llm_calls'],report['network_requests']),(0,0))
        self.assertTrue(all(c['proof'] for c in report['checks']))
        with self.assertRaises(ValueError):verify(self.batch,ROOT/'corpus/source-check.json')

    def test_changed_cache_is_deferred_and_never_accepted_as_exact(self):
        for page in self.pages:
            dest=self.root/'data/dictionary-cache'/f"molina2-{page['prefix']}-500.html"
            dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/'data/dictionary-cache'/dest.name,dest)
        for dest in (self.root/'data/dictionary-cache').iterdir():dest.write_bytes(dest.read_bytes()+b'changed')
        dest=self.root/'editorial/check.json'
        with patch('nahuatl_local.editorial_release.ROOT',self.root):result=verify(self.batch,dest)
        checks=json.loads(dest.read_text())['checks']
        self.assertEqual(sum('changed_cache' in c['errors'] for c in checks),50)
        self.assertGreaterEqual(result['states']['deferred'],50)
        self.assertTrue(any('lexical_dependency_not_accepted' in c['errors'] for c in checks))

    def test_publication_preserves_private_data_edits_and_repeats_without_duplicates(self):
        self.accepted()
        person,token=self.store.save_profile(dict(alias='Synthetic QA',variant_id='inali-04',own_name='',community='',experience='childhood',historical='none',participation_consent=True))
        r=copy.deepcopy(self.store.records()['sense-atl']);r['notes']='Local QA note';r['expected_version']=r['version']
        self.store.import_bundle(dict(schema_version=1,records=[r]),'QA','Preservation test')
        with self.store.db() as db:before=snapshot(db)
        result=self.apply();self.assertEqual(result['added_records'],139)
        self.assertTrue(all(result['tables_preserved'].values()));self.assertFalse(result['training_changed'])
        self.assertEqual(Path(result['backup']).stat().st_mode&0o777,0o600)
        again=self.apply();self.assertEqual(again['state'],'already_published')
        self.assertEqual(self.store.person(token)['id'],person['id'])
        self.assertEqual(self.store.records()['sense-atl']['notes'],'Local QA note')
        with self.store.db() as db:after=snapshot(db)
        for table in before:
            self.assertTrue(all(r in after[table] for r in before[table]))
        manifest=self.root/'corpus/editorial-releases.json'
        releases=editorial_releases(manifest);self.assertEqual(len(releases),1)
        # New installations load the same release, without needing source caches.
        with patch('nahuatl_local.corpus.editorial_releases',return_value=releases):fresh=CorpusStore(self.root/'fresh.sqlite3')
        self.assertEqual(len(fresh.records()),len(self.store.records()))
        for r in json.loads(self.bundle.read_text())['records']:
            self.assertEqual({k:v for k,v in fresh.records()[r['id']].items() if k!='version'},r)

    def test_modified_bundle_dependency_and_source_rules_stop_before_backup(self):
        self.accepted();original=self.bundle.read_bytes()
        changed=json.loads(original);changed['records'][0]['label']='Invented definition';self.bundle.write_bytes(encoded(changed))
        with self.assertRaisesRegex(ValueError,'difiere'):self.apply()
        self.bundle.write_bytes(original)
        rules=self.root/'corpus/glyph-link-rules-v7.json';rules.write_bytes(rules.read_bytes()+b' ')
        with self.assertRaisesRegex(ValueError,'Cambió'):self.apply()
        shutil.copyfile(ROOT/'corpus/glyph-link-rules-v7.json',rules)
        r=copy.deepcopy(self.store.records()['glyph-xochitl']);r['context']='Changed local evidence';r['expected_version']=r['version']
        self.store.import_bundle(dict(schema_version=1,records=[r]),'QA','Changed dependency test')
        with self.assertRaisesRegex(ValueError,'dependencia'):self.apply()
        self.assertFalse((self.root/'data/backups').exists())

    def test_interrupted_registration_resumes_from_private_backup(self):
        self.accepted()
        real_replace=Path.replace
        def interrupt(path,target):
            if Path(target).name=='editorial-releases.json':raise OSError('Synthetic interrupted registration')
            return real_replace(path,target)
        with patch.object(Path,'replace',interrupt),self.assertRaises(OSError):self.apply()
        self.assertFalse((self.root/'corpus/editorial-releases.json').exists())
        with self.store.db() as db:committed=snapshot(db)
        result=self.apply();self.assertEqual(result['added_records'],139)
        with self.store.db() as db:self.assertEqual(snapshot(db),committed)
        self.assertEqual(len(editorial_releases(self.root/'corpus/editorial-releases.json')),1)

    def test_one_command_cycle_is_bounded_resumable_and_requires_apply(self):
        registry=lambda manifest=None:editorial_releases(manifest or self.root/'corpus/editorial-releases.json')
        with patch('nahuatl_local.editorial_release.ROOT',self.root),patch('nahuatl_local.editorial_release.editorial_releases',side_effect=registry):
            before=self.db.read_bytes()
            ready=run('cycle-test',ROOT/'configs/editorial-pipeline.json',self.db)
            self.assertEqual(ready['state'],'ready');self.assertEqual(ready['records'],139)
            self.assertFalse((self.root/'corpus/editorial-releases.json').exists())
            self.assertEqual(self.db.read_bytes(),before)
            changed=self.root/'changed-config.json';changed.write_text('{}')
            with self.assertRaisesRegex(ValueError,'configuración'):run('cycle-test',changed,self.db)
            self.assertEqual(run('cycle-test',db_path=self.db)['state'],'ready')
            applied=run('cycle-test',db_path=self.db,apply=True)
            self.assertEqual(applied['publication']['added_records'],139)
            self.assertEqual(run('cycle-test',db_path=self.db,apply=True)['state'],'already_published')

    def test_registry_detects_changed_release_file(self):
        self.accepted();self.apply()
        file=self.root/'corpus/editorial-test-batch.json';file.write_bytes(file.read_bytes()+b' ')
        with self.assertRaisesRegex(ValueError,'cambió'):editorial_releases(self.root/'corpus/editorial-releases.json')


if __name__=='__main__':unittest.main()
