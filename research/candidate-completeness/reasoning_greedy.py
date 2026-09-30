"""One frozen, batch-bounded local deliberation control; no API or downloads."""
import argparse
import json
import os
import platform
import time
from pathlib import Path
from study import ROOT, REPO, ORDERS, rows, read, write, write_rows, sha, file_hash, utc
import local_run as L

PLAN=ROOT/'plans/reasoning_greedy.jsonl';FREEZE=ROOT/'reasoning_greedy_freeze.json'
OUT=ROOT/'results/reasoning_greedy_responses.jsonl';LEDGER=ROOT/'results/reasoning_greedy_attempts.jsonl'
LIMIT=512

def chunks(jobs):
    result=[]
    for phase in ('smoke','primary'):
        group=[j for j in jobs if j['phase']==phase]
        for i in range(0,len(group),4):
            batch=group[i:i+4];longest=max(j['input_tokens'] for j in batch)
            # Prefill + at most 511 decode positions + final full prefill.
            bound=len(batch)*(2*longest+2*LIMIT+16)
            result.append({'batch_id':f'{phase}_{i//4:03d}','phase':phase,'job_ids':[j['job_id'] for j in batch],
                           'reserved_token_positions':bound,'reserved_forwards':LIMIT+1})
    return result

def freeze(model_path):
    if FREEZE.exists() or OUT.exists() or LEDGER.exists():raise RuntimeError('Existing reasoning artifacts; overwrite refused')
    L.verify(model_path)
    from transformers import AutoTokenizer
    tok=AutoTokenizer.from_pretrained(str(model_path),local_files_only=True)
    close=tok.encode('</think>',add_special_tokens=False);assert len(close)==1
    jobs=[]
    for j in rows(ROOT/'plans/primary.jsonl'):
        prompt=tok.apply_chat_template([{'role':'user','content':L.prompt_content(j['body'])}],tokenize=False,add_generation_prompt=True,enable_thinking=True)
        assert prompt.endswith('<|im_start|>assistant\n')
        prompt+='<think>\n'
        ids=tok.encode(prompt,add_special_tokens=False)
        jobs.append({k:j[k] for k in ('job_id','case_id','phase','option_order','request_sha256')}|
                    {'prompt':prompt,'prompt_sha256':sha(prompt.encode()),'input_ids':ids,'input_tokens':len(ids)})
    batches=chunks(jobs);assert len(batches)==38 and sum(b['reserved_token_positions'] for b in batches)<=1_000_000
    write_rows(PLAN,jobs);write_rows(ROOT/'plans/reasoning_greedy_batches.jsonl',batches)
    write(FREEZE,{'created_at_utc':utc(),'model':L.MODEL,'revision':L.REVISION,'max_new_tokens':512,
        'max_decisions':150,'max_batches':38,'max_physical_forwards':19494,'max_processed_token_positions':1_000_000,
        'reserved_token_positions':sum(b['reserved_token_positions'] for b in batches),
        'closing_token_id':close[0],'model_eos_token_id':tok.eos_token_id,'pad_token_id':tok.pad_token_id,
        'candidate_ids':read(L.FREEZE)['candidate_ids'],
        'sha256_lf':{n:file_hash(ROOT/n) for n in ('REASONING_PROTOCOL.md','REASONING_GREEDY_V2.md','reasoning_greedy.py','reasoning_freeze.json','generation_config_audit.json','plans/reasoning_greedy.jsonl','plans/reasoning_greedy_batches.jsonl','local_freeze.json','checkpoint_audit.json')},
        'timing_disclosure':'After all Jev/native outputs and six stopped sampled smoke jobs; before all greedy-v2 outputs'})
    return {'jobs':150,'batches':38,'reserved_token_positions':sum(b['reserved_token_positions'] for b in batches)}

def verify():
    L.verify();f=read(FREEZE)
    for n,h in f['sha256_lf'].items():assert file_hash(ROOT/n)==h,n
    jobs=rows(PLAN);original=rows(ROOT/'plans/primary.jsonl');assert len(jobs)==150
    for j,o in zip(jobs,original):
        assert all(j[k]==o[k] for k in ('job_id','case_id','phase','option_order','request_sha256'))
        assert sha(j['prompt'].encode())==j['prompt_sha256'] and len(j['input_ids'])==j['input_tokens']
    assert chunks(jobs)==rows(ROOT/'plans/reasoning_greedy_batches.jsonl')
    return f

def completion():
    events=rows(LEDGER);out=rows(OUT)
    starts={e['batch_id']:e for e in events if e['event']=='started'}
    ends={e['batch_id']:e for e in events if e['event']=='finished'}
    assert len(starts)==sum(e['event']=='started' for e in events) and len(ends)==sum(e['event']=='finished' for e in events)
    if set(starts)!=set(ends):raise RuntimeError('Unfinished batch: reconciliation required; no automatic replay')
    if any(not e['ok'] for e in ends.values()):raise RuntimeError('Recorded failed batch; stop')
    assert len({r['job_id'] for r in out})==len(out)
    expected=[r for e in ends.values() for r in e['responses']]
    if expected!=out:raise RuntimeError('Partial or inconsistent batch terminal writes; reconcile without rerun')
    return starts,ends,out

def tensorize(torch,sequences,pad):
    length=max(map(len,sequences))
    ids=torch.tensor([[pad]*(length-len(s))+s for s in sequences],device='cuda')
    mask=torch.tensor([[0]*(length-len(s))+[1]*len(s) for s in sequences],device='cuda')
    return {'input_ids':ids,'attention_mask':mask}

def execute(phase,model_path):
    f=verify();starts,ends,out=completion();byid={j['job_id']:j for j in rows(PLAN)}
    if phase=='primary':assert sum(r['phase']=='smoke' and r['ok'] for r in out)==6
    todo=[b for b in rows(ROOT/'plans/reasoning_greedy_batches.jsonl') if b['phase']==phase and b['batch_id'] not in ends]
    if not todo:print(json.dumps({'phase':phase,'new_forwards':0}));return
    lock=REPO/'.local/coverage-reasoning-greedy.lock';fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.close(fd)
    try:
        L.verify(model_path)
        import torch
        import transformers
        from transformers import AutoTokenizer,AutoModelForCausalLM,GenerationConfig
        torch.manual_seed(20260930);torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
        tok=AutoTokenizer.from_pretrained(str(model_path),local_files_only=True)
        t=time.perf_counter()
        model=AutoModelForCausalLM.from_pretrained(str(model_path),local_files_only=True,torch_dtype=torch.bfloat16,device_map='cuda',attn_implementation='sdpa').eval()
        torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats()
        L.append(ROOT/'results/reasoning_greedy_runtime.jsonl',{'phase':phase,'started_at_utc':utc(),'model':L.MODEL,'revision':L.REVISION,
            'python':platform.python_version(),'torch':torch.__version__,'transformers':transformers.__version__,
            'cuda':torch.version.cuda,'gpu':torch.cuda.get_device_name(0),'dtype':str(model.dtype),'attention':model.config._attn_implementation,
            'seed':20260930,'tf32':False,'batch_size':4,'load_s':time.perf_counter()-t})
        cfg=GenerationConfig(do_sample=False,max_new_tokens=LIMIT,eos_token_id=[f['closing_token_id'],f['model_eos_token_id']],pad_token_id=f['pad_token_id'],use_cache=True)
        effective,unused=model._prepare_generation_config(cfg,use_model_defaults=False,do_sample=False)
        assert not effective.do_sample and effective.get_generation_mode().value=='greedy_search' and not unused
        L.append(ROOT/'results/reasoning_greedy_runtime.jsonl',{'phase':phase,'event':'effective_generation_config','ts_utc':utc(),'config':effective.to_dict(),'mode':effective.get_generation_mode().value})
        work={'physical_forwards':0,'processed_token_positions':0}
        def count(module,args,kwargs):
            x=kwargs.get('input_ids')
            if x is None:x=args[0]
            work['physical_forwards']+=1;work['processed_token_positions']+=x.numel()
        handle=model.register_forward_pre_hook(count,with_kwargs=True)
        for batch in todo:
            starts,ends,out=completion()
            if len(starts)>=f['max_batches'] or len(out)+len(batch['job_ids'])>f['max_decisions']:raise RuntimeError('Batch/decision limit')
            for key,limit in [('reserved_token_positions','max_processed_token_positions'),('reserved_forwards','max_physical_forwards')]:
                if sum(e[key] for e in starts.values())+batch[key]>f[limit]:raise RuntimeError('Work reservation limit')
            jobs=[byid[k] for k in batch['job_ids']]
            for j in jobs:assert tok.encode(j['prompt'],add_special_tokens=False)==j['input_ids']
            L.append(LEDGER,{'event':'started',**batch,'ts_utc':utc()})
            work.update(physical_forwards=0,processed_token_positions=0);t=time.perf_counter()
            try:
                enc=tensorize(torch,[j['input_ids'] for j in jobs],f['pad_token_id']);width=enc['input_ids'].shape[1]
                with torch.inference_mode():generated=model.generate(**enc,generation_config=cfg,use_model_defaults=False,do_sample=False)
                torch.cuda.synchronize();generation_s=time.perf_counter()-t
                tails=generated[:,width:].tolist();responses=[];finals=[]
                for j,tail in zip(jobs,tails):
                    stop=next((i for i,x in enumerate(tail) if x in (f['closing_token_id'],f['model_eos_token_id'])),None)
                    tokens=tail if stop is None else tail[:stop+1]
                    assert len(tokens)<=LIMIT
                    reason='budget' if stop is None else ('think_end' if tokens[-1]==f['closing_token_id'] else 'model_eos')
                    trace=tok.decode(tokens,skip_special_tokens=False)
                    # EOS is retained in raw tokens, removed only from the next prompt.
                    used=tokens if reason!='model_eos' else tokens[:-1]
                    body=tok.decode(used,skip_special_tokens=False)
                    final=j['prompt']+body+('' if reason=='think_end' else '\n</think>')+'\n\n'
                    ids=tok.encode(final,add_special_tokens=False)
                    for letter in 'ABC':assert tok.encode(final+letter,add_special_tokens=False)==ids+f['candidate_ids'][letter]
                    finals.append(ids)
                    responses.append({k:j[k] for k in ('job_id','case_id','phase','option_order','request_sha256','prompt_sha256','input_tokens')}|
                        {'batch_id':batch['batch_id'],'model':L.MODEL,'revision':L.REVISION,'generated_token_ids':tokens,
                         'generated_text':trace,'generated_tokens':len(tokens),'stop_reason':reason,'forced_boundary':reason!='think_end',
                         'final_prompt_sha256':sha(final.encode()),'final_input_ids':ids,'final_input_tokens':len(ids)})
                finalenc=tensorize(torch,finals,f['pad_token_id'])
                with torch.inference_mode():logits=model(**finalenc,logits_to_keep=1).logits[:,-1,:].float()
                assert bool(torch.isfinite(logits).all())
                for i,(j,r) in enumerate(zip(jobs,responses)):
                    ids=[f['candidate_ids'][x][0] for x in 'ABC'];chosen=logits[i,ids]
                    probs=torch.softmax(chosen,dim=-1);full=torch.softmax(logits[i],dim=-1)
                    lp={x:float(probs[k].item()) for k,x in enumerate('ABC')};letter=max(lp,key=lp.get);mapping=ORDERS[j['option_order']]
                    raw={x:float(full[v[0]].item()) for x,v in f['candidate_ids'].items()};mass=sum(raw[x] for x in 'ABC');assert mass>0
                    r.update({'ok':True,'letter':letter,'prediction':mapping['ABC'.index(letter)],'probabilities':{mapping[k]:lp[x] for k,x in enumerate('ABC')},
                              'letter_probabilities':lp,'candidate_logits':{x:float(chosen[k].item()) for k,x in enumerate('ABC')},
                              'candidate_mass':mass,'raw_token_probabilities':raw,'top_token_id':int(torch.argmax(logits[i]).item())})
                torch.cuda.synchronize()
                assert work['physical_forwards']<=batch['reserved_forwards'] and work['processed_token_positions']<=batch['reserved_token_positions']
                end={'event':'finished','batch_id':batch['batch_id'],'phase':phase,'ts_utc':utc(),'ok':True,
                     'responses':responses,'generation_s':generation_s,'batch_latency_s':time.perf_counter()-t,
                     'peak_allocated_mib':torch.cuda.max_memory_allocated()/1024**2,**work}
                L.append(LEDGER,end)
                for r in responses:L.append(OUT,r)
                print(json.dumps({'batch':batch['batch_id'],'decisions':len(responses),'generated_tokens':sum(r['generated_tokens'] for r in responses),
                    'forced_boundaries':sum(r['forced_boundary'] for r in responses),'elapsed_s':round(end['batch_latency_s'],2)}),flush=True)
                del enc,generated,finalenc,logits
            except Exception as exc:
                # If a finish was already written, never append a contradictory second finish.
                if not any(e['event']=='finished' and e['batch_id']==batch['batch_id'] for e in rows(LEDGER)):
                    L.append(LEDGER,{'event':'finished','batch_id':batch['batch_id'],'phase':phase,'ts_utc':utc(),'ok':False,'error':type(exc).__name__,**work})
                raise
        handle.remove()
    finally:lock.unlink(missing_ok=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['freeze','verify','run']);p.add_argument('--phase',choices=['smoke','primary']);p.add_argument('--model-path',type=Path,default=L.DEFAULT);a=p.parse_args()
    if a.command=='freeze':print(json.dumps(freeze(a.model_path),indent=2))
    elif a.command=='verify':print(json.dumps({'valid':bool(verify())}))
    else:
        if not a.phase:p.error('--phase required')
        execute(a.phase,a.model_path)
