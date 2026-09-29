"""Frozen exploratory boundary diagnostic. Cached weights only; no new training."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import random
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / 'next-study'
sys.path.insert(0, str(PRIOR))
import study as prior
from verify_study import verified_manifest as prior_manifest

LAYOUTS = ('L0', 'L1', 'L2')
ARMS = ('N0', 'N1', 'K1')
QUERY = 'Select the option justified by the supplied evidence and policy.'
SEED = 20260930
GATE = 1e-4
read_rows, write_json, canonical, sha = prior.read_rows, prior.write_json, prior.canonical, prior.sha


def fields(case, layout):
    evidence, policy = case['state'], case['instruction']
    if layout == 'L0':
        return evidence, policy
    if layout == 'L1':
        return policy + '\n\n' + evidence, QUERY
    if layout == 'L2':
        return policy, evidence + '\n\n' + QUERY
    raise ValueError('Unknown layout')


def prompt_for(case, layout, order):
    state, instruction = fields(case, layout)
    return prior.native_prompt({'state':state, 'instruction':instruction}, order)


def load_tokenizer(cache):
    from transformers import AutoTokenizer
    path = Path(cache)/'models--Qwen--Qwen3-4B-Base/snapshots'/prior.BASE_REV
    return AutoTokenizer.from_pretrained(path, local_files_only=True)


def plans_for(tokenizer):
    sys.path.insert(0, str(PRIOR/'vendor'))
    from kev.model import encode
    cases = read_rows(PRIOR/'data/cases.jsonl')
    prior.validate(cases)
    anchors = {(r['id'],r['mapping']):r for r in read_rows(PRIOR/'results/K1.jsonl')}
    native_anchors = {(r['id'],r['mapping']):r for r in read_rows(PRIOR/'results/N0.jsonl')}
    candidates = [tokenizer.encode(' '+x, add_special_tokens=False) for x in 'ABC']
    if any(len(x)!=1 for x in candidates) or len({x[0] for x in candidates})!=3:
        raise ValueError('Invalid native answer tokens')
    result = []
    for case in cases:
        for mapping, order in enumerate(prior.MAPS):
            triple=[]
            for layout in LAYOUTS:
                state, instruction = fields(case, layout)
                prompt = prompt_for(case, layout, order)
                ids = tokenizer.encode(prompt, add_special_tokens=False)
                for letter, candidate in zip('ABC', candidates):
                    if tokenizer.encode(prompt+' '+letter, add_special_tokens=False)!=ids+candidate:
                        raise ValueError('Native answer boundary mismatch')
                enc = encode(tokenizer, {'state':state,'questions':[{'instr':instruction,
                    'options':[prior.OPTIONS[x] for x in order],'label':0}]}, strict=True, option_isolation=False)
                if enc['state_truncated'] or enc['pos']!=list(range(len(enc['ids']))):
                    raise ValueError('Unexpected pointer truncation/positions')
                plan = {'id':case['id'],'parent':case['parent'],'family':case['family'],
                    'variant':case['variant'],'split':case['split'],'layout':layout,
                    'mapping':mapping,'order':order,'state':state,'instruction':instruction,
                    'options':[prior.OPTIONS[x] for x in order], 'prompt':prompt,
                    'native_token_ids':ids,'candidate_ids':[x[0] for x in candidates],
                    'pointer_encoding':enc}
                if layout=='L0':
                    a,b=anchors[case['id'],mapping],native_anchors[case['id'],mapping]
                    for field, key in (('token_ids','ids'),('position_ids','pos'),('segments','seg'),
                                       ('decide_idx','decide_idx'),('option_idx','opt_idx')):
                        if a[field]!=enc[key]: raise ValueError('Original pointer input drift')
                    if b['token_ids']!=ids or b['candidate_ids']!=plan['candidate_ids'] or b['prompt']!=prompt:
                        raise ValueError('Original native input drift')
                triple.append(plan)
            if any(triple[1][k]!=triple[2][k] for k in ('prompt','native_token_ids','candidate_ids','order')):
                raise ValueError('L1/L2 native input is not identical')
            if triple[1]['pointer_encoding']['ids']==triple[2]['pointer_encoding']['ids']:
                raise ValueError('Boundary control did not change pointer input')
            result.extend(triple)
    return result


def freeze():
    paths = ['PROTOCOL.md','layout_study.py','layout_analyze.py','data/inputs.jsonl','preflight.json',
             '../next-study/manifest.json','../next-study/study.py','../next-study/analyze_study.py',
             '../next-study/vendor/kev/model.py','../next-study/data/cases.jsonl',
             '../next-study/results/weight_checksums.json'] + [f'../next-study/results/{a}.jsonl' for a in ARMS]
    obj = {'study':'layout-boundary-v0.1','parent_config_hash':prior_manifest()['config_hash'],
           'base':prior.BASE,'base_revision':prior.BASE_REV,'adapter':prior.ADAPTER,
           'adapter_revision':prior.ADAPTER_REV,'source_revision':prior.SOURCE_REV,
           'arms':list(ARMS),'layouts':list(LAYOUTS),'seed':SEED,'gate':GATE,
           'logical_records':2592,'scientific_forwards':2016,'parity_forwards':864,'warmup_forwards':6,
           'backbone_dtype':'bfloat16','head_dtype':'float32','sdpa_kernel':'math_only',
           'tf32':False,'quantization':None,'new_training':False,'paid_api_calls':0,
           'independent_human_reviewed':False,'previously_inspected_data':True,
           'file_sha256_lf':{p:sha((HERE/p).read_bytes().replace(b'\r\n',b'\n')) for p in paths}}
    obj['config_hash']=sha(canonical(obj).encode())
    path=HERE/'manifest.json'
    if path.exists():
        if json.loads(path.read_text(encoding='utf-8'))!=obj:
            raise ValueError('Frozen study changed; preserve and version')
    else:
        write_json(path,obj)
    return obj


def build(cache):
    if (HERE/'manifest.json').exists():
        freeze()
        print('Existing freeze verified; no files written.')
        return
    prior_manifest()
    plans=plans_for(load_tokenizer(cache))
    (HERE/'data').mkdir(exist_ok=True)
    with (HERE/'data/inputs.jsonl').open('w',encoding='utf-8',newline='\n') as stream:
        for plan in plans: stream.write(json.dumps(plan,ensure_ascii=False)+'\n')
    write_json(HERE/'preflight.json',{'status':'passed','scored_model_records':0,
        'plans':len(plans),'native_identical_pairs':288,'original_anchor_inputs':288,
        'max_native_tokens':max(len(p['native_token_ids']) for p in plans),
        'max_pointer_tokens':max(len(p['pointer_encoding']['ids']) for p in plans),
        'max_pointer_state_tokens':max(p['pointer_encoding']['seg'].count(0) for p in plans),
        'tokenizer_revision':prior.BASE_REV,'no_truncation':True})
    print(json.dumps(freeze(),indent=2))


def record_identity(plan,arm,manifest):
    keys=('id','parent','family','variant','split','layout','mapping','order')
    return {**{k:plan[k] for k in keys},'arm':arm,'config_hash':manifest['config_hash'],
            'forward_id':f"{arm}/{plan['id']}/{plan['mapping']}/{plan['layout']}"}


def run(cache):
    import importlib.metadata
    import platform
    import torch
    from transformers import AutoModelForCausalLM
    from peft import PeftModel
    manifest=freeze()
    out=HERE/'results'
    if out.exists() and any(out.iterdir()): raise ValueError('Existing output found; preserve rather than select a rerun')
    out.mkdir(exist_ok=True)
    environment={'config_hash':manifest['config_hash'],'status':'loading','python':platform.python_version(),
        'gpu':torch.cuda.get_device_name(0),'cuda':torch.version.cuda,
        'packages':{p:importlib.metadata.version(p) for p in ('torch','transformers','peft','huggingface-hub','numpy')},
        'sdpa_kernel':'math_only','backbone_dtype':'bfloat16','head_dtype':'float32',
        'new_training':False,'paid_api_calls':0,'scientific_forwards':0,'parity_forwards':0,
        'shared_records':0,'logical_records':0,'warmup_forwards':0,
        'start_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        'execution_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=HERE,text=True).strip()}
    write_json(out/'runtime.json',environment)
    started=time.perf_counter()
    try:
        torch.manual_seed(SEED)
        torch.backends.cuda.matmul.allow_tf32=False
        torch.backends.cudnn.allow_tf32=False
        torch.backends.cuda.enable_flash_sdp(False)
        torch.backends.cuda.enable_mem_efficient_sdp(False)
        torch.backends.cuda.enable_cudnn_sdp(False)
        torch.backends.cuda.enable_math_sdp(True)
        torch.cuda.reset_peak_memory_stats()
        base=Path(cache)/'models--Qwen--Qwen3-4B-Base/snapshots'/prior.BASE_REV
        adapter=Path(cache)/'models--jaredpalmer--kev-4b/snapshots'/prior.ADAPTER_REV
        expected=json.loads((PRIOR/'results/weight_checksums.json').read_text(encoding='utf-8'))
        checked={}
        for key, digest in expected.items():
            if key.startswith(prior.BASE+'@'+prior.BASE_REV+'/'):
                path=base/key.split(prior.BASE_REV+'/',1)[1]
            elif key.startswith(prior.ADAPTER+'@'+prior.ADAPTER_REV+'/'):
                path=adapter/key.split(prior.ADAPTER_REV+'/',1)[1]
            else: raise ValueError('Foreign weight identity')
            h=hashlib.sha256()
            with path.open('rb') as stream:
                for chunk in iter(lambda:stream.read(8*1024*1024),b''): h.update(chunk)
            if h.hexdigest()!=digest: raise ValueError('Cached weight checksum mismatch')
            checked[key]=digest
        write_json(out/'weight_checksums.json',checked)
        plans=read_rows(HERE/'data/inputs.jsonl')
        tokenizer=load_tokenizer(cache)
        if plans_for(tokenizer)!=plans: raise ValueError('Pinned tokenizer plans changed')
        meta=torch.load(adapter/'head.pt',map_location='cpu',weights_only=True)
        if meta['base']!=prior.BASE or meta.get('option_isolation',False) or meta.get('base_revision') not in (None,prior.BASE_REV):
            raise ValueError('Checkpoint architecture mismatch')
        lm=AutoModelForCausalLM.from_pretrained(base,torch_dtype=torch.bfloat16,
            attn_implementation='sdpa',local_files_only=True).to('cuda').eval()
        lookup={(p['id'],p['mapping'],p['layout']):p for p in plans}
        pairs=list(dict.fromkeys((p['id'],p['mapping']) for p in plans))
        random.Random(SEED).shuffle(pairs)
        sys.path.insert(0,str(PRIOR/'vendor'))
        from kev.model import DecisionModel,PointerHead
        max_anchor_delta=max_parity_delta=0.
        for arm in ARMS:
            if arm=='N1':
                lm.model=PeftModel.from_pretrained(lm.model,adapter,is_trainable=False)
                lm.eval()
                from safetensors.torch import load_file
                saved=load_file(adapter/'adapter_model.safetensors')
                actual=dict(lm.model.named_parameters())
                for name,tensor in saved.items():
                    loaded=name.replace('.lora_A.weight','.lora_A.default.weight').replace('.lora_B.weight','.lora_B.default.weight')
                    if loaded not in actual or not torch.equal(actual[loaded].detach().cpu().float(),tensor.float()):
                        raise ValueError('Adapter load mismatch')
                write_json(out/'adapter_audit.json',{'status':'passed','exact_tensors':len(saved),
                    'parameters':sum(x.numel() for x in saved.values())})
                if any(p.dtype!=torch.bfloat16 for n,p in lm.model.named_parameters() if 'lora_' not in n):
                    raise ValueError('Backbone dtype drift')
            if arm=='K1':
                pointer=DecisionModel.__new__(DecisionModel)
                torch.nn.Module.__init__(pointer)
                pointer.lm,pointer.device,pointer.pad_id=lm.model,'cuda',tokenizer.pad_token_id
                pointer.head=PointerHead(lm.config.hidden_size,dp=meta.get('head_dim',256)).to('cuda')
                pointer.head.load_state_dict(meta['head']);pointer.eval()
            for _ in range(2):
                with torch.inference_mode(): lm(input_ids=torch.tensor([[tokenizer.eos_token_id]],device='cuda'))
                environment['warmup_forwards']+=1
            anchors={(r['id'],r['mapping']):r for r in read_rows(PRIOR/f'results/{arm}.jsonl')}
            for number,(case_id,mapping) in enumerate(pairs,1):
                shared=None
                for layout in LAYOUTS:
                    plan=lookup[case_id,mapping,layout]
                    record=record_identity(plan,arm,manifest)
                    if arm!='K1' and layout=='L2':
                        if shared is None: raise ValueError('Missing shared native forward')
                        record.update(copy.deepcopy(shared))
                        record.update(record_identity(plan,arm,manifest))
                        record.update(executed_forward=False,shared_from_forward_id=shared['forward_id'],latency_s=0.)
                        environment['shared_records']+=1
                    else:
                        torch.cuda.synchronize(); tick=time.perf_counter()
                        with torch.inference_mode():
                            if arm!='K1':
                                full_z=lm(input_ids=torch.tensor([plan['native_token_ids']],device='cuda')).logits[0,-1].float()
                                z=full_z[plan['candidate_ids']]
                                record.update(prompt=plan['prompt'],token_ids=plan['native_token_ids'],
                                    candidate_ids=plan['candidate_ids'],candidate_mass=torch.softmax(full_z,-1)[plan['candidate_ids']].sum().item())
                            else:
                                enc=plan['pointer_encoding'];z=pointer.forward(enc)[0]
                                record.update(state=plan['state'],instruction=plan['instruction'],options=plan['options'],
                                    token_ids=enc['ids'],position_ids=enc['pos'],segments=enc['seg'],
                                    decide_idx=enc['decide_idx'],option_idx=enc['opt_idx'])
                            p=torch.softmax(z,-1)
                        torch.cuda.synchronize()
                        record.update(executed_forward=True,shared_from_forward_id=None,
                            latency_s=time.perf_counter()-tick,logits=z.detach().cpu().tolist(),
                            probabilities=p.detach().cpu().tolist(),prediction=plan['order'][int(p.argmax())],
                            input_tokens=len(record['token_ids']),ok=True)
                        environment['scientific_forwards']+=1
                        if arm=='K1':
                            tick=time.perf_counter()
                            with torch.inference_mode():
                                h=pointer.lm(input_ids=torch.tensor([enc['ids']],device='cuda'),
                                    position_ids=torch.tensor([enc['pos']],device='cuda')).last_hidden_state[0].float()
                                causal=pointer.head(h[enc['decide_idx'][0]],h[torch.tensor(enc['opt_idx'][0],device='cuda')])
                                delta=(p-torch.softmax(causal,-1)).abs().max().item()
                            torch.cuda.synchronize()
                            environment['parity_forwards']+=1
                            record['parity']={'causal_logits':causal.cpu().tolist(),'max_probability_delta':delta,
                                'prediction_matches':int(p.argmax())==int(causal.argmax()),'latency_s':time.perf_counter()-tick}
                            max_parity_delta=max(max_parity_delta,delta)
                        if arm!='K1' and layout=='L1': shared=copy.deepcopy(record)
                    if layout=='L0':
                        anchor=anchors[case_id,mapping]
                        for key in ('token_ids','candidate_ids','position_ids','segments','decide_idx','option_idx'):
                            if key in anchor and record[key]!=anchor[key]: raise ValueError('Anchor encoding mismatch')
                        delta=max(abs(a-b) for a,b in zip(record['probabilities'],anchor['probabilities']))
                        record['anchor']={'max_probability_delta':delta,'prediction_matches':record['prediction']==anchor['prediction']}
                        max_anchor_delta=max(max_anchor_delta,delta)
                    environment['logical_records']+=1
                    with (out/f'{arm}.jsonl').open('a',encoding='utf-8',newline='\n') as stream:
                        stream.write(json.dumps(record,ensure_ascii=False,allow_nan=False)+'\n');stream.flush()
                    for gate in ('anchor','parity'):
                        if gate in record and (record[gate]['max_probability_delta']>=GATE or not record[gate]['prediction_matches']):
                            raise ValueError(gate+' gate failed on '+record['forward_id'])
                if number%24==0:
                    write_json(out/'runtime.json',environment)
                    print(f'{arm}: {number}/288 input/order pairs, {environment["scientific_forwards"]} scientific forwards',flush=True)
            environment[arm]={'logical_records':864,'status':'complete'}
        environment.update(status='complete',max_anchor_delta=max_anchor_delta,max_parity_delta=max_parity_delta,
            peak_allocated_mib=torch.cuda.max_memory_allocated()/1024**2,elapsed_s=time.perf_counter()-started)
        write_json(out/'runtime.json',environment)
        print(json.dumps(environment,indent=2),flush=True)
    except BaseException as error:
        environment.update(status='failed',error_type=type(error).__name__,error=str(error),elapsed_s=time.perf_counter()-started)
        write_json(out/'runtime.json',environment)
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['build','run'])
    parser.add_argument('--cache',default='G:/jev-lab/hf-cache')
    args=parser.parse_args()
    build(args.cache) if args.command=='build' else run(args.cache)
