"""Finite refund-predicate specification example. No model, network or execution.

This is a small application of possible-world / certain-answer semantics, not a
new inference algorithm. See CONTRACT.md for the finite-domain assumptions.
"""
import argparse
import json
from pathlib import Path

VALID = 'VALID_DESTINATION'
INVALID = 'INVALID_DESTINATION'
UNKNOWN = 'NOT_ESTABLISHED'


class ContractError(ValueError):
    """An invalid specification must not be scored as an ordinary unknown."""


def require(condition, message):
    if not condition:
        raise ContractError(message)


def keys(obj, expected, name):
    require(isinstance(obj, dict) and set(obj) == set(expected), name + ': wrong fields')


def string(value):
    return isinstance(value, str) and bool(value.strip())


def domain(value, universe, name, allow_empty=False):
    require(isinstance(value, list), name + ': must be a list')
    require(all(string(v) for v in value), name + ': invalid identifier')
    require(len(set(value)) == len(value), name + ': duplicate identifier')
    require(allow_empty or bool(value), name + ': empty domain')
    require(set(value) <= set(universe), name + ': outside declared universe')


def matches(record, selector):
    return record[selector['kind']] == selector['value']


def validate(state):
    keys(state, ('version', 'payment_methods', 'original_method_universe',
                 'request', 'records', 'retrieval'), 'state')
    require(type(state['version']) is int and state['version'] == 1, 'unsupported version')
    methods = state['payment_methods']
    require(isinstance(methods, dict) and bool(methods), 'payment_methods: empty or invalid')
    require(all(string(k) and v in ('ordinary', 'gift_card') for k, v in methods.items()),
            'payment_methods: invalid method')
    universe = state['original_method_universe']
    domain(universe, methods, 'original_method_universe')
    require(all(methods[v] == 'ordinary' for v in universe), 'toy originals must be ordinary')
    request = state['request']
    keys(request, ('selector', 'destination_id'), 'request')
    selector = request['selector']
    keys(selector, ('kind', 'value'), 'selector')
    require(selector['kind'] in ('order_id', 'product') and string(selector['value']),
            'invalid selector')
    require(request['destination_id'] is None or string(request['destination_id']),
            'invalid destination identifier')
    records = state['records']
    require(isinstance(records, list), 'records: must be a list')
    ids = []
    for record in records:
        keys(record, ('order_id', 'product', 'original_methods'), 'record')
        require(string(record['order_id']) and string(record['product']), 'invalid record identifier')
        ids.append(record['order_id'])
        domain(record['original_methods'], universe, 'record.original_methods')
    require(len(set(ids)) == len(ids), 'duplicate order ID')
    retrieval = state['retrieval']
    keys(retrieval, ('query', 'additional_matches', 'omitted_original_methods'), 'retrieval')
    require(retrieval['query'] == selector, 'retrieval contract does not cover the requested selector')
    extra = retrieval['additional_matches']
    require(extra in ('none', 'possible', 'at_least_one'), 'invalid additional_matches')
    domain(retrieval['omitted_original_methods'], universe, 'omitted_original_methods', extra == 'none')
    require(extra != 'none' or not retrieval['omitted_original_methods'], 'none with a hidden domain')
    visible = [r for r in records if matches(r, selector)]
    require(not (selector['kind'] == 'order_id' and visible and extra == 'at_least_one'),
            'unique ID cannot have both a visible and an omitted matching order')
    return visible


def projected_worlds(state):
    """Exact decision-relevant projections, not counts/probabilities of databases.

    Unnamed omitted product matches are collapsed to target_id=None. This cannot
    establish identity, and preserves every outcome for this unary predicate.
    """
    visible = validate(state)
    selector = state['request']['selector']
    extra = state['retrieval']['additional_matches']
    out = [{'target_exists': True, 'target_id': r['order_id'], 'original_method': m}
           for r in visible for m in sorted(r['original_methods'])]
    can_hide = extra != 'none' and not (selector['kind'] == 'order_id' and visible)
    if can_hide:
        out.extend({'target_exists': True,
                    'target_id': selector['value'] if selector['kind'] == 'order_id' else None,
                    'original_method': m}
                   for m in sorted(state['retrieval']['omitted_original_methods']))
    if not visible and extra != 'at_least_one':
        out.append({'target_exists': False, 'target_id': None, 'original_method': None})
    require(bool(out), 'no consistent projected world')
    return sorted(out, key=lambda row: json.dumps(row, sort_keys=True))


def evaluate(state):
    worlds = projected_worlds(state)
    destination = state['request']['destination_id']
    existing_gift = state['payment_methods'].get(destination) == 'gift_card'
    annotated = []
    for world in worlds:
        outcome = (UNKNOWN if not world['target_exists'] or destination is None else
                   VALID if existing_gift or destination == world['original_method'] else INVALID)
        annotated.append({**world, 'outcome': outcome})
    outcomes = {w['outcome'] for w in annotated}
    predicate = next(iter(outcomes)) if len(outcomes) == 1 else UNKNOWN
    target_ids = {w['target_id'] for w in worlds}
    unique = all(w['target_exists'] for w in worlds) and None not in target_ids and len(target_ids) == 1
    witnesses = {outcome: next(w for w in annotated if w['outcome'] == outcome)
                 for outcome in sorted(outcomes)}
    return {'predicate_only': predicate,
            'unique_target_required': predicate if unique else UNKNOWN,
            'identity_established': unique,
            'target_id': next(iter(target_ids)) if unique else None,
            'execution_authorized': False,
            'projected_worlds': annotated,
            'witnesses_by_outcome': witnesses}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path, help='One contract JSON object, not a model prompt')
    args = parser.parse_args()
    try:
        result = {'status': 'VALID_CONTRACT', **evaluate(json.loads(args.input.read_text(encoding='utf-8')))}
    except (ContractError, json.JSONDecodeError) as exc:
        result = {'status': 'INVALID_CONTRACT', 'error': str(exc), 'execution_authorized': False}
        print(json.dumps(result, indent=2)); raise SystemExit(2)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
