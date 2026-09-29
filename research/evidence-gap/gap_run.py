"""Development-only cached-model execution. Reserved inference has no CLI route."""
from __future__ import annotations
import argparse
import hashlib
import json
import random
import subprocess
import sys
import time
from pathlib import Path
from gap_data import HERE,build_rows,validate

PRIOR=HERE.parent/'next-study'
sys.path.insert(0,str(PRIOR))
import study as spec
ARMS=('N0','N1','K1')
GATE=1e-4
read_rows,write_json,sha,canonical=spec.read_rows,spec.write_json,spec.sha,spec.canonical


def null_text(case):
    return case['state'].splitlines()[0]+'\nEvidence: no records supplied.',case['instruction']


def encode_plans(tokenizer):
    sys.path.insert(0,str(PRIOR/'vendor'))
    from kev.model import encode
    cases=read_rows(HERE/'data/cases.jsonl');validate(cases)
    candidates=[tokenizer.encode(' '+x,add_special_tokens=False) for x in 'ABC']
    if any(len(c)!=1 for c in candidates) or len({c[0] for c in candidates})!=3:raise ValueError('Invalid answer tokens')
    texts=[];parents={}
    for c in cases:
        texts.append({k:c[k] for k in ('id','parent','family','variant','split','state','instruction')})
        if c['parent'] in parents:
            if null_text(c)!=null_text(parents[c['parent']]):raise ValueError('Parent null reference changed across views')
        else:parents[c['parent']]=c
    for parent,c in parents.items():
        state,instruction=null_text(c)
        texts.append({'id':parent+'-null','parent':parent,'family':c['family'],'variant':'null',
            'split':c['split'],'state':state,'instruction':instruction})
    plans=[]
    for text in texts:
        for mapping,order in enumerate(spec.MAPS):
            prompt=spec.native_prompt(text,order);ids=tokenizer.encode(prompt,add_special_tokens=False)
            for letter,candidate in zip('ABC',candidates):
                if tokenizer.encode(prompt+' '+letter,add_special_tokens=False)!=ids+candidate:raise ValueError('Answer boundary drift')
            enc=encode(tokenizer,{'state':text['state'],'questions':[{'instr':text['instruction'],
                'options':[spec.OPTIONS[x] for x in order],'label':0}]},strict=True,option_isolation=False)
            if enc['state_truncated'] or enc['pos']!=list(range(len(enc['ids']))):raise ValueError('Unexpected pointer input')
            plans.append({**text,'kind':'null' if text['variant']=='null' else 'main',
                'mapping':mapping,'order':order,'prompt':prompt,'native_token_ids':ids,
                'candidate_ids':[c[0] for c in candidates],'pointer_encoding':enc})
    return plans


def development_plans(plans):
    selected=[p for p in plans if p['split']=='development']
    expected={c['id'] for c in read_rows(HERE/'data/cases.jsonl') if c['split']=='development'}
    parents={c['parent'] for c in read_rows(HERE/'data/cases.jsonl') if c['split']=='development'}
    if len(selected)!=252 or len({(p['id'],p['mapping']) for p in selected})!=252:raise ValueError('Invalid development grid')
    if {p['id'] for p in selected if p['kind']=='main'}!=expected or {p['parent'] for p in selected if p['kind']=='null'}!=parents:
        raise ValueError('Reserved/foreign input in development selection')
    if any(p['family']=='composed_route' for p in selected):raise ValueError('Reserved mechanism in execution')
    return selected


def tokenizer_for(cache):
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(Path(cache)/'models--Qwen--Qwen3-4B-Base/snapshots'/spec.BASE_REV,local_files_only=True)


def freeze():
    paths=['PROTOCOL.md','gap_data.py','gap_run.py','gap_methods.py','gap_analyze.py',
        'data/cases.jsonl','data/solver_audit.json','data/inputs.jsonl','preflight.json',
        '../next-study/study.py','../next-study/vendor/kev/model.py','../next-study/results/weight_checksums.json']
    obj={'study':'evidence-gap-development-v0.1','base':spec.BASE,'base_revision':spec.BASE_REV,
        'adapter':spec.ADAPTER,'adapter_revision':spec.ADAPTER_REV,'source_revision':spec.SOURCE_REV,
        'arms':list(ARMS),'allowed_splits':['development'],'methods':['raw','null_subtract','two_order'],
        'alpha':1,'null_cache_scope':'parent/order/arm','seed':20261001,'parity_gate':GATE,
        'scientific_forwards':756,'main_forwards':648,'null_forwards':108,'parity_forwards':252,
        'warmup_forwards':6,'method_predictions':1944,'reserved_model_records':0,
        'backbone_dtype':'bfloat16','head_dtype':'float32','sdpa_kernel':'math_only','tf32':False,
        'new_training':False,'paid_api_calls':0,'independent_human_reviewed':False,
        'file_sha256_lf':{p:sha((HERE/p).read_bytes().replace(b'\r\n',b'\n')) for p in paths}}
    obj['config_hash']=sha(canonical(obj).encode());path=HERE/'manifest.json'
    if path.exists():
        if json.loads(path.read_text(encoding='utf-8'))!=obj:raise ValueError('Frozen development study changed; version it')
    else:write_json(path,obj)
    return obj


def build(cache):
    if (HERE/'manifest.json').exists():freeze();print('Existing freeze verified without writes.');return
    if read_rows(HERE/'data/cases.jsonl')!=build_rows():raise ValueError('Corpus differs from generator')
    plans=encode_plans(tokenizer_for(cache));selected=development_plans(plans)
    with (HERE/'data/inputs.jsonl').open('w',encoding='utf-8',newline='\n') as stream:
        for p in plans:stream.write(json.dumps(p,ensure_ascii=False)+'\n')
    write_json(HERE/'preflight.json',{'status':'passed','model_calls':0,'all_plans':len(plans),
        'development_plans_per_arm':len(selected),'reserved_plans':len(plans)-len(selected),
        'max_native_tokens':max(len(p['native_token_ids']) for p in plans),
        'max_pointer_tokens':max(len(p['pointer_encoding']['ids']) for p in plans),
        'max_pointer_state_tokens':max(p['pointer_encoding']['seg'].count(0) for p in plans),
        'no_truncation':True,'tokenizer_revision':spec.BASE_REV})
    print(json.dumps(freeze(),indent=2))


def run(cache):
    import importlib.metadata
    import platform
    import torch
    from transformers import AutoModelForCausalLM
    from peft import PeftModel
    manifest=freeze();out=HERE/'results'
    if out.exists() and any(out.iterdir()):raise ValueError('Existing outputs; preserve rather than rerun/select')
    out.mkdir(exist_ok=True)
    env={'status':'loading','config_hash':manifest['config_hash'],'allowed_splits':['development'],
        'python':platform.python_version(),'gpu':torch.cuda.get_device_name(0),'cuda':torch.version.cuda,
        'packages':{p:importlib.metadata.version(p) for p in ('torch','transformers','peft','huggingface-hub','numpy')},
        'new_training':False,'paid_api_calls':0,'scientific_forwards':0,'main_forwards':0,'null_forwards':0,
        'parity_forwards':0,'warmup_forwards':0,'reserved_model_records':0,
        'start_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        'execution_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=HERE,text=True).strip()}
    write_json(out/'runtime.json',env);started=time.perf_counter()
    try:
        torch.manual_seed(20261001);torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
        torch.backends.cuda.enable_flash_sdp(False);torch.backends.cuda.enable_mem_efficient_sdp(False)
        torch.backends.cuda.enable_cudnn_sdp(False);torch.backends.cuda.enable_math_sdp(True)
        torch.cuda.reset_peak_memory_stats()
        base=Path(cache)/'models--Qwen--Qwen3-4B-Base/snapshots'/spec.BASE_REV
        adapter=Path(cache)/'models--jaredpalmer--kev-4b/snapshots'/spec.ADAPTER_REV
        expected=json.loads((PRIOR/'results/weight_checksums.json').read_text(encoding='utf-8'))
        for key,digest in expected.items():
            if key.startswith(spec.BASE+'@'+spec.BASE_REV+'/'):path=base/key.split(spec.BASE_REV+'/',1)[1]
            elif key.startswith(spec.ADAPTER+'@'+spec.ADAPTER_REV+'/'):path=adapter/key.split(spec.ADAPTER_REV+'/',1)[1]
            else:raise ValueError('Foreign cached weight')
            h=hashlib.sha256()
            with path.open('rb') as stream:
                for chunk in iter(lambda:stream.read(8*1024*1024),b''):h.update(chunk)
            if h.hexdigest()!=digest:raise ValueError('Cached weight checksum mismatch')
        write_json(out/'weight_checksums.json',expected)
        tok=tokenizer_for(cache);all_plans=read_rows(HERE/'data/inputs.jsonl')
        if encode_plans(tok)!=all_plans:raise ValueError('Pinned tokenizer plan mismatch')
        jobs=development_plans(all_plans);random.Random(20261001).shuffle(jobs)
        meta=torch.load(adapter/'head.pt',map_location='cpu',weights_only=True)
        if meta['base']!=spec.BASE or meta.get('option_isolation',False):raise ValueError('Pointer checkpoint mismatch')
        lm=AutoModelForCausalLM.from_pretrained(base,torch_dtype=torch.bfloat16,
            attn_implementation='sdpa',local_files_only=True).to('cuda').eval()
        sys.path.insert(0,str(PRIOR/'vendor'))
        from kev.model import DecisionModel,PointerHead
        maximum=0.
        for arm in ARMS:
            if arm=='N1':
                lm.model=PeftModel.from_pretrained(lm.model,adapter,is_trainable=False);lm.eval()
                from safetensors.torch import load_file
                saved=load_file(adapter/'adapter_model.safetensors');actual=dict(lm.model.named_parameters())
                for name,value in saved.items():
                    key=name.replace('.lora_A.weight','.lora_A.default.weight').replace('.lora_B.weight','.lora_B.default.weight')
                    if key not in actual or not torch.equal(actual[key].detach().cpu().float(),value.float()):raise ValueError('Adapter load mismatch')
                if any(p.dtype!=torch.bfloat16 for n,p in lm.model.named_parameters() if 'lora_' not in n):raise ValueError('Backbone dtype mismatch')
                write_json(out/'adapter_audit.json',{'status':'passed','exact_tensors':len(saved),'parameters':sum(t.numel() for t in saved.values())})
            if arm=='K1':
                pointer=DecisionModel.__new__(DecisionModel);torch.nn.Module.__init__(pointer)
                pointer.lm,pointer.device,pointer.pad_id=lm.model,'cuda',tok.pad_token_id
                pointer.head=PointerHead(lm.config.hidden_size,dp=meta.get('head_dim',256)).to('cuda')
                pointer.head.load_state_dict(meta['head']);pointer.eval()
            for _ in range(2):
                with torch.inference_mode():lm(input_ids=torch.tensor([[tok.eos_token_id]],device='cuda'))
                env['warmup_forwards']+=1
            for number,p in enumerate(jobs,1):
                r={k:p[k] for k in ('id','parent','family','variant','split','kind','mapping','order')}
                r.update(arm=arm,config_hash=manifest['config_hash'],forward_id=f"{arm}/{p['id']}/{p['mapping']}")
                torch.cuda.synchronize();tick=time.perf_counter()
                with torch.inference_mode():
                    if arm!='K1':
                        full=lm(input_ids=torch.tensor([p['native_token_ids']],device='cuda')).logits[0,-1].float()
                        z=full[p['candidate_ids']]
                        r.update(prompt=p['prompt'],token_ids=p['native_token_ids'],candidate_ids=p['candidate_ids'],
                            candidate_mass=torch.softmax(full,-1)[p['candidate_ids']].sum().item())
                    else:
                        enc=p['pointer_encoding'];z=pointer.forward(enc)[0]
                        r.update(state=p['state'],instruction=p['instruction'],options=[spec.OPTIONS[x] for x in p['order']],
                            token_ids=enc['ids'],position_ids=enc['pos'],segments=enc['seg'],decide_idx=enc['decide_idx'],option_idx=enc['opt_idx'])
                    probs=torch.softmax(z,-1)
                torch.cuda.synchronize()
                r.update(ok=True,latency_s=time.perf_counter()-tick,input_tokens=len(r['token_ids']),
                    logits=z.cpu().tolist(),probabilities=probs.cpu().tolist(),prediction=p['order'][int(probs.argmax())])
                env['scientific_forwards']+=1;env[p['kind']+'_forwards']+=1
                if arm=='K1':
                    with torch.inference_mode():
                        h=pointer.lm(input_ids=torch.tensor([enc['ids']],device='cuda'),position_ids=torch.tensor([enc['pos']],device='cuda')).last_hidden_state[0].float()
                        causal=pointer.head(h[enc['decide_idx'][0]],h[torch.tensor(enc['opt_idx'][0],device='cuda')])
                        delta=(probs-torch.softmax(causal,-1)).abs().max().item()
                    env['parity_forwards']+=1;maximum=max(maximum,delta)
                    r['parity']={'causal_logits':causal.cpu().tolist(),'max_probability_delta':delta,
                                 'prediction_matches':int(probs.argmax())==int(causal.argmax())}
                with (out/f'{arm}.jsonl').open('a',encoding='utf-8',newline='\n') as stream:
                    stream.write(json.dumps(r,ensure_ascii=False,allow_nan=False)+'\n');stream.flush()
                if arm=='K1' and (delta>=GATE or not r['parity']['prediction_matches']):raise ValueError('Pointer parity gate failed on '+r['forward_id'])
                if number%36==0:
                    write_json(out/'runtime.json',env);print(f'{arm}: {number}/252 development main/null forwards',flush=True)
            env[arm]={'main':216,'null':36,'status':'complete'}
        env.update(status='complete',max_parity_delta=maximum,peak_allocated_mib=torch.cuda.max_memory_allocated()/1024**2,
            sdpa_kernel='math_only',backbone_dtype='bfloat16',head_dtype='float32',elapsed_s=time.perf_counter()-started)
        write_json(out/'runtime.json',env);print(json.dumps(env,indent=2),flush=True)
    except BaseException as error:
        env.update(status='failed',error_type=type(error).__name__,error=str(error),elapsed_s=time.perf_counter()-started)
        write_json(out/'runtime.json',env);raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['build','run'])
    parser.add_argument('--cache',default='G:/jev-lab/hf-cache')
    args=parser.parse_args();build(args.cache) if args.command=='build' else run(args.cache)
