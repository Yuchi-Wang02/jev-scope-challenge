"""Post-hoc label-replacement diagnostic on the saved line pilot; no inference.

Every replacement uses program construction records unavailable to a runtime
system. Results are diagnostic counterfactuals, never scores for a new method.
"""
import argparse
import itertools
import json

from data_tools import HERE, original_cases
from fact_run import read_rows
from interface import compile_visible, execute
from line_analyze import analyze
from line_evidence import aggregate_line_choices, visible_lines
from line_run import OUT

CATEGORIES = ('wrong_request', 'wrong_field', 'wrong_polarity', 'missed_relevant')
DEST = HERE / 'line_results/v0.1/oracle_decomposition.json'


def relation(row, case, field):
    source = case['records'][row['line_index']]
    reference = ('IRRELEVANT' if source['scope'] != case['target'] or
                 source['field'] != field else
                 'POSITIVE' if source['value'] else 'NEGATIVE')
    model = row['prediction']
    if model == reference:
        return 'correct', reference
    if model == 'IRRELEVANT':
        return 'missed_relevant', reference
    if source['scope'] != case['target']:
        return 'wrong_request', reference
    if source['field'] != field:
        return 'wrong_field', reference
    if reference != 'IRRELEVANT':
        return 'wrong_polarity', reference
    raise ValueError('Unclassified model/reference disagreement')


def compute():
    summary, saved_decisions, saved_claims = analyze()
    cases = original_cases()
    raw = read_rows(OUT / 'N1.jsonl')
    lookup = {(r['source_id'], r['field'], r['line_index']): r for r in raw}
    truth = {(r['source_id'], r['field']): r['reference_status'] for r in saved_claims}
    baseline = {r['source_id']: r for r in saved_decisions}
    classified = {}
    counts = {kind: {'line_judgments': 0, 'affected_cases': set(),
                     'parent_groups': set()} for kind in CATEGORIES}
    for case in cases:
        schema = compile_visible(case['state'], case['instruction'])
        for field in schema['fields']:
            key = (case['id'], field['name'])
            classified[key] = []
            for line in visible_lines(case['state']):
                row = lookup[(case['id'], field['name'], line['line_index'])]
                kind, reference = relation(row, case, field['name'])
                classified[key].append((line['line_index'], row['prediction'],
                                        reference, kind))
                if kind in counts:
                    counts[kind]['line_judgments'] += 1
                    counts[kind]['affected_cases'].add(case['id'])
                    counts[kind]['parent_groups'].add(case['parent'])
    categories = {kind: {'line_judgments': value['line_judgments'],
                         'affected_cases': len(value['affected_cases']),
                         'parent_groups': len(value['parent_groups'])}
                  for kind, value in counts.items()}
    if ([categories[k]['line_judgments'] for k in CATEGORIES[:3]] != [73, 172, 4] or
            len(lookup) != 548 or len(classified) != 168):
        raise ValueError('Pilot grid or error partition drift')

    rows = []
    for n in range(len(CATEGORIES) + 1):
        for selected in itertools.combinations(CATEGORIES, n):
            repairs = set(selected)
            outcomes = []
            correct_fields = exact_vectors = 0
            for case in cases:
                schema = compile_visible(case['state'], case['instruction'])
                vector = {}
                for field in schema['fields']:
                    name = field['name']
                    choices = {index: (reference if kind in repairs else model)
                               for index, model, reference, kind in classified[(case['id'], name)]}
                    vector[name] = aggregate_line_choices(case['state'], name, choices)['status']
                    correct_fields += vector[name] == truth[(case['id'], name)]
                exact_vectors += all(vector[name] == truth[(case['id'], name)] for name in vector)
                prediction = execute(schema, vector)
                outcomes.append({'id': case['id'], 'parent': case['parent'],
                                 'gold': case['gold'], 'prediction': prediction,
                                 'correct': prediction == case['gold']})
            uncertain = [r for r in outcomes if r['gold'] == 'INSUFFICIENT']
            determined = [r for r in outcomes if r['gold'] != 'INSUFFICIENT']
            rows.append({
                'replaced_categories': list(selected),
                'oracle_replaced_judgments': sum(categories[k]['line_judgments'] for k in selected),
                'correct_decisions': sum(r['correct'] for r in outcomes),
                'false_commitments': sum(r['prediction'] != 'INSUFFICIENT' for r in uncertain),
                'determined_correct': sum(r['correct'] for r in determined),
                'false_insufficient': sum(r['prediction'] == 'INSUFFICIENT' for r in determined),
                'wrong_supported_actions': sum(r['prediction'] != 'INSUFFICIENT' and not r['correct']
                                               for r in determined),
                'correct_fields': correct_fields,
                'exact_fact_vectors': exact_vectors,
                'baseline_errors_recovered': sum(r['correct'] and
                                                 not baseline[r['id']]['correct'] for r in outcomes),
                'baseline_correct_regressed': sum(not r['correct'] and
                                                  baseline[r['id']]['correct'] for r in outcomes),
                'complete_parent_groups': sum(all(r['correct'] for r in outcomes
                                                  if r['parent'] == parent)
                                              for parent in {r['parent'] for r in outcomes})})
    if len(rows) != 16 or any(r['correct_decisions'] != r['determined_correct'] +
                                  24 - r['false_commitments'] for r in rows):
        raise ValueError('Counterfactual decision accounting drift')
    base, full = rows[0], rows[-1]
    if (base['correct_decisions'], base['false_commitments'], base['determined_correct'],
            base['correct_fields'], base['exact_fact_vectors']) != (
            summary['correct_decisions'], summary['false_commitments'],
            summary['determined_correct'], summary['correct_fields'],
            summary['exact_fact_vectors']):
        raise ValueError('No-replacement arm differs from saved pilot')
    if (full['correct_decisions'], full['correct_fields'], full['exact_fact_vectors']) != (72, 168, 72):
        raise ValueError('Full construction-label replacement must recover program truth')
    return {'status': 'post_hoc_program_oracle_diagnostic_only',
            'source_config_hash': summary['config_hash'], 'arm': 'N1',
            'original_development_inputs': 72, 'parent_groups': 12,
            'saved_model_forwards': 548, 'new_model_forwards': 0,
            'independent_human_annotations': 0,
            'category_priority': list(CATEGORIES),
            'error_categories': categories, 'counterfactuals': rows,
            'interpretation_limit': ('Ground-truth replacements are unavailable to a runtime method; '
                                     'rows are interacting counterfactuals on known development cases, '
                                     'not new model scores or independent trials.')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    payload = (json.dumps(compute(), indent=2) + '\n').encode('utf-8')
    if args.verify:
        if DEST.read_bytes().replace(b'\r\n', b'\n') != payload:
            raise ValueError('Oracle decomposition artifact drift')
    elif DEST.exists():
        raise ValueError('Preserve existing oracle decomposition; version a changed analysis')
    else:
        DEST.write_bytes(payload)
    print(json.dumps({'status': 'verified' if args.verify else 'built',
                      'counterfactuals': 16, 'new_model_forwards': 0}))


if __name__ == '__main__':
    main()
