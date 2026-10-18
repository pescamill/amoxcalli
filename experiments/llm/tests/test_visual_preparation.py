import os
import builtins
import copy
from importlib import metadata
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from nahuatl_local.community import ROOT
from nahuatl_local.documentary_evaluation import load_development
from experiments.llm import visual_preparation as visual


class VisualPreparationTests(unittest.TestCase):
    def setUp(self):
        # Ruta real (sin enlaces simbólicos) y portable: en macOS /tmp apunta a /private/tmp.
        self.temp = tempfile.TemporaryDirectory(dir=os.path.realpath(tempfile.gettempdir()))
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        self.registry = self.root / 'configuration_auto.py'
        self.registry.write_text('CONFIG_MAPPING_NAMES = OrderedDict([("qwen3", "Qwen3Config")])')

    def packages(self, present=('torch', 'transformers', 'peft')):
        registry = self.registry
        class Distribution:
            version = 'fixture-version'
            def locate_file(self, relative):
                if relative != visual.REGISTRY:
                    raise AssertionError('Unexpected package file')
                return registry
        def distribution(name):
            if name not in present:
                raise metadata.PackageNotFoundError(name)
            return Distribution()
        return patch.object(visual.metadata, 'distribution', side_effect=distribution)

    def test_metadata_registry_absence_and_missing_packages_are_explicit(self):
        with self.packages():
            result = visual.preflight()
        self.assertEqual(result['state'], 'architecture_missing')
        self.assertEqual(result['registration'], dict(status='checked_literal_registry', qwen3=True, qwen3_vl=False))
        self.assertFalse(result['packages']['mlx']['installed'])
        with self.packages(present=()):
            missing = visual.preflight()
        self.assertEqual(missing['state'], 'dependencies_or_registry_pending')
        self.assertIsNone(missing['registration']['qwen3_vl'])
        self.assertTrue(all(v['version'] is None for v in missing['packages'].values()))

    def test_registered_architecture_does_not_claim_inference_or_hardware_fit(self):
        self.registry.write_text('CONFIG_MAPPING_NAMES = OrderedDict([("qwen3_vl", "Qwen3VLConfig")])')
        with self.packages():
            result = visual.preflight()
        self.assertEqual(result['state'], 'metadata_ready_inference_unverified')
        self.assertTrue(result['registration']['qwen3_vl'])
        for key in ('inference_verified', 'hardware_fit_verified', 'automatic_upgrade'):
            self.assertFalse(result[key])
        self.assertNotIn(str(self.root), json.dumps(result))

    def test_ast_never_executes_package_code_and_invalid_or_symlink_registry_is_unknown(self):
        marker = self.root / 'executed'
        self.registry.write_text('CONFIG_MAPPING_NAMES = OrderedDict([("qwen3", "Qwen3Config")])\n'
                                 f'open({str(marker)!r}, "w").write("bad")\n')
        with self.packages():
            self.assertFalse(visual.preflight()['registration']['qwen3_vl'])
        self.assertFalse(marker.exists())
        self.registry.write_text('CONFIG_MAPPING_NAMES = dangerous_function()')
        with self.packages():
            self.assertEqual(visual.preflight()['registration']['status'], 'registry_unreadable')
        self.registry.unlink()
        self.registry.symlink_to(marker)
        with self.packages():
            self.assertEqual(visual.preflight()['registration']['status'], 'registry_unreadable')

    def test_real_preflight_uses_metadata_without_model_imports_or_paths_in_payload(self):
        original_import = builtins.__import__
        def guarded(name, *args, **kwargs):
            if name.split('.')[0] in ('torch', 'transformers', 'peft', 'mlx'):
                raise AssertionError('Model library imported')
            return original_import(name, *args, **kwargs)
        with patch('builtins.__import__', side_effect=guarded):
            result = visual.preflight()
        try:
            expected = metadata.version('transformers')
        except metadata.PackageNotFoundError:
            expected = None
        self.assertEqual(result['packages']['transformers']['version'], expected)
        self.assertFalse(result['inference_verified'])
        self.assertNotIn(str(ROOT), json.dumps(result))

    def test_projection_preserves_development_references_and_separates_input(self):
        queries = load_development(modality='visual')
        with self.packages():
            result = visual.review()
        self.assertTrue(result['available'])
        self.assertEqual(result['case_count'], 52)
        self.assertEqual({c['id'] for c in result['cases']}, {q['id'] for q in queries})
        by_id = {q['id']: q for q in queries}
        for case in result['cases']:
            query = by_id[case['id']]
            self.assertEqual(case['reference'], query['reference'])
            self.assertEqual(case['rights'], query['rights'])
            self.assertEqual(case['review_status'], 'source_derived_not_human_validated')
            self.assertEqual((case['split'], case['modality']), ('development', 'visual'))
            self.assertEqual(case['proposed_input']['question'], query['question'])
            self.assertEqual(set(case['proposed_input']), {'question', 'image_reference_urls', 'catalog_page_url'})
            self.assertNotIn('reference', case['proposed_input'])
        result['cases'][0]['reference']['fields'][0]['value'] = 'detached edit'
        self.assertNotEqual(result['cases'][0]['reference'], queries[0]['reference'])
        self.assertEqual(result['candidate']['status'], 'not_run')
        self.assertIsNone(result['candidate']['metrics'])
        self.assertIsNone(result['candidate']['cost'])
        self.assertFalse(result['execution_enabled'])

    def test_public_status_has_no_cases_or_reference_keys(self):
        with self.packages():
            result = visual.status()
        self.assertEqual(result['case_count'], 52)
        forbidden = {'cases', 'reference', 'fields', 'proposed_input', 'source_hashes'}
        def inspect(value):
            if isinstance(value, dict):
                self.assertFalse(forbidden.intersection(value))
                for item in value.values():
                    inspect(item)
            elif isinstance(value, list):
                for item in value:
                    inspect(item)
        inspect(result)

    def test_wrong_split_is_rejected_even_if_loader_contract_is_bypassed(self):
        query = copy.deepcopy(load_development(modality='visual')[0])
        query['split'] = 'reserve'
        with self.packages(), patch.object(visual, 'load_development', return_value=[query]) as loader:
            result = visual.review()
        loader.assert_called_once_with(modality='visual', root=ROOT)
        self.assertFalse(result['available'])
        self.assertEqual(result['cases'], [])

    def test_stale_sources_and_raised_image_permissions_fail_closed(self):
        raw = (ROOT / 'configs/documentary-evaluation-v1.json').read_bytes()
        battery = json.loads(raw)
        for relative in [*battery['source_hashes'], 'configs/documentary-evaluation-v1.json']:
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, destination)
        changed = copy.deepcopy(battery)
        query = next(q for q in changed['queries'] if q['split'] == 'development' and q['modality'] == 'visual')
        query['rights']['image_model_input'] = True
        path = self.root / 'configs/documentary-evaluation-v1.json'
        path.write_text(json.dumps(changed))
        with self.packages():
            self.assertFalse(visual.review(self.root)['available'])
        path.write_bytes(raw)
        catalog = self.root / 'corpus/pictography/catalog.json'
        catalog.write_bytes(catalog.read_bytes() + b'\n')
        with self.packages():
            result = visual.review(self.root)
        self.assertFalse(result['available'])
        self.assertEqual(result['cases'], [])
        self.assertEqual(result['validation_errors'], ['development_battery_or_sources_invalid'])

    def test_projection_opens_only_public_recipe_inputs_and_registry_no_weights_or_image_io(self):
        battery = json.loads((ROOT / 'configs/documentary-evaluation-v1.json').read_text())
        allowed = {ROOT / p for p in battery['source_hashes']} | {ROOT / 'configs/documentary-evaluation-v1.json', self.registry}
        opened = []
        original_open = Path.open
        def guarded(path, *args, **kwargs):
            self.assertIn(path, allowed)
            self.assertNotIn('data/community', str(path))
            self.assertNotIn('models/', str(path))
            opened.append(path)
            return original_open(path, *args, **kwargs)
        with self.packages(), patch.object(Path, 'open', guarded), patch('urllib.request.urlopen', side_effect=AssertionError('Image/network IO')):
            result = visual.review()
        self.assertTrue(result['available'])
        self.assertTrue(opened)
        self.assertEqual(result['candidate']['images_processed'], 0)
        self.assertEqual(result['candidate']['model_calls'], 0)


if __name__ == '__main__':
    unittest.main()
