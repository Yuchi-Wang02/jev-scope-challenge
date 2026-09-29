"""Frozen, original-development-only classification; no reserved/rewrite inference route."""
import argparse
import itertools
import json
import sys
from pathlib import Path
from data_tools import HERE, original_cases
from interface import compile_visible, instruction, STATUS_ORDERS, STATUS_OPTIONS
from gap_run import spec, read_rows, write_json, sha, canonical, tokenizer_for, GATE, ARMS

SEED=20261003


def queries(cases):
    if cases!=original_cases():raise ValueError('Only the exact original development corpus is executable')
    rows=[]
    for c in cases:
        schema=compile_visible(c['state'],c['instruction'])
        fields=[None]+[f['name'] for f in schema['fields']]
        for field in fields:
            kind='direct' if field is None else 'fact'
            for mapping,order in enumerate(spec.MAPS if kind=='direct' else STATUS_ORDERS):
                options=spec.OPTIONS if kind=='direct' else STATUS_OPTIONS
                rows.append({k:c[k] for k in ('parent','family','variant','split','state')} | {
                    'id':c['id']+'/'+kind+('/'+field if field else ''), 'source_id':c['id'],
                    'kind':kind,'field':field,'representation':'original','mapping':mapping,'order':order,
                    'instruction':instruction(schema,c['instruction'],kind,field),
                    'options':[options[x] for x in order]})
    if len(rows)!=552 or sum(r['kind']=='direct' for r in rows)!=216:raise ValueError('Query grid drift')
    return rows


def native_prompt(row):
    choices='\n'.join(f'{letter}. {text}' for letter,text in zip('ABCD',row['options']))
    return row['state']+'\n\n'+row['instruction']+'\n'+choices+'\nAnswer:'


def encode_plans(tok):
    sys.path.insert(0,str(HERE.parent/'next-study/vendor'))
    from kev.model import encode
    answer_ids=[tok.encode(' '+c,add_special_tokens=False) for c in 'ABCD']
    if any(len(x)!=1 for x in answer_ids) or len({x[0] for x in answer_ids})!=4:raise ValueError('Answer tokens')
    plans=[]
    for row in queries(read_rows(HERE/'data/original_cases.jsonl')):
        prompt=native_prompt(row);ids=tok.encode(prompt,add_special_tokens=False);candidates=answer_ids[:len(row['order'])]
        for letter,candidate in zip('ABCD',candidates):
            if tok.encode(prompt+' '+letter,add_special_tokens=False)!=ids+candidate:raise ValueError('Boundary drift')
        enc=encode(tok,{'state':row['state'],'questions':[{'instr':row['instruction'],'options':row['options'],'label':0}]},strict=True,option_isolation=False)
        if enc['state_truncated'] or enc['pos']!=list(range(len(enc['ids']))):raise ValueError('Pointer truncation/positions')
        plans.append(row | {'prompt':prompt,'native_token_ids':ids,'candidate_ids':[x[0] for x in candidates],'pointer_encoding':enc})
    return plans


def executor_audit():
    from gap_data import direct_truth, keys, policy_for
    from interface import execute, STATUSES
    rows=[]
    for family in ('joint_approval','reversal_exception','route_lookup'):
        case={'family':family,'sites':['site-AAAAA','site-BBBBB'],'target':'request-AAAAA'}
        schema=compile_visible('Request: allow action for request request-AAAAA.',policy_for(case))
        for values in itertools.product(STATUSES,repeat=len(keys(family))):
            facts=dict(zip(keys(family),values));records=[]
            for field,status in facts.items():
                records.extend({'scope':case['target'],'field':field,'value':v} for v in {
                    'TRUE':[True],'FALSE':[False],'MISSING':[],'CONFLICT':[False,True]}[status])
            expected=direct_truth(case | {'records':records});actual=execute(schema,facts)
            if expected!=actual:raise ValueError('Independent direct solver disagreement')
            rows.append({'family':family,'facts':facts,'decision':actual})
    return {'status':'passed','states':len(rows),'scope':'all four-state vectors of three development policies','checks':rows}


def freeze():
    paths=['PROTOCOL.md','interface.py','interface_schema.json','data_tools.py','fact_run.py','fact_analyze.py',
        'data/original_cases.jsonl','data/reference_facts.jsonl','data/inputs.jsonl','data/executor_audit.json','preflight.json',
        'review/candidate_rewrites.jsonl','review/blind_pairs.json','review/blank.csv','review/manifest.json',
        '../evidence-gap/gap_data.py','../evidence-gap/gap_run.py','../evidence-gap/verify_gap.py',
        '../evidence-gap/manifest.json','../evidence-gap/results/N0.jsonl','../evidence-gap/results/N1.jsonl','../evidence-gap/results/K1.jsonl',
        '../next-study/study.py','../next-study/vendor/kev/model.py','../next-study/results/weight_checksums.json']
    obj={'study':'fact-execution-original-development-v0.1','base':spec.BASE,'base_revision':spec.BASE_REV,
        'adapter':spec.ADAPTER,'adapter_revision':spec.ADAPTER_REV,'source_revision':spec.SOURCE_REV,
        'arms':list(ARMS),'seed':SEED,'parity_gate':GATE,'allowed_splits':['development'],
        'allowed_representations':['original'],'scientific_forwards':1656,'direct_forwards':648,'fact_forwards':1008,
        'parity_forwards':552,'warmup_forwards':6,'reserved_model_records':0,'rewrite_model_records':0,
        'new_training':False,'paid_api_calls':0,'independent_human_reviewed':False,
        'post_hoc':True,'previous_development_results_known':True,
        'file_sha256_lf':{p:sha((HERE/p).read_bytes().replace(b'\r\n',b'\n')) for p in paths}}
    obj['config_hash']=sha(canonical(obj).encode());path=HERE/'manifest.json'
    if path.exists():
        if json.loads(path.read_text(encoding='utf-8'))!=obj:raise ValueError('Frozen study changed; version it')
    else:write_json(path,obj)
    return obj


def build(cache):
    if (HERE/'manifest.json').exists():freeze();print('Existing freeze verified without writes.');return
    from data_tools import files
    for name,payload in files().items():
        if (HERE/name).read_text(encoding='utf-8')!=payload:raise ValueError('Preparation drift')
    plans=encode_plans(tokenizer_for(cache))
    (HERE/'data/inputs.jsonl').write_text(''.join(json.dumps(p,ensure_ascii=False)+'\n' for p in plans),encoding='utf-8',newline='\n')
    write_json(HERE/'data/executor_audit.json',executor_audit())
    write_json(HERE/'preflight.json',{'status':'passed','model_calls':0,'plans_per_arm':552,
        'direct_plans_per_arm':216,'fact_plans_per_arm':336,'original_inputs':72,'reference_fields':168,
        'max_native_tokens':max(len(p['native_token_ids']) for p in plans),
        'max_pointer_tokens':max(len(p['pointer_encoding']['ids']) for p in plans),
        'max_pointer_state_tokens':max(p['pointer_encoding']['seg'].count(0) for p in plans),
        'no_truncation':True,'reserved_plans':0,'rewrite_plans':0,'tokenizer_revision':spec.BASE_REV})
    print(json.dumps(freeze(),indent=2))


def run(cache):
    import hashlib
    import importlib.metadata
    import platform
    import random
    import subprocess
    import time
    import torch
    from transformers import AutoModelForCausalLM
    from peft import PeftModel
    manifest=freeze();out=HERE/'results'
    if out.exists() and any(out.iterdir()):raise ValueError('Existing outputs; preserve rather than rerun/select')
    out.mkdir(exist_ok=True)
    env={'status':'loading','config_hash':manifest['config_hash'],'allowed_splits':['development'],
        'python':platform.python_version(),'gpu':torch.cuda.get_device_name(0),'cuda':torch.version.cuda,
        'packages':{p:importlib.metadata.version(p) for p in ('torch','transformers','peft','huggingface-hub','numpy')},
        'new_training':False,'paid_api_calls':0,'scientific_forwards':0,'direct_forwards':0,'fact_forwards':0,
        'parity_forwards':0,'warmup_forwards':0,'reserved_model_records':0,'rewrite_model_records':0,
        'start_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        'execution_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=HERE,text=True).strip()}
    write_json(out/'runtime.json',env);started=time.perf_counter()
    try:
        torch.manual_seed(SEED);torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
        torch.backends.cuda.enable_flash_sdp(False);torch.backends.cuda.enable_mem_efficient_sdp(False)
        torch.backends.cuda.enable_cudnn_sdp(False);torch.backends.cuda.enable_math_sdp(True);torch.cuda.reset_peak_memory_stats()
        base=Path(cache)/'models--Qwen--Qwen3-4B-Base/snapshots'/spec.BASE_REV
        adapter=Path(cache)/'models--jaredpalmer--kev-4b/snapshots'/spec.ADAPTER_REV
        expected=json.loads((HERE.parent/'next-study/results/weight_checksums.json').read_text(encoding='utf-8'))
        for key,digest in expected.items():
            if key.startswith(spec.BASE+'@'+spec.BASE_REV+'/'):path=base/key.split(spec.BASE_REV+'/',1)[1]
            elif key.startswith(spec.ADAPTER+'@'+spec.ADAPTER_REV+'/'):path=adapter/key.split(spec.ADAPTER_REV+'/',1)[1]
            else:raise ValueError('Foreign cached weight')
            h=hashlib.sha256()
            with path.open('rb') as stream:
                for chunk in iter(lambda:stream.read(8*1024*1024),b''):h.update(chunk)
            if h.hexdigest()!=digest:raise ValueError('Cached weight checksum mismatch')
        write_json(out/'weight_checksums.json',expected)
        tok=tokenizer_for(cache);jobs=read_rows(HERE/'data/inputs.jsonl')
        if encode_plans(tok)!=jobs:raise ValueError('Pinned tokenizer plan mismatch')
        random.Random(SEED).shuffle(jobs)
        meta=torch.load(adapter/'head.pt',map_location='cpu',weights_only=True)
        if meta['base']!=spec.BASE or meta.get('option_isolation',False):raise ValueError('Pointer checkpoint mismatch')
        lm=AutoModelForCausalLM.from_pretrained(base,torch_dtype=torch.bfloat16,attn_implementation='sdpa',local_files_only=True).to('cuda').eval()
        sys.path.insert(0,str(HERE.parent/'next-study/vendor'))
        from kev.model import DecisionModel,PointerHead
        maximum=0.
        for arm in ARMS:
            if arm=='N1':
                lm.model=PeftModel.from_pretrained(lm.model,adapter,is_trainable=False);lm.eval()
                from safetensors.torch import load_file
                saved=load_file(adapter/'adapter_model.safetensors');actual=dict(lm.model.named_parameters())
                for name,value in saved.items():
                    key=name.replace('.lora_A.weight','.lora_A.default.weight').replace('.lora_B.weight','.lora_B.default.weight')
                    if key not in actual or not torch.equal(actual[key].detach().cpu().float(),value.float()):raise ValueError('Adapter mismatch')
                if len(saved)!=504 or sum(t.numel() for t in saved.values())!=33030144:raise ValueError('Adapter inventory mismatch')
                if any(p.dtype!=torch.bfloat16 for n,p in lm.model.named_parameters() if 'lora_' not in n):raise ValueError('Backbone dtype mismatch')
                write_json(out/'adapter_audit.json',{'status':'passed','exact_tensors':len(saved),'parameters':sum(t.numel() for t in saved.values())})
            if arm=='K1':
                pointer=DecisionModel.__new__(DecisionModel);torch.nn.Module.__init__(pointer)
                pointer.lm,pointer.device,pointer.pad_id=lm.model,'cuda',tok.pad_token_id
                pointer.head=PointerHead(lm.config.hidden_size,dp=meta.get('head_dim',256)).to('cuda');pointer.head.load_state_dict(meta['head']);pointer.eval()
            for _ in range(2):
                with torch.inference_mode():lm(input_ids=torch.tensor([[tok.eos_token_id]],device='cuda'))
                env['warmup_forwards']+=1
            for number,p in enumerate(jobs,1):
                r={k:p[k] for k in ('id','source_id','parent','family','variant','split','representation','kind','field','mapping','order')}
                r.update(arm=arm,config_hash=manifest['config_hash'],forward_id=f"{arm}/{p['id']}/{p['mapping']}")
                torch.cuda.synchronize();tick=time.perf_counter()
                with torch.inference_mode():
                    if arm!='K1':
                        full=lm(input_ids=torch.tensor([p['native_token_ids']],device='cuda')).logits[0,-1].float();z=full[p['candidate_ids']]
                        r.update(prompt=p['prompt'],token_ids=p['native_token_ids'],candidate_ids=p['candidate_ids'],candidate_mass=torch.softmax(full,-1)[p['candidate_ids']].sum().item())
                    else:
                        enc=p['pointer_encoding'];z=pointer.forward(enc)[0]
                        r.update(state=p['state'],instruction=p['instruction'],options=p['options'],token_ids=enc['ids'],position_ids=enc['pos'],segments=enc['seg'],decide_idx=enc['decide_idx'],option_idx=enc['opt_idx'])
                    probs=torch.softmax(z,-1)
                torch.cuda.synchronize();r.update(ok=True,latency_s=time.perf_counter()-tick,input_tokens=len(r['token_ids']),logits=z.cpu().tolist(),probabilities=probs.cpu().tolist(),prediction=p['order'][int(probs.argmax())])
                env['scientific_forwards']+=1;env[p['kind']+'_forwards']+=1
                if arm=='K1':
                    with torch.inference_mode():
                        h=pointer.lm(input_ids=torch.tensor([enc['ids']],device='cuda'),position_ids=torch.tensor([enc['pos']],device='cuda')).last_hidden_state[0].float()
                        causal=pointer.head(h[enc['decide_idx'][0]],h[torch.tensor(enc['opt_idx'][0],device='cuda')]);delta=(probs-torch.softmax(causal,-1)).abs().max().item()
                    env['parity_forwards']+=1;maximum=max(maximum,delta)
                    r['parity']={'causal_logits':causal.cpu().tolist(),'max_probability_delta':delta,'prediction_matches':int(probs.argmax())==int(causal.argmax())}
                with (out/f'{arm}.jsonl').open('a',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(r,ensure_ascii=False,allow_nan=False)+'\n');stream.flush()
                if arm=='K1' and (delta>=GATE or not r['parity']['prediction_matches']):raise ValueError('Parity gate failed')
                if number%48==0:write_json(out/'runtime.json',env);print(f'{arm}: {number}/552 original development forwards',flush=True)
            env[arm]={'direct':216,'fact':336,'status':'complete'}
        env.update(status='complete',max_parity_delta=maximum,peak_allocated_mib=torch.cuda.max_memory_allocated()/1024**2,sdpa_kernel='math_only',backbone_dtype='bfloat16',head_dtype='float32',elapsed_s=time.perf_counter()-started)
        write_json(out/'runtime.json',env);print(json.dumps(env,indent=2),flush=True)
    except BaseException as error:
        env.update(status='failed',error_type=type(error).__name__,error=str(error),elapsed_s=time.perf_counter()-started);write_json(out/'runtime.json',env);raise


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['build','run']);p.add_argument('--cache',default='G:/jev-lab/hf-cache');a=p.parse_args()
    build(a.cache) if a.command=='build' else run(a.cache)
