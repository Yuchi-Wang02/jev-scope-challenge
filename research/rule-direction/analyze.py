"""Replay frozen requests and saved observations; no inference or label updates."""
import argparse
from collections import Counter
import json
from pathlib import Path
from plan import HERE,ROOT,existing,encoded,digest,lfhash
from specification import grammar_control


def load(path):return json.loads(path.read_bytes())


def build(directory):
    manifest=load(HERE/'manifest.json');freeze=load(HERE/'freeze.json')
    grid=load(HERE/'request_plan.json');cases=load(HERE/'cases.json')
    if digest(encoded(grid))!=manifest['plan_sha256'] or digest(encoded(cases))!=manifest['case_sha256']:raise ValueError('Frozen data drift')
    if any(lfhash(ROOT/name)!=sha for name,sha in freeze['source_hashes_lf'].items()):raise ValueError('Frozen code drift')
    lookup={c['id']:c for c in cases}
    if any(grammar_control(c['state'])!=c['reference'] for c in cases):raise ValueError('Grammar baseline drift')
    observations=[];backends={}
    for backend in ('jev','qwen'):
        jobs=[j for j in grid['jobs'] if j['backend']==backend]
        events=existing.journal.read_events(directory/(backend+'.jsonl'))
        state=existing.journal.replay(events,plan_hash=manifest['plan_sha256'],backend=backend,jobs=jobs)
        complete=(len(state['results'])==len(jobs) and state['active_job'] is None and state['active_session'] is None and not state['halted'])
        metadata=[e['backend_metadata'] for e in events if e['event']=='session_start']
        for j in jobs:
            result=state['results'].get(j['id']);action=None
            if result:
                d=result['detail']
                if backend=='jev' and 'raw_response' in d:
                    reread=existing.adapt_jev(d['raw_response'],d['http_status'],j['options'],result['latency_seconds'])
                    if reread['action']!=result['action'] or reread['status']!=result['status']:raise ValueError('Jev action drift')
                if backend=='qwen' and result['status']=='ok':
                    reread=existing.parse_generated(d['decoded_body'],arm='semantic',options=j['options'],
                        ended_eos=d['ended_eos'],unsupported_special=d['unsupported_special'])
                    if reread['action']!=result['action']:raise ValueError('Qwen parse drift')
                    if len(d['output_ids'])!=result['output_tokens'] or d['physical_forwards']!=len(d['output_ids']):raise ValueError('Forward/token mismatch')
                action=result['action']
            case=lookup.get(j['item_id'])
            ref=case['reference'] if case else j['expected_smoke_action']
            observations.append({'job_id':j['id'],'item_id':j['item_id'],'backend':backend,
                'phase':j['phase'],'mapping':j['mapping'],'family_id':j['tree_id'],
                'relation':case['relation'] if case else None,'fact_state':case['fact_state'] if case else None,
                'reference':ref,'executed':result is not None,'action':action,'correct':action==ref,
                'invalid':result is not None and action is None})
        mine=[o for o in observations if o['backend']==backend];main=[o for o in mine if o['phase']=='main']
        mapped={}
        for mapping in (0,1):
            obs=[o for o in main if o['mapping']==mapping]
            byid={o['item_id']:o for o in obs}
            cells={rel:{fact:{'correct':sum(o['correct'] for o in obs if o['relation']==rel and o['fact_state']==fact),
                'denominator':12,'actions':dict(Counter(str(o['action']) for o in obs if o['relation']==rel and o['fact_state']==fact))}
                for fact in ('positive','negative','unknown')} for rel in ('sufficient','necessary','equivalent')}
            pairs={fact:sum(all(byid[f'r{n:02d}_{rel}_{fact}']['correct'] for rel in ('sufficient','necessary')) for n in range(1,13)) for fact in ('positive','negative')}
            mapped[str(mapping)]={'correct':sum(o['correct'] for o in obs),'denominator':108,
                'executed':sum(o['executed'] for o in obs),'invalid':sum(o['invalid'] for o in obs),'cells':cells,
                'critical_pairs_correct':pairs,'critical_pairs_denominator_each':12,
                'unknown_triples_correct':sum(all(byid[f'r{n:02d}_{rel}_unknown']['correct'] for rel in ('sufficient','necessary','equivalent')) for n in range(1,13)),
                'strict_families_correct':sum(all(o['correct'] for o in obs if o['family_id']==f'r{n:02d}') for n in range(1,13)),
                'false_commitments':sum(o['reference']=='maybe' and o['action'] in ('yes','no') for o in obs),
                'false_commitment_denominator':60,'unnecessary_deferrals':sum(o['reference']!='maybe' and o['action']=='maybe' for o in obs),
                'determined_denominator':48}
        bykey={(o['item_id'],o['mapping']):o for o in main}
        signatures={}
        for name,rel,fact,action in (('necessary_positive_as_yes','necessary','positive','yes'),('sufficient_negative_as_no','sufficient','negative','no')):
            signatures[name]=[f'r{n:02d}' for n in range(1,13) if all(bykey[(f'r{n:02d}_{rel}_{fact}',m)]['action']==action for m in (0,1))]
        costs={phase:{'calls':sum(j['id'] in state['results'] for j in jobs if j['phase']==phase),
            'input_tokens':sum(state['results'][j['id']]['input_tokens'] or 0 for j in jobs if j['phase']==phase and j['id'] in state['results']),
            'output_tokens':sum(state['results'][j['id']]['output_tokens'] or 0 for j in jobs if j['phase']==phase and j['id'] in state['results']),
            'callback_seconds':sum(state['results'][j['id']]['latency_seconds'] for j in jobs if j['phase']==phase and j['id'] in state['results'])}
            for phase in ('smoke','main')}
        backends[backend]={'complete':complete,'attempts':len(state['started']),'results':len(state['results']),
            'halted':state['halted'],'unknown_usage':state['unknown_usage'],'sessions':state['sessions'],
            'session_seconds':state['session_seconds'],'costs':costs,'mapping':mapped,
            'smoke_correct':sum(o['correct'] for o in mine if o['phase']=='smoke'),'smoke_denominator':6,
            'mapping_disagreements':sum(bykey[(c['id'],0)]['action']!=bykey[(c['id'],1)]['action'] for c in cases),
            'both_mappings_correct':sum(all(bykey[(c['id'],m)]['correct'] for m in (0,1)) for c in cases),
            'critical_signature_families':signatures,'exploratory_screen_met':any(len(v)>=3 for v in signatures.values()),
            'physical_forwards':sum(r['detail'].get('physical_forwards',0) for r in state['results'].values()) if backend=='qwen' else None,
            'backend_metadata':metadata,'journal_sha256':lfhash(directory/(backend+'.jsonl'))}
    return {'complete':all(b['complete'] for b in backends.values()),'study':'rule-direction-v1',
        'plan_sha256':manifest['plan_sha256'],'vocabulary_families':12,'logical_patterns':3,'inputs':108,
        'reference_updates':0,'independent_human_reviews':0,'always_maybe_correct_per_mapping':60,
        'grammar_control_correct':108,'backends':backends,'observations':observations}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=('build','verify'));p.add_argument('--directory',type=Path,default=HERE/'results');a=p.parse_args()
    report=build(a.directory);path=HERE/'report.json'
    if a.command=='build':path.write_bytes(encoded(report))
    elif encoded(load(path))!=encoded(report):raise ValueError('Derived report drift')
    print(json.dumps({'complete':report['complete'],'backends':{name:{k:b[k] for k in ('complete','attempts','smoke_correct','mapping_disagreements','critical_signature_families','exploratory_screen_met')} for name,b in report['backends'].items()}}))
