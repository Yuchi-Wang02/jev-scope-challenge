"""Replay frozen inputs and journals; report incomplete coverage without fake zeros."""
import argparse
from collections import Counter,defaultdict
import importlib.util
import json
import math
from pathlib import Path

from compile_plan import ROOT,HERE,CACHE,readable,audit,lfhash,ORDERS
from observations import adapt_jev,extract
from readout import parse_generated,strict_majority

spec=importlib.util.spec_from_file_location('interface_analysis_journal',ROOT/'research/qa4pc-stage-attribution/journal.py')
journal=importlib.util.module_from_spec(spec);spec.loader.exec_module(journal)


def equivalent(a,b):
    if type(a)==float and type(b)==float:return math.isfinite(a) and math.isfinite(b) and math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12)
    if type(a)!=type(b):return False
    if isinstance(a,dict):return a.keys()==b.keys() and all(equivalent(a[k],b[k]) for k in a)
    if isinstance(a,list):return len(a)==len(b) and all(equivalent(x,y) for x,y in zip(a,b))
    return a==b


def summarize(plan,refs,paths):
    manifest=json.loads((HERE/'plan_manifest.json').read_bytes())
    if audit.digest(readable(plan))!=manifest['plan_sha256'] or audit.digest(readable(refs))!=manifest['references_sha256']:
        raise ValueError('Frozen private artifacts mismatch')
    if len(refs)!=24 or len({r['tree_id'] for r in refs})!=12:raise ValueError('Reference grain mismatch')
    rm={r['item_id']:r for r in refs};results={};cost={};smokes=[];hashes={}
    for backend in ('jev','qwen'):
        jobs=[j for j in plan['jobs'] if j['backend']==backend]
        events=journal.read_events(paths[backend]);state=journal.replay(events,
            plan_hash=manifest['plan_sha256'],backend=backend,jobs=jobs)
        if state['active_job'] is not None or state['active_session'] is not None:raise ValueError('Live/unresolved journal; do not publish as settled')
        results.update(state['results']);hashes[backend]=lfhash(paths[backend])
        grouped=defaultdict(lambda:{'calls':0,'input_tokens':0,'output_tokens':0,'callback_seconds':0.,'physical_forwards':0,'unknown_usage_calls':0})
        for j in jobs:
            if j['id'] not in results:continue
            r=results[j['id']];d=r['detail'];g=grouped[j['phase']+'_'+j['arm']];g['calls']+=1
            g['callback_seconds']+=r['latency_seconds'];g['physical_forwards']+=d.get('physical_forwards',0)
            for k in ('input_tokens','output_tokens'):
                if r[k] is not None:g[k]+=r[k]
            g['unknown_usage_calls']+=int(r['input_tokens'] is None or r['output_tokens'] is None)
            if r['status']=='ok':
                if backend=='jev':
                    checked=adapt_jev(d['raw_response'],d['http_status'],j['options'],r['latency_seconds'])
                    if checked['status']!='ok' or checked['action']!=r['action']:raise ValueError('Native action mismatch')
                else:
                    checked=extract(d['first_candidate_logits'],d['first_full_logsumexp'],d['first_top_token_id'],d['first_top_logit'],j['options'])
                    if not equivalent(checked,d['first_letter_readout']):raise ValueError('Logit observation mismatch')
                    if j['arm']=='finite':action=checked['action']
                    else:
                        parsed=parse_generated(d['decoded_body'],arm=j['arm'],options=j['options'],
                            ended_eos=d['ended_eos'],unsupported_special=d['unsupported_special'])
                        if parsed!=d['generated']:raise ValueError('Generated parser mismatch')
                        if len(d['output_ids'])!=r['output_tokens']:raise ValueError('Generated token accounting mismatch')
                        action=parsed['action']
                    if action!=r['action']:raise ValueError('Local action mismatch')
                    if d['physical_forwards']!=(1 if j['arm']=='finite' else r['output_tokens']):raise ValueError('Forward accounting mismatch')
            if j['phase']=='smoke':
                if r['status']=='ok' and d['smoke']!={'expected':j['expected_smoke_action'],'observed':r['action'],
                    'correct':r['action']==j['expected_smoke_action'],'semantic_accuracy_is_gate':False}:raise ValueError('Smoke annotation mismatch')
                smokes.append({'job_id':j['id'],'arm':j['arm'],'expected':j['expected_smoke_action'],
                    'action':r['action'],'status':r['status']})
        cost[backend]={'planned':len(jobs),'started':len(state['started']),'completed':len(state['results']),
            'halted':state['halted'],'unknown_usage':state['unknown_usage'],
            'input_tokens':state['input_tokens'],'output_tokens':state['output_tokens'],
            'session_seconds':state['session_seconds'],'by_phase_arm':dict(grouped),
            'loads':[e['backend_metadata'] for e in events if e['event']=='session_start']}
    observations=[]
    for j in plan['jobs']:
        if j['phase']!='main':continue
        r=results.get(j['id']);observations.append({'job_id':j['id'],'item_id':j['item_id'],
            'tree_id':j['tree_id'],'arm':j['arm'],'mapping':j['mapping'],'reference':rm[j['item_id']]['label'],
            'executed':r is not None,'action':r['action'] if r else None,
            'status':r['status'] if r else 'not_executed'})
    tables={};stability={};aggregates={}
    for arm in ('native','finite','letter','semantic'):
        part=[o for o in observations if o['arm']==arm];rows=[];peritem={}
        for mapping in range(6):
            sub=[o for o in part if o['mapping']==mapping];done=[o for o in sub if o['executed']]
            rows.append({'mapping':mapping,'options':list(ORDERS[mapping]),'denominator':24,'executed':len(done),
                'correct':sum(o['action']==o['reference'] for o in done) if done else None,
                'invalid':sum(o['action'] is None for o in done),
                'confusion':dict(sorted(Counter(o['reference']+'->'+str(o['action']) for o in done).items())),
                'strict_trees':sum(all(o['executed'] and o['action']==o['reference'] for o in sub if o['tree_id']==tid)
                    for tid in {r['tree_id'] for r in refs}) if len(done)==24 else None})
        tables[arm]=rows
        for uid in rm:
            subset=sorted([o for o in part if o['item_id']==uid],key=lambda o:o['mapping'])
            complete=all(o['executed'] for o in subset)
            actions=[o['action'] for o in subset]
            peritem[uid]={'complete':complete,'actions':actions,'aggregate':strict_majority(actions) if complete else None}
        stable_valid=sum(x['complete'] and all(a is not None for a in x['actions']) and len(set(x['actions']))==1 for x in peritem.values())
        stability[arm]={'denominator':24,'all_six_executed':sum(x['complete'] for x in peritem.values()),
            'all_six_valid':sum(x['complete'] and all(a is not None for a in x['actions']) for x in peritem.values()),
            'all_six_valid_and_same':stable_valid,
            'all_six_correct':sum(x['complete'] and all(a==rm[uid]['label'] for a in x['actions']) for uid,x in peritem.items())}
        aggregates[arm]={'denominator':24,'complete_items':sum(x['complete'] for x in peritem.values()),
            'correct':sum(x['complete'] and x['aggregate']==rm[uid]['label'] for uid,x in peritem.items()),
            'abstentions':sum(x['complete'] and x['aggregate'] is None for x in peritem.values()),
            'items':peritem}
    paired={}
    lookup={(o['item_id'],o['mapping'],o['arm']):o for o in observations}
    for a,b in (('finite','letter'),('letter','semantic'),('native','semantic')):
        pair=[]
        for m in range(6):
            sub=[(lookup[uid,m,a],lookup[uid,m,b]) for uid in rm]
            done=[(x,y) for x,y in sub if x['executed'] and y['executed']]
            pair.append({'mapping':m,'executed_both':len(done),
                'fixes':sum(x['action']!=x['reference'] and y['action']==y['reference'] for x,y in done),
                'regressions':sum(x['action']==x['reference'] and y['action']!=y['reference'] for x,y in done),
                'valid_both':sum(x['action'] is not None and y['action'] is not None for x,y in done),
                'valid_changes':sum(x['action'] is not None and y['action'] is not None and x['action']!=y['action'] for x,y in done),
                'invalid_either':sum(x['action'] is None or y['action'] is None for x,y in done)})
        paired[a+'->'+b]=pair
    return {'study':manifest['study'],'plan_sha256':manifest['plan_sha256'],'journal_sha256':hashes,
        'complete':all(c['completed']==c['planned'] and not c['halted'] for c in cost.values()),
        'unit':'24 scenarios clustered in 12 policy trees; six repeated mappings',
        'source_label_counts':dict(Counter(r['label'] for r in refs)),
        'constant_output_agreement':{l:sum(r['label']==l for r in refs) for l in ('yes','no','maybe')},
        'cost':cost,'smokes':smokes,'per_mapping':tables,'stability':stability,
        'strict_majority':aggregates,'paired':paired,'observations':observations}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=('build','verify'))
    a=p.parse_args();plan=json.loads((CACHE/'plan.json').read_bytes());refs=json.loads((CACHE/'references.json').read_bytes())
    report=summarize(plan,refs,{b:HERE/'results'/f'{b}.jsonl' for b in ('jev','qwen')})
    output=HERE/'report.json'
    if a.command=='build':output.write_bytes(readable(report))
    elif not equivalent(report,json.loads(output.read_bytes())):raise ValueError('Report drift')
    print(json.dumps({'complete':report['complete'],'per_mapping':{k:[r['correct'] for r in rows] for k,rows in report['per_mapping'].items()},
        'invalid':{k:[r['invalid'] for r in rows] for k,rows in report['per_mapping'].items()},'stability':report['stability']}))


if __name__=='__main__':main()
