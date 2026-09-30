"""Audit the single repaired reasoning arm, retaining the stopped sampled attempt."""
import argparse
import math
from collections import Counter
from statistics import median
from study import ROOT, LABELS, ORDERS, rows, read, write, sha, smokes
from analyze import endpoints, analyze as native_analysis
import reasoning_run as stopped
import reasoning_greedy as greedy

def aggregate(cases,records):
    maps={str(m):endpoints(cases,{r['case_id']:r['prediction'] for r in records if r['phase']=='primary' and r['option_order']==m}) for m in (0,1)}
    by={(r['case_id'],r['option_order']):r for r in records if r['phase']=='primary'}
    references={s['case_id']:s['reference'] for s in smokes()}
    smoke=[r for r in records if r['phase']=='smoke']
    return {'mappings':maps,'strict_complete_parents':sum(all(maps[str(m)]['parent_complete'][p] for m in (0,1)) for p in maps['0']['parent_complete']),
        'parent_n':12,'option_order_disagreements':{'count':sum(by[(c['case_id'],0)]['prediction']!=by[(c['case_id'],1)]['prediction'] for c in cases),'n':72},
        'smoke_correct':sum(r['prediction']==references[r['case_id']] for r in smoke),'smoke_n':len(smoke)}

def accounting(ends,records):
    e=list(ends.values())
    return {'decisions':len(records),'batches':len(e),'generated_nonpadding_tokens':sum(r['generated_tokens'] for r in records),
        'prompt_tokens_unpadded':sum(r['input_tokens'] for r in records),'final_prefill_tokens_unpadded':sum(r['final_input_tokens'] for r in records),
        'physical_forwards':sum(x['physical_forwards'] for x in e),
        'processed_token_positions_including_padding':sum(x['processed_token_positions'] for x in e),
        'summed_batch_latency_s':sum(x['batch_latency_s'] for x in e),
        'peak_allocated_mib':max(x['peak_allocated_mib'] for x in e),
        'stop_reasons':dict(Counter(r['stop_reason'] for r in records)),
        'forced_boundaries':sum(r['forced_boundary'] for r in records)}

def analyze():
    f=greedy.verify();stopped.verify();starts,ends,records=greedy.completion()
    assert len(records)==150 and len(ends)==38
    jobs={j['job_id']:j for j in rows(greedy.PLAN)}
    old_jobs={j['job_id']:j for j in rows(stopped.PLAN)}
    assert jobs==old_jobs # Only execution merging changes; prompts and schedule stay exact.
    assert {r['job_id'] for r in records}==set(jobs)
    plan_batches={b['batch_id']:b for b in rows(ROOT/'plans/reasoning_greedy_batches.jsonl')}
    for bid,start in starts.items():
        assert all(start[k]==v for k,v in plan_batches[bid].items())
        end=ends[bid];assert end['physical_forwards']<=start['reserved_forwards']
        assert end['processed_token_positions']<=start['reserved_token_positions']
        assert [r['job_id'] for r in end['responses']]==start['job_ids']
    for r in records:
        j=jobs[r['job_id']]
        assert r['ok'] and all(r[k]==j[k] for k in ('case_id','phase','option_order','request_sha256','prompt_sha256','input_tokens'))
        assert r['generated_tokens']==len(r['generated_token_ids'])<=512
        assert r['final_input_tokens']==len(r['final_input_ids'])
        assert r['stop_reason'] in ('budget','think_end','model_eos')
        assert r['forced_boundary']==(r['stop_reason']!='think_end')
        if r['stop_reason']=='budget':assert r['generated_tokens']==512
        if r['stop_reason']=='think_end':assert r['generated_token_ids'][-1]==f['closing_token_id'] and r['generated_text'].endswith('</think>')
        text=r['generated_text']
        if r['stop_reason']=='model_eos':
            assert r['generated_token_ids'][-1]==f['model_eos_token_id'] and text.endswith('<|im_end|>')
            text=text[:-len('<|im_end|>')]
        final=j['prompt']+text+('' if r['stop_reason']=='think_end' else '\n</think>')+'\n\n'
        assert sha(final.encode())==r['final_prompt_sha256']
        logits=r['candidate_logits'];v={k:math.exp(x-max(logits.values())) for k,x in logits.items()}
        assert all(math.isfinite(x) for x in logits.values())
        assert all(abs(v[k]/sum(v.values())-r['letter_probabilities'][k])<1e-6 for k in v)
        assert r['letter']==max(r['letter_probabilities'],key=r['letter_probabilities'].get)
        assert r['prediction']==ORDERS[r['option_order']]['ABC'.index(r['letter'])]
        assert all(r['probabilities'][ORDERS[r['option_order']][i]]==r['letter_probabilities'][k] for i,k in enumerate('ABC'))
        assert abs(sum(r['raw_token_probabilities'][k] for k in 'ABC')-r['candidate_mass'])<1e-9
    runtime=rows(ROOT/'results/reasoning_greedy_runtime.jsonl')
    configs=[x for x in runtime if x.get('event')=='effective_generation_config']
    assert {x['phase'] for x in configs}=={'smoke','primary'}
    for x in configs:assert x['mode']=='greedy_search' and x['config']['do_sample'] is False
    cases=rows(ROOT/'data/cases.jsonl');native=native_analysis();s=aggregate(cases,records)
    s['work']=accounting(ends,records)
    assert s['work']['physical_forwards']<=19494 and s['work']['processed_token_positions_including_padding']<=1_000_000
    assert s['work']['generated_nonpadding_tokens']<=76800
    _,old_ends,old_records=stopped.completion();assert len(old_records)==6 and all(r['phase']=='smoke' for r in old_records)
    s['stopped_sampled_smoke_work']=accounting(old_ends,old_records)
    s['total_control_decisions_including_stopped']=len(records)+len(old_records)
    s['status']='Outcome-aware exploratory control; zero independent reviews of these inputs'
    ref={c['case_id']:c['reference'] for c in cases}
    main=[r for r in records if r['phase']=='primary']
    s['termination_strata']={reason:{'records':sum(r['stop_reason']==reason for r in main),
        'correct':sum(r['stop_reason']==reason and r['prediction']==ref[r['case_id']] for r in main),
        'unknown_reference_records':sum(r['stop_reason']==reason and ref[r['case_id']]==LABELS[2] for r in main),
        'unknown_correct':sum(r['stop_reason']==reason and ref[r['case_id']]==LABELS[2] and r['prediction']==LABELS[2] for r in main)} for reason in ('think_end','budget','model_eos')}
    s['readout']={'candidate_mass_min':min(r['candidate_mass'] for r in main),
                  'candidate_mass_median':median(r['candidate_mass'] for r in main),
                  'low_mass_records':sum(r['candidate_mass']<.01 for r in main)}
    old={(r['case_id'],r['option_order']):r for r in rows(ROOT/'results/local_responses.jsonl') if r['phase']=='primary'}
    s['paired_vs_native']={str(m):{'corrections':sum(old[(r['case_id'],m)]['prediction']!=ref[r['case_id']] and r['prediction']==ref[r['case_id']] for r in main if r['option_order']==m),
        'regressions':sum(old[(r['case_id'],m)]['prediction']==ref[r['case_id']] and r['prediction']!=ref[r['case_id']] for r in main if r['option_order']==m),
        'complete_parents_native':native['qwen_native']['mappings'][str(m)]['complete_parents'],
        'complete_parents_reasoning':s['mappings'][str(m)]['complete_parents']} for m in (0,1)}
    return s

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--verify',action='store_true');a=p.parse_args();s=analyze()
    if a.verify:assert read(ROOT/'results/reasoning_summary.json')==s
    else:write(ROOT/'results/reasoning_summary.json',s)
    print(__import__('json').dumps({'correct':{m:v['correct'] for m,v in s['mappings'].items()},'strict_parents':s['strict_complete_parents'],'work':s['work']},indent=2))
