"""Offline record audit and predeclared completion-based cap selection."""
import argparse
import hashlib
import json
import re
import statistics
import subprocess
from collections import Counter
from pathlib import Path
from interface import parse_final
from prepare import ROOT, material


def select_cap(records, caps, run_completed):
    if not run_completed or len(records) != 24:
        return None
    return next((cap for cap in caps if all(r['parsed']['status'] == 'valid'
               and r['ended_with_eos'] and r['generated_tokens'] <= cap for r in records)), None)


def analyze():
    run = json.loads((ROOT/'results/run.json').read_text(encoding='utf-8'))
    token_audit = json.loads((ROOT/'token_audit.json').read_text(encoding='utf-8'))
    assert token_audit['run_sha256'] == hashlib.sha256((ROOT/'results/run.json').read_bytes()).hexdigest()
    assert token_audit['records_checked'] == 48 and token_audit['model_forwards'] == 0
    plan = json.loads((ROOT/'plan.json').read_text(encoding='utf-8'))
    assert plan == material()
    assert run['status'] in ('completed','deadline','failed'), 'Run is still live'
    for name, expected in run['source_hashes'].items():
        source = subprocess.check_output(['git','show',run['commit']+':research/generation-calibration/'+name],cwd=ROOT)
        assert hashlib.sha256(source).hexdigest() == expected, name
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == expected, name
    assert run['calls_started'] == len(run['records']) <= len(plan['calls'])
    if run['status'] == 'completed': assert len(run['records']) == 48
    refs = {r['id']:r['reference'] for r in plan['cases']}
    counts = []
    for saved, planned in zip(run['records'], plan['calls']):
        assert all(saved[k] == v for k,v in planned.items())
        assert saved['presence_penalty'] == 1.5
        cfg = saved['effective_generation_config']
        assert cfg['do_sample'] is True and cfg['max_new_tokens'] == planned['max_new_tokens']
        assert cfg['temperature'] == (1.0 if planned['thinking'] else 0.7)
        assert cfg['top_p'] == (0.95 if planned['thinking'] else 0.8)
        assert cfg['top_k'] == 20 and cfg['min_p'] == 0 and cfg['repetition_penalty'] == 1
        if saved['status'] != 'completed':
            assert run['status'] == 'failed'
            continue
        assert 0 < saved['generated_tokens'] == len(saved['output_ids']) <= saved['max_new_tokens']
        assert saved['ended_with_eos'] == (saved['output_ids'][-1] == cfg['eos_token_id'])
        assert saved['hit_token_cap'] == (saved['generated_tokens'] == saved['max_new_tokens'] and not saved['ended_with_eos'])
        parsed = parse_final(saved['decoded_output'], saved['thinking'], saved['ended_with_eos'])
        assert parsed == saved['parsed']
        assert saved['content_match'] == (parsed['answer'] == refs[saved['case_id']])
        expected = ['GeneratedPresencePenalty']
        if not saved['thinking']: expected += ['TemperatureLogitsWarper']
        expected += ['TopKLogitsWarper','TopPLogitsWarper','MinPLogitsWarper']
        assert saved['actual_processor_order'] == expected
        counts.append(saved)
    assert sum(r['generated_tokens'] for r in counts) == run.get('generated_tokens',0) <= 55296
    assert run['planned_input_tokens'] <= 200000
    if run['status'] == 'completed':
        assert sum(len(r['input_ids']) for r in counts) == run['planned_input_tokens']
        assert not any(r['deadline_reached'] for r in counts)
    modes = {}
    for name, thinking in [('direct',False),('thinking',True)]:
        rs = [r for r in counts if r['thinking'] == thinking]
        caps = [256,512,1024,2048] if thinking else [256]
        modes[name] = {'completed_calls':len(rs), 'planned_calls':24,
            'natural_eos':sum(r['ended_with_eos'] for r in rs),
            'valid_final':sum(r['parsed']['status']=='valid' for r in rs),
            'content_matches':sum(r['content_match'] for r in rs),
            'token_caps':sum(r['hit_token_cap'] for r in rs),
            'parse_statuses':dict(Counter(r['parsed']['status'] for r in rs)),
            'generated_tokens':sum(r['generated_tokens'] for r in rs),
            'generation_seconds':sum(r['generation_seconds'] for r in rs),
            'length_min':min((r['generated_tokens'] for r in rs),default=None),
            'length_median':statistics.median(r['generated_tokens'] for r in rs) if rs else None,
            'length_max':max((r['generated_tokens'] for r in rs),default=None),
            'prefix_readiness':{str(cap):sum(r['ended_with_eos'] and r['parsed']['status']=='valid'
                                         and r['generated_tokens']<=cap for r in rs) for cap in caps},
            'selected_development_cap':select_cap(rs,caps,run['status']=='completed')}
    per_case = []
    for case in plan['cases']:
        row = {'id':case['id'],'reference':case['reference']}
        for name,thinking in [('direct',False),('thinking',True)]:
            rs=[r for r in counts if r['case_id']==case['id'] and r['thinking']==thinking]
            row[name] = [{'seed':r['seed'],'answer':r['parsed']['answer'],
                          'status':r['parsed']['status'],'tokens':r['generated_tokens'],
                          'match':r['content_match']} for r in rs]
        per_case.append(row)
    # Descriptive post-run inspection only. Never feeds the frozen cap selector.
    fenced = []
    for r in counts:
        if r['parsed']['status'] != 'invalid_json' or not r['ended_with_eos']:
            continue
        body = r['decoded_output'][:-len('<|im_end|>')]
        if r['thinking']:
            if body.count('</think>') != 1: continue
            body = body.split('</think>',1)[1]
        match = re.fullmatch(r'\s*```json\s*\n(.*?)\n```\s*', body, flags=re.DOTALL)
        if match:
            inspected = parse_final(match.group(1).strip()+'<|im_end|>',False,True)
            fenced.append({'id':r['id'],'inspection':inspected,
                           'inner_object_matches_reference':inspected['answer']==refs[r['case_id']]})
    return run, {'run_status':run['status'],'purpose':run['purpose'],'fixtures':12,
                 'independent_human_reviews':0,'modes':modes,'cases':per_case,
                 'total_generated_tokens':run.get('generated_tokens',0),
                 'planned_input_tokens':run['planned_input_tokens'],
                 'new_model_downloads':0,'paid_api_calls':0,
                 'posthoc_format_inspection':{'selected_after_outputs':True,
                    'changes_primary_results_or_cap_selection':False,
                    'single_json_fence_cases':fenced}}


def report(run, a):
    lines = ['# Qwen3.5 output-budget calibration: completion is separate from correctness','',
        'Development-only calibration on twelve newly authored elementary fixtures. '
        'This is not a Jev comparison, new independently reviewed research dataset, '
        'capability ceiling or a model ranking. The earlier 72-input research grids remain closed.','',
        f'Execution status: **{a["run_status"]}**. Protocol, prompts, seeds, settings, '
        f'parser and cap-selection rule were frozen at `{run["commit"]}` before outputs.','',
        '## What ran','',
        'Each of 12 fixtures was run with seeds 17 and 43 in direct and thinking modes: '
        '48 planned calls. These are repeated measurements of 12 synthetic development '
        'fixtures, not 48 independent research examples. Exact program references are '
        'balanced A/B/C, four each; no human labels are claimed.','',
        '|Mode|Completed calls|Natural EOS|Valid final JSON|Strict valid + content match|Token-cap stops|Generated tokens|Generate seconds|Selected development cap|',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for name,m in a['modes'].items():
        lines.append(f'|{name}|{m["completed_calls"]}/24|{m["natural_eos"]}/24|{m["valid_final"]}/24|'
             f'{m["content_matches"]}/24|{m["token_caps"]}|{m["generated_tokens"]:,}|'
             f'{m["generation_seconds"]:.3f}|{m["selected_development_cap"] or "None qualified"}|')
    lines += ['','The strict match column counts parser failures as unsuccessful delivery, '
        'not proven wrong answers. Content among accepted outputs and the rejected '
        'final wrappers are examined separately below.', '',
        f'Total generated tokens: {a["total_generated_tokens"]:,} /55,296; '
        f'planned input tokens: {a["planned_input_tokens"]:,} /200,000. '
        f'Generation-stage wall time: {run.get("generation_wall_seconds",0):.3f} seconds /1,800; '
        f'load time: {run.get("load_seconds",0):.3f} seconds. Peak allocated/reserved PyTorch '
        f'memory: {run.get("peak_allocated_bytes",0)/1024**3:.3f}/'
        f'{run.get("peak_reserved_bytes",0)/1024**3:.3f} GiB. '
        'Zero paid API calls, new weights or dependency downloads. No execution retries.','',
        '## Predeclared cap selection','',
        'A cap qualifies only when all 24 calls in the mode have naturally ended and '
        'yield strict final JSON by that token count. Correctness does not enter '
        'the selection. Lower-cap entries below are saved-trace availability checks, '
        'not additional model calls or measured lower-cap latency.','',
        '|Mode|256 tokens|512 tokens|1,024 tokens|2,048 tokens|',
        '|---|---:|---:|---:|---:|']
    for name,m in a['modes'].items():
        cells=[str(m['prefix_readiness'][str(c)])+'/24' if str(c) in m['prefix_readiness'] else 'Not executed' for c in [256,512,1024,2048]]
        lines.append('|'+name+'|'+'|'.join(cells)+'|')
    for name,m in a['modes'].items():
        if m['natural_eos'] == 24 and m['valid_final'] < 24:
            lines += ['',f'For {name}, every call reaches natural EOS, but '
                      f'{24-m["valid_final"]} final response(s) fail the strict format contract. '
                      'No cap qualifies for this interface. This is a format gate failure, '
                      'not evidence that increasing the token cap would fix it.']
    lines += ['','A selected cap is only a starting point for similar development prompts. '
        'It is not a demonstrated adequate budget for unseen reasoning tasks, long '
        'contexts or realistic policy decisions. If a mode has no qualifying cap, '
        'this run supplies no recommendation; do not extend it in search of a passing '
        'configuration. Content errors remain visible even if every output parses.','',
        '## Every fixture and both seeds','',
        'Cells list seed 17 then 43 as answer/status and generated-token length. '
        'Program references are elementary construction checks, not independent '
        'human judgments. Do not turn these counts into a benchmark headline.','',
        '|Fixture|Reference|Direct, seeds 17 /43|Thinking, seeds 17 /43|',
        '|---|---|---|---|']
    for c in a['cases']:
        cells=[]
        for name in ['direct','thinking']:
            cells.append(' / '.join(f'{r["answer"] or r["status"]} ({r["tokens"]})' for r in c[name]) or 'Not reached')
        lines.append(f'|{c["id"]}|{c["reference"]}|{cells[0]}|{cells[1]}|')
    fences = a['posthoc_format_inspection']['single_json_fence_cases']
    lines += ['','## Post-run format inspection, outside the primary gate','',
        f'Inspection after all outputs found {len(fences)} rejected finals consisting '
        'of exactly one json-marked Markdown code block. After inspecting only that '
        f'final block, {sum(x["inner_object_matches_reference"] for x in fences)} inner '
        'objects match their program references. This descriptive normalization was '
        'chosen after outputs and is not the frozen parser, a replacement primary '
        'score, or a new model run. It does not change cap qualification. No content '
        'is extracted from an unfinished thought.', '',
        'For each mode, accepted content matches / accepted strict outputs: '+
        '; '.join(f'{name} {m["content_matches"]}/{m["valid_final"]}' for name,m in a['modes'].items())+
        '. Distinguish a wrong answer from a correct answer in a rejected wrapper. '
        'A future interface may reasonably allow one final JSON fence or constrain '
        'the final schema, but it must declare that contract before new evaluation. '
        'Do not attribute this format mismatch to deficient reasoning or advertise '
        'it as a dedicated-model advantage.', '',
        '## Interface and scope','',
        'Pinned Qwen3.5-4B revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, '
        'BF16 on RTX 5070 Ti, Transformers 5.3.0 and torch 2.8.0+cu128. No '
        'quantization, CPU offload, constrained decoding or forced answer readout. '
        'The saved runtime and prior hash-verified model manifest identify the installation.','',
        'Sampling follows the pinned card\'s general-task row: direct temperature/top-p '
        '0.7/0.8, thinking 1.0/0.95, top-k 20, min-p 0, repetition penalty 1 and '
        'presence penalty 1.5. A tested standard processor subtracts the presence '
        'penalty once for each generated token type, excludes the prompt, and is '
        'asserted before temperature/top-k/top-p in every actual generation. This '
        'is established decoding logic, not an algorithmic contribution. It differs '
        'from the earlier smoke\'s zero-presence-penalty configuration; that smoke '
        'is not a matched causal control. These finite caps remain below the '
        'vendor\'s general benchmarking length recommendation.','',
        'The parser requires EOS, a completed thinking boundary where applicable, '
        'and exactly one final JSON object. It rejects duplicate keys, multiple '
        'answers, markdown fences, trailing prose and incomplete thoughts. The '
        'generation code never receives the reference answer. Later content checking '
        'does not modify an output or choose a different seed.','',
        '## Evidence, reproduction and next gate','',
        '- [Frozen protocol](PROTOCOL.md), [complete input/call plan](plan.json), '
        '[preparation log](PREPARATION.md), [CPU checks](cpu_checks.json).',
        '- [All raw inputs/outputs and token IDs](results/run.json), '
        '[derived summary](summary.json), [execution script](run.py). '
        '[Local-tokenizer audit](token_audit.json) reconstructed all 48 rendered '
        'inputs/input IDs and decoded output IDs without a model forward. '
        'Its [optional replay](audit_tokens.py) requires the local tokenizer; '
        'the CI audit checks its raw-record hash, not a fresh tokenizer run.',
        '- Sources: [pinned Qwen card](https://huggingface.co/Qwen/Qwen3.5-4B/blob/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a/README.md), '
        '[vLLM penalty semantics](https://github.com/vllm-project/vllm/blob/v0.11.0/vllm/model_executor/layers/utils.py). '
        'No vLLM source was copied, forked or executed.','',
        'Offline checks require full Git history, no weights or credentials:', '',
        '```bash','python research/generation-calibration/prepare.py',
        'python research/generation-calibration/analyze.py --verify',
        'python -m unittest discover -s tests -p test_generation_interface.py -v','```','',
        'Live replication uses the previously documented isolated Qwen3.5 environment '
        'and model directory, a clean committed checkout and a new output path. '
        'It performs additional local inference; no automatic rerun is part of verification:', '',
        '```bash','python -X utf8 research/generation-calibration/run.py --model-dir MODEL_DIR --output NEW_RUN_DIR','```','',
        'Milestone audit: the interface, strict parser and finite-budget selection '
        'are now exercised on saved real outputs. The remaining scientific gap is '
        'new, independently reviewed material and evidence that the task matters '
        'beyond a known-grammar program. Neither a valid JSON response nor a successful '
        'elementary check establishes reliability on that target. Next decisions must '
        'address task semantics and a capable comparison, not enlarge this calibration '
        'until it looks impressive. The previous research grids and human-review '
        'statuses are unchanged.','']
    return '\n'.join(lines)


if __name__ == '__main__':
    p=argparse.ArgumentParser(); p.add_argument('--verify', action='store_true'); args=p.parse_args()
    r,a=analyze(); outputs={'summary.json':json.dumps(a,indent=2)+'\n','README.md':report(r,a)}
    for name,text in outputs.items():
        path=ROOT/name
        if args.verify: assert path.read_text(encoding='utf-8')==text,name
        else: path.write_text(text,encoding='utf-8',newline='\n')
    print(json.dumps({'run_status':a['run_status'],'modes':a['modes'],'research_calls':0},indent=2))
