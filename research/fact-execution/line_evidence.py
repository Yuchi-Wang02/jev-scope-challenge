"""Unscored, original-development-only line evidence candidate.

One model classification is planned per visible evidence line and target field.
No model scores, program-derived facts, or gold labels are supplied to a prompt.
"""
import argparse
import json
from collections import Counter

from data_tools import original_cases
from interface import compile_visible

LABELS = ('POSITIVE', 'NEGATIVE', 'IRRELEVANT')
ORDERS = (LABELS, tuple(reversed(LABELS)))
OPTIONS = {
    'POSITIVE': 'This line explicitly records the positive value for this target field.',
    'NEGATIVE': 'This line explicitly records the negative value for this target field.',
    'IRRELEVANT': 'This line does not record either value for this target field.'}
ORIGINAL_HEADERS = {'Evidence:', 'Available records:', 'Decision notes:', 'Supplied facts:'}


def visible_lines(state):
    """Locate every record line; no semantic parsing or hidden construction facts."""
    lines = state.splitlines(keepends=True)
    if len(lines) < 3 or lines[1].rstrip('\r\n') not in ORIGINAL_HEADERS:
        raise ValueError('Only original one-line record blocks are supported')
    output = []
    offset = len(lines[0]) + len(lines[1])
    for index, line in enumerate(lines[2:]):
        content = line.rstrip('\r\n')
        if not content or '\r' in content:
            raise ValueError('Empty or multiline record')
        output.append({'line_index': index, 'start': offset,
                       'end': offset + len(content), 'text': content})
        offset += len(line)
    return output


def prompt(header, line, policy, field, order):
    """Give the model one line, visible policy, target and both value definitions."""
    if tuple(order) not in ORDERS:
        raise ValueError('Unknown candidate order')
    choices = '\n'.join(f'{letter}. {OPTIONS[label]}'
                        for letter, label in zip('ABC', order))
    return (f'{header}\nEvidence line under inspection: {line}\n\n'
            f'Policy: {policy}\nTarget field: {field["name"]}.\n'
            f'Positive definition: {field["positive"]}.\n'
            f'Negative definition: {field["negative"]}.\n'
            'Classify only this one line for the target field. A line about another '
            'request or a different field is irrelevant. Do not infer a recorded '
            'observation from the policy or the desired action.\n'
            f'{choices}\nAnswer:')


def plan_queries(cases):
    """Refuse rewrites, reserved inputs, or a changed original development set."""
    if cases != original_cases():
        raise ValueError('Only exact frozen original development inputs are allowed')
    plans = []
    for case in cases:
        schema = compile_visible(case['state'], case['instruction'])
        header = case['state'].splitlines()[0]
        for field in schema['fields']:
            for line in visible_lines(case['state']):
                for mapping, order in enumerate(ORDERS):
                    plans.append({'source_id': case['id'], 'parent': case['parent'],
                                  'family': case['family'], 'variant': case['variant'],
                                  'split': 'development', 'representation': 'original',
                                  'field': field['name'], 'line_index': line['line_index'],
                                  'evidence_span': {k: line[k] for k in ('start', 'end', 'text')},
                                  'mapping': mapping, 'order': list(order),
                                  'prompt': prompt(header, line['text'], case['instruction'],
                                                   field, order)})
    return plans


def aggregate_line_choices(state, field, choices):
    """Combine one label per source line; labels remain model claims, not truth."""
    lines = visible_lines(state)
    if set(choices) != {line['line_index'] for line in lines} or any(
            choice not in LABELS for choice in choices.values()):
        raise ValueError('Incomplete or invalid line classifications')
    cited = {label: [{k: line[k] for k in ('start', 'end', 'text')}
                     for line in lines if choices[line['line_index']] == label]
             for label in LABELS[:2]}
    positive, negative = cited['POSITIVE'], cited['NEGATIVE']
    status = ('CONFLICT' if positive and negative else 'TRUE' if positive else
              'FALSE' if negative else 'MISSING')
    return {'field': field, 'status': status, 'evidence_spans': positive + negative,
            'provenance': 'model_line_classification_with_program_offsets',
            'inspected_scope': 'complete_visible_record_lines'}


def audit_claim_known_grammar(state, policy, claim):
    """Offline-only reference audit; never use it to replace model predictions."""
    from cited_contract import verify_claim
    if (claim.get('provenance') != 'model_line_classification_with_program_offsets' or
            claim.get('inspected_scope') != 'complete_visible_record_lines'):
        raise ValueError('Not a complete line-classification claim')
    return verify_claim(state, policy,
                        {'field': claim['field'], 'status': claim['status'],
                         'spans': claim['evidence_spans'],
                         'inspected_scope': 'complete_visible_state'})


def audit_plan():
    plans = plan_queries(original_cases())
    counts = Counter(p['mapping'] for p in plans)
    if counts[0] != counts[1]:
        raise ValueError('Candidate-order plans are not paired')
    return {'status': 'dry_run_only', 'original_development_inputs': 72,
            'per_order_model_queries': counts[0], 'two_order_planned_queries': len(plans),
            'rewrite_queries': sum(p['representation'] != 'original' for p in plans),
            'reserved_queries': sum(p['split'] != 'development' for p in plans),
            'actual_model_forwards': 0, 'human_annotations_produced': 0}


def native_token_budget(cache):
    """Optional tokenizer-only preflight; this loads no model weights or logits."""
    from gap_run import spec, tokenizer_for
    tokenizer = tokenizer_for(cache)
    answer_ids = [tokenizer.encode(' ' + letter, add_special_tokens=False)
                  for letter in 'ABC']
    if any(len(ids) != 1 for ids in answer_ids) or len({ids[0] for ids in answer_ids}) != 3:
        raise ValueError('Answer letters are not distinct single tokens')
    totals = Counter()
    maximum = 0
    for plan in plan_queries(original_cases()):
        ids = tokenizer.encode(plan['prompt'], add_special_tokens=False)
        for letter, candidate in zip('ABC', answer_ids):
            if tokenizer.encode(plan['prompt'] + ' ' + letter,
                                add_special_tokens=False) != ids + candidate:
                raise ValueError('Answer token boundary drift')
        totals[plan['mapping']] += len(ids)
        maximum = max(maximum, len(ids))
    return {'status': 'tokenizer_only_no_inference', 'tokenizer_revision': spec.BASE_REV,
            'native_input_tokens_by_order': dict(sorted(totals.items())),
            'max_native_input_tokens': maximum, 'actual_model_forwards': 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-token-budget', action='store_true')
    parser.add_argument('--cache', default='G:/jev-lab/hf-cache')
    args = parser.parse_args()
    report = audit_plan()
    if args.native_token_budget:
        report['native_token_budget'] = native_token_budget(args.cache)
    print(json.dumps(report, indent=2))
