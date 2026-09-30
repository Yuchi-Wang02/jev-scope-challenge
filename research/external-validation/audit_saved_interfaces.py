"""Exercise new readout auditing on pinned historical technical-smoke records.

No ShARC inputs, model calls, API requests or historical score changes.
"""
import argparse
import copy
import json
from pathlib import Path

from analyze_comparison import audit_result, local_checker
from comparison_plan import ROOT, sha

SOURCE_HASHES = {
    'jev': '746065434596e8163ab20ed6a49147b91ea4a9a469eedaad5787354dc9039690',
    'qwen': '2a0f2e7d49ad78936761dcd156e3d98fa676e37deeb92e66e988c42f8bfcbebc',
}


def audit(model_dir):
    checker = local_checker(model_dir)
    checked = {}
    negative_checks = []
    for backend, expected in SOURCE_HASHES.items():
        path = ROOT / 'research/action-backends/results' / backend / 'run.json'
        payload = path.read_bytes()
        if sha(payload) != expected:
            raise ValueError('Historical smoke bytes changed')
        run = json.loads(payload)
        if run['status'] != 'completed' or len(run['records']) != 8:
            raise ValueError('Unexpected historical technical run')
        ids = []
        for r in run['records']:
            if backend == 'jev':
                job = {'backend': 'jev', 'options': r['options']}
                stored = {'status': 'ok', 'action': r['parsed']['action'],
                    'input_tokens': r['parsed']['input_tokens'], 'output_tokens': r['parsed']['output_tokens'],
                    'latency_seconds': r['latency_seconds'],
                    'detail': {'http_status': r['http_status'], 'raw_response': r['raw_response'],
                               'parsed': r['parsed']}}
            else:
                job = {k: r[k] for k in ('prompt', 'thinking', 'input_ids', 'rendered_input', 'max_new_tokens')}
                job['backend'] = 'qwen'
                stored = {'status': 'ok', 'action': r['adapted']['parsed']['action'],
                    'input_tokens': len(r['input_ids']), 'output_tokens': r['generated_tokens'],
                    'latency_seconds': r['latency_seconds'], 'detail': {
                        'output_ids': r['output_ids'], 'adapted': r['adapted'],
                        'effective_generation_config': r['effective_generation_config'],
                        'presence_penalty': r['presence_penalty'],
                        'processor_order': r['actual_processor_order']}}
            audit_result(job, stored, checker)
            if backend == 'qwen' and not ids:
                mutations = {
                    'temperature': lambda d: d['effective_generation_config'].update(temperature=.5),
                    'null_to_false_output_flag': lambda d: d['effective_generation_config'].update(output_attentions=False),
                    'presence_penalty': lambda d: d.update(presence_penalty=0),
                    'processor_order': lambda d: d['processor_order'].reverse(),
                    'generated_token_ids': lambda d: d['output_ids'].pop(),
                }
                for name, mutate in mutations.items():
                    changed = copy.deepcopy(stored)
                    mutate(changed['detail'])
                    try:
                        audit_result(job, changed, checker)
                    except ValueError:
                        negative_checks.append(name)
                    else:
                        raise ValueError('Altered in-memory evidence was accepted: ' + name)
            ids.append(r['id'])
        checked[backend] = ids
    return {'status': 'historical_technical_readout_audit_passed',
            'source_hashes': SOURCE_HASHES, 'checked_record_ids': checked,
            'rejected_in_memory_mutations': negative_checks,
            'new_http_attempts': 0, 'new_model_forwards': 0, 'sharc_items': 0,
            'historical_score_updates': 0}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--model-dir', type=Path, required=True)
    args = p.parse_args()
    print(json.dumps(audit(args.model_dir), indent=2))
