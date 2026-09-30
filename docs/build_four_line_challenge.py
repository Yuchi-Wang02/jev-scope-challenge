"""Build or verify a focused, offline replay of the frozen S01 case.

The page is an invitation to inspect saved evidence, not a new model run.
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core import grammar_reference  # noqa: E402 - root is added above

CASES = ROOT / 'data' / 'cases.jsonl'
DECISIONS = ROOT / 'results' / 'decisions.csv'
SUMMARY = ROOT / 'results' / 'summary.json'
TEMPLATE = ROOT / 'docs' / 'four_line_template.html'
OUTPUTS = (ROOT / 'docs' / 'four_line_challenge.html',
           ROOT / 'docs' / 'index.html')
MARKER = '__CHALLENGE_DATA__'
BACKENDS = ('jev', 'qwen')
ROUNDS = ('0', '1')
MAPPINGS = ('cancel_first', 'keep_first')
VARIANTS = ('A', 'B', 'C', 'D')


def challenge_data():
    cases = [json.loads(line) for line in CASES.read_text(encoding='utf-8').splitlines()
             if line.strip()]
    cases = sorted((case for case in cases if case['parent_id'] == 'S01'),
                   key=lambda case: case['variant'])
    if ([case['variant'] for case in cases] != list(VARIANTS) or
            {case['target'] for case in cases} != {'mobile plan'} or
            [case['gold'] for case in cases] != ['KEEP', 'CANCEL', 'KEEP', 'CANCEL']):
        raise ValueError('Frozen S01 case structure changed')
    multisets = {tuple(sorted(re.findall(r'[a-z]+', case['customer_message'].lower())))
                 for case in cases}
    if len(multisets) != 1:
        raise ValueError('S01 messages no longer have the same word multiset')
    visible = [{key: case[key] for key in ('id', 'variant', 'target',
                                          'customer_message', 'gold')}
               for case in cases]
    case_by_id = {case['id']: case for case in cases}
    records = {}
    with DECISIONS.open(newline='', encoding='utf-8') as source:
        for row in csv.DictReader(source):
            if row['case_id'] not in case_by_id:
                continue
            key = (row['backend'], row['replicate'], row['mapping'], row['case_id'])
            if key in records:
                raise ValueError('Duplicate S01 decision: ' + str(key))
            if (row['gold'] != case_by_id[row['case_id']]['gold'] or
                    row['prediction'] not in ('KEEP', 'CANCEL') or
                    row['ok'] != 'True' or
                    (row['prediction'] == row['gold']) != (row['correct'] == 'True')):
                raise ValueError('Invalid or mismatched S01 decision: ' + str(key))
            records[key] = row['prediction']
    expected = {(backend, round_, mapping, case['id'])
                for backend in BACKENDS for round_ in ROUNDS
                for mapping in MAPPINGS for case in cases}
    if set(records) != expected:
        raise ValueError('S01 decision matrix is incomplete or unexpected')
    counts = {backend: {round_: sum(
        records[(backend, round_, mapping, case['id'])] == case['gold']
        for mapping in MAPPINGS for case in cases)
        for round_ in ROUNDS} for backend in BACKENDS}
    if counts != {'jev': {'0': 8, '1': 8}, 'qwen': {'0': 6, '1': 6}}:
        raise ValueError('S01 headline counts changed')
    code_reference = [
        {'case_id': case['id'],
         'prediction': grammar_reference({'target': case['target'],
                                          'customer_message': case['customer_message']})}
        for case in cases]
    if any(row['prediction'] != case_by_id[row['case_id']]['gold']
           for row in code_reference):
        raise ValueError('Known-grammar code no longer solves S01')
    code_summary = json.loads(SUMMARY.read_text(encoding='utf-8'))[
        'references']['known_grammar']['rounds']['0']
    if code_summary['correct'] != 96 or code_summary['robust_pass'] != 12:
        raise ValueError('Published full-probe code reference changed')
    return {'cases': visible, 'records': [
        {'backend': backend, 'round': round_, 'mapping': mapping,
         'case_id': case['id'], 'prediction': records[(backend, round_, mapping, case['id'])]}
        for round_ in ROUNDS for mapping in MAPPINGS
        for backend in BACKENDS for case in cases],
        'counts': counts, 'code_reference': code_reference,
        'code_complete_cases': code_summary['robust_pass']}


def render():
    template = TEMPLATE.read_text(encoding='utf-8')
    if template.count(MARKER) != 1:
        raise ValueError('Challenge data placeholder changed')
    payload = json.dumps(challenge_data(), ensure_ascii=False,
                         separators=(',', ':')).replace('<', '\\u003c')
    return template.replace(MARKER, payload).encode('utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('build', 'verify'))
    args = parser.parse_args()
    result = render()
    if args.command == 'build':
        for output in OUTPUTS:
            output.write_bytes(result)
    elif any(output.read_bytes() != result for output in OUTPUTS):
        raise ValueError('Published challenge differs from frozen cases/results/template')
    print(json.dumps({'status': args.command, 'cases': 4,
                      'saved_model_decisions': 32,
                      'derived_code_decisions': 4, 'new_model_calls': 0,
                      'outputs': [str(output) for output in OUTPUTS]}))


if __name__ == '__main__':
    main()
