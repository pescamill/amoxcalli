import argparse
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from nahuatl_local import autotrain as auto

class AutomationTests(unittest.TestCase):
    def test_regression_guard_blocks_lower_loss_when_generation_degrades(self):
        original=dict(ids=['one','two'],dataset_sha256='fixed',chrF_plus_plus=22.,truncated=0,repeated_trigram_fraction=0.)
        candidate=dict(original,chrF_plus_plus=16.,truncated=3,repeated_trigram_fraction=.25)
        self.assertFalse(auto.generation_guard(original,candidate))
        self.assertTrue(auto.generation_guard(original,dict(original,chrF_plus_plus=23.)))
        self.assertTrue(auto.generation_guard(original,dict(original,chrF_plus_plus=27.96,repeated_trigram_fraction=.028)))
        self.assertFalse(auto.generation_guard(original,dict(original,chrF_plus_plus=27.96,repeated_trigram_fraction=.25)))
        with self.assertRaisesRegex(ValueError,'no coinciden'):
            auto.generation_guard(original,dict(original,ids=['other']))

    def test_plateau_and_nonfinite(self):
        p = {'best': 4., 'stale_stages': 0}
        p = auto.advance_policy(p, 3.995, .01)
        self.assertEqual(p['stale_stages'], 1)
        p = auto.advance_policy(p, 3.98, .01)
        self.assertEqual(p, {'best': 3.98, 'stale_stages': 0})
        with self.assertRaises(ValueError): auto.advance_policy(p, float('nan'), .01)

    def test_partial_stage_resume_does_not_count_as_plateau(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            data = out / 'data'; data.mkdir()
            for split in ['train', 'validation', 'test']:
                (data / (split+'.jsonl')).write_text('{"id":"'+split+'"}\n')
            adapter = out/'initial'; adapter.mkdir(); (adapter/'adapter_model.safetensors').write_bytes(b'weights')
            config = {'data': str(data)}
            auto.write(out/'train-config.json', config)
            state = dict(config=config, config_sha256=auto.digest(out/'train-config.json'), dataset_sha256=auto.hashes(data),
                         initial_adapter=str(adapter), initial_adapter_sha256=auto.digest(adapter/'adapter_model.safetensors'),
                         status='paused_budget', next_target=10, stage_steps=10, max_steps=20, patience=1, min_delta=.01,
                         policy=None, history=[], generation_best_step=None)
            auto.write(out/'automation.json', state); auto.write(out/'generation-before.json', {})
            partial=out/'run/best-writing';partial.mkdir(parents=True);(partial/'marker').write_text('partial')
            seen=[]
            def trainer(module, args, logfile):
                self.assertEqual(module, 'nahuatl_local.train')
                seen.append(args)
                step = 5 if len(seen)==1 else 10
                run=out/'run/last'; run.mkdir(parents=True, exist_ok=True)
                auto.write(run/'progress.json', dict(completed_steps=step,validation_loss_before=4.,
                           validation=[{'step':step,'loss':4.1}], best_step=0,best_validation_loss=4.,validation_rows=2))
            args=argparse.Namespace(output=str(out),budget_minutes=1)
            with patch.object(auto,'execute',trainer),patch.object(auto,'finish'):
                auto.run(args)
                saved=auto.read(out/'automation.json')
                self.assertEqual(saved['status'],'paused_budget')
                self.assertEqual(saved['history'],[])
                self.assertTrue((out/'interrupted-initialization/best-writing/marker').exists())
                auto.run(args)
            saved=auto.read(out/'automation.json')
            self.assertEqual(saved['status'],'early_stopped')
            self.assertEqual(len(saved['history']),1)
            self.assertIn('--resume',seen[1])
            self.assertEqual(auto.hashes(data),state['dataset_sha256'])
            (data/'test.jsonl').write_text('changed')
            with self.assertRaisesRegex(ValueError,'corpus cambió'):auto.run(args)

    def test_single_writer_lock(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'lock'
            with auto.lock(path):
                with self.assertRaisesRegex(RuntimeError,'Ya hay'):
                    with auto.lock(path):pass

    def test_terminal_run_finishes_pending_generation(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder);run=out/'run/last';run.mkdir(parents=True)
            auto.write(run/'progress.json',{'best_step':10})
            state={'generation_best_step':None}
            with patch.object(auto,'generation') as generate,patch.object(auto,'summary'):
                auto.finish(out,state)
            generate.assert_called_once()
            self.assertEqual(auto.read(out/'automation.json')['generation_best_step'],10)

if __name__=='__main__':unittest.main()
