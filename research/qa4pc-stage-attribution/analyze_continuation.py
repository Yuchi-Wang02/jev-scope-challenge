"""Analyze separately replayed original and amended journals without replacing either."""
import argparse
from collections import Counter,defaultdict
import json
import math
from pathlib import Path

from plan import HERE,CACHE,read,readable,audit,lfhash
from journal import read_events,replay
from runner import adapt_jev,extract
from continuation import predecessor,make_plan


def combined_state(parent,journals,backend):
    jobs=[j for j in parent['jobs'] if j['backend']==backend]
    path=journals[backend];events=read_events(path)
    state=replay(events,plan_hash=audit.digest(readable(parent)),backend=backend,jobs=jobs)
    if backend=='jev':return state,events,{'original':lfhash(path)}
    predecessor(parent,events)
    successor=make_plan(parent,events)
    successor_hash=audit.digest(readable(successor))
    freeze=read(HERE/'continuation_freeze.json')
    if successor_hash!=freeze['plan_sha256']:raise ValueError('Successor plan differs from freeze')
    path2=journals['qwen_continuation'];events2=read_events(path2)
    suffix=replay(events2,plan_hash=successor_hash,backend='qwen',jobs=successor['jobs'])
    if set(state['started']) & set(suffix['started']):raise ValueError('Duplicate physical job across journals')
    merged={**suffix,'started':state['started']+suffix['started'],
        'results':{**state['results'],**suffix['results']},'original_halted':state['halted'],
        'sessions':state['sessions']+suffix['sessions'],
        'session_seconds':state['session_seconds']+suffix['session_seconds'],
        'input_tokens':state['input_tokens']+suffix['input_tokens'],
        'output_tokens':state['output_tokens']+suffix['output_tokens'],
        'unknown_usage':state['unknown_usage'] or suffix['unknown_usage']}
    if merged['started']!=[j['id'] for j in jobs[:len(merged['started'])]]:raise ValueError('Merged order differs')
    return merged,events+events2,{'original':lfhash(path),'continuation':lfhash(path2)}


def equivalent(a,b):
    """Float-only tolerance for Python-version summation differences, never labels."""
    if type(a)==float and type(b)==float:
        return math.isfinite(a) and math.isfinite(b) and math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12)
    if type(a)!=type(b):return False
    if isinstance(a,dict):return a.keys()==b.keys() and all(equivalent(a[k],b[k]) for k in a)
    if isinstance(a,list):return len(a)==len(b) and all(equivalent(x,y) for x,y in zip(a,b))
    return a==b


def summarize(plan,refs,journals):
    results={};cost={};journal_hashes={};smokes={}
    plan_hash=audit.digest(readable(plan))
    for backend in ('jev','qwen'):
        jobs=[j for j in plan['jobs'] if j['backend']==backend]
        state,events,hashes=combined_state(plan,journals,backend)
        results[backend]=state['results']
        smokes[backend]=[]
        byphase=defaultdict(lambda:{'completed':0,'input_tokens':0,'output_tokens':0,'callback_seconds':0.0,'unknown_usage_calls':0})
        for job in jobs:
            r=state['results'].get(job['id'])
            if r is None:continue
            if job['phase']=='smoke':
                observed=r['detail'].get('smoke_observed_action',r['action'])
                smokes[backend].append({'job_id':job['id'],'expected':job['expected_smoke_action'],
                    'observed':observed,'matches':observed==job['expected_smoke_action'],
                    'status':r['status'],'gate_failed':r['detail'].get('smoke_gate_failed',False)})
                amended=r['detail'].get('amended_smoke_policy')
                if amended is not None and amended!={'expected':job['expected_smoke_action'],'observed':r['action'],
                    'correct':r['status']=='ok' and r['action']==job['expected_smoke_action'],'semantic_accuracy_is_gate':False}:
                    raise ValueError('Amended smoke annotation differs')
            if backend=='qwen' and r['detail'].get('smoke_gate_failed'):
                d=r['detail'];parsed=extract(d['candidate_logits'],d['full_logsumexp'],d['top_token_id'],d['top_logit'],job['options'])
                if (not equivalent(parsed,d['parsed']) or parsed['action']!=d['smoke_observed_action'] or
                    r['action'] is not None or r['status']!='protocol_error' or
                    parsed['action']==job['expected_smoke_action'] or d['physical_forwards']!=1):
                    raise ValueError('Stored smoke failure does not reproduce')
            if r['status']=='ok':
                if backend=='jev':
                    parsed=adapt_jev(r['detail']['raw_response'],r['detail']['http_status'],job['options'],r['latency_seconds'])
                    if not equivalent(parsed,r):raise ValueError('Stored Jev result does not reproduce')
                else:
                    d=r['detail'];parsed=extract(d['candidate_logits'],d['full_logsumexp'],d['top_token_id'],d['top_logit'],job['options'])
                    if not equivalent(parsed,d['parsed']) or parsed['action']!=r['action'] or d['physical_forwards']!=1:
                        raise ValueError('Stored Qwen result does not reproduce')
            k=job['phase']+'_'+job['arm'];a=byphase[k];a['completed']+=1
            a['callback_seconds']+=r['latency_seconds']
            for key in ('input_tokens','output_tokens'):a[key]+=r[key] or 0
            a['unknown_usage_calls']+=r['input_tokens'] is None or r['output_tokens'] is None
        cost[backend]={'planned':len(jobs),'attempts':len(state['started']),'completed':len(state['results']),
            'unexecuted':len(jobs)-len(state['started']),'active_job':state['active_job'],'active_session':state['active_session'],
            'halted':state['halted'],'original_halted':state.get('original_halted',False),'unknown_usage':state['unknown_usage'],
            'input_tokens':state['input_tokens'],'output_tokens':state['output_tokens'],
            'callback_session_seconds':state['session_seconds'],'by_phase_arm':dict(byphase),
            'sessions':[e['backend_metadata'] for e in events if e['event']=='session_start']}
        journal_hashes[backend]=hashes
    stats={};per_items={};paired={};orders={}
    for backend in ('jev','qwen'):
        for mapping in (0,1):
            grid={(j['item_id'],j['arm'],j['question_id']):j for j in plan['jobs']
                  if j['backend']==backend and j['mapping']==mapping and j['phase']=='main'}
            def action(job):
                r=results[backend].get(job['id'])
                return r['action'] if r and r['status']=='ok' else None
            items=[];fact_counts=Counter();fact_total=0;fact_correct=0;fact_invalid=0;fact_masked=0;fact_executed=0
            for ref in refs:
                uid=ref['item_id'];pred={arm:action(grid[(uid,arm,None)]) for arm in ('D','G','L')}
                fs={qid:action(grid[(uid,'F',qid)]) for qid in ref['facts']}
                executed={arm:grid[(uid,arm,None)]['id'] in results[backend] for arm in ('D','G','L')}
                f_done={qid:grid[(uid,'F',qid)]['id'] in results[backend] for qid in ref['facts']}
                executed['F']=all(f_done.values());fact_executed+=sum(f_done.values())
                fact_total+=len(fs);fact_correct+=sum(fs[q]==v for q,v in ref['facts'].items())
                fact_invalid+=sum(fs[q] is None and f_done[q] for q in fs)
                for q,v in ref['facts'].items():fact_counts[f'{v}->{fs[q] or ("INVALID" if f_done[q] else "NOT_RUN")}']+=1
                pred['F']=audit.execute(audit.parse_logic(ref['expression']),fs) if all(v is not None for v in fs.values()) else None
                wrong_facts=sum(fs[q]!=v for q,v in ref['facts'].items()) if executed['F'] else None
                fact_masked+=all(v is not None for v in fs.values()) and wrong_facts>0 and pred['F']==ref['label']
                items.append({'item_id':uid,'tree_id':ref['tree_id'],'source_label':ref['label'],
                              'predictions':pred,'executed':executed,'fact_predictions':fs,'fact_disagreements_including_invalid':wrong_facts})
            key=f'{backend}_mapping{mapping}';per_items[key]=items
            for arm in ('D','G','F','L'):
                trees=defaultdict(list);confusion=Counter();correct=invalid=completed=0
                for item in items:
                    p=item['predictions'][arm];r=item['source_label'];done=item['executed'][arm]
                    correct+=p==r;invalid+=p is None and done;completed+=done
                    confusion[f'{r}->{p or ("INVALID" if done else "NOT_RUN")}']+=1;trees[item['tree_id']].append(p==r)
                stats[f'{key}_{arm}']={'correct':correct if completed else None,'total':len(items),'invalid':invalid,
                    'evaluated':completed,'unexecuted':len(items)-completed,
                    'strict_trees_correct':sum(all(x) for x in trees.values()) if completed==len(items) else None,'trees':len(trees),
                    'source_label_confusion':dict(sorted(confusion.items())),
                    'maybe_to_determined':sum(i['source_label']=='maybe' and i['predictions'][arm] in ('yes','no') for i in items),
                    'determined_to_maybe':sum(i['source_label'] in ('yes','no') and i['predictions'][arm]=='maybe' for i in items)}
            stats[f'{key}_facts']={'correct':fact_correct if fact_executed else None,'total':fact_total,'invalid':fact_invalid,
                'evaluated':fact_executed,'unexecuted':fact_total-fact_executed,
                'source_label_confusion':dict(sorted(fact_counts.items())),
                'wrong_valid_facts_masked_at_final':fact_masked}
            paired[key]={'comparison_available':all(all(i['executed'][a] for a in ('D','G','F')) for i in items),
                'G_to_F_improved':sum(i['predictions']['G']!=i['source_label'] and i['predictions']['F']==i['source_label'] for i in items),
                'G_to_F_regressed':sum(i['predictions']['G']==i['source_label'] and i['predictions']['F']!=i['source_label'] for i in items),
                'D_to_G_improved':sum(i['predictions']['D']!=i['source_label'] and i['predictions']['G']==i['source_label'] for i in items),
                'D_to_G_regressed':sum(i['predictions']['D']==i['source_label'] and i['predictions']['G']!=i['source_label'] for i in items)}
            if not paired[key]['comparison_available']:
                paired[key]={k:v if k=='comparison_available' else None for k,v in paired[key].items()}
        a,b=per_items[f'{backend}_mapping0'],per_items[f'{backend}_mapping1']
        if [x['item_id'] for x in a]!=[x['item_id'] for x in b]:raise ValueError('Order comparison IDs differ')
        for arm in ('D','G','F','L'):
            both=[(x['predictions'][arm],y['predictions'][arm]) for x,y in zip(a,b)]
            orders[f'{backend}_{arm}']={'valid_both':sum(x is not None and y is not None for x,y in both),
                'changed_valid_actions':sum(x is not None and y is not None and x!=y for x,y in both),
                'invalid_either':sum((x['executed'][arm] and x['predictions'][arm] is None) or
                                    (y['executed'][arm] and y['predictions'][arm] is None) for x,y in zip(a,b)),
                'unexecuted_either':sum(not x['executed'][arm] or not y['executed'][arm] for x,y in zip(a,b))}
    letters=defaultdict(Counter);masses=[];ties=[]
    for job in plan['jobs']:
        if job['backend']!='qwen' or job['phase']!='main':continue
        r=results['qwen'].get(job['id'])
        if not r or r['status']!='ok':continue
        d=r['detail'];p=d['parsed'];letters[f"{job['arm']}_mapping{job['mapping']}"][p['letter'] or 'TIE']+=1
        masses.append(p['full_vocabulary_candidate_mass'])
        if p['exact_tie']:ties.append({'job_id':job['id'],'logits':d['candidate_logits']})
    diagnostics={'main_exact_ties':ties,'letter_counts':{k:dict(v) for k,v in letters.items()},
        'candidate_mass':{'count':len(masses),'minimum':min(masses) if masses else None,
            'mean':sum(masses)/len(masses) if masses else None,'maximum':max(masses) if masses else None}}
    return {'study':plan['study'],'status':'outcome-aware gate amendment; exploratory source agreement; no new human adjudication',
        'qwen_readout_diagnostics':diagnostics,
        'continuation_plan_sha256':read(HERE/'continuation_freeze.json')['plan_sha256'],
        'plan_sha256':plan_hash,'journal_lf_sha256':journal_hashes,'metrics':stats,'transitions':paired,
        'order_sensitivity':orders,'cost':cost,'smoke_results':smokes,'per_item':per_items,'new_human_labels':0}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=('build','verify'));a=p.parse_args()
    plan=read(CACHE/'plan.json');refs=read(CACHE/'references.json');freeze=read(HERE/'freeze.json')
    if audit.digest(readable(plan))!=freeze['plan_sha256'] or audit.digest(readable(refs))!=freeze['references_sha256']:
        raise ValueError('Frozen analysis inputs drift')
    paths={b:HERE/'results'/f'{b}.jsonl' for b in ('jev','qwen')}
    paths['qwen_continuation']=HERE/'results/qwen_continuation.jsonl'
    report=summarize(plan,refs,paths);raw=readable(report);out=HERE/'continuation_report.json'
    if a.command=='build':out.write_bytes(raw)
    elif not equivalent(read(out),report):raise ValueError('Derived report differs')
    print(json.dumps({'metrics':{k:{x:v[x] for x in ('correct','total','invalid')} for k,v in report['metrics'].items()},
                      'transitions':report['transitions'],'order_sensitivity':report['order_sensitivity'],
                      'cost':{k:{x:v[x] for x in ('planned','attempts','completed','input_tokens','output_tokens','callback_session_seconds')} for k,v in report['cost'].items()}}))


if __name__=='__main__':main()
