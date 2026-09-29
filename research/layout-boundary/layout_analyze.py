"""Read-only raw-evidence checks and grouped boundary analysis; no model dependency."""
import argparse
import csv
import json
import math
from collections import Counter
from layout_study import HERE,PRIOR,ARMS,LAYOUTS,GATE,read_rows,freeze,write_json,canonical,sha
import study as prior
from analyze_study import stats,probabilities


def check_equal(actual,expected,path='summary'):
    if isinstance(expected,dict):
        if not isinstance(actual,dict) or actual.keys()!=expected.keys(): raise ValueError(path+' key mismatch')
        for k in expected: check_equal(actual[k],expected[k],path+'.'+k)
    elif isinstance(expected,list):
        if not isinstance(actual,list) or len(actual)!=len(expected): raise ValueError(path+' list mismatch')
        for i,(a,b) in enumerate(zip(actual,expected)): check_equal(a,b,path+f'[{i}]')
    elif isinstance(expected,float):
        if not isinstance(actual,(int,float)) or not math.isclose(actual,expected,rel_tol=1e-12,abs_tol=1e-12):
            raise ValueError(path+' numeric mismatch')
    elif type(actual)!=type(expected) or actual!=expected:
        raise ValueError(path+' exact mismatch')


def analyze():
    manifest=freeze()
    runtime=json.loads((HERE/'results/runtime.json').read_text(encoding='utf-8'))
    if runtime['status']!='complete' or runtime['config_hash']!=manifest['config_hash'] or runtime['sdpa_kernel']!='math_only':
        raise ValueError('Incomplete or foreign execution')
    plans=read_rows(HERE/'data/inputs.jsonl')
    cases={r['id']:r for r in read_rows(PRIOR/'data/cases.jsonl')}
    lookup={(p['id'],p['mapping'],p['layout']):p for p in plans}
    if len(plans)!=864 or len(lookup)!=864: raise ValueError('Invalid encoded plan grid')
    old=json.loads((PRIOR/'results/summary.json').read_text(encoding='utf-8'))
    results,contrasts,flat={},{},[]
    executed=shared=parity=anchor_count=0
    max_parity=max_anchor=0.
    for arm in ARMS:
        rows=read_rows(HERE/f'results/{arm}.jsonl')
        bykey={(r['id'],r['mapping'],r['layout']):r for r in rows}
        if len(rows)!=864 or set(bykey)!=set(lookup): raise ValueError('Incomplete or duplicate record grid')
        anchors={(r['id'],r['mapping']):r for r in read_rows(PRIOR/f'results/{arm}.jsonl')}
        for key,row in bykey.items():
            plan=lookup[key]
            for field in ('id','parent','family','variant','split','layout','mapping','order'):
                if row[field]!=plan[field]: raise ValueError('Record metadata mismatch')
            if row['arm']!=arm or row['config_hash']!=manifest['config_hash'] or not row['ok']:
                raise ValueError('Foreign record identity')
            if row['forward_id']!=f"{arm}/{row['id']}/{row['mapping']}/{row['layout']}": raise ValueError('Physical forward identity mismatch')
            z=row['logits']
            if len(z)!=3 or any(not math.isfinite(x) for x in z) or len(row['probabilities'])!=3:
                raise ValueError('Invalid logits/probabilities')
            p=probabilities(z)
            if any(not math.isclose(a,b,rel_tol=2e-5,abs_tol=1e-7) for a,b in zip(p,row['probabilities'])):
                raise ValueError('Probability/logit mismatch')
            if row['prediction']!=row['order'][max(range(3),key=p.__getitem__)]: raise ValueError('Prediction/logit mismatch')
            if row['input_tokens']!=len(row['token_ids']) or row['latency_s']<0: raise ValueError('Invalid token/cost accounting')
            if arm!='K1':
                if row['prompt']!=plan['prompt'] or row['token_ids']!=plan['native_token_ids'] or row['candidate_ids']!=plan['candidate_ids']:
                    raise ValueError('Native input differs from frozen plan')
                if row['layout']=='L2':
                    source=bykey[row['id'],row['mapping'],'L1']
                    if row['executed_forward'] or row['shared_from_forward_id']!=source['forward_id'] or row['latency_s']!=0:
                        raise ValueError('Invalid native sharing accounting')
                    for f in ('prompt','token_ids','candidate_ids','logits','probabilities','prediction','candidate_mass'):
                        if row[f]!=source[f]: raise ValueError('Shared native result differs')
                    shared+=1
                elif not row['executed_forward'] or row['shared_from_forward_id'] is not None:
                    raise ValueError('Expected physical native forward')
            else:
                enc=plan['pointer_encoding']
                for f,k in (('token_ids','ids'),('position_ids','pos'),('segments','seg'),('decide_idx','decide_idx'),('option_idx','opt_idx')):
                    if row[f]!=enc[k]: raise ValueError('Pointer input differs from frozen plan')
                for f in ('state','instruction','options'):
                    if row[f]!=plan[f]: raise ValueError('Pointer payload mismatch')
                if not row['executed_forward'] or row['shared_from_forward_id'] is not None: raise ValueError('Expected physical pointer forward')
                gate=row['parity'];q=probabilities(gate['causal_logits'])
                delta=max(abs(a-b) for a,b in zip(row['probabilities'],q))
                if delta>=GATE or abs(delta-gate['max_probability_delta'])>1e-6 or not gate['prediction_matches'] or max(range(3),key=q.__getitem__)!=max(range(3),key=p.__getitem__):
                    raise ValueError('Pointer parity gate inconsistent/failed')
                parity+=1;max_parity=max(max_parity,gate['max_probability_delta'])
            executed+=int(row['executed_forward'])
            if row['layout']=='L0':
                a=anchors[row['id'],row['mapping']]
                delta=max(abs(x-y) for x,y in zip(row['probabilities'],a['probabilities']))
                if delta>=GATE or row['prediction']!=a['prediction'] or not row['anchor']['prediction_matches'] or abs(delta-row['anchor']['max_probability_delta'])>1e-12:
                    raise ValueError('Original regression anchor failed')
                anchor_count+=1;max_anchor=max(max_anchor,delta)
        arm_results={}
        for layout in LAYOUTS:
            arm_results[layout]={}
            for split in ('development','calibration','exploratory_test'):
                panel=[r for r in rows if r['layout']==layout and r['split']==split]
                raw=stats(panel,cases)
                raw['variant_correct']={v:sum(r['prediction']==cases[r['id']]['gold'] for r in panel if r['variant']==v) for v in ('full','hold','flip','missing')}
                raw['variant_decisions']={v:sum(r['variant']==v for r in panel) for v in ('full','hold','flip','missing')}
                arm_results[layout][split]={'raw':raw,
                    'prior_temperature':stats(panel,cases,old['results'][arm]['calibration_temperature'])}
        results[arm]=arm_results
        contrasts[arm]={}
        for first,second in (('L0','L1'),('L0','L2'),('L1','L2')):
            entry={}
            for split in ('development','calibration','exploratory_test','all'):
                keys=[(c['id'],m) for c in cases.values() if split=='all' or c['split']==split for m in range(3)]
                changed=[];corrected=regressed=0
                for i,m in keys:
                    a,b=bykey[i,m,first],bykey[i,m,second]
                    if a['prediction']!=b['prediction']: changed.append(i)
                    corrected+=int(a['prediction']!=cases[i]['gold'] and b['prediction']==cases[i]['gold'])
                    regressed+=int(a['prediction']==cases[i]['gold'] and b['prediction']!=cases[i]['gold'])
                entry[split]={'decisions':len(keys),'changed_decisions':len(changed),
                    'changed_inputs':len(set(changed)),'changed_parents':len({cases[i]['parent'] for i in changed}),
                    'corrected':corrected,'regressed':regressed}
            contrasts[arm][first+'->'+second]=entry
        flat.extend(rows)
    if (executed,shared,parity,anchor_count)!=(2016,576,864,864): raise ValueError('Physical/scientific accounting mismatch')
    for k,v in {'scientific_forwards':executed,'shared_records':shared,'parity_forwards':parity,'logical_records':len(flat),'warmup_forwards':6}.items():
        if runtime[k]!=v: raise ValueError('Runtime forward counts mismatch')
    check_equal(runtime['max_anchor_delta'],max_anchor)
    check_equal(runtime['max_parity_delta'],max_parity)
    # N0/N1 use literally identical inputs and answer slots under every layout.
    n0={(r['id'],r['mapping'],r['layout']):r for r in flat if r['arm']=='N0'}
    for r in flat:
        if r['arm']=='N1':
            a=n0[r['id'],r['mapping'],r['layout']]
            if any(a[f]!=r[f] for f in ('prompt','token_ids','candidate_ids','order')): raise ValueError('N0/N1 input changed')
    for arm in ('N0','N1'):
        if contrasts[arm]['L1->L2']['all']['changed_decisions']!=0: raise ValueError('Identical native control changed')
    hashes={a:sha((HERE/f'results/{a}.jsonl').read_bytes().replace(b'\r\n',b'\n')) for a in ARMS}
    summary={'status':'complete_exploratory_diagnostic','config_hash':manifest['config_hash'],
        'logical_records':len(flat),'scientific_forwards':executed,'shared_records':shared,
        'parity_forwards':parity,'original_anchor_records':anchor_count,'max_anchor_delta':max_anchor,
        'max_parity_delta':max_parity,'file_sha256_lf':hashes,'results':results,'contrasts':contrasts,
        'independent_human_reviewed':False,'previously_inspected_data':True,'new_training':False,'paid_api_calls':0}
    return summary,flat


def write_outputs(summary,rows):
    write_json(HERE/'results/summary.json',summary)
    cases={c['id']:c for c in read_rows(PRIOR/'data/cases.jsonl')}
    with (HERE/'results/decisions.csv').open('w',encoding='utf-8',newline='') as stream:
        w=csv.writer(stream);w.writerow(['arm','layout','id','parent','split','variant','mapping','gold','prediction','correct','executed_forward','shared_from_forward_id'])
        for r in rows: w.writerow([r[k] for k in ('arm','layout','id','parent','split','variant','mapping')]+[cases[r['id']]['gold'],r['prediction'],r['prediction']==cases[r['id']]['gold'],r['executed_forward'],r['shared_from_forward_id']])
    text=['# Same Native Tokens, Different Pointer Boundaries','',
          'Real local diagnostic on previously inspected synthetic data; no independent labels or new training.','',
          '2592 logical decisions; 2016 scientific forwards, 576 explicitly shared native records; 864 additional parity forwards.','',
          '## Prior exploratory-test panel (12 parent groups)','','|Arm|Layout|Correct / 144|Complete / 12|Correct missing / 36|Order-sensitive inputs|',
          '|---|---|---:|---:|---:|---:|']
    for arm in ARMS:
        for layout in LAYOUTS:
            r=summary['results'][arm][layout]['exploratory_test']['raw']
            text.append(f"|{arm}|{layout}|{r['correct']}|{r['complete_parents']}|{r['variant_correct']['missing']}|{r['order_sensitive_inputs']}|")
    text+=['','## Primary boundary contrast L1 → L2','','|Arm|Changed decisions / 144|Changed inputs / 48|Changed parents / 12|Corrected|Regressed|',
           '|---|---:|---:|---:|---:|---:|']
    for arm in ARMS:
        c=summary['contrasts'][arm]['L1->L2']['exploratory_test']
        text.append(f"|{arm}|{c['changed_decisions']}|{c['changed_inputs']}|{c['changed_parents']}|{c['corrected']}|{c['regressed']}|")
    text+=['','L1/L2 native tokens are identical and reused explicitly. Pointer field boundaries, delimiter positions and whitespace tokens change. This is not a head-only causal intervention.',
           '', 'All layouts, splits, variant scores and prior-temperature transfer metrics are in summary.json. No layout was chosen as a new test-time method.',
           '', 'No new independent sample, broader distribution claim, head-only training, current default Kev evaluation or Jev/Laya call. The original labels still await independent review.']
    (HERE/'results/REPORT.md').write_text('\n'.join(text)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify',action='store_true')
    args=parser.parse_args()
    summary,rows=analyze()
    if args.verify: check_equal(summary,json.loads((HERE/'results/summary.json').read_text(encoding='utf-8')))
    else: write_outputs(summary,rows)
    print(json.dumps({'status':'passed','logical_records':summary['logical_records'],
        'scientific_forwards':summary['scientific_forwards'],'parity_forwards':summary['parity_forwards'],
        'read_only':args.verify}))
