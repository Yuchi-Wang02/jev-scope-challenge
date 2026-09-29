"""Freeze an ID-only, token-budgeted direct control; never run a model."""
import argparse
import hashlib
import json

from data_tools import HERE, original_cases
from gap_run import spec, tokenizer_for
from joint_route import native_token_budget
from joint_route_plan import PREP, digest, direct_queries, json_lines
from line_evidence import visible_lines

TARGET_INPUT_TOKENS = 95889  # pinned joint-route primary tokenizer-only budget
COSTS = PREP / 'joint_direct_all_token_costs.jsonl'
SELECTED = PREP / 'joint_direct_token_matched.jsonl'
MANIFEST = PREP / 'joint_direct_token_manifest.json'
SOURCE_PATHS = ('JOINT_TOKEN_CONTROL.md', 'joint_token_control.py',
                'joint_route.py', 'joint_route_plan.py',
                'preparation/joint_route_query_manifest.json',
                'preparation/joint_direct_queries.jsonl',
                '../next-study/study.py')


def identity(row):
    return row['source_id'], row['mapping']


def all_costs(cache):
    """Tokenizer-only count plus A-C answer-boundary check on all six orders."""
    if native_token_budget(cache)['planned_input_tokens_by_order'][0] != TARGET_INPUT_TOKENS:
        raise ValueError('Joint-route primary token target drift')
    tok = tokenizer_for(cache)
    candidates = {letter: tok.encode(' ' + letter, add_special_tokens=False)
                  for letter in 'ABC'}
    if any(len(ids) != 1 for ids in candidates.values()) or len(
            {ids[0] for ids in candidates.values()}) != 3:
        raise ValueError('Direct answer letters are not distinct single tokens')
    costs = []
    for row in direct_queries(original_cases(), all_orders=True):
        ids = tok.encode(row['prompt'], add_special_tokens=False)
        for letter in 'ABC':
            if tok.encode(row['prompt'] + ' ' + letter,
                          add_special_tokens=False) != ids + candidates[letter]:
                raise ValueError('Direct answer-token boundary drift')
        costs.append({'source_id': row['source_id'], 'mapping': row['mapping'],
                      'input_tokens': len(ids),
                      'prompt_sha256_lf': digest(row['prompt'].encode('utf-8'))})
    return costs


def choose(costs):
    """Add distinct orders in ID-hash rounds until no next order fits."""
    cases = original_cases()
    all_rows = direct_queries(cases, all_orders=True)
    base = direct_queries(cases)
    by_id = {identity(row): row for row in all_rows}
    by_cost = {identity(row): row['input_tokens'] for row in costs}
    if (len(costs) != 432 or len(by_cost) != 432 or
            set(by_id) != set(by_cost) or any(n <= 0 for n in by_cost.values())):
        raise ValueError('Incomplete all-order direct cost grid')
    selected = list(base)
    spent = sum(by_cost[identity(row)] for row in selected)
    if spent >= TARGET_INPUT_TOKENS:
        raise ValueError('Call-matched direct already exceeds target')
    ordered_cases = sorted(cases, key=lambda c: hashlib.sha256(
        c['id'].encode('utf-8')).hexdigest())
    for extra_round in range(6):
        for case in ordered_cases:
            mapping = len(visible_lines(case['state'])) + extra_round
            key = case['id'], mapping
            if key not in by_id:
                continue
            cost = by_cost[key]
            if spent + cost <= TARGET_INPUT_TOKENS:
                selected.append(by_id[key])
                spent += cost
    return [row | {'planned_input_tokens': by_cost[identity(row)]}
            for row in selected], spent


def expected(costs):
    all_rows = direct_queries(original_cases(), all_orders=True)
    if len(costs) != len(all_rows):
        raise ValueError('Direct cost grid length drift')
    for recorded, row in zip(costs, all_rows):
        if (identity(recorded) != identity(row) or
                recorded['prompt_sha256_lf'] != digest(row['prompt'].encode('utf-8')) or
                not isinstance(recorded['input_tokens'], int) or
                recorded['input_tokens'] <= 0):
            raise ValueError('Direct prompt cost identity drift')
    chosen, spent = choose(costs)
    costs_bytes, chosen_bytes = json_lines(costs), json_lines(chosen)
    manifest = {
        'status': 'tokenizer_only_unscored_preparation',
        'source_sha256_lf': {path: digest((HERE / path).read_bytes()) for path in SOURCE_PATHS},
        'tokenizer_revision': spec.BASE_REV,
        'selection_rule': ('Start with all 228 call-matched queries; traverse each next unused '
                           'order in rounds, cases sorted by SHA256(source_id), include only if '
                           'the recorded input-token total stays <= target. No labels used.'),
        'joint_primary_target_input_tokens': TARGET_INPUT_TOKENS,
        'all_six_order_direct_queries': len(costs),
        'call_matched_direct_queries': 228,
        'token_matched_direct_queries': len(chosen),
        'additional_direct_queries': len(chosen) - 228,
        'call_matched_input_tokens': sum(r['input_tokens'] for r in costs
                                          if identity(r) in {identity(b) for b in
                                                             direct_queries(original_cases())}),
        'token_matched_direct_input_tokens': spent,
        'input_token_gap': TARGET_INPUT_TOKENS - spent,
        'all_costs_sha256_lf': digest(costs_bytes),
        'selected_queries_sha256_lf': digest(chosen_bytes),
        'actual_model_forwards': 0, 'rewrite_or_reserved_queries': 0,
        'independent_human_annotations': 0,
        'verification_limit': ('Offline verification checks source prompts, every stored cost, '
                               'selection and hashes. Exact tokenizer counts require the '
                               'pinned local tokenizer and verify-tokenizer.')}
    if manifest['call_matched_input_tokens'] != 76855 or manifest['input_token_gap'] >= 435:
        raise ValueError('Direct budget or closeness drift')
    manifest_bytes = (json.dumps(manifest, indent=2) + '\n').encode('utf-8')
    return ((COSTS, costs_bytes), (SELECTED, chosen_bytes), (MANIFEST, manifest_bytes)), manifest


def run(command, cache):
    if command in ('build', 'verify-tokenizer'):
        costs = all_costs(cache)
    else:
        costs = [json.loads(line) for line in COSTS.read_text(encoding='utf-8').splitlines()]
    artifacts, manifest = expected(costs)
    if command == 'build':
        PREP.mkdir(exist_ok=True)
    for path, content in artifacts:
        if path.exists():
            if path.read_bytes().replace(b'\r\n', b'\n') != content:
                raise ValueError(f'Token-control preparation drift: {path.name}')
        elif command == 'build':
            path.write_bytes(content)
        else:
            raise ValueError(f'Missing token-control preparation: {path.name}')
    return {'status': 'verified' if command != 'build' else 'built',
            'direct_queries': manifest['token_matched_direct_queries'],
            'input_tokens': manifest['token_matched_direct_input_tokens'],
            'gap': manifest['input_token_gap'], 'new_model_forwards': 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('build', 'verify', 'verify-tokenizer'))
    parser.add_argument('--cache', default='G:/jev-lab/hf-cache')
    args = parser.parse_args()
    print(json.dumps(run(args.command, args.cache), indent=2))
