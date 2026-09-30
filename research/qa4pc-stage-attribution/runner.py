"""Three-class Jev / single-prefill Qwen backends; no calls on import."""
import argparse
from contextlib import contextmanager
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

from plan import (ROOT,HERE,CACHE,MODEL,LETTERS,TOKEN_IDS,ORDERS,QWEN_REVISION,
                  options_checked,read,check,checked_tokenizer)
from journal import execute
from comparison_backends import file_hash,decode_api_body


def probability(x): return type(x) in (int,float) and math.isfinite(x) and 0<=x<=1


def adapt_jev(raw,status,options,latency):
    options=options_checked(options)
    detail={'http_status':status,'raw_response':raw,'readout':'three_class_native_choice_v1'}
    result={'status':'protocol_error','action':None,'input_tokens':None,'output_tokens':None,
            'latency_seconds':latency,'detail':detail}
    usage=raw.get('usage',{}) if isinstance(raw,dict) else {}
    if isinstance(usage,dict):
        for key in ('input_tokens','output_tokens'):
            if type(usage.get(key))==int and usage[key]>=0: result[key]=usage[key]
    try:
        if status!=200: raise ValueError('http_failure')
        if not isinstance(raw,dict) or raw.get('model')!=MODEL: raise ValueError('served_model')
        answers=raw.get('answers')
        if not isinstance(answers,dict) or set(answers)!={'decision'}: raise ValueError('answer_keys')
        answer=answers['decision']
        if not isinstance(answer,dict) or answer.get('type')!='choice': raise ValueError('answer_type')
        choice=answer.get('choice')
        if not isinstance(choice,str) or len(choice)!=1 or choice not in LETTERS: raise ValueError('choice')
        if result['input_tokens'] is None or result['output_tokens'] is None: raise ValueError('usage')
        p=answer.get('probabilities'); keys=isinstance(p,dict) and set(p)==set(LETTERS)
        valid=keys and all(probability(x) for x in p.values())
        total=sum(p.values()) if valid else None
        top=[l for l,v in p.items() if v==max(p.values())] if valid and total else []
        detail['metadata_quality']={'probability_keys_valid':keys,'probability_values_valid':valid,
            'raw_sum':total,'normalization_applied':False,'calibration_quality_established':False,
            'unique_argmax_action':options[LETTERS.index(top[0])] if len(top)==1 else None,
            'choice_is_displayed_argmax':choice in top if top else None,
            'displayed_top_tie':len(top)>1 if top else None,
            'confidence_valid':probability(answer.get('confidence'))}
        result.update(status='ok',action=options[LETTERS.index(choice)])
    except (ValueError,KeyError,TypeError) as error:
        detail['error']=str(error) if isinstance(error,ValueError) else type(error).__name__
    return result


def extract(values,norm,top_id,top_logit,options):
    options=options_checked(options)
    if len(values)!=3 or any(type(x) not in (int,float) or not math.isfinite(x) for x in [*values,norm,top_logit]) or type(top_id)!=int or top_id<0:
        raise ValueError('Invalid logit metadata')
    maximum=max(values)
    if norm<top_logit-1e-9 or top_logit<maximum-1e-9: raise ValueError('Impossible normalizer')
    if top_id in TOKEN_IDS and top_logit!=values[TOKEN_IDS.index(top_id)]: raise ValueError('Top mismatch')
    z=sum(math.exp(v-maximum) for v in values); mass=math.exp(maximum+math.log(z)-norm)
    if mass>1+1e-9: raise ValueError('Impossible candidate mass')
    winners=[i for i,v in enumerate(values) if v==maximum]
    winner=winners[0] if len(winners)==1 else None
    return {'action':options[winner] if winner is not None else None,
        'letter':LETTERS[winner] if winner is not None else None,'exact_tie':winner is None,
        'conditional_probabilities':{l:math.exp(v-maximum)/z for l,v in zip(LETTERS,values)},
        'full_vocabulary_candidate_mass':mass,'unconstrained_top_is_candidate':top_id in TOKEN_IDS}


def smoke_gate(job,result):
    if job['phase']=='smoke' and (result['status']!='ok' or result['action']!=job['expected_smoke_action']):
        result['detail']['smoke_observed_action']=result['action']
        result.update(status='protocol_error',action=None)
        result['detail']['smoke_gate_failed']=True
    return result


@contextmanager
def jev_backend():
    import httpx
    sys.path.insert(0,str(ROOT/'research/payment-ownership'))
    from run_api_v02 import load_key,sanitize
    key=load_key()
    with httpx.Client(timeout=60,follow_redirects=False,transport=httpx.HTTPTransport(retries=0)) as client:
        def call(job,remaining_seconds):
            start=time.monotonic()
            response=client.post('https://api.typesafe.ai/v1/systemone',json=job['request'],
                                headers={'Authorization':'Bearer '+key})
            raw=sanitize(decode_api_body(response.text),key)
            return smoke_gate(job,adapt_jev(raw,response.status_code,job['options'],time.monotonic()-start))
        yield call,{'model':MODEL,'python':sys.version,'httpx':httpx.__version__,
                    'transport_retries':0,'timeout_seconds':60,'redirects':False,
                    'execution_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()}


@contextmanager
def qwen_backend(model_dir):
    for key in ('HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','HF_HUB_DISABLE_TELEMETRY','HF_HUB_DISABLE_PROGRESS_BARS'): os.environ[key]='1'
    import torch,transformers,peft
    if (torch.__version__,transformers.__version__,peft.__version__)!=('2.8.0+cu128','5.3.0','0.18.1'):
        raise ValueError('Runtime version mismatch')
    start=time.monotonic();tokenizer,_=checked_tokenizer(model_dir)
    model_files=read(ROOT/'research/baseline-readiness/qwen35-smoke-repaired/run.json')['model_files']
    for f in model_files:
        p=model_dir/f['name']
        if p.stat().st_size!=f['bytes'] or file_hash(p)!=f['sha256']: raise ValueError('Model bytes mismatch')
    verify_seconds=time.monotonic()-start;start=time.monotonic();torch.cuda.reset_peak_memory_stats()
    model=transformers.Qwen3_5ForConditionalGeneration.from_pretrained(model_dir,dtype=torch.bfloat16,
        device_map={'':'cuda:0'},attn_implementation='sdpa',local_files_only=True,trust_remote_code=False)
    model.eval();torch.cuda.synchronize()
    if {str(p.dtype) for p in model.parameters()}!={'torch.bfloat16'} or {str(p.device) for p in model.parameters()}!={'cuda:0'}:
        raise ValueError('Placement/precision mismatch')
    count=[0]
    def hook(module,inputs): count[0]+=1
    handle=model.register_forward_pre_hook(hook)
    metadata={'model':'Qwen/Qwen3.5-4B','revision':QWEN_REVISION,'python':sys.version,
        'torch':torch.__version__,'transformers':transformers.__version__,'peft':peft.__version__,
        'gpu':torch.cuda.get_device_name(0),'model_files':model_files,'verification_seconds':verify_seconds,
        'load_seconds':time.monotonic()-start,'warmup_forwards':0,
        'execution_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()}
    def call(job,remaining_seconds):
        start=time.monotonic();before=count[0];ids=torch.tensor([job['input_ids']],device='cuda:0')
        torch.cuda.synchronize()
        with torch.inference_mode():
            out=model(input_ids=ids,attention_mask=torch.ones_like(ids),use_cache=True,logits_to_keep=1,return_dict=True)
        torch.cuda.synchronize();logits=out.logits[0,-1].double();forwards=count[0]-before
        if forwards!=1 or not bool(torch.isfinite(logits).all().item()):
            return {'status':'protocol_error','action':None,'input_tokens':len(job['input_ids']),'output_tokens':0,
                'latency_seconds':time.monotonic()-start,'detail':{'error':'bad_forward_or_logits','physical_forwards':forwards}}
        values=logits[TOKEN_IDS].tolist();top_id=int(logits.argmax().item());top_logit=float(logits[top_id].item())
        norm=float(torch.logsumexp(logits,dim=0).item());parsed=extract(values,norm,top_id,top_logit,job['options'])
        return smoke_gate(job,{'status':'ok','action':parsed['action'],'input_tokens':len(job['input_ids']),
            'output_tokens':0,'latency_seconds':time.monotonic()-start,
            'detail':{'candidate_logits':values,'full_logsumexp':norm,'top_token_id':top_id,'top_logit':top_logit,
                'top_token_text':tokenizer.decode([top_id]),'parsed':parsed,'physical_forwards':forwards,
                'stage_peak_allocated_bytes':torch.cuda.max_memory_allocated(),
                'stage_peak_reserved_bytes':torch.cuda.max_memory_reserved()}})
    try: yield call,metadata
    finally:
        handle.remove();del model;torch.cuda.empty_cache()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--backend',choices=('jev','qwen'),required=True)
    p.add_argument('--source-dir',type=Path,required=True);p.add_argument('--model-dir',type=Path,required=True)
    a=p.parse_args();plan,_,manifest=check(a.source_dir,a.model_dir)
    directory=CACHE/('execution-'+manifest['plan_sha256'])
    factory=jev_backend if a.backend=='jev' else lambda:qwen_backend(a.model_dir)
    result=execute(directory,plan,manifest['plan_sha256'],a.backend,factory)
    print(json.dumps({'backend':a.backend,'status':result['status'],'attempts':len(result['state']['started']),
        'finished':len(result['state']['results']),'input_tokens':result['state']['input_tokens'],
        'output_tokens':result['state']['output_tokens'],'overruns':result['overruns']}))


if __name__=='__main__': main()
