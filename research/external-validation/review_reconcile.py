"""Prepare private, source-label-hidden adjudication after two full ShARC reviews."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path

from prepare_sharc_review import (
    CSV_FIELDS, ROOT, STUDY, digest, item_id, pair_id,
    prepare_with_selection, readable, validate_review_rows, verify_manifest,
)

ADJUDICATION_FIELDS = (
    'pair_id', 'item_1_id', 'item_2_id', 'final_action_1',
    'final_action_2', 'pair_validity', 'reason', 'adjudicator', 'date',
)


def load_review(path):
    payload = path.read_bytes()
    with io.StringIO(payload.decode('utf-8-sig'), newline='') as source:
        reader = csv.DictReader(source)
        if tuple(reader.fieldnames or ()) != CSV_FIELDS:
            raise ValueError('Unexpected reviewer CSV columns')
        rows = list(reader)
    return rows, hashlib.sha256(payload).hexdigest()


def reconciliation(pack, selected, rows_a, rows_b):
    statuses = [validate_review_rows(CSV_FIELDS, rows, pack)
                for rows in (rows_a, rows_b)]
    if any(status['pending'] for status in statuses):
        raise ValueError('Both reviewer exports must cover all 60 items')
    declared_ids = [{row['reviewer'].strip() for row in rows}
                    for rows in (rows_a, rows_b)]
    if any(len(names) != 1 for names in declared_ids) or (
            next(iter(declared_ids[0])) == next(iter(declared_ids[1]))):
        raise ValueError('Two distinct, consistent declared reviewer IDs are required')
    reviewers = [next(iter(names)) for names in declared_ids]
    by_id = {item['item_id']: item for item in pack['items']}
    a_by_id = {row['item_id']: row for row in rows_a}
    b_by_id = {row['item_id']: row for row in rows_b}
    agreed = sum(a_by_id[ident]['action'].strip() ==
                 b_by_id[ident]['action'].strip() for ident in by_id)
    pairs = []
    for candidate in selected:
        members = []
        for row in candidate['rows']:
            ident = item_id(row)
            visible = by_id[ident]
            members.append({
                **visible,
                'review_a': {'action': a_by_id[ident]['action'].strip(),
                             'reason': a_by_id[ident]['reason'].strip()},
                'review_b': {'action': b_by_id[ident]['action'].strip(),
                             'reason': b_by_id[ident]['reason'].strip()},
            })
        pairs.append({'pair_id': pair_id(candidate), 'items': members})
    if (len(pairs) != len(selected) or
            len({pair['pair_id'] for pair in pairs}) != len(selected)):
        raise ValueError('Adjudication pairing drift')
    pairs.sort(key=lambda pair: digest([STUDY, 'adjudication-order',
                                         pair['pair_id']]))
    return {
        'status': 'needs_human_adjudication_not_model_ground_truth',
        'study': STUDY,
        'declared_reviewers': reviewers,
        'declared_identity_distinct': True,
        'actual_human_independence_verified': False,
        'semantic_correctness_verified': False,
        'model_inference_open': False,
        'individual_items': len(by_id),
        'item_level_agreement': agreed,
        'item_level_disagreement': len(by_id) - agreed,
        'pairs': pairs,
    }


def blank_adjudication_csv(report):
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=ADJUDICATION_FIELDS,
                            lineterminator='\n')
    writer.writeheader()
    for pair in report['pairs']:
        writer.writerow({
            'pair_id': pair['pair_id'],
            'item_1_id': pair['items'][0]['item_id'],
            'item_2_id': pair['items'][1]['item_id'],
        })
    return output.getvalue().encode('utf-8')


def private_directory(directory):
    local_path = ROOT / '.local'
    if local_path.is_symlink():
        raise ValueError('Private export root may not be a symlink')
    local = local_path.resolve()
    directory = directory.resolve()
    if directory != local and local not in directory.parents:
        raise ValueError('Adjudication material may only be written inside .local')
    return directory


def preserve_outputs(directory, report, csv_bytes):
    directory = private_directory(directory)
    targets = (directory / 'adjudication_queue.json',
               directory / 'adjudication_blank.csv')
    payloads = (readable(report), csv_bytes)
    if all(path.exists() for path in targets):
        if any(path.read_bytes() != payload for path, payload in zip(targets, payloads)):
            raise ValueError('Existing private adjudication output differs; preserve it')
        return targets, 'verified_existing'
    if any(path.exists() for path in targets):
        raise FileExistsError('Partial adjudication output exists; preserve it')
    directory.mkdir(parents=True, exist_ok=True)
    for path, payload in zip(targets, payloads):
        with path.open('xb') as output:
            output.write(payload)
    return targets, 'created'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review-a', type=Path, required=True)
    parser.add_argument('--review-b', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path,
                        default=ROOT / '.local' / STUDY)
    args = parser.parse_args()
    if args.review_a.resolve() == args.review_b.resolve():
        parser.error('The two reviewer exports must be separate files')
    manifest, pack_bytes, _, selected = prepare_with_selection()
    verify_manifest(manifest)
    rows_a, hash_a = load_review(args.review_a)
    rows_b, hash_b = load_review(args.review_b)
    report = reconciliation(json.loads(pack_bytes), selected, rows_a, rows_b)
    report['selection_sha256'] = manifest['selection_sha256']
    report['review_a_sha256'] = hash_a
    report['review_b_sha256'] = hash_b
    targets, output_status = preserve_outputs(
        args.output_dir, report, blank_adjudication_csv(report))
    print(json.dumps({
        'status': output_status,
        'items': report['individual_items'],
        'pairs': len(report['pairs']),
        'item_agreement': report['item_level_agreement'],
        'item_disagreement': report['item_level_disagreement'],
        'actual_human_independence_verified': False,
        'semantic_correctness_verified': False,
        'model_inference_open': False,
        'private_outputs': [str(path) for path in targets],
    }))


if __name__ == '__main__':
    main()
