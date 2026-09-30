"""Validate private ShARC adjudication and apply frozen reserve order before inference."""
import argparse
import csv
import hashlib
import json
from datetime import date
from pathlib import Path

from prepare_sharc_review import (
    REVIEW_ACTIONS, ROOT, STRATA, STUDY, item_id, pair_id,
    prepare_with_selection, readable, verify_manifest,
)
from review_reconcile import (
    ADJUDICATION_FIELDS, blank_adjudication_csv, load_review,
    private_directory, reconciliation,
)

VALIDITY = {'VALID', 'INVALID'}


def validate_adjudication_rows(header, rows, queue):
    if tuple(header or ()) != ADJUDICATION_FIELDS:
        raise ValueError('Unexpected adjudication CSV columns')
    if any(set(row) != set(ADJUDICATION_FIELDS) or
           any(not isinstance(value, str) for value in row.values())
           for row in rows):
        raise ValueError('Malformed adjudication CSV row')
    expected = {pair['pair_id']: (pair['items'][0]['item_id'],
                                  pair['items'][1]['item_id'])
                for pair in queue['pairs']}
    observed = [row['pair_id'] for row in rows]
    if (len(observed) != len(expected) or len(set(observed)) != len(observed)
            or set(observed) != set(expected)):
        raise ValueError('Missing, repeated or foreign adjudication pair ID')
    adjudicators = set()
    cleaned = {}
    for row in rows:
        pair_ident = row['pair_id']
        if (row['item_1_id'], row['item_2_id']) != expected[pair_ident]:
            raise ValueError('Adjudication item IDs do not match the frozen pair')
        a, b = row['final_action_1'].strip(), row['final_action_2'].strip()
        validity, reason = row['pair_validity'].strip(), row['reason'].strip()
        adjudicator, when = row['adjudicator'].strip(), row['date'].strip()
        if (a not in REVIEW_ACTIONS or b not in REVIEW_ACTIONS or
                validity not in VALIDITY or not reason or not adjudicator):
            raise ValueError('Adjudication row is incomplete')
        if validity == 'VALID' and 'UNCLEAR' in (a, b):
            raise ValueError('A VALID pair cannot contain an UNCLEAR action')
        try:
            if date.fromisoformat(when).isoformat() != when:
                raise ValueError('Adjudication date must use YYYY-MM-DD')
        except ValueError as error:
            raise ValueError('Adjudication date must use YYYY-MM-DD') from error
        adjudicators.add(adjudicator)
        cleaned[pair_ident] = {
            'item_ids': list(expected[pair_ident]),
            'actions': [a, b],
            'validity': validity,
            'reason': reason,
            'adjudicator': adjudicator,
            'date': when,
        }
    if len(adjudicators) != 1:
        raise ValueError('Use one consistent declared adjudicator ID')
    return cleaned


def apply_frozen_reserves(selected, adjudicated):
    by_stratum = {stratum: {'primary': [], 'reserve': []}
                  for stratum in STRATA}
    for candidate in selected:
        ident = pair_id(candidate)
        if ident not in adjudicated:
            raise ValueError('Selected pair lacks adjudication')
        by_stratum[candidate['stratum']][candidate['role']].append(candidate)
    final = []
    replaced = []
    skipped_invalid_reserves = []
    for stratum in STRATA:
        primaries = by_stratum[stratum]['primary']
        reserves = iter(by_stratum[stratum]['reserve'])
        for primary in primaries:
            if adjudicated[pair_id(primary)]['validity'] == 'VALID':
                final.append(primary)
                continue
            replacement = None
            for reserve in reserves:
                if adjudicated[pair_id(reserve)]['validity'] == 'VALID':
                    replacement = reserve
                    break
                skipped_invalid_reserves.append(pair_id(reserve))
            if replacement is None:
                raise ValueError('Frozen reserves exhausted; version a new study')
            final.append(replacement)
            replaced.append({'primary': pair_id(primary),
                             'reserve': pair_id(replacement)})
    if (len(final) != sum(len(by_stratum[s]['primary']) for s in STRATA)
            or len({candidate['tree_id'] for candidate in final}) != len(final)):
        raise ValueError('Final reviewed tree selection drift')
    return final, replaced, skipped_invalid_reserves


def reviewed_manifest(selected, adjudicated, selection_digest,
                      review_hashes, adjudication_hash):
    final, replaced, skipped = apply_frozen_reserves(selected, adjudicated)
    items = []
    for candidate in final:
        ident = pair_id(candidate)
        entry = adjudicated[ident]
        items.append({
            'pair_id': ident,
            'item_ids': [item_id(row) for row in candidate['rows']],
            'adjudicated_actions': entry['actions'],
        })
    return {
        'status': 'private_adjudicated_development_labels_not_model_evaluation',
        'study': STUDY,
        'selection_sha256': selection_digest,
        'review_a_sha256': review_hashes[0],
        'review_b_sha256': review_hashes[1],
        'adjudication_csv_sha256': adjudication_hash,
        'declared_identity_checked_not_independence_proven': True,
        'semantic_correctness_automatically_verified': False,
        'model_inference_open': False,
        'final_pairs': len(items),
        'final_individual_items': len(items) * 2,
        'replacements': replaced,
        'skipped_invalid_reserves': skipped,
        'adjudicated_action_flips': sum(
            actions['adjudicated_actions'][0] != actions['adjudicated_actions'][1]
            for actions in items),
        'selected': items,
    }


def load_adjudication(path):
    payload = path.read_bytes()
    with path.open(encoding='utf-8-sig', newline='') as source:
        reader = csv.DictReader(source)
        rows = list(reader)
        header = reader.fieldnames
    return header, rows, hashlib.sha256(payload).hexdigest()


def preserve_final(directory, result):
    directory = private_directory(directory)
    target = directory / 'reviewed_selection.json'
    payload = readable(result)
    if target.exists():
        if target.read_bytes() != payload:
            raise ValueError('Existing reviewed selection differs; preserve it')
        return target, 'verified_existing'
    directory.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as output:
        output.write(payload)
    return target, 'created'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review-a', type=Path, required=True)
    parser.add_argument('--review-b', type=Path, required=True)
    parser.add_argument('--adjudication', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path,
                        default=ROOT / '.local' / STUDY)
    args = parser.parse_args()
    if len({args.review_a.resolve(), args.review_b.resolve(),
            args.adjudication.resolve()}) != 3:
        parser.error('Reviewer and adjudication exports must be separate files')
    directory = private_directory(args.output_dir)
    manifest, pack_bytes, _, selected = prepare_with_selection()
    verify_manifest(manifest)
    rows_a, hash_a = load_review(args.review_a)
    rows_b, hash_b = load_review(args.review_b)
    queue = reconciliation(json.loads(pack_bytes), selected, rows_a, rows_b)
    queue['selection_sha256'] = manifest['selection_sha256']
    queue['review_a_sha256'], queue['review_b_sha256'] = hash_a, hash_b
    if ((directory / 'adjudication_queue.json').read_bytes() != readable(queue) or
            (directory / 'adjudication_blank.csv').read_bytes() !=
            blank_adjudication_csv(queue)):
        raise ValueError('Adjudication inputs do not match saved blind reviews')
    header, rows, adjudication_hash = load_adjudication(args.adjudication)
    adjudicated = validate_adjudication_rows(header, rows, queue)
    result = reviewed_manifest(
        selected, adjudicated, manifest['selection_sha256'],
        (hash_a, hash_b), adjudication_hash)
    target, status = preserve_final(directory, result)
    print(json.dumps({
        'status': status,
        'final_pairs': result['final_pairs'],
        'adjudicated_action_flips': result['adjudicated_action_flips'],
        'reserve_replacements': len(result['replacements']),
        'model_inference_open': False,
        'private_output': str(target),
    }))


if __name__ == '__main__':
    main()
