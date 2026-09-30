"""Build or verify a local-loss explainer from frozen N1 development decisions."""
import argparse
import json
import math
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FACT = ROOT / 'research' / 'fact-execution'
sys.path.insert(0, str(FACT))
from paired_parent_audit import audit, digest, indexed, rows, selected  # noqa: E402
sys.path.insert(0, str(FACT.parent / 'evidence-gap'))
from verify_gap import text_reference  # noqa: E402 - visible-text grammar control

OLD = FACT / 'results' / 'decisions.jsonl'
LINE = FACT / 'line_results' / 'v0.1' / 'decisions.jsonl'
OLD_SUMMARY = FACT / 'results' / 'summary.json'
LINE_SUMMARY = FACT / 'line_results' / 'v0.1' / 'summary.json'
VISIBLE = FACT / 'data' / 'original_cases.jsonl'
TEMPLATE = ROOT / 'docs' / 'risk_tradeoff_template.html'
OUTPUT = ROOT / 'docs' / 'risk_tradeoff.html'
MARKER = '__TRADEOFF_DATA__'


def counts(records):
    values = list(records.values())
    categories = {
        'correct': sum(row['correct'] for row in values),
        'false_commitments': sum(row['gold'] == 'INSUFFICIENT' and
                                 row['prediction'] != 'INSUFFICIENT'
                                 for row in values),
        'wrong_supported_actions': sum(row['gold'] != 'INSUFFICIENT' and
                                       row['prediction'] != 'INSUFFICIENT' and
                                       not row['correct'] for row in values),
        'needless_deferrals': sum(row['gold'] != 'INSUFFICIENT' and
                                  row['prediction'] == 'INSUFFICIENT'
                                  for row in values),
        'all_deferrals': sum(row['prediction'] == 'INSUFFICIENT' for row in values),
        'calls': sum(row['model_calls'] for row in values),
        'input_tokens': sum(row['input_tokens'] for row in values),
        'forward_seconds': sum(row['summed_forward_latency_s'] for row in values),
    }
    categories['wrong_actions'] = (categories['false_commitments'] +
                                   categories['wrong_supported_actions'])
    if (len(values) != 72 or categories['correct'] +
            categories['wrong_actions'] + categories['needless_deferrals'] != 72):
        raise ValueError('Decision outcomes do not partition 72 views')
    return categories


def always_defer(state, policy):
    """A constant runtime policy: no reference labels or model outputs are read."""
    return 'INSUFFICIENT'


def derived_records(cases, predictor):
    result = {}
    for case in cases:
        prediction = predictor(case['state'], case['instruction'])
        if prediction not in ('ALLOW', 'DENY', 'INSUFFICIENT'):
            raise ValueError('Invalid derived baseline action')
        result[case['id']] = {
            'source_id': case['id'], 'parent': case['parent'],
            'family': case['family'], 'variant': case['variant'],
            'gold': case['gold'], 'prediction': prediction,
            'correct': prediction == case['gold'],
            'model_calls': 0, 'input_tokens': 0, 'summed_forward_latency_s': 0,
        }
    return result


def lower_envelope(methods, deferral_key):
    """Exact lower envelope for nonnegative ratios, using rational arithmetic."""
    curves = {}
    for name, values in methods.items():
        a, b = values['wrong_actions'], values[deferral_key]
        if type(a) is not int or type(b) is not int or min(a, b) < 0:
            raise ValueError('Loss endpoints must be nonnegative integer counts')
        curves[name] = (Fraction(a), Fraction(b))
    if not curves:
        raise ValueError('Empty cost comparison')
    cuts = {Fraction(0)}
    for a, b in curves.values():
        for c, d in curves.values():
            if a != c:
                intersection = (d - b) / (a - c)
                if intersection >= 0:
                    cuts.add(intersection)
    points = sorted(cuts)

    def winners(ratio):
        losses = {name: a * ratio + b for name, (a, b) in curves.items()}
        lowest = min(losses.values())
        return [name for name, value in losses.items() if value == lowest]

    intervals = []
    for index, left in enumerate(points):
        right = points[index + 1] if index + 1 < len(points) else None
        sample = (left + right) / 2 if right is not None else left + 1
        best = winners(sample)
        if intervals and intervals[-1]['winners'] == best:
            intervals[-1]['end'] = str(right) if right is not None else None
        else:
            intervals.append({'start': str(left),
                              'end': str(right) if right is not None else None,
                              'winners': best})
    boundaries = [{'ratio': segment['start'],
                   'winners': winners(Fraction(segment['start']))}
                  for segment in intervals]
    return {'intervals': intervals, 'boundaries': boundaries}


def data():
    # Reuse the parent-paired audit's independent source/summary integrity gates.
    audit()
    previous = rows(OLD)
    methods = {
        'direct': selected(previous, 'direct_0'),
        'facts': selected(previous, 'facts_0'),
        'line': indexed(rows(LINE)),
    }
    cases = rows(VISIBLE)
    if len(cases) != 72 or len({case['id'] for case in cases}) != 72:
        raise ValueError('Visible corpus must contain 72 unique cases')
    methods['defer'] = derived_records(cases, always_defer)
    methods['grammar'] = derived_records(cases, text_reference)
    reference = methods['facts']
    for name, records in methods.items():
        if set(records) != set(reference):
            raise ValueError(f'{name} source IDs differ')
        for source_id, row in records.items():
            if any(row[key] != reference[source_id][key] for key in
                   ('parent', 'family', 'variant', 'gold')):
                raise ValueError(f'{name} paired metadata differs: {source_id}')
    old_summary = json.loads(OLD_SUMMARY.read_text(encoding='utf-8'))
    line_summary = json.loads(LINE_SUMMARY.read_text(encoding='utf-8'))
    result = {}
    for name, records in methods.items():
        totals = counts(records)
        saved = (line_summary if name == 'line' else
                 old_summary['methods']['N1'][name + '_0']['all']) if name in (
                     'direct', 'facts', 'line') else None
        mapping = {
            'correct': 'correct_decisions' if name == 'line' else 'correct',
            'false_commitments': 'false_commitments',
            'wrong_supported_actions': 'wrong_supported_actions',
            'needless_deferrals': 'false_insufficient',
            'calls': 'model_calls',
            'input_tokens': 'input_tokens',
        }
        if saved and any(totals[key] != saved[field] for key, field in mapping.items()):
            raise ValueError(f'{name} outcomes differ from saved summary')
        if saved and not math.isclose(totals['forward_seconds'],
                            saved['summed_forward_latency_s'],
                            rel_tol=0, abs_tol=1e-9):
            raise ValueError(f'{name} summed forward latency drifted')
        by_parent = {}
        for parent in sorted({row['parent'] for row in records.values()}):
            subset = {source_id: row for source_id, row in records.items()
                      if row['parent'] == parent}
            if len(subset) != 6:
                raise ValueError(f'{name} parent view count changed')
            parent_counts = counts_for_parent(subset)
            by_parent[parent] = parent_counts
        result[name] = {**totals, 'parents': by_parent,
                        'kind': 'saved_model' if saved else 'derived_baseline'}
        if not saved:
            result[name]['forward_seconds'] = None
    if ({name: (r['wrong_actions'], r['needless_deferrals'])
         for name, r in result.items()} != {
             'direct': (36, 5), 'facts': (20, 8), 'line': (6, 37),
             'defer': (0, 48), 'grammar': (0, 0)}):
        raise ValueError('Expected cost-curve endpoints drifted')
    if {name: values['all_deferrals'] for name, values in result.items()} != {
            'direct': 6, 'facts': 18, 'line': 55, 'defer': 72, 'grammar': 24}:
        raise ValueError('All-deferral counts drifted')
    if (result['grammar']['correct'] != 72 or result['defer']['correct'] != 24 or
            old_summary['known_grammar_reference']['correct'] != 72):
        raise ValueError('Derived reference correctness mismatch')
    generic = {name: result[name] for name in ('direct', 'facts', 'line', 'defer')}
    envelopes = {key: lower_envelope(generic, key)
                 for key in ('needless_deferrals', 'all_deferrals')}
    expected_intervals = {
        'needless_deferrals': [('0', '3/16', ['direct']),
                               ('3/16', '2', ['facts']),
                               ('2', None, ['defer'])],
        'all_deferrals': [('0', '3/4', ['direct']),
                         ('3/4', '37/14', ['facts']),
                         ('37/14', '17/6', ['line']),
                         ('17/6', None, ['defer'])],
    }
    for key, envelope in envelopes.items():
        if [(s['start'], s['end'], s['winners']) for s in envelope['intervals']] != expected_intervals[key]:
            raise ValueError('Exact weighted-loss envelope drifted: ' + key)
    complete_envelopes = {key: lower_envelope(result, key)
                          for key in ('needless_deferrals', 'all_deferrals')}
    if complete_envelopes['needless_deferrals']['intervals'] != [
            {'start': '0', 'end': None, 'winners': ['grammar']}] or (
            complete_envelopes['all_deferrals']['intervals'] != [
                {'start': '0', 'end': '1/2', 'winners': ['direct']},
                {'start': '1/2', 'end': None, 'winners': ['grammar']}]):
        raise ValueError('Complete comparator envelope drifted')
    return {
        'status': 'post_hoc_original_development_only',
        'methods': result,
        'exact_envelopes_without_grammar': envelopes,
        'exact_envelopes_with_grammar': complete_envelopes,
        'input_count': 72,
        'parent_count': 12,
        'wrong_action_definition': ('Non-INSUFFICIENT prediction that differs '
                                    'from the program-derived gold action'),
        'needless_deferral_definition': ('INSUFFICIENT prediction when the '
                                         'program-derived gold is determined'),
        'source_sha256_lf': {'whole_state_decisions': digest(OLD),
                             'line_decisions': digest(LINE),
                             'visible_original_cases': digest(VISIBLE),
                             'grammar_reference_wrapper': digest(
                                 FACT.parent / 'evidence-gap' / 'verify_gap.py'),
                             'grammar_parser_and_solver': digest(
                                 FACT.parent / 'evidence-gap' / 'gap_data.py')},
        'new_model_forwards': 0,
        'independent_human_annotations': 0,
        'jev_results': 0,
    }


def counts_for_parent(records):
    values = list(records.values())
    if len(values) != 6:
        raise ValueError('Expected six views per parent')
    return {
        'wrong_actions': sum(row['prediction'] != 'INSUFFICIENT' and
                             not row['correct'] for row in values),
        'needless_deferrals': sum(row['prediction'] == 'INSUFFICIENT' and
                                  row['gold'] != 'INSUFFICIENT'
                                  for row in values),
        'all_deferrals': sum(row['prediction'] == 'INSUFFICIENT' for row in values),
    }


def render():
    template = TEMPLATE.read_text(encoding='utf-8')
    if template.count(MARKER) != 1:
        raise ValueError('Tradeoff template marker changed')
    payload = json.dumps(data(), ensure_ascii=False,
                         separators=(',', ':')).replace('<', '\\u003c')
    return template.replace(MARKER, payload).encode('utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('build', 'verify'))
    args = parser.parse_args()
    expected = render()
    if args.command == 'build':
        OUTPUT.write_bytes(expected)
    elif OUTPUT.read_bytes() != expected:
        raise ValueError('Risk tradeoff page differs from frozen decisions/template')
    print(json.dumps({'status': args.command, 'original_inputs': 72,
                      'saved_methods': 3, 'derived_baselines': 2,
                      'new_model_forwards': 0,
                      'output': str(OUTPUT)}))


if __name__ == '__main__':
    main()
