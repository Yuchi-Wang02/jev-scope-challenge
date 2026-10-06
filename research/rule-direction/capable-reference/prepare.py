"""Compile and freeze a bounded ordinary-model reference; no network access."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD = HERE.parent
MODEL = 'claude-sonnet-5-5'
MAX_OUTPUT = 8192
MAX_ATTEMPTS = 222
MAX_INPUT_RESERVE = 600_000
MAX_MICROUSD = 20_000_000
INPUT_ALLOWANCE = 2048
FROZEN_FILES = ('prepare.py', 'runner.py', 'analyze.py', 'test_runner.py',
                'README.md', 'PROTOCOL.md', 'requests.json', 'token_counts.json',
                'model_metadata.json', 'count_tokens.py', 'token_count_attempts.jsonl',
                'preparation-history/count_tokens-before-rate-limit.py',
                'preparation-history/token-count-rate-limit.json')


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def lfhash(path):
    return hashlib.sha256(Path(path).read_bytes().replace(b'\r\n', b'\n')).hexdigest()


def payload_hash(payload):
    return hashlib.sha256(encoded(payload)).hexdigest()


def preserve(path, value):
    raw = encoded(value)
    if path.exists():
        if path.read_bytes().replace(b'\r\n', b'\n') != raw:
            raise ValueError('Refusing to replace existing artifact: ' + path.name)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(raw)


def source_hashes(old=OLD):
    manifest = load(old / 'manifest.json')
    hashes = {name: lfhash(old / name) for name in
              ('request_plan.json', 'cases.json', 'manifest.json')}
    if hashes['request_plan.json'] != manifest['plan_sha256']:
        raise ValueError('Old plan LF hash differs from its manifest')
    if hashes['cases.json'] != manifest['case_sha256']:
        raise ValueError('Old cases LF hash differs from its manifest')
    return hashes


def contract_hashes(old=OLD):
    return {name: lfhash(old / name) for name in ('PROTOCOL.md', 'freeze.json', 'RESULTS.md', 'report.json')}


def compile_requests(old=OLD):
    sources = source_hashes(old)
    source_jobs = [j for j in load(old / 'request_plan.json')['jobs'] if j['backend'] == 'qwen']
    if len(source_jobs) != MAX_ATTEMPTS or len({j['id'] for j in source_jobs}) != MAX_ATTEMPTS:
        raise ValueError('Expected exactly 222 unique original Qwen jobs')
    if sum(j['phase'] == 'smoke' for j in source_jobs) != 6:
        raise ValueError('Expected six original smoke jobs')
    jobs = []
    for source in source_jobs:
        payload = {'model': MODEL, 'max_tokens': MAX_OUTPUT,
                   'thinking': {'type': 'adaptive', 'display': 'summarized'},
                   'output_config': {'effort': 'high'},
                   'messages': [{'role': 'user', 'content': source['prompt']}]}
        jobs.append({'job_id': source['id'], 'item_id': source['item_id'],
                     'phase': source['phase'], 'mapping': source['mapping'],
                     'tree_id': source['tree_id'], 'payload': payload})
    return {'study': 'rule-direction-capable-reference-v1', 'model': MODEL,
            'old_sources_sha256_lf': sources,
            'limits': {'http_attempts': MAX_ATTEMPTS, 'retries': 0,
                       'input_reserve_tokens': MAX_INPUT_RESERVE,
                       'input_allowance_per_request': INPUT_ALLOWANCE,
                       'max_output_tokens_per_request': MAX_OUTPUT,
                       'max_microusd': MAX_MICROUSD}, 'jobs': jobs}


def integer(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def validate_inputs(root=HERE, old=OLD):
    requests = load(root / 'requests.json')
    if requests != compile_requests(old):
        raise ValueError('Requests differ from the unchanged original prompts/configuration')
    metadata = load(root / 'model_metadata.json')
    if metadata.get('id') != MODEL:
        raise ValueError('Metadata must identify the fixed model')
    counts = load(root / 'token_counts.json')
    if counts.get('model') != MODEL or counts.get('requests_sha256_lf') != lfhash(root / 'requests.json'):
        raise ValueError('Token counts are for a different model/request plan')
    records = counts.get('counts', [])
    if not isinstance(records, list) or len(records) != MAX_ATTEMPTS:
        raise ValueError('Need one input-token estimate for every job')
    by_id = {}
    for row in records:
        if not isinstance(row, dict) or row.get('job_id') in by_id or not integer(row.get('input_tokens')):
            raise ValueError('Invalid/duplicate token count')
        by_id[row.get('job_id')] = row['input_tokens']
    if set(by_id) != {j['job_id'] for j in requests['jobs']}:
        raise ValueError('Token-count job coverage mismatch')
    reserved_input = sum(n + INPUT_ALLOWANCE for n in by_id.values())
    reserved_cost = 2 * reserved_input + 10 * MAX_OUTPUT * MAX_ATTEMPTS
    if reserved_input > MAX_INPUT_RESERVE or reserved_cost > MAX_MICROUSD:
        raise ValueError('Whole-grid reservation exceeds the frozen input or dollar bound')
    return requests, by_id, {'input_reserve_tokens': reserved_input,
                           'cost_reserve_microusd': reserved_cost,
                           'estimated_input_tokens': sum(by_id.values())}


def seal(root=HERE, old=OLD):
    if (root / 'results' / 'journal.jsonl').exists():
        raise ValueError('Do not freeze/reseal after a journal exists')
    requests, _, budget = validate_inputs(root, old)
    freeze = {'study': requests['study'], 'status': 'prepared; no generation calls',
              'old_sources_sha256_lf': source_hashes(old),
              'old_contracts_sha256_lf': contract_hashes(old),
              'files_sha256_lf': {name: lfhash(root / name) for name in FROZEN_FILES},
              'budget': budget}
    preserve(root / 'freeze.json', freeze)
    return verify(root, old)


def verify(root=HERE, old=OLD):
    frozen = load(root / 'freeze.json')
    if set(frozen['files_sha256_lf']) != set(FROZEN_FILES):
        raise ValueError('Frozen execution-file inventory mismatch')
    if frozen['old_sources_sha256_lf'] != source_hashes(old):
        raise ValueError('Old sources changed after freeze')
    if frozen.get('old_contracts_sha256_lf') != contract_hashes(old):
        raise ValueError('Old protocol/freeze changed after supplemental freeze')
    for name, digest in frozen['files_sha256_lf'].items():
        if lfhash(root / name) != digest:
            raise ValueError('Frozen file changed: ' + name)
    requests, counts, budget = validate_inputs(root, old)
    if budget != frozen['budget']:
        raise ValueError('Frozen budget differs')
    return requests, counts, budget


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=('compile', 'seal', 'verify'))
    args = parser.parse_args()
    if args.command == 'compile':
        preserve(HERE / 'requests.json', compile_requests())
        print(json.dumps({'jobs': MAX_ATTEMPTS, 'requests_sha256_lf': lfhash(HERE / 'requests.json')}))
    else:
        _, _, summary = seal() if args.command == 'seal' else verify()
        print(json.dumps(summary))
