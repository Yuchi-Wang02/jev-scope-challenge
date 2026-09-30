"""Frozen, offline-only ordinary Qwen native three-choice readout."""
import argparse
import hashlib
import json
import os
import platform
import time
from pathlib import Path

from study import ROOT, REPO, ORDERS, canonical, rows, read, write, write_rows, sha, utc, file_hash, verify_freeze

REVISION='1cfa9a7208912126459214e8b04321603b3df60c'
MODEL='Qwen/Qwen3-4B'
DEFAULT=Path(r'C:\Users\yuchi\Downloads\p1\hf_cache\hub\models--Qwen--Qwen3-4B\snapshots')/REVISION
PLAN=ROOT/'plans/local.jsonl'
FREEZE=ROOT/'local_freeze.json'
OUT=ROOT/'results/local_responses.jsonl'
LEDGER=ROOT/'results/local_attempts.jsonl'

def digest_file(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def append(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a',encoding='utf-8',newline='\n') as f:
        f.write(canonical(value)+'\n');f.flush();os.fsync(f.fileno())

def prompt_content(body):
    q=body['questions']['decision']
    return ('STATE\n'+json.dumps(body['state'],ensure_ascii=False,sort_keys=True,indent=2)
            +'\n\nQUESTION\n'+q['instructions']+'\nOPTIONS\n'
            +'\n'.join(f'{k}: {v}' for k,v in q['criteria'].items())
            +'\nReturn exactly one letter: A, B, or C.')

def freeze(model_path):
    if FREEZE.exists() or OUT.exists() or LEDGER.exists():raise RuntimeError('Existing freeze/output; overwrite refused')
    verify_freeze()
    from transformers import AutoTokenizer
    assert model_path.name==REVISION
    tok=AutoTokenizer.from_pretrained(str(model_path),local_files_only=True)
    choices={s:tok.encode(s,add_special_tokens=False) for s in ('A','B','C',' A',' B',' C')}
    assert all(len(ids)==1 for ids in choices.values())
    jobs=[]
    for j in rows(ROOT/'plans/primary.jsonl'):
        prompt=tok.apply_chat_template([{'role':'user','content':prompt_content(j['body'])}],
                                      tokenize=False,add_generation_prompt=True,enable_thinking=False)
        ids=tok.encode(prompt,add_special_tokens=False)
        for letter in 'ABC':assert tok.encode(prompt+letter,add_special_tokens=False)==ids+choices[letter]
        assert len(ids)<=8192
        jobs.append({k:j[k] for k in ('job_id','case_id','phase','option_order','request_sha256')}|
                    {'prompt':prompt,'prompt_sha256':sha(prompt.encode()),'input_ids':ids,'input_tokens':len(ids)})
    assert len(jobs)==150 and sum(j['input_tokens'] for j in jobs)<=1_000_000
    write_rows(PLAN,jobs)
    files=sorted(p for p in model_path.iterdir() if p.is_file() and (p.suffix in ('.safetensors','.json','.jinja') or p.name in ('vocab.json','merges.txt')))
    weights=[p for p in files if p.suffix=='.safetensors'];assert weights
    write(FREEZE,{'created_at_utc':utc(),'model':MODEL,'revision':REVISION,'max_forwards':150,
          'max_input_tokens':1_000_000,'planned_input_tokens':sum(j['input_tokens'] for j in jobs),
          'candidate_ids':choices,'chat_template_sha256':sha(tok.chat_template.encode()),
          'model_files_sha256':{p.name:digest_file(p) for p in files},
          'sha256_lf':{n:file_hash(ROOT/n) for n in ('LOCAL_PROTOCOL.md','local_run.py','plans/local.jsonl','freeze.json')},
          'readout':'native ABC candidate-normalized next-token logits; thinking disabled',
          'timing_disclosure':'After six Jev smoke outputs, before all Jev main and new local outputs'})
    return {'jobs':150,'input_tokens':sum(j['input_tokens'] for j in jobs),'model_files':len(files)}

def verify(model_path=None):
    verify_freeze();f=read(FREEZE)
    for n,h in f['sha256_lf'].items():assert file_hash(ROOT/n)==h,n
    jobs=rows(PLAN);original=rows(ROOT/'plans/primary.jsonl')
    assert len(jobs)==len(original)==150
    for j,o in zip(jobs,original):
        assert all(j[k]==o[k] for k in ('job_id','case_id','phase','option_order','request_sha256'))
        assert sha(j['prompt'].encode())==j['prompt_sha256'] and len(j['input_ids'])==j['input_tokens']
    assert sum(j['input_tokens'] for j in jobs)==f['planned_input_tokens']
    if model_path:
        assert model_path.name==f['revision']
        for name,h in f['model_files_sha256'].items():assert digest_file(model_path/name)==h,name
    return f

def terminal_state(jobs):
    output=rows(OUT);events=rows(LEDGER);byid={j['job_id']:j for j in jobs}
    assert len({r['job_id'] for r in output})==len(output)
    starts=[e for e in events if e['event']=='started'];ends=[e for e in events if e['event']=='finished']
    assert len({e['job_id'] for e in starts})==len(starts)
    assert len({e['job_id'] for e in ends})==len(ends)
    if {e['job_id'] for e in starts}!={e['job_id'] for e in ends}:raise RuntimeError('Unfinished local forward; reconciliation required')
    if {e['job_id'] for e in ends}!={r['job_id'] for r in output}:raise RuntimeError('Ledger/terminal mismatch; reconcile without new forward')
    for r in output:
        assert r['ok'] and r['job_id'] in byid and r['prompt_sha256']==byid[r['job_id']]['prompt_sha256']
    assert len(starts)<=150 and sum(e['input_tokens'] for e in starts)<=1_000_000
    return {r['job_id']:r for r in output},starts

def execute(phase,model_path):
    f=verify();jobs=rows(PLAN);completed,starts=terminal_state(jobs)
    if phase=='primary':assert all(j['job_id'] in completed for j in jobs if j['phase']=='smoke')
    todo=[j for j in jobs if j['phase']==phase and j['job_id'] not in completed]
    if not todo:print(json.dumps({'phase':phase,'new_forwards':0,'status':'all jobs already recorded'}));return
    lock=REPO/'.local/coverage-local.lock';lock.parent.mkdir(exist_ok=True)
    fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.close(fd)
    try:
        verify(model_path)
        import torch
        import transformers
        from transformers import AutoModelForCausalLM,AutoTokenizer
        torch.manual_seed(20260930);torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
        assert torch.cuda.is_available()
        tok=AutoTokenizer.from_pretrained(str(model_path),local_files_only=True)
        assert sha(tok.chat_template.encode())==f['chat_template_sha256']
        t=time.perf_counter()
        model=AutoModelForCausalLM.from_pretrained(str(model_path),local_files_only=True,torch_dtype=torch.bfloat16,
                                                 device_map='cuda',attn_implementation='sdpa').eval()
        torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats()
        runtime={'event':'runtime','phase':phase,'ts_utc':utc(),'torch':torch.__version__,
                 'transformers':transformers.__version__,'python':platform.python_version(),'cuda':torch.version.cuda,
                 'gpu':torch.cuda.get_device_name(0),'dtype':str(model.dtype),'attention':model.config._attn_implementation,
                 'tf32':False,'seed':20260930,'model_load_s':time.perf_counter()-t,'model':MODEL,'revision':REVISION}
        append(ROOT/'results/local_runtime.jsonl',runtime)
        print(json.dumps({'phase':phase,'remaining':len(todo),'runtime':runtime}),flush=True)
        for index,j in enumerate(todo):
            if len(starts)>=f['max_forwards'] or sum(s['input_tokens'] for s in starts)+j['input_tokens']>f['max_input_tokens']:
                raise RuntimeError('Local forward/token cap')
            assert tok.encode(j['prompt'],add_special_tokens=False)==j['input_ids']
            start={'event':'started','job_id':j['job_id'],'phase':phase,'input_tokens':j['input_tokens'],'ts_utc':utc()}
            append(LEDGER,start);starts.append(start)
            result={k:j[k] for k in ('job_id','case_id','phase','option_order','request_sha256','prompt_sha256','input_tokens')}
            result.update({'model':MODEL,'revision':REVISION,'ts_utc':utc()})
            t=time.perf_counter()
            try:
                enc=torch.tensor([j['input_ids']],device='cuda');mask=torch.ones_like(enc)
                torch.cuda.synchronize()
                with torch.inference_mode():
                    logits=model(input_ids=enc,attention_mask=mask,logits_to_keep=1).logits[0,-1,:].float()
                    ids=[f['candidate_ids'][x][0] for x in 'ABC'];chosen=logits[ids]
                    assert bool(torch.isfinite(logits).all())
                    conditional=torch.softmax(chosen,dim=-1);full=torch.softmax(logits,dim=-1)
                    raw={s:float(full[v[0]].item()) for s,v in f['candidate_ids'].items()}
                    lp={s:float(conditional[i].item()) for i,s in enumerate('ABC')}
                    mass=sum(raw[s] for s in 'ABC');assert mass>0
                    letter=max(lp,key=lp.get);mapping=ORDERS[j['option_order']]
                    top=int(torch.argmax(logits).item())
                    result.update({'ok':True,'letter':letter,'prediction':mapping['ABC'.index(letter)],
                         'probabilities':{mapping[i]:lp[s] for i,s in enumerate('ABC')},'letter_probabilities':lp,
                         'candidate_logits':{s:float(chosen[i].item()) for i,s in enumerate('ABC')},
                         'raw_token_probabilities':raw,'candidate_mass':mass,'low_mass':mass<.01,
                         'top_token_id':top,'top_token_text':tok.decode([top]),'top_token_probability':float(full[top].item())})
                torch.cuda.synchronize()
            except Exception as exc:
                result.update({'ok':False,'error':type(exc).__name__})
            result['latency_s']=time.perf_counter()-t
            result['peak_allocated_mib']=torch.cuda.max_memory_allocated()/1024**2
            append(LEDGER,{'event':'finished',**result});append(OUT,result)
            if not result['ok']:raise RuntimeError('Persisted local failure; inspect ledger before further work')
            if (index+1)%12==0 or index+1==len(todo):print(json.dumps({'phase':phase,'finished':index+1,'remaining':len(todo)-index-1}),flush=True)
    finally:lock.unlink(missing_ok=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['freeze','verify','run']);p.add_argument('--phase',choices=['smoke','primary']);p.add_argument('--model-path',type=Path,default=DEFAULT)
    a=p.parse_args()
    if a.command=='freeze':print(json.dumps(freeze(a.model_path),indent=2))
    elif a.command=='verify':print(json.dumps({'valid':bool(verify())}))
    else:
        if not a.phase:p.error('--phase is required for run')
        execute(a.phase,a.model_path)
