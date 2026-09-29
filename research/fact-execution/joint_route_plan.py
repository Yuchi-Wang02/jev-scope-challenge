"""Prepare and verify unscored joint-route and call-matched direct prompts."""
import argparse
import hashlib
import json

from data_tools import HERE, original_cases
from gap_run import spec, tokenizer_for
from interface import compile_visible, instruction
from joint_route import native_token_budget, plan_queries
from line_evidence import visible_lines

PREP = HERE / 'preparation'
JOINT = PREP / 'joint_route_queries.jsonl'
DIRECT = PREP / 'joint_direct_queries.jsonl'
MANIFEST = PREP / 'joint_route_query_manifest.json'
DIRECT_ORDERS = (('ALLOW', 'DENY', 'INSUFFICIENT'),
                 ('DENY', 'INSUFFICIENT', 'ALLOW'),
                 ('INSUFFICIENT', 'ALLOW', 'DENY'),
                 ('ALLOW', 'INSUFFICIENT', 'DENY'),
                 ('DENY', 'ALLOW', 'INSUFFICIENT'),
                 ('INSUFFICIENT', 'DENY', 'ALLOW'))
SOURCE_PATHS = ('JOINT_ROUTE_PROTOCOL.md', 'joint_route.py', 'joint_route_plan.py',
                'interface.py', 'line_evidence.py', 'data_tools.py',
                'data/original_cases.jsonl', '../evidence-gap/gap_data.py',
                '../next-study/study.py')


def digest(payload):
    return hashlib.sha256(payload.replace(b'\r\n', b'\n')).hexdigest()


def json_lines(rows):
    return ''.join(json.dumps(r, ensure_ascii=False, separators=(',', ':')) + '\n'
                   for r in rows).encode('utf-8')


def direct_queries(cases, all_orders=False):
    if cases != original_cases():
        raise ValueError('Only exact original development inputs are planned')
    rows = []
    for case in cases:
        schema = compile_visible(case['state'], case['instruction'])
        call_count = len(visible_lines(case['state']))
        if not 2 <= call_count <= len(DIRECT_ORDERS):
            raise ValueError('Unsupported per-input direct budget')
        context = instruction(schema, case['instruction'], 'direct')
        for mapping, order in enumerate(DIRECT_ORDERS if all_orders else
                                        DIRECT_ORDERS[:call_count]):
            options = '\n'.join(f'{letter}. {spec.OPTIONS[label]}'
                                for letter, label in zip('ABC', order))
            rows.append({'source_id': case['id'], 'parent': case['parent'],
                         'family': case['family'], 'variant': case['variant'],
                         'split': 'development', 'representation': 'original',
                         'mapping': mapping, 'order': list(order),
                         'prompt': case['state'] + '\n\n' + context +
                                   '\n' + options + '\nAnswer:'})
    expected = 432 if all_orders else 228
    if len(rows) != expected or len({(r['source_id'], r['mapping']) for r in rows}) != expected:
        raise ValueError('Call-matched direct query grid drift')
    return rows


def expected():
    cases = original_cases()
    joint = plan_queries(cases)
    direct = direct_queries(cases)
    if (len({(r['source_id'], r['line_index'], r['mapping']) for r in joint}) != 456 or
            any(r['split'] != 'development' or r['representation'] != 'original'
                for r in joint + direct)):
        raise ValueError('Duplicate or foreign planned query')
    joint_bytes, direct_bytes = json_lines(joint), json_lines(direct)
    manifest = {
        'status': 'unscored_preparation_not_execution_freeze',
        'source_sha256_lf': {path: digest((HERE / path).read_bytes()) for path in SOURCE_PATHS},
        'joint_query_sha256_lf': digest(joint_bytes),
        'direct_query_sha256_lf': digest(direct_bytes),
        'original_development_inputs': len(cases),
        'joint_primary_queries': 228, 'joint_reverse_queries': 228,
        'call_matched_direct_queries': 228,
        'planned_arm': 'N1_historical_kev_lora_native',
        'actual_model_forwards': 0, 'rewrite_or_reserved_queries': 0,
        'independent_human_annotations': 0,
        'note': ('Only prompt is model input. IDs, variant, split and line offsets are '
                 'audit metadata. Encoded execution freeze and runner do not yet exist.')}
    return ((JOINT, joint_bytes), (DIRECT, direct_bytes),
            (MANIFEST, (json.dumps(manifest, indent=2) + '\n').encode('utf-8')))


def run(command):
    artifacts = expected()
    if command == 'build':
        PREP.mkdir(exist_ok=True)
    for path, content in artifacts:
        if path.exists():
            if path.read_bytes().replace(b'\r\n', b'\n') != content:
                raise ValueError(f'Joint-route preparation drift: {path.name}')
        elif command == 'build':
            path.write_bytes(content)
        else:
            raise ValueError(f'Missing joint-route preparation: {path.name}')
    return {'status': 'verified' if command == 'verify' else 'built',
            'joint_queries': 456, 'direct_queries': 228,
            'actual_model_forwards': 0}


def token_budget(cache):
    joint = native_token_budget(cache)
    tokenizer = tokenizer_for(cache)
    candidates = {letter: tokenizer.encode(' ' + letter, add_special_tokens=False)
                  for letter in 'ABC'}
    if any(len(ids) != 1 for ids in candidates.values()) or len(
            {ids[0] for ids in candidates.values()}) != 3:
        raise ValueError('Direct letters A-C are not distinct single tokens')
    direct_total = 0
    maximum = 0
    for row in direct_queries(original_cases()):
        ids = tokenizer.encode(row['prompt'], add_special_tokens=False)
        for letter in 'ABC':
            if tokenizer.encode(row['prompt'] + ' ' + letter,
                                add_special_tokens=False) != ids + candidates[letter]:
                raise ValueError('Direct answer-token boundary drift')
        direct_total += len(ids)
        maximum = max(maximum, len(ids))
    return {'status': 'tokenizer_only_no_inference',
            'joint_primary_input_tokens': joint['planned_input_tokens_by_order'][0],
            'joint_reverse_input_tokens': joint['planned_input_tokens_by_order'][1],
            'direct_call_matched_input_tokens': direct_total,
            'joint_max_input_tokens': joint['max_input_tokens'],
            'direct_max_input_tokens': maximum,
            'actual_model_forwards': 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('build', 'verify', 'budget'))
    parser.add_argument('--cache', default='G:/jev-lab/hf-cache')
    args = parser.parse_args()
    print(json.dumps(token_budget(args.cache) if args.command == 'budget' else
                     run(args.command), indent=2))
