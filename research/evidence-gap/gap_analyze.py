"""Read-only development evidence verification and fixed readout analysis."""
import argparse
import csv
import json
import math
from gap_run import HERE,PRIOR,ARMS,GATE,freeze,read_rows,write_json,sha,development_plans
from gap_data import VARIANTS,LABELS,parse_text,world_truth,exhaustive_solver_audit
from gap_methods import METHODS,softmax,readout


def equal(a,b,path='summary'):
    if isinstance(b,dict):
        if not isinstance(a,dict) or a.keys()!=b.keys():raise ValueError(path+' keys differ')
        for k in b:equal(a[k],b[k],path+'.'+k)
    elif isinstance(b,list):
        if not isinstance(a,list) or len(a)!=len(b):raise ValueError(path+' list differs')
        for i,(x,y) in enumerate(zip(a,b)):equal(x,y,path+f'[{i}]')
    elif isinstance(b,float):
        if not isinstance(a,(int,float)) or not math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12):raise ValueError(path+' number differs')
    elif type(a)!=type(b) or a!=b:raise ValueError(path+' exact value differs')


def metrics(rows,cases):
    parents={};lookup={(r['id'],r['mapping']):r for r in rows}
    variants={v:{'correct':0,'decisions':0} for v in VARIANTS}
    orders={};correct=0
    for r in rows:
        c=cases[r['id']];hit=r['prediction']==c['gold'];correct+=hit
        parents.setdefault(c['parent'],[]).append(hit);orders.setdefault(c['id'],[]).append(r['prediction'])
        variants[c['variant']]['correct']+=hit;variants[c['variant']]['decisions']+=1
    deletion_pair=triple=flip_pair=hold_pair=0
    for parent in parents:
        byvariant={c['variant']:c for c in cases.values() if c['parent']==parent}
        for m in range(3):
            hit={v:lookup[c['id'],m]['prediction']==c['gold'] for v,c in byvariant.items()}
            deletion_pair+=hit['decisive_missing'] and hit['nondecisive_missing']
            triple+=hit['full'] and hit['decisive_missing'] and hit['nondecisive_missing']
            flip_pair+=hit['full'] and hit['flip'];hold_pair+=hit['full'] and hit['nondecisive_missing']
    uncertain=[r for r in rows if cases[r['id']]['gold']=='INSUFFICIENT']
    return {'decisions':len(rows),'correct':correct,'parents':len(parents),
        'complete_parents':sum(len(v)==18 and all(v) for v in parents.values()),
        'variants':variants,'deletion_pair_correct':deletion_pair,'deletion_triplet_correct':triple,
        'paired_units':len(parents)*3,'flip_pair_correct':flip_pair,'nondecisive_preserve_correct':hold_pair,
        'false_commitments':sum(r['prediction']!='INSUFFICIENT' for r in uncertain),'uncertain_decisions':len(uncertain),
        'order_sensitive_inputs':sum(len(set(v))>1 for v in orders.values())}


def analyze():
    manifest=freeze();runtime=json.loads((HERE/'results/runtime.json').read_text(encoding='utf-8'))
    if runtime['config_hash']!=manifest['config_hash'] or runtime['status']!='complete' or runtime['allowed_splits']!=['development']:
        raise ValueError('Incomplete/foreign development run')
    if any(runtime[k]!=v for k,v in {'scientific_forwards':756,'main_forwards':648,'null_forwards':108,'parity_forwards':252,'warmup_forwards':6,'reserved_model_records':0}.items()):
        raise ValueError('Runtime count or reserved-split violation')
    plans=development_plans(read_rows(HERE/'data/inputs.jsonl'));plook={(p['id'],p['mapping']):p for p in plans}
    all_cases=read_rows(HERE/'data/cases.jsonl');cases={c['id']:c for c in all_cases if c['split']=='development'}
    results={};derived=[];raw=[];max_parity=0.
    weight_expected=json.loads((PRIOR/'results/weight_checksums.json').read_text(encoding='utf-8'))
    if json.loads((HERE/'results/weight_checksums.json').read_text(encoding='utf-8'))!=weight_expected:raise ValueError('Weight provenance changed')
    if json.loads((HERE/'results/adapter_audit.json').read_text(encoding='utf-8'))!={'status':'passed','exact_tensors':504,'parameters':33030144}:
        raise ValueError('Adapter load audit incomplete')
    for arm in ARMS:
        rows=read_rows(HERE/f'results/{arm}.jsonl');index={(r['id'],r['mapping']):r for r in rows}
        if len(rows)!=252 or set(index)!=set(plook):raise ValueError('Incomplete/duplicate/foreign scientific grid')
        for key,r in index.items():
            p=plook[key]
            if r['split']!='development':raise ValueError('Reserved model result detected')
            if r['config_hash']!=manifest['config_hash'] or r['arm']!=arm or not r['ok'] or r['forward_id']!=f"{arm}/{r['id']}/{r['mapping']}":raise ValueError('Record identity changed')
            for f in ('id','parent','family','variant','split','kind','mapping','order'):
                if r[f]!=p[f]:raise ValueError('Plan metadata mismatch')
            z=r['logits'];ps=softmax(z)
            if len(r['probabilities'])!=3 or any(not math.isclose(a,b,rel_tol=2e-5,abs_tol=1e-7) for a,b in zip(ps,r['probabilities'])):
                raise ValueError('Raw logit/probability mismatch')
            if r['prediction']!=r['order'][max(range(3),key=ps.__getitem__)] or r['input_tokens']!=len(r['token_ids']):raise ValueError('Prediction/input count mismatch')
            if arm!='K1':
                if any(r[f]!=p[k] for f,k in (('prompt','prompt'),('token_ids','native_token_ids'),('candidate_ids','candidate_ids'))):raise ValueError('Native input mismatch')
            else:
                enc=p['pointer_encoding']
                for f,k in (('token_ids','ids'),('position_ids','pos'),('segments','seg'),('decide_idx','decide_idx'),('option_idx','opt_idx')):
                    if r[f]!=enc[k]:raise ValueError('Pointer input mismatch')
                if r['state']!=p['state'] or r['instruction']!=p['instruction']:raise ValueError('Pointer text mismatch')
                q=softmax(r['parity']['causal_logits']);delta=max(abs(a-b) for a,b in zip(q,r['probabilities']))
                if delta>=GATE or abs(delta-r['parity']['max_probability_delta'])>1e-6 or not r['parity']['prediction_matches'] or max(range(3),key=q.__getitem__)!=max(range(3),key=ps.__getitem__):
                    raise ValueError('Pointer parity evidence failed')
                max_parity=max(max_parity,r['parity']['max_probability_delta'])
        mains=[r for r in rows if r['kind']=='main'];nulls=[r for r in rows if r['kind']=='null']
        panels={}
        for method in METHODS:
            predictions=[]
            for r in mains:
                reference=index[r['parent']+'-null',r['mapping']]
                neighbor=index[r['id'],(r['mapping']+1)%3]
                pred={k:r[k] for k in ('id','parent','family','variant','split','mapping','arm')}
                pred.update(method=method,**readout(r,reference,neighbor,method));predictions.append(pred)
            panels[method]={'all':metrics(predictions,cases),'families':{f:metrics([r for r in predictions if r['family']==f],{k:c for k,c in cases.items() if c['family']==f}) for f in sorted({c['family'] for c in cases.values()})}}
            if method!='raw':
                corrected=regressed=0
                for p in predictions:
                    base=index[p['id'],p['mapping']];gold=cases[p['id']]['gold']
                    corrected+=base['prediction']!=gold and p['prediction']==gold
                    regressed+=base['prediction']==gold and p['prediction']!=gold
                panels[method]['vs_raw']={'corrected':corrected,'regressed':regressed}
            derived.extend(predictions)
        results[arm]={'methods':panels,'null_reference_correct_insufficient':sum(r['prediction']=='INSUFFICIENT' for r in nulls),
            'null_reference_decisions':len(nulls),'actual_main_forwards':len(mains),'actual_null_forwards':len(nulls)}
        raw.extend(rows)
    n0={(r['id'],r['mapping']):r for r in raw if r['arm']=='N0'}
    for r in raw:
        if r['arm']=='N1' and any(r[f]!=n0[r['id'],r['mapping']][f] for f in ('prompt','token_ids','candidate_ids','order')):
            raise ValueError('N0/N1 scoring input changed')
    equal(max_parity,runtime['max_parity_delta'])
    code_rows=[]
    for c in cases.values():
        parsed=parse_text(c['state'],c['instruction'],c['family'],c['sites'])
        prediction=world_truth(parsed)[0]
        if prediction!=c['gold']:raise ValueError('Same-text reference differs from rule truth')
        code_rows.append({'id':c['id'],'prediction':prediction})
    summary={'status':'complete_development_only','config_hash':manifest['config_hash'],'scientific_forwards':len(raw),
        'main_forwards':648,'null_forwards':108,'parity_forwards':252,'derived_method_predictions':len(derived),
        'reserved_model_records':0,'development_parents':12,'reserved_calibration_parents':12,'reserved_test_parents':24,
        'independent_human_reviewed':False,'new_training':False,'paid_api_calls':0,'results':results,
        'code_reference':{'description':'known synthetic grammar and declared finite policy; not general NLP',
            'correct':len(code_rows),'inputs':len(code_rows)},
        'always_insufficient':{'correct':72,'decisions':216,'complete_parents':0},
        'file_sha256_lf':{a:sha((HERE/f'results/{a}.jsonl').read_bytes().replace(b'\r\n',b'\n')) for a in ARMS}}
    return summary,derived,code_rows


def write_outputs(s,rows,code):
    write_json(HERE/'results/summary.json',s)
    with (HERE/'results/predictions.jsonl').open('w',encoding='utf-8',newline='\n') as stream:
        for r in rows:stream.write(json.dumps(r,ensure_ascii=False)+'\n')
    write_json(HERE/'results/code_reference.json',code)
    cases={c['id']:c for c in read_rows(HERE/'data/cases.jsonl')}
    with (HERE/'results/decisions.csv').open('w',encoding='utf-8',newline='') as stream:
        w=csv.writer(stream);w.writerow(['arm','method','id','parent','variant','mapping','gold','prediction','correct','nominal_calls'])
        for r in rows:w.writerow([r[k] for k in ('arm','method','id','parent','variant','mapping')]+[cases[r['id']]['gold'],r['prediction'],r['prediction']==cases[r['id']]['gold'],r['nominal_calls']])
    text=['# Missing Evidence Is Not Just Deleted Text','',
        'Development only, 12 parents / 72 inputs; labels await independent human review. No reserved scores.','',
        '|Path|Method|Correct / 216|Complete / 12|Deletion pair / 36|False commitments / 72|',
        '|---|---|---:|---:|---:|---:|']
    for arm in ARMS:
        for method in METHODS:
            m=s['results'][arm]['methods'][method]['all']
            text.append(f"|{arm}|{method}|{m['correct']}|{m['complete_parents']}|{m['deletion_pair_correct']}|{m['false_commitments']}|")
    text+=['','756 actual scientific forwards, 252 extra parity forwards. 1944 derived decisions are not independent trials.',
        '', 'Null subtraction is an unvalidated ablation with a meaningful unknown control, not faithful contextual calibration. Two-order averaging is a standard additional-compute baseline.',
        '', 'All family/variant counts, corrections/regressions and sharing costs are reported. Calibration/test remain model-unscored; no training or new algorithm claim.']
    (HERE/'results/REPORT.md').write_text('\n'.join(text)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    s,rows,code=analyze()
    if args.verify:
        equal(s,json.loads((HERE/'results/summary.json').read_text(encoding='utf-8')))
        equal(rows,read_rows(HERE/'results/predictions.jsonl'))
        equal(code,json.loads((HERE/'results/code_reference.json').read_text(encoding='utf-8')))
    else:write_outputs(s,rows,code)
    print(json.dumps({'status':'passed','scientific_forwards':s['scientific_forwards'],
        'method_predictions':s['derived_method_predictions'],'reserved_model_records':s['reserved_model_records'],'read_only':args.verify}))
