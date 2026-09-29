"""Unscored joint request/field/polarity routing candidate on original development.

One visible source line gets one mutually exclusive choice. Construction facts
and gold decisions never enter a prompt or runtime aggregation.
"""
import argparse
import json
from collections import Counter

from data_tools import original_cases
from interface import compile_visible, status_for
from line_evidence import visible_lines

OTHER_REQUEST = 'OTHER_REQUEST'
NO_OBSERVATION = 'NO_CLEAR_TARGET_OBSERVATION'


def labels(schema):
    result = [OTHER_REQUEST, NO_OBSERVATION]
    for field in schema['fields']:
        result.extend((field['name'] + ':POSITIVE', field['name'] + ':NEGATIVE'))
    if len(result) not in (6, 8):
        raise ValueError('Unsupported field count for joint route')
    return result


def option(label, schema):
    if label == OTHER_REQUEST:
        return 'This line concerns a different request, not the requested target.'
    if label == NO_OBSERVATION:
        return 'This line does not clearly record any listed field value for the requested target.'
    field_name, polarity = label.split(':')
    field = next((f for f in schema['fields'] if f['name'] == field_name), None)
    if field is None or polarity not in ('POSITIVE', 'NEGATIVE'):
        raise ValueError('Unknown route option')
    definition = field['positive' if polarity == 'POSITIVE' else 'negative']
    return f'This line records {field_name} {polarity.lower()} for the requested target: {definition}.'


def prompt(header, line, policy, schema, order):
    if sorted(order) != sorted(labels(schema)):
        raise ValueError('Incomplete or foreign option order')
    definitions = '\n'.join(f"{f['name']}: positive = {f['positive']}; negative = {f['negative']}."
                            for f in schema['fields'])
    choices = '\n'.join(f'{letter}. {option(label, schema)}'
                        for letter, label in zip('ABCDEFGH', order))
    return (f'{header}\nEvidence line under inspection: {line}\n\n'
            f'Policy: {policy}\nTarget-field definitions (not observations):\n{definitions}\n'
            'Assign this one line to at most one request/field/value route. '
            'A line about another request cannot fill a target field. '
            'Do not infer an observation from a field definition, policy, or desired action. '
            'Choose the no-clear-observation option if the line cannot be bound.\n'
            f'{choices}\nAnswer:')


def plan_queries(cases):
    if cases != original_cases():
        raise ValueError('Only exact original development inputs are planned')
    plans = []
    for case in cases:
        schema = compile_visible(case['state'], case['instruction'])
        header = case['state'].splitlines()[0]
        for line in visible_lines(case['state']):
            canonical = labels(schema)
            for mapping, order in enumerate((canonical, list(reversed(canonical)))):
                plans.append({'source_id': case['id'], 'parent': case['parent'],
                              'family': case['family'], 'variant': case['variant'],
                              'split': 'development', 'representation': 'original',
                              'line_index': line['line_index'],
                              'evidence_span': {k: line[k] for k in ('start', 'end', 'text')},
                              'mapping': mapping, 'order': order,
                              'prompt': prompt(header, line['text'], case['instruction'],
                                               schema, order)})
    if len(plans) != 456 or Counter(p['mapping'] for p in plans) != {0: 228, 1: 228}:
        raise ValueError('Joint-route query grid drift')
    return plans


def aggregate(state, schema, choices):
    """Map model choices to four-state fields without reading construction facts."""
    lines = visible_lines(state)
    possible = set(labels(schema))
    if set(choices) != {line['line_index'] for line in lines} or any(
            value not in possible for value in choices.values()):
        raise ValueError('Incomplete or foreign joint routing choices')
    result, spans = {}, {}
    for field in schema['fields']:
        name = field['name']
        values, cited = [], []
        for line in lines:
            choice = choices[line['line_index']]
            if choice in (name + ':POSITIVE', name + ':NEGATIVE'):
                values.append(choice.endswith(':POSITIVE'))
                cited.append({k: line[k] for k in ('start', 'end', 'text')})
        result[name] = status_for(values)
        spans[name] = cited
    return {'facts': result, 'model_selected_spans': spans,
            'provenance': 'joint_model_route_with_program_offsets',
            'absence_certified': False}


def native_token_budget(cache):
    """Load only the pinned tokenizer; no model weights or logits."""
    from gap_run import spec, tokenizer_for

    tokenizer = tokenizer_for(cache)
    candidates = {letter: tokenizer.encode(' ' + letter, add_special_tokens=False)
                  for letter in 'ABCDEFGH'}
    if any(len(ids) != 1 for ids in candidates.values()) or len(
            {ids[0] for ids in candidates.values()}) != 8:
        raise ValueError('Answer letters A-H are not distinct single tokens')
    totals = Counter()
    maximum = 0
    for plan in plan_queries(original_cases()):
        ids = tokenizer.encode(plan['prompt'], add_special_tokens=False)
        for letter in 'ABCDEFGH'[:len(plan['order'])]:
            if tokenizer.encode(plan['prompt'] + ' ' + letter,
                                add_special_tokens=False) != ids + candidates[letter]:
                raise ValueError('Native answer-token boundary drift')
        totals[plan['mapping']] += len(ids)
        maximum = max(maximum, len(ids))
    return {'status': 'tokenizer_only_no_inference', 'tokenizer_revision': spec.BASE_REV,
            'planned_input_tokens_by_order': dict(sorted(totals.items())),
            'max_input_tokens': maximum, 'actual_model_forwards': 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-token-budget', action='store_true')
    parser.add_argument('--cache', default='G:/jev-lab/hf-cache')
    args = parser.parse_args()
    report = {'status': 'unscored_dry_plan', 'original_development_inputs': 72,
              'visible_lines': 228, 'planned_queries_per_order': 228,
              'both_orders_planned_queries': len(plan_queries(original_cases())),
              'actual_model_forwards': 0, 'rewrite_queries': 0,
              'reserved_queries': 0, 'independent_human_annotations': 0}
    if args.native_token_budget:
        report['native_token_budget'] = native_token_budget(args.cache)
    print(json.dumps(report, indent=2))
