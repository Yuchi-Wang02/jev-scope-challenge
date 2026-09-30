"""Explicit bounded live smoke. Imports make no HTTP requests or model loads."""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from adapters import jev_response, qwen_final
from plan import HERE, REPO, material


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(8*1024**2), b''): h.update(b)
    return h.hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
    temp.replace(path)


def event(path, value):
    with path.open('a', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(value, ensure_ascii=False)+'\n'); f.flush(); os.fsync(f.fileno())


def shared_modules():
    sys.path.insert(0, str(REPO/'research/generation-calibration'))
    from settings import make_config, assert_order, cpu_checks
    from interface import GeneratedPresencePenalty
    return make_config, assert_order, cpu_checks, GeneratedPresencePenalty


def main():
    p = argparse.ArgumentParser()
    p.add_argument('backend', choices=['jev', 'qwen'])
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--model-dir', type=Path)
    a = p.parse_args()
    assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=REPO).strip()
    plan = json.loads((HERE/'plan.json').read_text())
    assert plan == material()
    output = a.output.resolve()
    assert (REPO/'.local').resolve() in output.parents
    output.mkdir(parents=True, exist_ok=False)
    source_files = ['research/action-backends/'+name for name in
                    ('run.py', 'adapters.py', 'plan.py', 'plan.json', 'PROTOCOL.md')]
    source_files += ['research/external-validation/action_interface.py',
                     'research/generation-calibration/interface.py',
                     'research/generation-calibration/settings.py',
                     'research/payment-ownership/run_api_v02.py',
                     'research/payment-ownership/study.py']
    report = {'status': 'preflight', 'backend': a.backend, 'started_at_utc': utc(),
              'commit': subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
              'source_hashes': {n: digest(REPO/n) for n in source_files},
              'purpose': plan['purpose'], 'calls_started': 0, 'records': [], 'retries': 0,
              'downloads': 0, 'source_dataset_items': 0, 'human_reviews': 0}
    persist = lambda: save(output/'run.json', report)
    persist()
    references = {c['id']: c['reference'] for c in plan['cases']}
    try:
        if a.backend == 'jev':
            import httpx
            sys.path.insert(0, str(REPO/'research/payment-ownership'))
            from run_api_v02 import load_key, sanitize
            key = load_key()
            report['runtime'] = {'python': sys.version, 'httpx': httpx.__version__}
            assert plan['planned_jev_utf8_bytes_plus_256'] <= plan['max_jev_planning_units']
            report['input_tokens'] = 0; report['output_tokens'] = 0
            with httpx.Client(timeout=60, follow_redirects=False,
                              transport=httpx.HTTPTransport(retries=0)) as client:
                for call in plan['jev_calls']:
                    if report['input_tokens'] >= plan['max_jev_input_tokens']:
                        report['status'] = 'input_budget_stop'; persist(); return
                    r = {**call, 'status': 'started', 'started_at_utc': utc()}
                    report['records'].append(r); report['calls_started'] += 1
                    assert report['calls_started'] <= plan['max_http_attempts']
                    event(output/'events.jsonl', {'event':'started', 'id': r['id'], 'time': utc()})
                    persist(); start = time.perf_counter()
                    try:
                        response = client.post('https://api.typesafe.ai/v1/systemone', json=call['request'],
                                               headers={'Authorization': 'Bearer '+key})
                        r['http_status'] = response.status_code
                        try:
                            r['raw_response'] = sanitize(response.json(), key)
                        except ValueError:
                            r['error'] = 'non_json_response'
                        if response.status_code == 200 and 'raw_response' in r:
                            try:
                                r['parsed'] = jev_response(r['raw_response'], call['options'])
                            except (ValueError, TypeError, KeyError) as exc:
                                r['error'] = 'schema_'+type(exc).__name__
                        else:
                            r.setdefault('error', 'http_failure')
                    except Exception as exc:
                        r['error'] = 'transport_'+type(exc).__name__
                    r.update(status='finished', latency_seconds=time.perf_counter()-start)
                    # Usage can still be known for a schema-failed response.
                    usage = r.get('raw_response', {}).get('usage', {}) if isinstance(r.get('raw_response'), dict) else {}
                    for k in ('input_tokens', 'output_tokens'):
                        if type(usage.get(k)) == int and usage[k] >= 0:
                            report[k] += usage[k]
                    r['reference_match'] = r.get('parsed', {}).get('action') == references[call['case_id']]
                    event(output/'events.jsonl', {'event':'finished', 'id': r['id'], 'time': utc(),
                                                'record': r})
                    persist(); print(json.dumps({'id':r['id'], 'match':r['reference_match'],
                                                'error':r.get('error')}), flush=True)
                    if r.get('error') or not r['reference_match']:
                        report['status'] = 'smoke_failed'; persist(); return
            report['known_input_price_usd'] = report['input_tokens'] * .042 / 1e6
        else:
            assert a.model_dir is not None
            for key in ('HF_HUB_OFFLINE', 'TRANSFORMERS_OFFLINE', 'HF_HUB_DISABLE_TELEMETRY', 'HF_HUB_DISABLE_PROGRESS_BARS'):
                os.environ[key] = '1'
            import torch, transformers, peft
            from transformers import AutoTokenizer, Qwen3_5ForConditionalGeneration, StoppingCriteria, StoppingCriteriaList, LogitsProcessorList, set_seed
            assert transformers.__version__ == '5.3.0' and torch.__version__ == '2.8.0+cu128' and peft.__version__ == '0.18.1'
            make_config, assert_order, cpu_checks, Presence = shared_modules()
            manifest = json.loads((REPO/'research/baseline-readiness/qwen35-smoke-repaired/run.json').read_text())
            for f in manifest['model_files']:
                assert (a.model_dir/f['name']).stat().st_size == f['bytes']
                assert digest(a.model_dir/f['name']) == f['sha256']
            report['verified_model_files'] = manifest['model_files']
            report['model'] = 'Qwen/Qwen3.5-4B'
            report['revision'] = '851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a'
            report['runtime'] = {'transformers':transformers.__version__, 'torch':torch.__version__,
                                 'peft':peft.__version__, 'gpu':torch.cuda.get_device_name(0)}
            report['cpu_checks'] = cpu_checks(a.model_dir)
            tokenizer = AutoTokenizer.from_pretrained(a.model_dir, local_files_only=True, trust_remote_code=False)
            rendered = {}
            for call in plan['qwen_calls']:
                prompt = tokenizer.apply_chat_template([{'role':'user','content':call['prompt']}],
                         tokenize=False, add_generation_prompt=True, enable_thinking=call['thinking'])
                ids = tokenizer(prompt, add_special_tokens=False)['input_ids']
                # Exercise prompt-suffix and EOS checks before loading weights.
                qwen_final(tokenizer, [], thinking=call['thinking'], rendered_prompt=prompt,
                           max_new_tokens=call['max_new_tokens'])
                rendered[call['id']] = (prompt, ids)
            report['planned_input_tokens'] = sum(len(ids) for _, ids in rendered.values())
            assert report['planned_input_tokens'] <= plan['max_local_input_tokens']
            report['status'] = 'loading'; persist(); start = time.perf_counter()
            torch.cuda.reset_peak_memory_stats()
            model = Qwen3_5ForConditionalGeneration.from_pretrained(a.model_dir, dtype=torch.bfloat16,
                    device_map={'':'cuda:0'}, attn_implementation='sdpa', local_files_only=True, trust_remote_code=False)
            model.eval(); torch.cuda.synchronize(); report['load_seconds'] = time.perf_counter()-start
            assert {str(p.device) for p in model.parameters()} == {'cuda:0'}
            assert {str(p.dtype) for p in model.parameters()} == {'torch.bfloat16'}
            original = model._get_logits_processor
            r = None
            def audited(*args, **kwargs):
                procs = original(*args, **kwargs)
                r['actual_processor_order'] = assert_order(procs, r['thinking']); persist()
                return procs
            model._get_logits_processor = audited
            generation_start = time.perf_counter()
            class Deadline(StoppingCriteria):
                def __call__(self, input_ids, scores, **kwargs):
                    return time.perf_counter()-generation_start >= plan['local_generation_deadline_seconds']
            report['input_tokens'] = 0; report['generated_tokens'] = 0
            for call in plan['qwen_calls']:
                if time.perf_counter()-generation_start >= plan['local_generation_deadline_seconds']:
                    report['status'] = 'deadline'; persist(); return
                prompt, ids = rendered[call['id']]
                config = make_config(call['thinking'], tokenizer.eos_token_id, tokenizer.pad_token_id)
                config.max_new_tokens = call['max_new_tokens']
                effective, unused = model._prepare_generation_config(config)
                assert not unused
                r = {**call, 'status':'started', 'started_at_utc':utc(), 'rendered_input':prompt, 'input_ids':ids,
                     'effective_generation_config': effective.to_dict(), 'presence_penalty':1.5}
                report['records'].append(r); report['calls_started'] += 1
                assert report['calls_started'] <= plan['max_local_calls']
                report['input_tokens'] += len(ids)
                event(output/'events.jsonl', {'event':'started','id':r['id'],'time':utc()}); persist()
                set_seed(call['seed']); torch.cuda.synchronize(); start = time.perf_counter()
                inputs = {'input_ids':torch.tensor([ids],device='cuda:0'),
                          'attention_mask':torch.ones((1,len(ids)),device='cuda:0',dtype=torch.long)}
                with torch.inference_mode():
                    out = model.generate(**inputs, generation_config=config,
                          logits_processor=LogitsProcessorList([Presence(len(ids),1.5)]),
                          stopping_criteria=StoppingCriteriaList([Deadline()]))
                torch.cuda.synchronize()
                output_ids = out[0, len(ids):].tolist()
                r.update(status='finished', output_ids=output_ids, latency_seconds=time.perf_counter()-start,
                         generated_tokens=len(output_ids), adapted=qwen_final(tokenizer, output_ids,
                         thinking=call['thinking'], rendered_prompt=prompt, max_new_tokens=call['max_new_tokens']))
                r['reference_match'] = r['adapted']['parsed']['action'] == references[call['case_id']]
                report['generated_tokens'] += len(output_ids)
                assert report['generated_tokens'] <= plan['max_generated_tokens']
                report['generation_wall_seconds'] = time.perf_counter()-generation_start
                report['peak_allocated_bytes'] = torch.cuda.max_memory_allocated()
                report['peak_reserved_bytes'] = torch.cuda.max_memory_reserved()
                event(output/'events.jsonl', {'event':'finished','id':r['id'],'time':utc(),'record':r}); persist()
                print(json.dumps({'id':r['id'],'match':r['reference_match'],
                                  'generated':len(output_ids),'parsed':r['adapted']['parsed']}),flush=True)
                if not r['reference_match']:
                    report['status'] = 'smoke_failed'; persist(); return
        report['status'] = 'completed'; report['finished_at_utc'] = utc(); persist()
    except BaseException as exc:
        # No exception text or traceback: HTTP libraries may contain sensitive data.
        report['status'] = 'failed'; report['error_type'] = type(exc).__name__; persist()
        print(json.dumps({'status':'failed','error_type':type(exc).__name__}),flush=True)
        raise SystemExit(1)


if __name__ == '__main__':
    main()
