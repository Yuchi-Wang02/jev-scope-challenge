"""Recompute technical-smoke evidence without HTTP requests or model forwards."""
import argparse
import hashlib
import json
import subprocess
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from adapters import jev_response, qwen_final, parse_final
from plan import HERE, REPO, material


def sha(data): return hashlib.sha256(data).hexdigest()
def read(path): return json.loads(path.read_text(encoding='utf-8'))
def encoded(value): return (json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode('utf-8')


def audit_tokens(model_dir):
    from transformers import AutoTokenizer
    t = AutoTokenizer.from_pretrained(model_dir, local_files_only=True, trust_remote_code=False)
    path = HERE/'results/qwen/run.json'; run = read(path)
    checked = []
    for r in run['records']:
        rendered = t.apply_chat_template([{'role':'user','content':r['prompt']}], tokenize=False,
                                          add_generation_prompt=True, enable_thinking=r['thinking'])
        assert rendered == r['rendered_input']
        assert t(rendered, add_special_tokens=False)['input_ids'] == r['input_ids']
        if r['status'] != 'finished': continue
        actual = qwen_final(t, r['output_ids'], thinking=r['thinking'],
                            rendered_prompt=rendered, max_new_tokens=r['max_new_tokens'])
        assert actual == r['adapted']
        checked.append(r['id'])
    result = {'model_forwards':0, 'http_calls':0, 'run_sha256':sha(path.read_bytes()),
              'record_ids':checked, 'tokenizer_files':{n:sha((model_dir/n).read_bytes())
                     for n in ('tokenizer.json','tokenizer_config.json','chat_template.jinja')}}
    (HERE/'token_audit.json').write_bytes(encoded(result))


def analyze():
    plan = read(HERE/'plan.json'); assert plan == material()
    refs = {c['id']:c['reference'] for c in plan['cases']}
    summary = {'purpose':plan['purpose'], 'source_dataset_items':0, 'human_reviews':0,
               'technical_fixtures':4, 'backends':{}, 'source_line_endings':{}}
    for backend in ('jev','qwen'):
        root = HERE/'results'/backend; run = read(root/'run.json')
        assert run['status'] in ('completed','smoke_failed','failed','deadline','input_budget_stop')
        assert run['backend'] == backend and run['retries'] == run['downloads'] == 0
        for name, expected in run['source_hashes'].items():
            frozen = subprocess.check_output(['git','show',run['commit']+':'+name],cwd=REPO)
            candidates = {sha(frozen):'Git blob bytes',
                          sha(frozen.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')):'CRLF checkout bytes'}
            assert expected in candidates, name
            summary['source_line_endings'][name] = candidates[expected]
        calls = plan[backend+'_calls']
        assert run['calls_started'] == len(run['records']) <= 8
        if run['status']=='completed': assert len(run['records'])==8
        events = [json.loads(x) for x in (root/'events.jsonl').read_text(encoding='utf-8').splitlines()]
        started = [e['id'] for e in events if e['event']=='started']
        finished = [e for e in events if e['event']=='finished']
        assert started == [r['id'] for r in run['records']]
        assert len(set(started)) == len(started)
        assert [e['id'] for e in finished] == [r['id'] for r in run['records'] if r['status']=='finished']
        for r, call in zip(run['records'], calls):
            assert all(r[k]==v for k,v in call.items())
            if r['status']!='finished': continue
            assert next(e['record'] for e in finished if e['id']==r['id'])==r
            if backend=='jev':
                if 'parsed' in r: assert jev_response(r['raw_response'],r['options'])==r['parsed']
                action = r.get('parsed',{}).get('action')
            else:
                cfg = r['effective_generation_config']
                assert cfg['do_sample'] is True and cfg['max_new_tokens']==r['max_new_tokens']
                assert cfg['temperature']==(1.0 if r['thinking'] else .7)
                assert cfg['top_p']==(.95 if r['thinking'] else .8)
                assert cfg['top_k']==20 and cfg['min_p']==0 and cfg['repetition_penalty']==1
                assert r['presence_penalty']==1.5
                expected = ['GeneratedPresencePenalty'] + ([] if r['thinking'] else ['TemperatureLogitsWarper'])
                assert r['actual_processor_order']==expected+['TopKLogitsWarper','TopPLogitsWarper','MinPLogitsWarper']
                assert r['generated_tokens']==len(r['output_ids'])<=r['max_new_tokens']
                adapted = r['adapted']; action = adapted['parsed']['action']
                if adapted['final_text'] is not None:
                    assert adapted['parsed']==asdict(parse_final(adapted['final_text'],completion=adapted['completion']))
                if adapted['completion']=='natural_eos':
                    assert r['output_ids'][-1]==248046 and r['output_ids'].count(248046)==1
            assert r['reference_match']==(action==refs[r['case_id']])
        rs = [r for r in run['records'] if r['status']=='finished']
        result = {'run_status':run['status'], 'freeze_commit':run['commit'],
                  'calls_started':run['calls_started'], 'calls_finished':len(rs),
                  'matches':sum(r['reference_match'] for r in rs),
                  'latency_seconds_sum':sum(r['latency_seconds'] for r in rs),
                  'run_sha256':sha((root/'run.json').read_bytes()),
                  'events_sha256':sha((root/'events.jsonl').read_bytes())}
        if backend=='jev':
            result['input_tokens'] = sum(r.get('raw_response',{}).get('usage',{}).get('input_tokens',0) for r in rs)
            result['output_tokens'] = sum(r.get('raw_response',{}).get('usage',{}).get('output_tokens',0) for r in rs)
            assert result['input_tokens']==run['input_tokens']<=plan['max_jev_input_tokens']
            assert result['output_tokens']==run['output_tokens']
            result['input_price_estimate_usd'] = result['input_tokens']*.042/1e6
            result['usage_missing_attempts'] = sum('usage' not in r.get('raw_response',{}) for r in run['records'])
        else:
            result['input_tokens'] = sum(len(r['input_ids']) for r in run['records'])
            result['generated_tokens'] = sum(r['generated_tokens'] for r in rs)
            assert result['input_tokens']==run['input_tokens']<=plan['max_local_input_tokens']
            assert result['generated_tokens']==run['generated_tokens']<=plan['max_generated_tokens']
            audit = read(HERE/'token_audit.json')
            assert audit['run_sha256']==result['run_sha256'] and audit['model_forwards']==audit['http_calls']==0
            assert audit['record_ids']==[r['id'] for r in rs]
            pins = {x['name']:x['sha256'] for x in run['verified_model_files']}
            assert all(pins[n]==h for n,h in audit['tokenizer_files'].items())
            result['modes'] = {name:{'calls':len(group), 'matches':sum(r['reference_match'] for r in group),
                       'natural_eos':sum(r['adapted']['completion']=='natural_eos' for r in group),
                       'wrappers':dict(Counter(r['adapted']['parsed']['wrapper'] for r in group)),
                       'generated_tokens':sum(r['generated_tokens'] for r in group)}
                for name, group in [('direct',[r for r in rs if not r['thinking']]),
                                    ('thinking',[r for r in rs if r['thinking']])]}
            result['load_seconds']=run['load_seconds']
            result['generation_wall_seconds']=run['generation_wall_seconds']
        summary['backends'][backend]=result
    return summary


def report(s):
    j=s['backends']['jev']; q=s['backends']['qwen']
    return f'''# Four-action interfaces: live integration evidence

Technical label-copy smoke, not research task accuracy. Four AI-authored records
explicitly supply a selected label and a distractor. There are **zero source
dataset items and zero human reviews**. No ShARC, payment, or calibration grid
was rerun. These checks cannot rank Jev against Qwen or establish rule reasoning.

The [protocol](PROTOCOL.md), [call list](plan.json) and code were committed at
`{j['freeze_commit']}` before execution. Both backends ran once, with no retry,
new model download, prompt repair or extra seed. All traces and start/finish
accounting are retained in [Jev results](results/jev/run.json),
[Jev events](results/jev/events.jsonl), [Qwen results](results/qwen/run.json) and
[Qwen events](results/qwen/events.jsonl).

|Interface check|Finished|Copied label matches|Input tokens|Output work|
|---|---:|---:|---:|---:|
|Jev 1.13.0, two four-option mappings|{j['calls_finished']}/8|{j['matches']}|{j['input_tokens']}|{j['output_tokens']} returned output tokens|
|Qwen3.5-4B, direct/thinking|{q['calls_finished']}/8|{q['matches']}|{q['input_tokens']}|{q['generated_tokens']} generated tokens|

Statuses: Jev **{j['run_status']}**, Qwen **{q['run_status']}**. Known Jev input
price estimate: **${j['input_price_estimate_usd']:.9f}**, using the checked official
$0.042/M input-token rate, not an invoice. Attempts missing usage:
{j['usage_missing_attempts']}. Jev summed request latency {j['latency_seconds_sum']:.3f}s.
Qwen load {q['load_seconds']:.3f}s; generation-stage wall
{q['generation_wall_seconds']:.3f}s. These tiny prompts do not establish throughput
or cost on the research workload. Qwen ran locally; electricity cost is unmeasured.

Qwen direct wrappers: `{q['modes']['direct']['wrappers']}`; thinking wrappers:
`{q['modes']['thinking']['wrappers']}`. The wrapper-tolerant contract was declared
before these outputs. Strict JSON compliance remains separate from copied-label
correctness. No historical result is rescored.

The [token audit](token_audit.json) re-rendered all local prompts, retokenized inputs,
decoded saved output IDs, and recomputed EOS/thinking boundaries and final parses,
using the pinned tokenizer without model forwards. The offline analyzer checks
the freeze, exact scheduled calls, event records, mappings, settings and work sums.
The pre-existing credential helper was checked out with CRLF; its recorded raw
byte hash is compared against that line-ending form of the frozen Git blob.
No semantic source difference is accepted. Credentials and HTTP headers are absent
from public records. These integrity checks do not authenticate a human reviewer.

## Stage audit and next decision

The original question was whether both backends could deliver an auditable
four-action result under the proposed interface. This narrow integration now has
real invocation evidence. Copying a supplied label cannot establish that the
model will infer it correctly from ambiguous natural-language rules.

The [external task card](../external-validation/TASK_CARD.md) still requires
independent human review and adjudication, then a separately frozen task protocol
with matched evidence, explicit baselines, prompts, budgets and paired analysis.
No ShARC performance result is claimed. This smoke is closed; do not expand it
into another generic calibration search. The useful next evidence is reviewed
natural-language task material and the matched, frozen comparison on it.

Offline verification (no model or API):

```bash
python research/action-backends/plan.py
python research/action-backends/analyze.py --verify
```
'''


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--verify',action='store_true')
    p.add_argument('--tokenizer-dir',type=Path); a=p.parse_args()
    if a.tokenizer_dir: audit_tokens(a.tokenizer_dir)
    s=analyze(); outputs={HERE/'summary.json':encoded(s),HERE/'README.md':report(s).encode('utf-8')}
    for path,data in outputs.items():
        if a.verify: assert path.read_bytes().replace(b'\r\n',b'\n')==data
        else: path.write_bytes(data)
    print(json.dumps(s,indent=2))
