"""Publish all outcomes of the fixed-budget control, including execution deviation."""
import argparse
from study import ROOT, read
from analyze import analyze as native
from reasoning_analyze import analyze

def markdown(s,a):
    w=s['work'];old=s['stopped_sampled_smoke_work']
    text=['# Does a fixed reasoning budget change the native result?','',
          '**Completed outcome-aware exploratory control on the same 12 parents /72 inputs. New independent human review remains at zero.**','',
          'This arm uses the same Qwen3-4B instruction weights and user content as the no-thinking native arm. It allows up to 512 greedy deliberation tokens, closes the reasoning block if necessary, then reads A/B/C native logits once. It adds computation and changes the reasoning prefix/readout context; it is not a single-factor test of internal reasoning, natural free-form accuracy or an equal-budget comparison with Jev.','',
          'The repaired control improves aggregate correctness from 34/72 to 58/72 in mapping 0 and from 30/72 to 59/72 in mapping 1. However, it still gives a determined answer on every one of the 12 unknown-reference inputs in each mapping. Better determined-case reasoning does not establish correct evidence-sufficiency behavior in this fixed configuration.','',
          '|Arm / mapping|Correct /72|Complete parents /12|False commitments /12 unknown|Unnecessary deferrals /60 determined|','|---|---:|---:|---:|---:|']
    for name,x in [('Jev',a['jev']),('Qwen native, thinking off',a['qwen_native']),('Qwen deliberation cap 512',s)]:
        for m in ('0','1'):
            v=x['mappings'][m];text.append(f"|{name} / {m}|{v['correct']}|{v['complete_parents']}|{v['false_commitments']['count']}|{v['unnecessary_deferrals']['count']}|")
    text+=['',f"Strict complete parents across both mappings: Jev {a['jev']['strict_complete_parents']}/12, native Qwen {a['qwen_native']['strict_complete_parents']}/12, budgeted Qwen {s['strict_complete_parents']}/12. A known-grammar program is 12/12 and 72/72. Repeated mappings do not increase the number of independent parent scenarios.",'',
           '## Paired changes and all condition cells','',
           '|Mapping|Native errors corrected|Native correct answers regressed|Option-order note|','|---|---:|---:|---|']
    for m in ('0','1'):
        v=s['paired_vs_native'][m];text.append(f"|{m}|{v['corrections']}|{v['regressions']}|Same 72 inputs; no selection|")
    text+=['',f"The budgeted arm changes semantic answer across mappings on {s['option_order_disagreements']['count']}/72 inputs. Its repaired smoke score is {s['smoke_correct']}/6; smoke errors did not change the main grid.",'',
        '|Request / coverage|Jev map 0 /12|Native map 0 /12|Budgeted map 0 /12|Budgeted map 1 /12|','|---|---:|---:|---:|---:|']
    for cell in s['mappings']['0']['cells']:
        values=[a['jev']['mappings']['0']['cells'][cell]['correct'],a['qwen_native']['mappings']['0']['cells'][cell]['correct'],s['mappings']['0']['cells'][cell]['correct'],s['mappings']['1']['cells'][cell]['correct']]
        text.append('|'+cell.replace('__',' / ')+'|'+'|'.join(map(str,values))+'|')
    text+=['','![Complete six-cell comparison, including both option orders](figures/coverage_cells.png)','',
        '## Truncation and probability audit','',
        '|Reasoning termination, main only|Recorded decisions|Reference matches|Unknown-reference matches / records|','|---|---:|---:|---:|']
    for reason,v in s['termination_strata'].items():text.append(f"|{reason}|{v['records']}|{v['correct']}|{v['unknown_correct']} / {v['unknown_reference_records']}|")
    text+=['','All main terminations remain in the 144 repeated-decision records. Differences between natural termination and truncation are descriptive and confounded by difficulty; they do not show that raising the cap would repair errors. No second budget was searched.','',
        f"Final A/B/C full-vocabulary mass: minimum {s['readout']['candidate_mass_min']:.6f}, median {s['readout']['candidate_mass_median']:.6f}; {s['readout']['low_mass_records']}/144 main records below 0.01. Candidate-normalized scores are not calibrated confidence.",'',
        '## Exact work, including the stopped attempt','',
        '|Recorded work|Repaired greedy v2|Stopped sampled smoke|','|---|---:|---:|']
    for name,key in [('Decisions','decisions'),('Batches','batches'),('Initial prompt tokens, unpadded','prompt_tokens_unpadded'),('Generated nonpadding tokens','generated_nonpadding_tokens'),('Final prefill tokens, unpadded','final_prefill_tokens_unpadded'),('Physical model forwards','physical_forwards'),('Processed token positions including padding','processed_token_positions_including_padding')]:
        text.append(f"|{name}|{w[key]:,}|{old[key]:,}|")
    text+=['',f"Measured batch work totals {w['summed_batch_latency_s']:.2f}s for v2, plus {old['summed_batch_latency_s']:.2f}s for the stopped smoke. V2 peak allocated memory: {w['peak_allocated_mib']:.1f} MiB. Model loading is separately logged. This excludes publication, inspection and software checks. Token positions are a work-accounting measure, not FLOPs or billable hosted tokens.",'',
        'The baseline native arm used 150 single-sequence prefills; this arm uses batched generation and a final prefill. Both are measured configurations, not a controlled throughput contest. All work used existing local weights; no paid API or model download was added by this control. Earlier Jev usage remains reported separately.','',
        '## Why there are two execution versions','',
        'The original reasoning freeze was published at `db2837c`. Its first six smoke jobs completed, but Transformers 4.55.4 overrode default-valued `do_sample=False` with checkpoint defaults. A CPU-only check reproduces the resulting sampling mode. No original main job ran. Those outputs are preserved under `results/reasoning_*` and are not pooled into the intended greedy comparison.','',
        'Repair freeze `4527534` preceded all v2 outputs. It keeps prompts, cases, order and cap byte-identical, passes `use_model_defaults=False, do_sample=False`, asserts the resolved mode before inference, and logs the effective configuration. Total control decisions are 156, including the six stopped sampled smoke jobs. This is a disclosed execution correction, not a choice of the better-scoring decoding mode.','',
        '## Stage decision and limits','',
        'The fixed native and reasoning arms are now closed. The outcome tells us how two concrete interfaces behave; it does not settle whether more reasoning, another ordinary model, a different prompt or dedicated training is necessary. Program-derived labels, supplied coverage truth, one template family and no new independent review constrain all results. A readable trace is not evidence of a faithful model mechanism.','',
        'Next: obtain new-material semantic review and narrow a transfer question before proposing an intervention. Stronger ordinary baselines and fair cost controls remain necessary for replacement claims. Avoid a third prompt/cap search on these inspected cases. The [post-result nearest-work screen](RELATED_WORK_POSTRUN.md) identifies prior over-abstention, evidence-boundary and agentic-stopping work; no new general method is claimed.','',
        'Reproduce without inference: `python research/candidate-completeness/reasoning_analyze.py --verify` and `python research/candidate-completeness/reasoning_report.py --verify`. Read [v1 protocol](REASONING_PROTOCOL.md), [v2 amendment](REASONING_GREEDY_V2.md), [CPU configuration audit](generation_config_audit.json), [raw v2 outputs](results/reasoning_greedy_responses.jsonl) and [summary](results/reasoning_summary.json).','']
    return '\n'.join(text)

def publish(verify=False):
    s=analyze();a=native();text=markdown(s,a);path=ROOT/'REASONING_RESULTS.md'
    if verify:assert path.read_text(encoding='utf-8')==text
    else:path.write_text(text,encoding='utf-8',newline='\n')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--verify',action='store_true');publish(p.parse_args().verify)
    print('Reasoning control report generated/verified.')
