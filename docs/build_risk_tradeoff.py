"""Build or verify a local-loss explainer from frozen N1 development decisions."""
import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FACT = ROOT / 'research' / 'fact-execution'
sys.path.insert(0, str(FACT))
from paired_parent_audit import audit, digest, indexed, rows, selected  # noqa: E402

OLD = FACT / 'results' / 'decisions.jsonl'
LINE = FACT / 'line_results' / 'v0.1' / 'decisions.jsonl'
OLD_SUMMARY = FACT / 'results' / 'summary.json'
LINE_SUMMARY = FACT / 'line_results' / 'v0.1' / 'summary.json'
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


def data():
    # Reuse the parent-paired audit's independent source/summary integrity gates.
    audit()
    previous = rows(OLD)
    methods = {
        'direct': selected(previous, 'direct_0'),
        'facts': selected(previous, 'facts_0'),
        'line': indexed(rows(LINE)),
    }
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
                 old_summary['methods']['N1'][name + '_0']['all'])
        mapping = {
            'correct': 'correct_decisions' if name == 'line' else 'correct',
            'false_commitments': 'false_commitments',
            'wrong_supported_actions': 'wrong_supported_actions',
            'needless_deferrals': 'false_insufficient',
            'calls': 'model_calls',
            'input_tokens': 'input_tokens',
        }
        if any(totals[key] != saved[field] for key, field in mapping.items()):
            raise ValueError(f'{name} outcomes differ from saved summary')
        if not math.isclose(totals['forward_seconds'],
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
        result[name] = {**totals, 'parents': by_parent}
    if ({name: (r['wrong_actions'], r['needless_deferrals'])
         for name, r in result.items()} != {
             'direct': (36, 5), 'facts': (20, 8), 'line': (6, 37)}):
        raise ValueError('Expected cost-curve endpoints drifted')
    return {
        'status': 'post_hoc_original_development_only',
        'methods': result,
        'input_count': 72,
        'parent_count': 12,
        'wrong_action_definition': ('Non-INSUFFICIENT prediction that differs '
                                    'from the program-derived gold action'),
        'needless_deferral_definition': ('INSUFFICIENT prediction when the '
                                         'program-derived gold is determined'),
        'source_sha256_lf': {'whole_state_decisions': digest(OLD),
                             'line_decisions': digest(LINE)},
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
                      'saved_methods': 3, 'new_model_forwards': 0,
                      'output': str(OUTPUT)}))


if __name__ == '__main__':
    main()
