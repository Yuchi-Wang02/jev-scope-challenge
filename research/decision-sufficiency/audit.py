"""Compare projection against independent finite database enumeration.

The audit enumerates complete databases with zero, one and two omitted matches,
all independent original-payment assignments, and all possible intended targets.
This checks a finite fragment. The general projection argument is in CONTRACT.md.
"""
import copy
import itertools
from semantics import ContractError, evaluate, projected_worlds, VALID, INVALID, UNKNOWN
from examples import base, record


def brute_worlds(state):
    """Independent complete-database enumeration; no production resolver calls."""
    selector = state['request']['selector']
    extra = state['retrieval']['additional_matches']
    visible = state['records']
    hidden_counts = {'none': (0,), 'possible': (0, 1, 2), 'at_least_one': (1, 2)}[extra]
    full = set()
    for count in hidden_counts:
        if selector['kind'] == 'order_id':
            if count > 1 or (count and any(r['order_id'] == selector['value'] for r in visible)):
                continue
        hidden = [record(selector['value'] if selector['kind'] == 'order_id' else f'__hidden_{i}',
                         state['retrieval']['omitted_original_methods'], selector['value']
                         if selector['kind'] == 'product' else '__product_unobserved') for i in range(count)]
        records = visible + hidden
        for originals in itertools.product(*(r['original_methods'] for r in records)):
            targets = [(r, original, i >= len(visible)) for i, (r, original) in enumerate(zip(records, originals))
                       if r[selector['kind']] == selector['value']]
            if not targets:
                full.add((False, None, None))
            for target, original, is_hidden in targets:
                identity = None if is_hidden and selector['kind'] == 'product' else target['order_id']
                full.add((True, identity, original))
    return full


def brute_decision(worlds, state):
    dst = state['request']['destination_id']
    labels = set()
    identities = set()
    for exists, identity, original in worlds:
        identities.add(identity if exists else None)
        if not exists or dst is None:
            labels.add(UNKNOWN)
        elif dst == original or state['payment_methods'].get(dst) == 'gift_card':
            labels.add(VALID)
        else:
            labels.add(INVALID)
    label = next(iter(labels)) if len(labels) == 1 else UNKNOWN
    unique = len(identities) == 1 and None not in identities
    return label, label if unique else UNKNOWN


def exhaustive():
    domains = [['card_A'], ['card_B'], ['card_A', 'card_B']]
    omitted = [('none', [])] + [(kind, d) for kind in ('possible', 'at_least_one') for d in domains]
    count = invalid = separated = projections = 0
    for n in range(3):
        for assignments in itertools.product(domains, repeat=n):
            for (extra, hidden), dst, kind in itertools.product(omitted, ('card_A', 'card_B', 'gift_G', 'absent', None), ('product', 'order_id')):
                s = base(); s['original_method_universe'] = ['card_A', 'card_B']
                s['request'] = {'selector': {'kind': kind, 'value': 'mug' if kind == 'product' else 'order_1'}, 'destination_id': dst}
                s['records'] = [record(f'order_{i+1}', d) for i, d in enumerate(assignments)]
                s['retrieval'] = {'query': copy.deepcopy(s['request']['selector']), 'additional_matches': extra, 'omitted_original_methods': hidden}
                full = brute_worlds(s)
                try:
                    reduced = projected_worlds(s)
                except ContractError:
                    assert not full, 'Rejected a consistent finite contract'
                    invalid += 1; continue
                assert full == {(w['target_exists'], w['target_id'], w['original_method']) for w in reduced}
                answer = evaluate(s)
                assert (answer['predicate_only'], answer['unique_target_required']) == brute_decision(full, s)
                if answer['predicate_only'] != answer['unique_target_required']:
                    assert answer['unique_target_required'] == UNKNOWN
                    separated += 1
                assert not answer['execution_authorized']
                projections += len(full); count += 1
    return {'valid_contracts_checked': count, 'inconsistent_contracts_rejected': invalid,
            'decision_relevant_projections_checked': projections,
            'contracts_where_interfaces_differ': separated,
            'max_visible_records': 2, 'max_omitted_records_in_brute_force': 2,
            'original_payment_domain_size': 2, 'model_calls': 0,
            'independent_human_annotations': 0,
            'scope': 'Finite software verification, not a dataset score or new theorem'}
