"""Offline author-submission and second-reviewer package checks; no label adoption."""
import argparse
import csv
import hashlib
import io
import json
import re
import zipfile
from collections import Counter
from study import ROOT, rows, read
from review_check import validate

SUBMISSION = ROOT / 'review/submissions/yuchi'
CSV = SUBMISSION / 'payment_review_yuchi_excel.csv'
HASH = 'fa33f9f4761af2e5b517657a3cbbf6378c5bb495d9ea29b20c6bb458b26ebfb2'
PACKAGE = ROOT / 'review/reviewer_B_package.zip'


def package_files():
    return {
        'README.md': ROOT / 'review/handoff/README.md',
        'cover_note.txt': ROOT / 'review/handoff/cover_note.txt',
        'inputs.jsonl': ROOT / 'review/inputs.jsonl',
        'reviewer_B.csv': ROOT / 'review/reviewer_B.csv',
        'review.html': ROOT / 'review/review.html',
    }


def package_bytes(path):
    return path.read_bytes().replace(b'\r\n', b'\n')


def build_package():
    with zipfile.ZipFile(PACKAGE, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, source in package_files().items():
            info = zipfile.ZipInfo(name, date_time=(2026, 9, 30, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, package_bytes(source))


def resolve(values, tokens):
    if not tokens:
        return values
    token, *rest = tokens
    found = []
    for obj in values:
        if token == '*':
            assert isinstance(obj, list)
            found.extend(obj)
        else:
            found.append(obj[int(token)] if isinstance(obj, list) else obj[token])
    return resolve(found, rest)


def verify():
    assert hashlib.sha256(CSV.read_bytes()).hexdigest() == HASH, 'Original CSV bytes changed'
    validation = validate(CSV)
    assert validation['complete'] == 96 and validation['remaining'] == 0
    receipt = read(SUBMISSION / 'receipt.json')
    assert receipt['original_sha256'] == HASH
    assert receipt['labels_automatically_adopted'] is False
    assert receipt['second_reviewer_received'] is False
    with CSV.open(encoding='utf-8-sig', newline='') as f:
        records = list(csv.DictReader(f))
    inputs = {x['review_id']: x['state'] for x in rows(ROOT / 'review/inputs.jsonl')}
    mapping = {x['review_id']: x for x in rows(ROOT / 'review/mapping.jsonl')}
    cases = {x['case_id']: x for x in rows(ROOT / 'data/cases.jsonl')}
    affected = []
    path_count = wildcard_count = 0
    for row in records:
        state = inputs[row['review_id']]
        case = cases[mapping[row['review_id']]['case_id']]
        assert row['target_order_id'] == case['target_id']
        assert row['destination_id'] == case['destination_id']
        assert row['label'] == case['reference']
        for raw in row['evidence_paths'].split(';'):
            path = re.sub(r'\s*\([^)]*\)\s*$', '', raw.strip())
            assert resolve([state], re.findall(r'[^.\[\]]+', path))
            path_count += 1
            wildcard_count += '*' in path
        visible_ids = {order['order_id'] for order in state['orders']}
        assert set(re.findall(r'#W\d+', row['notes'])) <= visible_ids
        if case['style'] == 'item_reference':
            affected.append(row['review_id'])
    assert Counter(r['label'] for r in records) == {'VALID_DESTINATION': 48, 'INVALID_DESTINATION': 48}
    assert all(r['ambiguous'] == 'no' for r in records)
    assert affected == receipt['affected_review_items'] and len(affected) == 48
    assert path_count == receipt['valid_evidence_paths'] == 552
    assert wildcard_count == receipt['wildcard_paths_included'] == 24
    responses = rows(ROOT / 'results/responses.jsonl')
    for view in ('full', 'related'):
        for order in (0, 1):
            for style in ('explicit', 'item_reference'):
                group = [r for r in responses if r['phase'] == 'primary'
                         and r['input_view'] == view and r['option_order'] == order
                         and cases[r['case_id']]['style'] == style]
                score = {'requests': len(group), 'matches_original_reference':
                         sum(r['prediction'] == cases[r['case_id']]['reference'] for r in group)}
                assert score == receipt['original_scores_by_style'][f'{view}_{order}_{style}']
                assert score == {'requests': 24, 'matches_original_reference': 24}
    with zipfile.ZipFile(PACKAGE) as z:
        assert set(z.namelist()) == set(package_files())
        assert len(z.namelist()) == 5 and z.testzip() is None
        for name, source in package_files().items():
            assert z.read(name) == package_bytes(source)
        blank = list(csv.DictReader(io.StringIO(z.read('reviewer_B.csv').decode('utf-8'))))
        assert len(blank) == 96
        assert all(not v for r in blank for k, v in r.items() if k != 'review_id')
        embedded = re.search(r'const items=(.*?);const el=', z.read('review.html').decode('utf-8')).group(1)
        assert json.loads(embedded) == rows(ROOT / 'review/inputs.jsonl')
    return {'status': 'passed', 'author_reviewers': 1, 'author_review_items': 96,
            'non_author_review_submissions': 0, 'adjudicated_reference_updates': 0,
            'scope_disputed_review_items': 48, 'scope_disputed_base_inputs': 24,
            'evidence_paths_resolved': path_count, 'second_reviewer_package_files': 5,
            'new_model_calls': 0,
            'scope': 'File consistency and saved-score checks, not semantic certification or proof of reviewer independence'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--build-package', action='store_true')
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if args.build_package:
        build_package()
    print(json.dumps(verify(), indent=2))
