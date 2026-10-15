import json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
try:
    import torch
    from transformers import Qwen3Config,Qwen3ForCausalLM
    from safetensors.torch import load_file
except ImportError:  # Extra del laboratorio LLM: requirements.txt.
    raise unittest.SkipTest('torch/transformers no instalados')
from nahuatl_local import train
class Tokenizer:
    eos_token_id=2
    def apply_chat_template(self,*a,**kw):return [1,3,4]
    def __call__(self,*a,**kw):return {'input_ids':[5,6,7]}
def tiny(*a,**kw):return Qwen3ForCausalLM(Qwen3Config(vocab_size=16,hidden_size=16,intermediate_size=32,num_hidden_layers=1,num_attention_heads=2,num_key_value_heads=1,head_dim=8)),Tokenizer(),'cpu'
class ResumeTests(unittest.TestCase):
    def test_new_optimizer_inherits_cursor_after_best_checkpoint(self):
        with tempfile.TemporaryDirectory() as folder:
            d=Path(folder);data=d/'data';data.mkdir()
            for split in ['train','validation']:
                (data/f'{split}.jsonl').write_text(''.join(json.dumps({'es':str(i),'nah':'test'})+'\n' for i in range(6)))
            cfg=d/'config.json';cfg.write_text(json.dumps(dict(base_model='unused',data=str(data),seed=42,steps=3,max_length=16,learning_rate=.001,rank=2,alpha=4,gradient_accumulation=1,device='cpu',threads=1,validation_examples=2,eval_every=3)))
            original=d/'original';new=d/'new'
            with patch.object(sys,'argv',['train','--config',str(cfg),'--output',str(original)]),patch.object(train,'load_model',tiny):train.main()
            parent=torch.load(original/'last/state.pt',map_location='cpu',weights_only=True)
            self.assertEqual(parent['report']['best_step'],3)
            with patch.object(sys,'argv',['train','--config',str(cfg),'--output',str(new),'--steps','1',
                                          '--init-adapter',str(original/'best'),'--inherit-order-from',str(original/'last')]),patch.object(train,'load_model',tiny):train.main()
            child=torch.load(new/'last/state.pt',map_location='cpu',weights_only=True)
            self.assertEqual(child['order'],parent['order'])
            self.assertEqual(child['cursor'],parent['cursor']+1)
            self.assertEqual(child['report']['inherited_prior_steps'],3)

    def test_time_budget_keeps_initial_checkpoint_and_can_resume(self):
        with tempfile.TemporaryDirectory() as folder:
            d=Path(folder);data=d/'data';data.mkdir()
            for split in ['train','validation']:(data/f'{split}.jsonl').write_text(json.dumps({'es':'hola','nah':'test'})+'\n')
            config=d/'config.json';config.write_text(json.dumps(dict(base_model='unused',data=str(data),output=str(d/'run'),seed=42,steps=2,max_length=16,learning_rate=.001,rank=2,alpha=4,gradient_accumulation=1,device='cpu',threads=1,validation_examples=1,eval_every=1)))
            with patch.object(sys,'argv',['train','--config',str(config),'--max-seconds','0.000000001']),patch.object(train,'load_model',tiny):train.main()
            report=json.loads((d/'run/last/progress.json').read_text())
            self.assertEqual(report['completed_steps'],0)
            self.assertEqual(report['best_step'],0)
            self.assertTrue((d/'run/best/adapter_model.safetensors').exists())
            with patch.object(sys,'argv',['train','--config',str(config),'--resume',str(d/'run')]),patch.object(train,'load_model',tiny):train.main()
            self.assertEqual(json.loads((d/'run/last/progress.json').read_text())['completed_steps'],2)

    def test_resumption_same_weights_and_reject_data_change(self):
        with tempfile.TemporaryDirectory() as folder:
            d=Path(folder);data=d/'data';data.mkdir()
            for split in ['train','validation']:(data/f'{split}.jsonl').write_text(''.join(json.dumps({'es':str(i),'nah':'test'})+'\n' for i in range(6)))
            config=d/'config.json';config.write_text(json.dumps(dict(base_model='unused',data=str(data),seed=42,steps=4,max_length=16,learning_rate=.001,rank=2,alpha=4,gradient_accumulation=1,device='cpu',threads=1,validation_examples=2,eval_every=2)))
            def run(out,steps,resume=False):
                args=['train','--config',str(config),'--output',str(out),'--steps',str(steps)]
                if resume:args+=['--resume',str(out)]
                with patch.object(sys,'argv',args),patch.object(train,'load_model',tiny):train.main()
            full=d/'full';partial=d/'partial';run(full,4);run(partial,2);run(partial,4,True)
            a=load_file(full/'last/adapter_model.safetensors');b=load_file(partial/'last/adapter_model.safetensors')
            for key in a:self.assertTrue(torch.equal(a[key],b[key]))
            (data/'train.jsonl').write_text((data/'train.jsonl').read_text()+json.dumps({'es':'extra','nah':'new'})+'\n')
            with self.assertRaisesRegex(ValueError,'corpus cambió'):run(partial,5,True)
    def test_interrupted_save_recovers_previous(self):
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder)/'last';target.mkdir();(target/'marker').write_text('old');rename=Path.rename
            class Model:
                def save_pretrained(self,path,**kw):path.mkdir();(path/'adapter_config.json').write_text('{}')
            def interrupt(path,dest):
                if path.name=='last-writing':raise KeyboardInterrupt()
                return rename(path,dest)
            with patch.object(Path,'rename',interrupt):
                with self.assertRaises(KeyboardInterrupt):train.save(Model(),target)
            train.recover(target);self.assertEqual((target/'marker').read_text(),'old')
if __name__=='__main__':unittest.main()
