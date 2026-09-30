"""Independent raw-response recount and optional tokenizer replay; no model load."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def recount(model_dir=None):
    plan=json.loads((HERE/'request_plan.json').read_bytes())
    cases={r['id']:r for r in json.loads((HERE/'cases.json').read_bytes())}
    report=json.loads((HERE/'report.json').read_bytes())
    tokenizer=None
    if model_dir:
        from transformers import AutoTokenizer
        tokenizer=AutoTokenizer.from_pretrained(model_dir,local_files_only=True,trust_remote_code=False)
    records={};decoded=0;inputs_checked=0
    for backend in ('jev','qwen'):
        jobs=[j for j in plan['jobs'] if j['backend']==backend]
        events=[json.loads(line) for line in (HERE/'results'/f'{backend}.jsonl').read_text().splitlines()]
        starts=[e['job_id'] for e in events if e['event']=='call_start']
        finishes=[e for e in events if e['event']=='call_finish']
        if starts!=[j['id'] for j in jobs] or [e['job_id'] for e in finishes]!=starts:raise ValueError('Incomplete/repeated execution')
        counts=Counter();tokens=Counter();actions={};invalid=Counter()
        for job,event in zip(jobs,finishes):
            result=event['result'];d=result['detail']
            if result['status']!='ok':raise ValueError('Recount requires complete successful records')
            if backend=='jev':
                raw=d['raw_response']
                if raw['model']!='jev-1.13.0' or d['http_status']!=200:raise ValueError('API identity')
                choice=raw['answers']['decision']['choice']
                if choice not in ('A','B','C'):raise ValueError('Invalid native choice')
                action=job['options'][('A','B','C').index(choice)]
                if raw['usage']!={'input_tokens':result['input_tokens'],'output_tokens':result['output_tokens']}:raise ValueError('API usage')
            else:
                ids=d['output_ids'];body=d['decoded_body']
                if tokenizer:
                    if tokenizer.decode(ids[:-1],skip_special_tokens=False)!=body or tokenizer.decode(ids[-1:],skip_special_tokens=False)!='<|im_end|>':raise ValueError('Output token decode')
                    if tokenizer.encode(job['rendered_input'],add_special_tokens=False)!=job['input_ids']:raise ValueError('Input token drift')
                    decoded+=1;inputs_checked+=1
                valid=bool(ids and ids[-1]==248046 and ids.count(248046)==1 and not d['unsupported_special'])
                action=body.strip() if valid and body.strip() in ('yes','no','maybe') else None
                if len(ids)!=result['output_tokens'] or len(job['input_ids'])!=result['input_tokens']:raise ValueError('Local usage')
            if action!=result['action']:raise ValueError('Stored action differs')
            ref=cases[job['item_id']]['reference'] if job['phase']=='main' else job['expected_smoke_action']
            if job['phase']=='main':
                counts[job['mapping']]+=action==ref;invalid[job['mapping']]+=action is None
                actions[(job['item_id'],job['mapping'])]=action
            tokens['input']+=result['input_tokens'];tokens['output']+=result['output_tokens']
        saved=report['backends'][backend]
        if any(saved['mapping'][str(m)]['correct']!=counts[m] or saved['mapping'][str(m)]['invalid']!=invalid[m] for m in (0,1)):raise ValueError('Count mismatch')
        if any(sum(c[k+'_tokens'] for c in saved['costs'].values())!=tokens[k] for k in ('input','output')):raise ValueError('Token sum mismatch')
        records[backend]={'raw_results':len(finishes),'correct_by_mapping':[counts[m] for m in (0,1)],
            'invalid_by_mapping':[invalid[m] for m in (0,1)],'input_tokens':tokens['input'],'output_tokens':tokens['output']}
    return {'verified':True,'new_model_calls':0,'recounted_decisions':sum(r['raw_results'] for r in records.values()),
        'tokenizer_output_sequences_verified':decoded,'tokenizer_input_sequences_verified':inputs_checked,
        'records':records,'report_sha256':hashlib.sha256((HERE/'report.json').read_bytes().replace(b'\r\n',b'\n')).hexdigest()}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--model-dir',type=Path);p.add_argument('--write',action='store_true');a=p.parse_args()
    result=recount(a.model_dir)
    if a.write:(HERE/'verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result))
