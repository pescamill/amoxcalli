"""LoRA local con checkpoints completos, reanudación y validación por obra."""
import argparse,hashlib,json,math,random,shutil,time
from pathlib import Path
from .runtime import load_model,encode_pair,batch_tensor
from .data import load_rows

def evaluate_loss(model,rows,device):
    import torch
    model.eval();loss=tokens=0
    with torch.inference_mode():
        for row in rows:
            n=sum(x!=-100 for x in row['labels']);loss+=model(**batch_tensor(row,device)).loss.item()*n;tokens+=n
    return loss/tokens

def recover(path):
    old=path.with_name(path.name+'-previous')
    if not path.exists() and old.exists():old.rename(path)

def save(model,path,state=None):
    import torch
    recover(path);tmp=path.with_name(path.name+'-writing');old=path.with_name(path.name+'-previous')
    if tmp.exists():shutil.rmtree(tmp)
    model.save_pretrained(tmp,safe_serialization=True)
    p=tmp/'adapter_config.json';c=json.loads(p.read_text());c['base_model_name_or_path']='models/base';p.write_text(json.dumps(c,indent=2))
    if state is not None:
        torch.save(state,tmp/'state.pt')
        if 'report' in state:(tmp/'progress.json').write_text(json.dumps(state['report'],ensure_ascii=False,indent=2))
    if old.exists():shutil.rmtree(old)
    if path.exists():path.rename(old)
    tmp.rename(path)
    if old.exists():shutil.rmtree(old)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',default='configs/train.json');p.add_argument('--resume');p.add_argument('--init-adapter');p.add_argument('--inherit-order-from',help='Directorio last del mismo adaptador best; conserva orden y cursor, con optimizador nuevo');p.add_argument('--output');p.add_argument('--device');p.add_argument('--dtype',choices=['float32','bfloat16']);p.add_argument('--max-seconds',type=float)
    for name in ['steps','eval-every','max-length','validation-examples','gradient-accumulation']:p.add_argument('--'+name,type=int)
    a=p.parse_args()
    budget_start=time.perf_counter()
    if a.max_seconds is not None and a.max_seconds<=0:raise ValueError('--max-seconds debe ser positivo')
    if a.resume and a.init_adapter:raise ValueError('Elige reanudar estado o inicializar pesos, no ambos')
    if a.inherit_order_from and (a.resume or not a.init_adapter):raise ValueError('--inherit-order-from requiere --init-adapter sin --resume')
    c=json.loads(Path(a.config).read_text());c.setdefault('dtype','float32');c.setdefault('eval_every',40)
    for key in ['output','device','dtype','steps','eval_every','max_length','validation_examples','gradient_accumulation']:
        if getattr(a,key) is not None:c[key]=getattr(a,key)
    if min(c['steps'],c['eval_every'],c['gradient_accumulation'],c['validation_examples'])<1:raise ValueError('Los contadores deben ser positivos')
    out=Path(a.resume or c['output']);c['output']=str(out)
    if out.exists() and any(out.iterdir()) and not a.resume:raise ValueError('Usa --resume o un --output nuevo')
    out.mkdir(parents=True,exist_ok=True)
    import torch
    from peft import LoraConfig,TaskType,get_peft_model,PeftModel
    torch.set_num_threads(c['threads']);torch.manual_seed(c['seed'])
    model,tok,device=load_model(c['base_model'],device=c['device'],dtype=c['dtype']);model.config.use_cache=False
    if a.resume:
        recover(out/'last');recover(out/'best');model=PeftModel.from_pretrained(model,out/'last',is_trainable=True,local_files_only=True)
    elif a.init_adapter:
        ac=json.loads((Path(a.init_adapter)/'adapter_config.json').read_text())
        if ac['r']!=c['rank'] or ac['lora_alpha']!=c['alpha']:raise ValueError('Rank/alpha deben coincidir con el adaptador inicial')
        model=PeftModel.from_pretrained(model,Path(a.init_adapter),is_trainable=True,local_files_only=True)
    else:model=get_peft_model(model,LoraConfig(task_type=TaskType.CAUSAL_LM,r=c['rank'],lora_alpha=c['alpha'],target_modules=c.get('target_modules',['q_proj','v_proj']),lora_dropout=.05,bias='none'))
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False});model.enable_input_require_grads()
    rows=load_rows(Path(c['data'])/'train.jsonl');valid=load_rows(Path(c['data'])/'validation.jsonl');random.Random(c['seed']).shuffle(valid)
    train=[x for r in rows if (x:=encode_pair(tok,r,c['max_length'])) is not None];val=[x for r in valid if (x:=encode_pair(tok,r,c['max_length'])) is not None][:c['validation_examples']]
    if not train or not val:raise ValueError('No hay pares completos con este límite de tokens')
    hashes={s:hashlib.sha256((Path(c['data'])/f'{s}.jsonl').read_bytes()).hexdigest() for s in ['train','validation']}
    params=[p for p in model.parameters() if p.requires_grad];opt=torch.optim.AdamW(params,lr=c['learning_rate'],weight_decay=.01)
    rng=random.Random(c['seed']);order=list(range(len(train)));rng.shuffle(order);cursor=step=0;best=float('inf');elapsed=0
    report=dict(initial_adapter=a.init_adapter,config=c,device=device,torch=str(torch.__version__),base_revision=json.loads(Path('configs/sources.json').read_text())['model']['revision'],trainable_parameters=sum(p.numel() for p in params),usable_training_rows=len(train),validation_rows=len(val),dataset_sha256=hashes,quality_status='experimental_not_linguistically_validated',log=[],validation=[])
    if a.inherit_order_from:
        parent_path=Path(a.inherit_order_from).resolve()
        adapter=Path(a.init_adapter).resolve()
        if adapter!=parent_path.with_name('best'):raise ValueError('El adaptador inicial debe ser el best correspondiente al estado last')
        def checksum(path):
            with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
        if checksum(adapter/'adapter_model.safetensors')!=checksum(parent_path/'adapter_model.safetensors'):
            raise ValueError('Los pesos best no coinciden con last; no se puede heredar el cursor')
        parent=torch.load(parent_path/'state.pt',map_location='cpu',weights_only=True)
        prev=parent['report'];prior=prev['config']
        for key in ['seed','max_length','gradient_accumulation','rank','alpha','base_model']:
            if prior.get(key)!=c.get(key):raise ValueError(f'El estado anterior tiene {key} diferente')
        if prev['dataset_sha256']!=hashes or parent['step']!=prev['best_step'] or len(parent['order'])!=len(train):
            raise ValueError('El estado anterior no coincide con datos o adaptador best')
        order=parent['order'];cursor=parent['cursor'];rng.setstate(parent['shuffle_rng'])
        if sorted(order)!=list(range(len(train))) or not 0<=cursor<=len(order):raise ValueError('Orden heredado inválido')
        report['inherited_order_from']=str(parent_path)
        report['inherited_prior_steps']=parent['step'];report['inherited_cursor']=cursor
    if a.resume:
        state=torch.load(out/'last/state.pt',map_location='cpu',weights_only=True);previous=state['report']
        for key in ['dtype','max_length','rank','alpha','gradient_accumulation','learning_rate','seed','validation_examples','base_model','data','target_modules']:
            if previous['config'].get(key)!=c.get(key):raise ValueError(f'No cambies {key} al reanudar')
        if previous['dataset_sha256']!=hashes:raise ValueError('El corpus cambió: inicia otra ejecución')
        opt.load_state_dict(state['optimizer']);torch.set_rng_state(state['torch_rng']);rng.setstate(state['shuffle_rng']);order=state['order'];cursor=state['cursor'];step=state['step'];best=state['best'];report=previous;report['config']=c;elapsed=report['elapsed_seconds']
        if device=='cuda' and state.get('cuda_rng'):torch.cuda.set_rng_state_all(state['cuda_rng'])
        if device=='mps' and state.get('mps_rng') is not None:torch.mps.set_rng_state(state['mps_rng'])
    if step>=c['steps']:raise ValueError('--steps debe superar el último paso guardado')
    start=time.perf_counter()
    def checkpoint():
        report.update(completed_steps=step,best_validation_loss=best,elapsed_seconds=round(elapsed+time.perf_counter()-start,2),equivalent_training_passes=step*c['gradient_accumulation']/len(train))
        state=dict(report=report,optimizer=opt.state_dict(),torch_rng=torch.get_rng_state(),shuffle_rng=rng.getstate(),order=order,cursor=cursor,step=step,best=best,cuda_rng=torch.cuda.get_rng_state_all() if device=='cuda' else None,mps_rng=torch.mps.get_rng_state() if device=='mps' else None)
        save(model,out/'last',state)
        temp=out/'training-report.json.tmp';temp.write_text(json.dumps(report,ensure_ascii=False,indent=2));temp.replace(out/'training-report.json')
    if not a.resume:
        v=evaluate_loss(model,val,device);report['validation_loss_before']=v;report['validation'].append(dict(step=0,loss=v));print('Baseline',v,flush=True)
        if not math.isfinite(v):raise ValueError('Validación no finita')
        best=v;report['best_step']=0;save(model,out/'best');checkpoint()
    print(json.dumps({k:v for k,v in report.items() if k not in ['log','validation']},ensure_ascii=False),flush=True)
    try:
        while step<c['steps']:
            if a.max_seconds is not None and time.perf_counter()-budget_start>=a.max_seconds:
                print('Presupuesto agotado; checkpoint completo conservado.',flush=True);break
            model.train();opt.zero_grad(set_to_none=True);loss_sum=0
            for _ in range(c['gradient_accumulation']):
                if cursor==len(order):rng.shuffle(order);cursor=0
                loss=model(**batch_tensor(train[order[cursor]],device)).loss;cursor+=1
                if not math.isfinite(loss.item()):raise ValueError('Pérdida no finita')
                loss_sum+=loss.item();(loss/c['gradient_accumulation']).backward()
            torch.nn.utils.clip_grad_norm_(params,1);opt.step();step+=1
            item=dict(step=step,loss=loss_sum/c['gradient_accumulation'],elapsed_seconds=round(elapsed+time.perf_counter()-start,2));report['log'].append(item)
            if step==1 or step%10==0:print(json.dumps(item),flush=True)
            budget_ended=a.max_seconds is not None and time.perf_counter()-budget_start>=a.max_seconds
            if step%c['eval_every']==0 or step==c['steps'] or budget_ended:
                v=evaluate_loss(model,val,device);report['validation'].append(dict(step=step,loss=v));print('Validation',step,v,flush=True)
                if not math.isfinite(v):raise ValueError('Validación no finita; se conserva el checkpoint anterior')
                if v<best:best=v;report['best_step']=step;save(model,out/'best')
                checkpoint()
    except KeyboardInterrupt:print('Reanuda desde el último checkpoint completo.',flush=True)
if __name__=='__main__':main()
