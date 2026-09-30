"""v0.2 execution amendment; preserves original runner and shared attempt accounting."""
from __future__ import annotations
import argparse
import ctypes
import json
import os
import re
import time
from pathlib import Path
import httpx
from study import ROOT, REPO, PRICE, canonical, read, rows, sha, utc, validate_response, verify_freeze

LEDGER=ROOT/'results/attempts.jsonl'
OUTPUT=ROOT/'results/responses.jsonl'

def append(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a',encoding='utf-8',newline='\n') as f:
        f.write(canonical(value)+'\n'); f.flush(); os.fsync(f.fileno())

def load_key():
    key=os.environ.get('TYPESAFE_API_KEY')
    if key: return key
    if os.name!='nt': raise RuntimeError('Set TYPESAFE_API_KEY privately')
    path=Path(os.environ['USERPROFILE'])/'.codex/credentials/typesafe-api-key.dpapi'
    blob=path.read_bytes()
    try:
        text=blob.decode('ascii').strip()
        if re.fullmatch(r'[0-9a-fA-F]+',text): blob=bytes.fromhex(text)
    except UnicodeDecodeError: pass
    class Blob(ctypes.Structure):
        _fields_=[('size',ctypes.c_ulong),('data',ctypes.POINTER(ctypes.c_ubyte))]
    buf=(ctypes.c_ubyte*len(blob)).from_buffer_copy(blob)
    inp=Blob(len(blob),buf); out=Blob()
    crypt=ctypes.windll.crypt32.CryptUnprotectData
    crypt.argtypes=[ctypes.POINTER(Blob),ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_ulong,ctypes.POINTER(Blob)]
    crypt.restype=ctypes.c_int
    if not crypt(ctypes.byref(inp),None,None,None,None,1,ctypes.byref(out)):
        raise RuntimeError('DPAPI credential decryption failed')
    try:
        raw=ctypes.string_at(out.data,out.size)
        key=raw.decode('utf-16-le' if b'\x00' in raw else 'utf-8').strip()
    finally:
        ctypes.windll.kernel32.LocalFree.argtypes=[ctypes.c_void_p]
        ctypes.windll.kernel32.LocalFree(ctypes.cast(out.data,ctypes.c_void_p))
    if not key.startswith('apikey_'): raise RuntimeError('Credential format invalid (value suppressed)')
    return key

def sanitize(x,key):
    if isinstance(x,dict):
        return {k:sanitize(v,key) for k,v in x.items() if k.lower() not in ('authorization','headers','api_key','apikey')}
    if isinstance(x,list): return [sanitize(v,key) for v in x]
    if isinstance(x,str): return re.sub(r'apikey_[A-Za-z0-9_]+','[REDACTED]',x.replace(key,'[REDACTED]'))
    return x

def accounting(events):
    starts={e['attempt_id']:e for e in events if e['event']=='started'}
    ends={e['attempt_id']:e for e in events if e['event']=='finished'}
    if len(starts)!=sum(e['event']=='started' for e in events): raise ValueError('Duplicate attempt ID')
    if len(ends)!=sum(e['event']=='finished' for e in events): raise ValueError('Duplicate attempt completion')
    if set(ends)-set(starts): raise ValueError('Finish without start')
    return {'attempts':len(starts),'retries':sum(e['retry_index']>0 for e in starts.values()),
            'planned_input_units':sum(e['planned_input_units'] for e in starts.values()),
            'known_input_tokens':sum(e.get('input_tokens') or 0 for e in ends.values()),
            'unfinished':sorted(set(starts)-set(ends)),
            'unknown_usage_attempts':sum(e.get('input_tokens') is None for e in ends.values())}

def check_budget(events,job,retry_index,limits):
    a=accounting(events)
    if a['unfinished']: raise RuntimeError('Unfinished attempt requires reconciliation; automatic replay refused')
    if a['attempts']>=limits['attempt_limit']: raise RuntimeError('HTTP attempt cap reached')
    if retry_index and a['retries']>=limits['retry_limit']: raise RuntimeError('Retry cap reached')
    if a['planned_input_units']+job['planned_input_units']>limits['planned_input_limit']:
        raise RuntimeError('Planned input-unit cap reached')
    if a['known_input_tokens']+job['planned_input_units']>limits['planned_input_limit']:
        raise RuntimeError('Observed input tokens plus next reservation exceed cap')
    return a

def verify_execution():
    amendment=read(ROOT/'execution_v02.json')
    from study import file_hash
    for name,digest in amendment['sha256_lf'].items():
        if file_hash(ROOT/name)!=digest: raise RuntimeError('Execution amendment hash mismatch: '+name)
    snapshot=rows(ROOT/'results/checkpoints/v01_smoke_responses.jsonl')
    if rows(OUTPUT)[:len(snapshot)]!=snapshot: raise RuntimeError('Original smoke evidence changed')
    return amendment

def run(phase):
    verify_freeze(); verify_execution(); limits=read(ROOT/'freeze.json')
    jobs=rows(ROOT/'plans/primary.jsonl')
    all_jobs={j['job_id']:j for j in jobs}
    terminal=rows(OUTPUT)
    if len({r['job_id'] for r in terminal})!=len(terminal): raise RuntimeError('Duplicate terminal output')
    if any(not r['ok'] for r in terminal): raise RuntimeError('Prior terminal failure: reconcile before continuing')
    completed={r['job_id']:r for r in terminal}
    events=rows(LEDGER)
    if accounting(events)['unfinished']: raise RuntimeError('Unfinished previous attempt; will not reissue it')
    successful_jobs={e['job_id'] for e in events if e['event']=='finished' and e.get('ok')}
    if successful_jobs-set(completed): raise RuntimeError('Response persisted in attempt ledger only; reconcile without reissuing')
    if phase=='primary':
        smoke=[j for j in jobs if j['phase']=='smoke']
        if any(j['job_id'] not in completed or not completed[j['job_id']]['ok'] for j in smoke):
            raise RuntimeError('All six smoke requests must have valid responses before primary execution')
    lock=REPO/'.local/payment-run.lock';lock.parent.mkdir(parents=True,exist_ok=True)
    fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.close(fd)
    try:
        key=load_key(); todo=[j for j in jobs if j['phase']==phase and j['job_id'] not in completed]
        print(json.dumps({'phase':phase,'remaining':len(todo),'model':limits['model']}),flush=True)
        with httpx.Client(timeout=45,follow_redirects=False,trust_env=False) as client:
            for index,job in enumerate(todo):
                if sha(canonical(job['body']).encode())!=job['request_sha256']: raise RuntimeError('Request hash mismatch')
                for retry_index in range(2):
                    stats=check_budget(rows(LEDGER),job,retry_index,limits)
                    attempt_id=stats['attempts']+1; started=time.perf_counter()
                    append(LEDGER,{'event':'started','attempt_id':attempt_id,'job_id':job['job_id'],
                        'phase':phase,'execution_protocol':'EXECUTION_V02.md','retry_index':retry_index,'planned_input_units':job['planned_input_units'],
                        'request_sha256':job['request_sha256'],'ts_utc':utc()})
                    status=None; data=None; error=None; parsed=None; retry_after=1
                    try:
                        response=client.post('https://api.typesafe.ai/v1/systemone',json=job['body'],
                            headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
                        status=response.status_code
                        try: data=sanitize(response.json(),key)
                        except ValueError: error='non_json_response'
                        if status==200:
                            parsed=validate_response(data,job['option_order'])
                        else:
                            error='http_'+str(status)
                            value=response.headers.get('Retry-After','1')
                            if value.isdigit(): retry_after=max(1,int(value))
                    except Exception as exc:
                        error=type(exc).__name__ # Never persist exception/request reprs.
                    usage=(data or {}).get('usage',{}) if isinstance(data,dict) else {}
                    tokens=usage.get('input_tokens')
                    if type(tokens)!=int or tokens<0: tokens=None
                    record={'event':'finished','attempt_id':attempt_id,'job_id':job['job_id'],'phase':phase,
                        'execution_protocol':'EXECUTION_V02.md',
                        'ok':parsed is not None,'http_status':status,'error':error,'input_tokens':tokens,
                        'usage_estimated_cost_usd':None if tokens is None else tokens*PRICE,
                        'latency_s':time.perf_counter()-started,'ts_utc':utc(),'raw_response':data}
                    if parsed: record.update(parsed)
                    append(LEDGER,record)
                    transient=status in (408,429,500,502,503,504,529) or status is None
                    if not parsed and transient and retry_index==0 and retry_after<=30:
                        time.sleep(retry_after);continue
                    result={k:v for k,v in record.items() if k!='event'}
                    result.update({'execution_protocol':'EXECUTION_V02.md','case_id':job['case_id'],'input_view':job['input_view'],
                                   'option_order':job['option_order'],'request_sha256':job['request_sha256']})
                    append(OUTPUT,result)
                    if not parsed: raise RuntimeError('Stopped after persisted failed job; inspect redacted ledger')
                    break
                if (index+1)%10==0 or index+1==len(todo):
                    print(json.dumps({'phase':phase,'finished_this_run':index+1,'remaining':len(todo)-index-1}),flush=True)
        stats=accounting(rows(LEDGER)); stats['known_usage_estimated_cost_usd']=stats['known_input_tokens']*PRICE
        print(json.dumps(stats),flush=True)
    finally:
        lock.unlink(missing_ok=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--phase',choices=['primary'],required=True)
    run(p.parse_args().phase)
