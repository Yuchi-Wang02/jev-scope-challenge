"""Rebuild the exploratory report and static replay from recorded evidence."""
import argparse
import json
from pathlib import Path
from study import ROOT, REPO, rows, read
from analyze import analyze

def report(s):
    j=s['jev'];q=s['qwen_native']
    lines=['# One visible match: caution can also be wrong','',
        '**Exploratory result; 12 parent scenarios, 72 constructed inputs, zero independent human reviews of this new set.**','',
        'Jev recognized missing relevant candidates for product-name requests, but sometimes deferred even when an exact order ID already selected a visible target. Every Jev main error was an unnecessary NOT_ESTABLISHED on the explicit-ID / relevant-omission condition. This is not the originally proposed foreign-order payment substitution.','',
        '|Method / mapping|Correct /72|Complete parents /12|False commitments /12 unknown|Unnecessary deferrals /60 determined|',
        '|---|---:|---:|---:|---:|']
    for name,v in [('Jev 1.13.0',j),('Qwen3-4B native, thinking off',q)]:
        for m in ('0','1'):
            a=v['mappings'][m];lines.append(f"|{name}, {m}|{a['correct']}|{a['complete_parents']}|{a['false_commitments']['count']}|{a['unnecessary_deferrals']['count']}|")
    for name in ('scope_aware','ignore_scope','keyword_all','keyword_product'):
        a=s['baselines'][name];lines.append(f"|Code: {name}|{a['correct']}|{a['complete_parents']}|{a['false_commitments']['count']}|{a['unnecessary_deferrals']['count']}|")
    lines+=['','Constants VALID / INVALID / NOT_ESTABLISHED score 30/30/12 out of 72, with zero complete parents each. The known-grammar solver sees the same visible state and scores 72/72; it is an essential limit on model-necessity claims.','',
       f"The prespecified Jev screen fails in both mappings. Strict correctness across all six inputs and both mappings is {j['strict_complete_parents']}/12 parents for Jev and {q['strict_complete_parents']}/12 for Qwen. These are repeated measurements of 12 parents, not 144 independent examples.",'',
       '## Where the decisions differ','',
       '|Request / coverage|Jev map 0 /12|Jev map 1 /12|Qwen map 0 /12|Qwen map 1 /12|','|---|---:|---:|---:|---:|']
    for cell in j['mappings']['0']['cells']:
        vals=[v['mappings'][m]['cells'][cell]['correct'] for v in (j,q) for m in ('0','1')]
        lines.append('|'+cell.replace('__',' / ')+'|'+'|'.join(map(str,vals))+'|')
    lines+=['','Required product-answer changes are correct in 12/12 pairs per Jev mapping, as are product irrelevant-omission controls. Explicit-ID relevant-omission stability succeeds in 3/12 and 7/12 pairs; explicit-ID irrelevant omissions remain 12/12. Correctness requires both pair members to match their references.','',
        'Jev changes its semantic answer across option orders on 4/72 inputs. Five explicit-ID cases defer under both orders; four more defer only under mapping 0. This is a failure of this instrument/configuration, not a demonstrated internal mechanism or a universal scope deficit.','',
        'Qwen is not merely choosing the first letter: it predicts VALID on 68/72 inputs in mapping 0 and 72/72 in mapping 1. Its native readout has 12/12 false commitments in each mapping. No thinking or free-form generation was allowed in this arm. A weak native readout is not an estimate of the checkpoint\'s reasoning ceiling.','',
        '## Interface and accounting','',
        f"Jev smoke: {j['smoke_correct']}/6; Qwen smoke: {q['smoke_correct']}/6. All valid semantic errors were retained under the predeclared gate. No malformed response, retry, warmup forward or follow-up prompt search occurred.",'',
        f"Jev: {j['accounting']['attempts']} HTTP attempts, {j['all_input_tokens']:,} reported input tokens ({j['main_input_tokens']:,} main), estimated ${j['usage_estimated_cost_usd']:.9f}. The frozen plan reserved 522,016 conservative byte-based units, below 1,000,000; these are not exact billed tokens. Returned model: jev-1.13.0. Prices are usage estimates, not invoices.",'',
        f"Qwen: 150 local prefills, {q['all_input_tokens']:,} prompt tokens ({q['main_input_tokens']:,} main). Existing pinned instruction weights; BF16, SDPA, RTX 5070 Ti, Transformers 4.55.4 / torch 2.8.0+cu128, no training/downloads. Peak allocated memory {q['readout_audit']['peak_allocated_mib']:.1f} MiB. Candidate mass minimum {q['readout_audit']['candidate_mass_min']:.4f}, median {q['readout_audit']['candidate_mass_median']:.4f}; zero low-mass (<0.01) main records. The full-vocabulary top token is A/B/C in {q['readout_audit']['top_token_in_ABC_count']}/144 main records. Conditional probabilities are not calibrated confidence.",'',
        f"Median main measured latency: hosted Jev {j['main_latency_median_s']:.3f}s; local Qwen {q['main_latency_median_s']:.3f}s. They use different serving environments and tokenizers; this is not a deployment speed/cost ranking. Runtime load times and exact prompt IDs are separately retained.",'',
        '## Evidence chain and limits','',
        '- Jev inputs/code/protocol were published at `680fb6f` before calls. Local prompts/readout were published at `c327d59`, after the six Jev smoke responses but before either main grid and before all new local outputs.',
        '- Data selection is deterministic from pinned public simulated tau retail records; 12 users are disjoint from the earlier payment pilot. Coverage statements and omitted-world witnesses are constructed premises, not actual source retrieval failures.',
        '- The unique-target requirement is explicit. An order ID uniquely selects the visible order; unseen same-product orders do not make that ID ambiguous. The omission sentence describes product-name requests, not explicit-ID requests.',
        '- One wording family, simple templates, program-derived labels and no new independent review. The two earlier reviewers reviewed a different dataset. Later review cannot make these inspected data independent confirmation.',
        '- Qwen and Jev do not share a backbone, serialization or inference interface. Inputs/rubrics and options correspond, but this comparison does not isolate dedicated training. No new Kev or Laya model was executed.',
        '- No general novelty, model replacement, tau-bench agent score or paper-ready causal explanation is established. Established context-sufficiency and abstention work is discussed in [RELATED_WORK.md](RELATED_WORK.md).','',
        '## Decision and reproduction','',
        'Stop the frozen Jev/native grids here. The next justified control is one separately frozen fixed-budget Qwen reasoning arm on the same material, disclosed as outcome-aware exploration. Independent semantic review is needed before stronger reference claims. New-material confirmation and natural-language transfer are later gates, not completed work.','',
        'Run `python research/candidate-completeness/analyze.py --verify` and `python research/candidate-completeness/publish.py --verify` without API credentials or model weights. These verify recorded results, not model honesty or scientific validity. See [PROTOCOL.md](PROTOCOL.md), [LOCAL_PROTOCOL.md](LOCAL_PROTOCOL.md), [machine-readable summary](results/summary.json), [review-only package](review/README.md) and [replay](../../docs/candidate_coverage.html).','']
    return '\n'.join(lines)

def replay(s):
    payload={'summary':s,'cases':rows(ROOT/'data/cases.jsonl'),'jev':rows(ROOT/'results/responses.jsonl'),
             'qwen':rows(ROOT/'results/local_responses.jsonl'),'plans':rows(ROOT/'plans/primary.jsonl')}
    return (ROOT/'replay_template.html').read_text(encoding='utf-8').replace('__DATA__',json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c'))

def publish(verify=False):
    s=analyze()
    for path,text in [(ROOT/'RESULTS.md',report(s)),(REPO/'docs/candidate_coverage.html',replay(s))]:
        if verify:assert path.read_text(encoding='utf-8')==text,str(path)
        else:path.write_text(text,encoding='utf-8',newline='\n')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--verify',action='store_true');publish(p.parse_args().verify)
    print('Coverage report and replay verified/generated from complete records.')
