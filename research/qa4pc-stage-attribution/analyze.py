"""Analyze all frozen QA4PC jobs without shrinking incomplete denominators."""
import argparse
from collections import Counter,defaultdict
import json
from pathlib import Path

from plan import HERE,CACHE,read,readable,audit,lfhash
from journal import read_events,replay
from runner import adapt_jev,extract


def summarize(plan,refs,journals):
    results={};cost={};journal_hashes={}
    plan_hash=audit.digest(readable(plan))
    for backend in ('jev','qwen'):
        jobs=[j for j in plan['jobs'] if j['backend']==backend]
        path=journals[backend];events=read_events(path)
        state=replay(events,plan_hash=plan_hash,backend=backend,jobs=jobs)
        results[backend]=state['results']
        byphase=defaultdict(lambda:{'completed':0,'input_tokens':0,'output_tokens':0,'callback_seconds':0.0,'unknown_usage_calls':0})
        for job in jobs:
            r=state['results'].get(job['id'])
            if r is None:continue
            if r['status']=='ok':
                if backend=='jev':
                    parsed=adapt_jev(r['detail']['raw_response'],r['detail']['http_status'],job['options'],r['latency_seconds'])
                    if parsed!=r:raise ValueError('Stored Jev result does not reproduce')
                else:
                    d=r['detail'];parsed=extract(d['candidate_logits'],d['full_logsumexp'],d['top_token_id'],d['top_logit'],job['options'])
                    if parsed!=d['parsed'] or parsed['action']!=r['action'] or d['physical_forwards']!=1:
                        raise ValueError('Stored Qwen result does not reproduce')
            k=job['phase']+'_'+job['arm'];a=byphase[k];a['completed']+=1
            a['callback_seconds']+=r['latency_seconds']
            for key in ('input_tokens','output_tokens'):a[key]+=r[key] or 0
            a['unknown_usage_calls']+=r['input_tokens'] is None or r['output_tokens'] is None
        cost[backend]={'planned':len(jobs),'attempts':len(state['started']),'completed':len(state['results']),
            'unexecuted':len(jobs)-len(state['started']),'active_job':state['active_job'],'active_session':state['active_session'],
            'halted':state['halted'],'unknown_usage':state['unknown_usage'],
            'input_tokens':state['input_tokens'],'output_tokens':state['output_tokens'],
            'callback_session_seconds':state['session_seconds'],'by_phase_arm':dict(byphase),
            'sessions':[e['backend_metadata'] for e in events if e['event']=='session_start']}
        journal_hashes[backend]=lfhash(path) if path.exists() else None
    stats={};per_items={};paired={};orders={}
    for backend in ('jev','qwen'):
        for mapping in (0,1):
            grid={(j['item_id'],j['arm'],j['question_id']):j for j in plan['jobs']
                  if j['backend']==backend and j['mapping']==mapping and j['phase']=='main'}
            def action(job):
                r=results[backend].get(job['id'])
                return r['action'] if r and r['status']=='ok' else None
            items=[];fact_counts=Counter();fact_total=0;fact_correct=0;fact_invalid=0;fact_masked=0
            for ref in refs:
                uid=ref['item_id'];pred={arm:action(grid[(uid,arm,None)]) for arm in ('D','G','L')}
                fs={qid:action(grid[(uid,'F',qid)]) for qid in ref['facts']}
                fact_total+=len(fs);fact_correct+=sum(fs[q]==v for q,v in ref['facts'].items())
                fact_invalid+=sum(x is None for x in fs.values())
                for q,v in ref['facts'].items():fact_counts[f'{v}->{fs[q] or "INVALID"}']+=1
                pred['F']=audit.execute(audit.parse_logic(ref['expression']),fs) if all(v is not None for v in fs.values()) else None
                wrong_facts=sum(fs[q]!=v for q,v in ref['facts'].items())
                fact_masked+=all(v is not None for v in fs.values()) and wrong_facts>0 and pred['F']==ref['label']
                items.append({'item_id':uid,'tree_id':ref['tree_id'],'source_label':ref['label'],
                              'predictions':pred,'fact_predictions':fs,'fact_disagreements_including_invalid':wrong_facts})
            key=f'{backend}_mapping{mapping}';per_items[key]=items
            for arm in ('D','G','F','L'):
                trees=defaultdict(list);confusion=Counter();correct=invalid=0
                for item in items:
                    p=item['predictions'][arm];r=item['source_label'];correct+=p==r;invalid+=p is None
                    confusion[f'{r}->{p or "INVALID"}']+=1;trees[item['tree_id']].append(p==r)
                stats[f'{key}_{arm}']={'correct':correct,'total':len(items),'invalid':invalid,
                    'strict_trees_correct':sum(all(x) for x in trees.values()),'trees':len(trees),
                    'source_label_confusion':dict(sorted(confusion.items())),
                    'maybe_to_determined':sum(i['source_label']=='maybe' and i['predictions'][arm] in ('yes','no') for i in items),
                    'determined_to_maybe':sum(i['source_label'] in ('yes','no') and i['predictions'][arm]=='maybe' for i in items)}
            stats[f'{key}_facts']={'correct':fact_correct,'total':fact_total,'invalid':fact_invalid,
                'source_label_confusion':dict(sorted(fact_counts.items())),
                'wrong_valid_facts_masked_at_final':fact_masked}
            paired[key]={'G_to_F_improved':sum(i['predictions']['G']!=i['source_label'] and i['predictions']['F']==i['source_label'] for i in items),
                'G_to_F_regressed':sum(i['predictions']['G']==i['source_label'] and i['predictions']['F']!=i['source_label'] for i in items),
                'D_to_G_improved':sum(i['predictions']['D']!=i['source_label'] and i['predictions']['G']==i['source_label'] for i in items),
                'D_to_G_regressed':sum(i['predictions']['D']==i['source_label'] and i['predictions']['G']!=i['source_label'] for i in items)}
        a,b=per_items[f'{backend}_mapping0'],per_items[f'{backend}_mapping1']
        if [x['item_id'] for x in a]!=[x['item_id'] for x in b]:raise ValueError('Order comparison IDs differ')
        for arm in ('D','G','F','L'):
            both=[(x['predictions'][arm],y['predictions'][arm]) for x,y in zip(a,b)]
            orders[f'{backend}_{arm}']={'valid_both':sum(x is not None and y is not None for x,y in both),
                'changed_valid_actions':sum(x is not None and y is not None and x!=y for x,y in both),
                'invalid_either':sum(x is None or y is None for x,y in both)}
    return {'study':plan['study'],'status':'exploratory source agreement; no new human adjudication',
        'plan_sha256':plan_hash,'journal_lf_sha256':journal_hashes,'metrics':stats,'transitions':paired,
        'order_sensitivity':orders,'cost':cost,'per_item':per_items,'new_human_labels':0}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=('build','verify'));a=p.parse_args()
    plan=read(CACHE/'plan.json');refs=read(CACHE/'references.json');freeze=read(HERE/'freeze.json')
    if audit.digest(readable(plan))!=freeze['plan_sha256'] or audit.digest(readable(refs))!=freeze['references_sha256']:
        raise ValueError('Frozen analysis inputs drift')
    paths={b:HERE/'results'/f'{b}.jsonl' for b in ('jev','qwen')}
    report=summarize(plan,refs,paths);raw=readable(report);out=HERE/'report.json'
    if a.command=='build':out.write_bytes(raw)
    elif out.read_bytes().replace(b'\r\n',b'\n')!=raw:raise ValueError('Derived report differs')
    print(json.dumps({'metrics':{k:{x:v[x] for x in ('correct','total','invalid')} for k,v in report['metrics'].items()},
                      'transitions':report['transitions'],'order_sensitivity':report['order_sensitivity'],
                      'cost':{k:{x:v[x] for x in ('planned','attempts','completed','input_tokens','output_tokens','callback_session_seconds')} for k,v in report['cost'].items()}}))


if __name__=='__main__':main()
