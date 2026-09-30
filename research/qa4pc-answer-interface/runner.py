"""Execute the frozen four-route grid. No weight/API calls on import."""
import argparse
from contextlib import contextmanager
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from compile_plan import ROOT,HERE,CACHE,MODEL,QWEN_REVISION,TOKEN_IDS,checked_tokenizer
from observations import adapt_jev,extract
from readout import parse_generated
from generation_config import make_config,audit_config
from comparison_backends import file_hash,decode_api_body

spec=importlib.util.spec_from_file_location('interface_journal',ROOT/'research/qa4pc-stage-attribution/journal.py')
journal=importlib.util.module_from_spec(spec);spec.loader.exec_module(journal)


def smoke_metadata(job,result):
    if job['phase']=='smoke':
        result['detail']['smoke']={'expected':job['expected_smoke_action'],'observed':result['action'],
            'correct':result['action']==job['expected_smoke_action'],'semantic_accuracy_is_gate':False}
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
            return smoke_metadata(job,adapt_jev(raw,response.status_code,job['options'],time.monotonic()-start))
        yield call,{'model':MODEL,'python':sys.version,'httpx':httpx.__version__,
            'transport_retries':0,'timeout_seconds':60,'redirects':False,
            'execution_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()}


@contextmanager
def qwen_backend(model_dir):
    for k in ('HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','HF_HUB_DISABLE_TELEMETRY','HF_HUB_DISABLE_PROGRESS_BARS'):os.environ[k]='1'
    import torch,transformers,peft
    from transformers import StoppingCriteria,StoppingCriteriaList
    if (torch.__version__,transformers.__version__,peft.__version__)!=('2.8.0+cu128','5.3.0','0.18.1'):
        raise ValueError('Runtime version mismatch')
    start=time.monotonic();tokenizer,_=checked_tokenizer(model_dir)
    configuration=audit_config(model_dir)
    saved=json.loads((HERE/'generation_audit.json').read_bytes())
    if configuration!=saved:raise ValueError('Generation configuration drift')
    files=json.loads((ROOT/'research/baseline-readiness/qwen35-smoke-repaired/run.json').read_bytes())['model_files']
    for f in files:
        p=model_dir/f['name']
        if p.stat().st_size!=f['bytes'] or file_hash(p)!=f['sha256']:raise ValueError('Model bytes mismatch')
    verify_seconds=time.monotonic()-start;start=time.monotonic();torch.cuda.reset_peak_memory_stats()
    model=transformers.Qwen3_5ForConditionalGeneration.from_pretrained(model_dir,dtype=torch.bfloat16,
        device_map={'':'cuda:0'},attn_implementation='sdpa',local_files_only=True,trust_remote_code=False)
    model.eval();torch.cuda.synchronize()
    if {str(p.dtype) for p in model.parameters()}!={'torch.bfloat16'} or {str(p.device) for p in model.parameters()}!={'cuda:0'}:
        raise ValueError('Placement/precision mismatch')
    effective,unused=model._prepare_generation_config(make_config(),return_dict_in_generate=True,output_logits=True)
    if unused or effective.to_dict()!=configuration['effective_generation_config']:raise ValueError('Loaded generation config mismatch')
    count=[0]
    def hook(module,inputs):count[0]+=1
    handle=model.register_forward_pre_hook(hook)
    processor_records=[];original_processors=model._get_logits_processor
    def audited_processors(*args,**kwargs):
        processors=original_processors(*args,**kwargs)
        names=[type(p).__name__ for p in processors];processor_records.append(names)
        if names!=configuration['processor_order']:raise ValueError('Actual processor order mismatch')
        return processors
    model._get_logits_processor=audited_processors
    metadata={'model':'Qwen/Qwen3.5-4B','revision':QWEN_REVISION,'python':sys.version,
        'torch':torch.__version__,'transformers':transformers.__version__,'peft':peft.__version__,
        'gpu':torch.cuda.get_device_name(0),'model_files':files,'verification_seconds':verify_seconds,
        'load_seconds':time.monotonic()-start,'warmup_forwards':0,'generation_audit':configuration,
        'execution_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()}
    def call(job,remaining_seconds):
        start=time.monotonic();before=count[0];processor_records.clear()
        ids=torch.tensor([job['input_ids']],device='cuda:0');inputs={'input_ids':ids,'attention_mask':torch.ones_like(ids)}
        detail={'arm':job['arm']};output_ids=[]
        class Deadline(StoppingCriteria):
            def __call__(self,input_ids,scores,**kwargs):return time.monotonic()-start>=remaining_seconds
        torch.cuda.synchronize()
        with torch.inference_mode():
            if job['arm']=='finite':
                out=model(**inputs,use_cache=True,logits_to_keep=1,return_dict=True)
                logits=out.logits[0,-1].double()
            else:
                out=model.generate(**inputs,generation_config=make_config(),return_dict_in_generate=True,
                    output_logits=True,stopping_criteria=StoppingCriteriaList([Deadline()]))
                output_ids=out.sequences[0,len(job['input_ids']):].tolist()
                if not out.logits or len(out.logits)!=len(output_ids):raise ValueError('Missing generation logits')
                if len(processor_records)!=1:raise ValueError('Missing processor audit')
                logits=out.logits[0][0].double()
        torch.cuda.synchronize();forwards=count[0]-before
        if not bool(torch.isfinite(logits).all().item()):raise ValueError('Nonfinite first logits')
        if forwards!=(1 if job['arm']=='finite' else len(output_ids)):raise ValueError('Forward accounting mismatch')
        top_id=int(logits.argmax().item());top_logit=float(logits[top_id].item())
        norm=float(torch.logsumexp(logits,dim=0).item());values=logits[list(TOKEN_IDS)].tolist()
        parsed=extract(values,norm,top_id,top_logit,job['options'])
        detail.update(first_candidate_logits=values,first_full_logsumexp=norm,first_top_token_id=top_id,
            first_top_logit=top_logit,first_top_tie_count=int((logits==logits.max()).sum().item()),
            first_letter_readout=parsed,physical_forwards=forwards)
        if job['arm']=='finite':action=parsed['action']
        else:
            eos=tokenizer.eos_token_id
            if eos!=248046 or tokenizer.decode([eos],skip_special_tokens=False)!='<|im_end|>':raise ValueError('EOS mismatch')
            ended=bool(output_ids and output_ids[-1]==eos and output_ids.count(eos)==1)
            body_ids=output_ids[:-1] if ended else output_ids
            body=tokenizer.decode(body_ids,skip_special_tokens=False)
            special=any(t in set(tokenizer.all_special_ids) for t in body_ids) or any(s in body for s in ('<|','|>','<think>','</think>'))
            generated=parse_generated(body,arm=job['arm'],options=job['options'],ended_eos=ended,unsupported_special=special)
            action=generated['action']
            detail.update(output_ids=output_ids,decoded_body=body,ended_eos=ended,
                unsupported_special=special,generated=generated,processor_order=processor_records[0],
                reached_length_limit=len(output_ids)==job['max_new_tokens'],
                reached_deadline=time.monotonic()-start>=remaining_seconds)
        detail.update(stage_peak_allocated_bytes=torch.cuda.max_memory_allocated(),
            stage_peak_reserved_bytes=torch.cuda.max_memory_reserved())
        return smoke_metadata(job,{'status':'ok','action':action,'input_tokens':len(job['input_ids']),
            'output_tokens':len(output_ids),'latency_seconds':time.monotonic()-start,'detail':detail})
    try:yield call,metadata
    finally:
        model._get_logits_processor=original_processors;handle.remove();del model;torch.cuda.empty_cache()


def main():
    from freeze import verify
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--backend',choices=('jev','qwen'),required=True)
    p.add_argument('--source-dir',type=Path,required=True);p.add_argument('--model-dir',type=Path,required=True)
    a=p.parse_args();plan,manifest=verify(a.source_dir,a.model_dir)
    factory=jev_backend if a.backend=='jev' else lambda:qwen_backend(a.model_dir)
    result=journal.execute(CACHE/('execution-'+manifest['plan_sha256']),plan,manifest['plan_sha256'],a.backend,factory)
    print(json.dumps({'backend':a.backend,'status':result['status'],'attempts':len(result['state']['started']),
        'finished':len(result['state']['results']),'input_tokens':result['state']['input_tokens'],
        'output_tokens':result['state']['output_tokens'],'overruns':result['overruns']}))


if __name__=='__main__':main()
