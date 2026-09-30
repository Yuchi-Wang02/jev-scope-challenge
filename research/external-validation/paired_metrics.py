"""Prospective per-condition paired metrics; no I/O, inference or label adoption.

Only finalized, clear references belong in a real evaluation. This function
checks shape, not the validity or independence of human judgments.
"""
from collections import Counter
from action_interface import ACTIONS


def ratio(numerator, denominator):
    return {'numerator': numerator, 'denominator': denominator,
            'rate': numerator / denominator if denominator else None}


def validate_pairs(pairs):
    """Validate the shared cohort without inventing any predictions or scores."""
    if not isinstance(pairs, list) or not pairs:
        raise ValueError('A nonempty finalized pair list is required')
    pair_ids, tree_ids, item_ids = set(), set(), set()
    for pair in pairs:
        if not isinstance(pair, dict) or set(pair) != {
                'pair_id', 'tree_id', 'item_ids', 'reference_actions'}:
            raise ValueError('Unexpected pair schema')
        for field, seen in (('pair_id', pair_ids), ('tree_id', tree_ids)):
            value = pair[field]
            if not isinstance(value, str) or not value.strip() or value in seen:
                raise ValueError('Require unique pair IDs and one pair per tree')
            seen.add(value)
        ids, refs = pair['item_ids'], pair['reference_actions']
        if (not isinstance(ids, list) or len(ids) != 2 or
                not isinstance(refs, list) or len(refs) != 2):
            raise ValueError('Each pair needs exactly two ordered items/actions')
        for item, ref in zip(ids, refs):
            if (not isinstance(item, str) or not item.strip() or item in item_ids or
                    not isinstance(ref, str) or ref not in ACTIONS):
                raise ValueError('Repeated/invalid item or unresolved reference')
            item_ids.add(item)
    return pair_ids, tree_ids, item_ids


def score_condition(pairs, predictions, *, condition):
    """One prediction per item, one pair per tree, one condition per call.

    pairs: exact dictionaries with pair_id, tree_id, item_ids, reference_actions.
    predictions: exact dictionaries with item_id and action (semantic action or
    None for a recorded failed output). Missing rows are an integrity failure,
    not inferred abstentions. No repeats, mappings or seeds may be pooled here.
    """
    if not isinstance(condition, str) or not condition.strip():
        raise ValueError('A named condition is required')
    if not isinstance(predictions, list):
        raise ValueError('Predictions must be a list')
    pair_ids, tree_ids, item_ids = validate_pairs(pairs)
    by_item = {}
    for row in predictions:
        if not isinstance(row, dict) or set(row) != {'item_id', 'action'}:
            raise ValueError('Unexpected prediction schema')
        item, action = row['item_id'], row['action']
        if not isinstance(item, str) or item not in item_ids or item in by_item:
            raise ValueError('Foreign or repeated prediction item')
        if action is not None and (not isinstance(action, str) or action not in ACTIONS):
            raise ValueError('Invalid semantic action; failed output must be None')
        by_item[item] = action
    if set(by_item) != item_ids:
        raise ValueError('Missing prediction rows; preserve failures explicitly')

    confusion = {ref: {pred: 0 for pred in (*ACTIONS, 'INVALID_OUTPUT')}
                 for ref in ACTIONS}
    correctness = Counter({'both_correct': 0, 'first_only': 0,
                           'second_only': 0, 'neither_correct': 0})
    strata = {kind: {'pairs': 0, 'both_correct': 0, 'prediction_changed': 0,
                     'prediction_same': 0, 'incomplete_pair': 0}
              for kind in ('reference_changed', 'reference_same')}
    item_correct = failures = decisive_when_ask = ask_when_decisive = 0
    ask_refs = decisive_refs = 0
    traces = []
    for pair in pairs:
        refs = pair['reference_actions']
        preds = [by_item[item] for item in pair['item_ids']]
        correct = [a == b for a, b in zip(refs, preds)]
        bucket = {(True, True): 'both_correct', (True, False): 'first_only',
                  (False, True): 'second_only', (False, False): 'neither_correct'}[tuple(correct)]
        correctness[bucket] += 1
        kind = 'reference_changed' if refs[0] != refs[1] else 'reference_same'
        group = strata[kind]
        group['pairs'] += 1
        group['both_correct'] += all(correct)
        complete = None not in preds
        group['incomplete_pair' if not complete else
              'prediction_changed' if preds[0] != preds[1] else 'prediction_same'] += 1
        for ref, pred, good in zip(refs, preds, correct):
            confusion[ref]['INVALID_OUTPUT' if pred is None else pred] += 1
            item_correct += good
            failures += pred is None
            ask_refs += ref == 'ASK'
            decisive_refs += ref in ('Yes', 'No')
            decisive_when_ask += ref == 'ASK' and pred in ('Yes', 'No')
            ask_when_decisive += ref in ('Yes', 'No') and pred == 'ASK'
        traces.append({'pair_id': pair['pair_id'], 'tree_id': pair['tree_id'],
                       'item_ids': pair['item_ids'], 'references': refs,
                       'predictions': preds, 'correctness': bucket,
                       'reference_changed': refs[0] != refs[1],
                       'prediction_changed': preds[0] != preds[1] if complete else None})
    for group in strata.values():
        group['pair_both_correct'] = ratio(group['both_correct'], group['pairs'])
    return {
        'condition': condition, 'tree_units': len(tree_ids),
        'pairs': len(pairs), 'items': len(item_ids),
        'item_accuracy': ratio(item_correct, len(item_ids)),
        'pair_both_correct': ratio(correctness['both_correct'], len(pairs)),
        'invalid_output': ratio(failures, len(item_ids)),
        'decisive_when_reference_ask': ratio(decisive_when_ask, ask_refs),
        'ask_when_reference_decisive': ratio(ask_when_decisive, decisive_refs),
        'confusion': confusion, 'correctness_counts': dict(correctness),
        'change_strata': strata,
        'pair_records': sorted(traces, key=lambda row: row['pair_id']),
    }
