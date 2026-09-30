"""Offline replay of the bounded prefill control, with no new inference."""
import argparse
import json
import math
from statistics import mean

import finite_readout as study
from execution_journal import read_events, replay, exclusive_lock, stop_reason, outcome
from analyze_comparison import condition_resources
from paired_metrics import score_condition


def close_tree(a,b):
    if type(a) is float and type(b) is float:
        return math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-12)
    if type(a) is not type(b):return False
    if isinstance(a,dict):return a.keys()==b.keys() and all(close_tree(a[k],b[k]) for k in a)
    if isinstance(a,list):return len(a)==len(b) and all(close_tree(x,y) for x,y in zip(a,b))
    return a==b


def analyze(plan,freeze,events):
    state=replay(events,plan_hash=freeze['plan_sha256'],backend='qwen',jobs=plan['jobs'])
    jobs={j['id']:j for j in plan['jobs']}
    results=state['results']
    for ident,r in results.items():
        j=jobs[ident];d=r['detail']
        if r['status']=='execution_error':continue
        if r['input_tokens']!=len(j['input_ids']) or r['output_tokens']!=0:
            raise ValueError('Usage differs from prefill contract')
        if r['status']=='protocol_error' and d.get('error')=='nonfinite_logits_or_forward_count':continue
        expected=study.extract(d['candidate_logits'],d['full_logsumexp'],d['top_token_id'],d['top_logit'],j['options'])
        if not close_tree(expected,d['parsed']) or d['physical_forwards']!=1 or d['use_cache'] is not True or d['logits_to_keep']!=1:
            raise ValueError('Logit readout or physical call count changed')
        smoke_miss=j['phase']=='smoke' and expected['action']!=j['expected_smoke_action']
        if (r['status']!=('protocol_error' if smoke_miss else 'ok') or
                r['action']!=(None if smoke_miss else expected['action'])):
            raise ValueError('Saved semantic decision differs from readout')
    refs=study.read(study.PARENT/'references.json')
    old=study.read(study.PARENT/'results/comparison.json')
    conditions={};predictions={}
    smoke=[j for j in plan['jobs'] if j['phase']=='smoke']
    smoke_pass=sum(j['id'] in results and results[j['id']]['status']=='ok' and
                   results[j['id']]['action']==j['expected_smoke_action'] for j in smoke)
    if any(j['phase']=='main' for j in plan['jobs'] if j['id'] in state['started']) and smoke_pass!=8:
        raise ValueError('Main tasks started without a complete smoke pass')
    ledger={j['id']:{'state':'finished','result_status':results[j['id']]['status'],
             **{k:results[j['id']][k] for k in ('input_tokens','output_tokens','latency_seconds')}}
             for j in plan['jobs'] if j['id'] in results}
    for j in plan['jobs']:
        ledger.setdefault(j['id'],{'state':'started_without_result' if j['id'] in state['started'] else 'not_started'})
    for order in (0,1):
        name=f'prefill_order{order}';cohort=[j for j in plan['jobs'] if j.get('condition')==name]
        finished=[j for j in cohort if j['id'] in results]
        complete=len(finished)==len(cohort)
        rows=[{'item_id':j['item_id'],'action':results[j['id']]['action']} for j in finished]
        prior=old['conditions'][f'qwen_direct_order{order}']['metric']
        prev={ident:action for p in prior['pair_records'] for ident,action in zip(p['item_ids'],p['predictions'])}
        targets={ident:action for p in refs for ident,action in zip(p['item_ids'],p['reference_actions'])}
        transitions=[{'item_id':r['item_id'],'reference':targets[r['item_id']],
            'previous_direct':prev[r['item_id']],'prefill':r['action'],
            'action_changed':prev[r['item_id']]!=r['action'],
            'status':('unchanged_agreement' if (prev[r['item_id']]==targets[r['item_id']])==(r['action']==targets[r['item_id']])
                      else 'improved' if r['action']==targets[r['item_id']] else 'regressed')} for r in rows]
        quality=[results[j['id']]['detail']['parsed'] for j in finished if results[j['id']]['status']=='ok']
        mass=[r['full_vocabulary_candidate_mass'] for r in quality]
        conditions[name]={'complete':complete,'planned':len(cohort),'finished':len(finished),
            'metric':score_condition(refs,rows,condition=name) if complete else None,
            'prior_direct_metric':prior,'transitions':transitions,
            'improved':sum(t['status']=='improved' for t in transitions),
            'regressed':sum(t['status']=='regressed' for t in transitions),
            'changed_action':sum(t['action_changed'] for t in transitions),
            'resources':condition_resources(cohort,ledger),
            'probability_mass':{'minimum':min(mass) if mass else None,'mean':mean(mass) if mass else None,
                                'maximum':max(mass) if mass else None,'observations':len(mass)},
            'unconstrained_top_is_legal':sum(r['unconstrained_top_is_candidate'] for r in quality)}
        predictions[name]={r['item_id']:r['action'] for r in rows}
    left,right=predictions.values()
    valid=[i for i in left if i in right and left[i] is not None and right[i] is not None]
    reason=stop_reason(state,'qwen',plan['jobs'],plan['limits'],state['session_seconds'])
    return {'study':study.STUDY,'status':reason or 'stopped','source_basis':plan['reference_basis'],
        'source_truth_verified':False,'independent_human_reviews':0,'parent_scenes':12,
        'smoke':{'planned':8,'passed':smoke_pass},'conditions':conditions,
        'order_effects':{'available':all(c['complete'] for c in conditions.values()),'valid_in_both':len(valid),
                         'changed_valid_action':sum(left[i]!=right[i] for i in valid)},
        'controls':old['controls'], 'jev_native_context':{n:c['metric'] for n,c in old['conditions'].items() if n.startswith('jev_native')},
        'resources':{'attempts':len(state['started']),'finished':len(results),'input_tokens':state['input_tokens'],
            'output_tokens':state['output_tokens'],'unknown_usage':state['unknown_usage'],
            'physical_forwards_reported':sum(r['detail'].get('physical_forwards',0) for r in results.values()),
            'closed_session_seconds':state['session_seconds'],
            'session_incomplete':state['active_session'] is not None,
            'overruns':outcome(reason,state,'qwen',plan['limits'])['overruns'],
            'sessions':[e['backend_metadata'] for e in events if e['event']=='session_start']},
        'new_model_calls_during_analysis':0,'parent_comparison_sha256':freeze['parent_hashes_lf']['results/comparison.json']}


def markdown(r):
    ratio=lambda x:f"{x['numerator']}/{x['denominator']}"
    lines=['# Single-prefill finite-choice results','','Source-label agreement on the same inspected 12 trees /24 inputs. **Zero new human reviews.**',
        'This joint prompt/verbalizer/readout change is an outcome-aware diagnostic, not confirmation.',
        'See the [protocol](PROTOCOL.md) and [source concerns](../source-label-screen/SOURCE_REVIEW.md).','',
        '|Condition|Finished|Item agreement|Both pair members|Invalid|Improved / regressed vs JSON|',
        '|---|---:|---:|---:|---:|---:|']
    for name,c in r['conditions'].items():
        m=c['metric'];values=[ratio(m[k]) for k in ('item_accuracy','pair_both_correct','invalid_output')] if m else ['unavailable']*3
        lines.append(f"|{name}|{c['finished']}/{c['planned']}|"+'|'.join(values)+f"|{c['improved']} / {c['regressed']}|")
    lines+=['','The prior direct JSON results are 11/24 and 12/24, with 3/12 fully matching pairs in each mapping.',
            'Jev native context is 18/24 and 8/12 pairs in both mappings; this is not a new API run.','',
            '|Non-model control|Item agreement|Both pair members|','|---|---:|---:|']
    for name,m in r['controls'].items():lines.append(f"|{name}|{ratio(m['item_accuracy'])}|{ratio(m['pair_both_correct'])}|")
    lines+=['','## Candidate probability mass and work','',
        '|Condition|Raw candidate mass: min / mean / max|Unconstrained top is legal|Input tokens|Callback seconds|',
        '|---|---|---:|---:|---:|']
    for name,c in r['conditions'].items():
        m=c['probability_mass'];mass=' / '.join(f'{m[k]:.6f}' if m[k] is not None else 'unavailable' for k in ('minimum','mean','maximum'))
        cost=c['resources'];lines.append(f"|{name}|{mass}|{c['unconstrained_top_is_legal']}/{m['observations']}|{cost['known_input_tokens']}|{cost['recorded_call_latency_seconds']:.3f}|")
    cost=r['resources']
    lines+=['',f"Smoke: {r['smoke']['passed']}/8 passed. Total attempts: {cost['attempts']}; recorded physical prefills: {cost['physical_forwards_reported']}; "
            f"input tokens: {cost['input_tokens']}; generated tokens: {cost['output_tokens']}. Closed session: {cost['closed_session_seconds']:.3f} seconds.",
            f"Overruns: `{json.dumps(cost['overruns'],sort_keys=True)}`. Status: `{r['status']}`.",
            f"Observed mapping differences: `{json.dumps(r['order_effects'],sort_keys=True)}`.",'',
            'Every condition keeps invalid outputs in its denominator. Raw candidate mass is separate from',
            'probabilities renormalized among four letters; neither is calibrated correctness. The recorded',
            'full-vocabulary normalizer is not independently reconstructible from four stored logits.',
            'Setup, load timing, errors and peak memory are retained in the [raw journal](results/qwen.jsonl).',
            'Prior JSON callback sums were 12.986 and 13.251 seconds in a different session. Hardware serving,',
            'prompt changes and session conditions prevent a controlled architectural-speed claim.','',
            '[Structured report](results/report.json) contains all item transitions, confusion matrices and paired strata.',
            'A legal output by construction is not evidence of semantic improvement. No source label was changed,',
            'and no prefix search, retry, model download or training-review-queue inference was performed.','',
            '```bash','python research/finite-choice-readout/analyze_finite.py verify','```','']
    return '\n'.join(lines).encode()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=('capture','verify'));args=p.parse_args()
    plan,freeze=study.check()
    target=study.HERE/'results/qwen.jsonl'
    if args.command=='capture':
        source=study.ROOT/'.local'/study.STUDY/('execution-'+freeze['plan_sha256'])
        with exclusive_lock(source/'qwen.lock'):
            events=read_events(source/'qwen.jsonl')
            report=analyze(plan,freeze,events)
            if report['resources']['session_incomplete']:raise ValueError('Session still open')
            study.preserve(target,(source/'qwen.jsonl').read_bytes())
    else:report=analyze(plan,freeze,read_events(target))
    report['journal_sha256']=study.sha(target.read_bytes())
    for path,data in ((study.HERE/'results/report.json',study.readable(report)),(study.HERE/'RESULTS.md',markdown(report))):
        if args.command=='capture':study.preserve(path,data)
        elif path.read_bytes().replace(b'\r\n',b'\n')!=data:raise ValueError('Saved report differs')
    print(json.dumps({'status':report['status'],'smoke':report['smoke'],'new_model_calls':0}))


if __name__=='__main__':main()
