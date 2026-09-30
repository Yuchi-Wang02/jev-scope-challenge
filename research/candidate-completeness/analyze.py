"""Recompute declared endpoints from complete recorded grids; no inference."""
import argparse
import math
import statistics
from collections import Counter
from study import ROOT, LABELS, ORDERS, MODEL, PRICE, rows, read, write, smokes, resolve, validate_response, verify_freeze
import local_run
import run as api_run

def endpoints(cases, predictions):
    assert set(predictions)=={c['case_id'] for c in cases}
    assert all(p in LABELS for p in predictions.values())
    parents=sorted({c['parent_id'] for c in cases})
    def correct(c):return predictions[c['case_id']]==c['reference']
    cells={}
    for style in ('explicit','product'):
        for coverage in ('complete','relevant_omission','irrelevant_omission'):
            group=[c for c in cases if c['style']==style and c['coverage']==coverage]
            cells[style+'__'+coverage]={'correct':sum(map(correct,group)),'n':len(group)}
    complete={p:all(correct(c) for c in cases if c['parent_id']==p) for p in parents}
    pairs={}
    for style,coverage,key in [('product','relevant_omission','product_required_change'),
                               ('product','irrelevant_omission','product_harmless_omission'),
                               ('explicit','relevant_omission','explicit_relevant_stability'),
                               ('explicit','irrelevant_omission','explicit_irrelevant_stability')]:
        groups=[[c for c in cases if c['parent_id']==p and c['style']==style and c['coverage'] in ('complete',coverage)] for p in parents]
        assert all(len(g)==2 for g in groups)
        pairs[key]={'both_correct':sum(all(map(correct,g)) for g in groups),'n':len(groups)}
    unknown=[c for c in cases if c['reference']==LABELS[2]]
    determined=[c for c in cases if c['reference']!=LABELS[2]]
    false_commitments=sum(predictions[c['case_id']]!=LABELS[2] for c in unknown)
    needless=sum(predictions[c['case_id']]==LABELS[2] for c in determined)
    return {'correct':sum(map(correct,cases)),'n':len(cases),'complete_parents':sum(complete.values()),
        'parent_n':len(parents),'parent_complete':complete,'cells':cells,'paired':pairs,
        'false_commitments':{'count':false_commitments,'n':len(unknown)},
        'unnecessary_deferrals':{'count':needless,'n':len(determined)},
        'wrong_accepts':{'count':sum(c['reference']==LABELS[1] and predictions[c['case_id']]==LABELS[0] for c in cases),'n':sum(c['reference']==LABELS[1] for c in cases)},
        'wrong_rejects':{'count':sum(c['reference']==LABELS[0] and predictions[c['case_id']]==LABELS[1] for c in cases),'n':sum(c['reference']==LABELS[0] for c in cases)},
        'prediction_counts':dict(Counter(predictions.values())),
        'screen_pass':sum(complete.values())>=10 and false_commitments<=1 and needless<=1,
        'errors':[{'case_id':c['case_id'],'reference':c['reference'],'prediction':predictions[c['case_id']]} for c in cases if not correct(c)]}

def model_metrics(cases,records):
    mappings={str(m):endpoints(cases,{r['case_id']:r['prediction'] for r in records if r['phase']=='primary' and r['option_order']==m}) for m in (0,1)}
    bykey={(r['case_id'],r['option_order']):r for r in records if r['phase']=='primary'}
    smoke={s['case_id']:s['reference'] for s in smokes()}
    smoke_rows=[r for r in records if r['phase']=='smoke']
    return {'mappings':mappings,'strict_complete_parents':sum(all(mappings[str(m)]['parent_complete'][p] for m in (0,1)) for p in mappings['0']['parent_complete']),
        'parent_n':12,'option_order_disagreements':{'count':sum(bykey[(c['case_id'],0)]['prediction']!=bykey[(c['case_id'],1)]['prediction'] for c in cases),'n':72},
        'smoke_correct':sum(r['prediction']==smoke[r['case_id']] for r in smoke_rows),'smoke_n':len(smoke_rows),
        'main_input_tokens':sum(r['input_tokens'] for r in records if r['phase']=='primary'),
        'all_input_tokens':sum(r['input_tokens'] for r in records),
        'main_latency_median_s':statistics.median(r['latency_s'] for r in records if r['phase']=='primary'),
        'all_measured_latency_s':sum(r['latency_s'] for r in records)}

def validate_records(jobs,records):
    assert len(records)==150 and len({r['job_id'] for r in records})==150
    byid={j['job_id']:j for j in jobs};assert {r['job_id'] for r in records}==set(byid)
    for r in records:
        j=byid[r['job_id']]
        assert r['ok'] and all(r[k]==j[k] for k in ('case_id','phase','option_order','request_sha256'))
        assert r['input_tokens']>0 and math.isfinite(r['latency_s']) and r['latency_s']>=0
        assert set(r['probabilities'])==set(LABELS) and all(math.isfinite(p) and 0<=p<=1 for p in r['probabilities'].values())
        assert abs(sum(r['probabilities'].values())-1)<.021 # Provider returns rounded probabilities.
        assert r['prediction'] in LABELS

def analyze():
    verify_freeze();local_run.verify()
    cases=rows(ROOT/'data/cases.jsonl');jobs=rows(ROOT/'plans/primary.jsonl')
    jev=rows(ROOT/'results/responses.jsonl');local=rows(local_run.OUT)
    validate_records(jobs,jev);validate_records(jobs,local)
    ledger=rows(ROOT/'results/attempts.jsonl');account=api_run.accounting(ledger)
    assert not account['unfinished'] and account['unknown_usage_attempts']==0
    assert account['attempts']<=155 and account['retries']<=5 and account['planned_input_units']<=1_000_000
    starts={e['attempt_id']:e for e in ledger if e['event']=='started'}
    finishes={e['attempt_id']:e for e in ledger if e['event']=='finished'}
    plan={j['job_id']:j for j in jobs}
    for e in starts.values():
        j=plan[e['job_id']];assert e['request_sha256']==j['request_sha256'] and e['planned_input_units']==j['planned_input_units']
    for r in jev:
        assert starts[r['attempt_id']]['job_id']==r['job_id']
        e=finishes[r['attempt_id']]
        assert all(r[k]==v for k,v in e.items() if k!='event')
        parsed=validate_response(r['raw_response'],r['option_order'])
        assert all(r[k]==v for k,v in parsed.items())
        assert r['input_tokens']==r['raw_response']['usage']['input_tokens']
    local_run.terminal_state(rows(local_run.PLAN))
    local_ends={e['job_id']:e for e in rows(local_run.LEDGER) if e['event']=='finished'}
    for r in local:
        assert {k:v for k,v in local_ends[r['job_id']].items() if k!='event'}==r
        assert r['model']==local_run.MODEL and r['revision']==local_run.REVISION
        j=next(j for j in rows(local_run.PLAN) if j['job_id']==r['job_id'])
        assert r['input_tokens']==j['input_tokens']
        logits=r['candidate_logits'];maximum=max(logits.values());v={k:math.exp(x-maximum) for k,x in logits.items()};total=sum(v.values())
        assert all(abs(v[k]/total-r['letter_probabilities'][k])<1e-6 for k in v)
        assert r['letter']==max(r['letter_probabilities'],key=r['letter_probabilities'].get)
        assert r['prediction']==ORDERS[r['option_order']]['ABC'.index(r['letter'])]
        assert all(r['probabilities'][ORDERS[r['option_order']][i]]==r['letter_probabilities'][k] for i,k in enumerate('ABC'))
        assert abs(sum(r['raw_token_probabilities'][k] for k in 'ABC')-r['candidate_mass'])<1e-9
    results={'study':'candidate-completeness-v1','status':'exploratory; zero independent reviews of these new inputs',
             'cases':72,'independent_parent_scenarios':12,'jev':model_metrics(cases,jev),'qwen_native':model_metrics(cases,local),
             'baselines':{m:endpoints(cases,{c['case_id']:resolve(c['state'],m) for c in cases}) for m in ('scope_aware','ignore_scope','keyword_all','keyword_product')}}
    for label in LABELS:results['baselines']['constant_'+label]=endpoints(cases,{c['case_id']:label for c in cases})
    results['jev']['accounting']=account
    results['jev']['usage_estimated_cost_usd']=account['known_input_tokens']*PRICE
    main=[r for r in local if r['phase']=='primary']
    results['qwen_native']['readout_audit']={'candidate_mass_min':min(r['candidate_mass'] for r in main),
        'candidate_mass_median':statistics.median(r['candidate_mass'] for r in main),
        'low_mass_count':sum(r['low_mass'] for r in main),'top_token_in_ABC_count':sum(r['top_token_text'] in 'ABC' and len(r['top_token_text'])==1 for r in main),
        'letter_counts':dict(Counter(r['letter'] for r in main)),
        'peak_allocated_mib':max(r['peak_allocated_mib'] for r in local)}
    results['paired_comparison']={str(m):{'jev_only_complete_parents':sum(results['jev']['mappings'][str(m)]['parent_complete'][p] and not results['qwen_native']['mappings'][str(m)]['parent_complete'][p] for p in results['jev']['mappings']['0']['parent_complete']),
        'qwen_only_complete_parents':sum(results['qwen_native']['mappings'][str(m)]['parent_complete'][p] and not results['jev']['mappings'][str(m)]['parent_complete'][p] for p in results['jev']['mappings']['0']['parent_complete'])} for m in (0,1)}
    return results

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--verify',action='store_true');a=p.parse_args();result=analyze()
    if a.verify:assert read(ROOT/'results/summary.json')==result
    else:write(ROOT/'results/summary.json',result)
    print(__import__('json').dumps({k:{'mapping0':v['mappings']['0']['correct'],'mapping1':v['mappings']['1']['correct'],'strict_parents':v['strict_complete_parents']} for k,v in result.items() if k in ('jev','qwen_native')},indent=2))
