"""Freeze a small ShARC train-only human-review queue without publishing source rows."""
import argparse
import csv
import hashlib
import io
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

from inspect_sharc import ARCHIVE_SHA256, HERE
from inspect_sharc_pairs import (
    action, dedupe_visible, iter_one_answer_pairs, load_train_rows, summarize,
)

ROOT = HERE.parents[1]
MANIFEST = HERE / 'sharc_review_manifest.json'
STUDY = 'sharc-train-contrast-review-v0.1'
STRATA = ('No/Yes', 'ASK/No', 'ASK/Yes')
PRIMARY_EACH = 8
RESERVE_EACH = 2
CSV_FIELDS = ('item_id', 'action', 'reason', 'reviewer', 'date')
REVIEW_ACTIONS = {'Yes', 'No', 'Irrelevant', 'ASK', 'UNCLEAR'}


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(',', ':')) + '\n').encode('utf-8')


def readable(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def identity(candidate):
    return [candidate['tree_id'], candidate['ids'][0],
            candidate['ids'][1], candidate['stratum']]


def pair_candidates(kept):
    candidates = defaultdict(list)
    for left, right in iter_one_answer_pairs(kept):
        labels = tuple(sorted((action(left), action(right))))
        if labels[0] == labels[1]:
            continue
        stratum = '/'.join(labels)
        if stratum not in STRATA:
            raise ValueError('Unexpected changed-action stratum')
        pair = sorted((left, right), key=lambda row: str(row['utterance_id']))
        if str(pair[0]['utterance_id']) == str(pair[1]['utterance_id']):
            raise ValueError('Repeated utterance ID in a contrast pair')
        candidate = {
            'tree_id': str(pair[0]['tree_id']),
            'ids': tuple(str(row['utterance_id']) for row in pair),
            'stratum': stratum,
            'rows': pair,
        }
        candidate['rank'] = digest([STUDY, 'rank', identity(candidate)])
        candidates[stratum].append(candidate)
    return candidates


def choose(candidates):
    ordered = {stratum: sorted(candidates[stratum],
                               key=lambda candidate: candidate['rank'])
               for stratum in STRATA}
    used_trees = set()
    selected = []
    for round_index in range(PRIMARY_EACH + RESERVE_EACH):
        for stratum in STRATA:
            candidate = next((item for item in ordered[stratum]
                              if item['tree_id'] not in used_trees), None)
            if candidate is None:
                raise ValueError('Too few independent tree groups for review')
            selected.append({**candidate,
                             'role': 'primary' if round_index < PRIMARY_EACH
                             else 'reserve'})
            used_trees.add(candidate['tree_id'])
    if len(selected) != 30 or len(used_trees) != 30:
        raise ValueError('Tree-cluster selection drift')
    return selected


def safe_history(row):
    return [{'follow_up_question': str(turn['follow_up_question']),
             'follow_up_answer': str(turn['follow_up_answer'])}
            for turn in row['history']]


def review_pack(selected):
    items = []
    for candidate in selected:
        for row in candidate['rows']:
            items.append({
                'item_id': digest([STUDY, 'item-id',
                                   str(row['tree_id']),
                                   str(row['utterance_id'])])[:24],
                'snippet': str(row['snippet']),
                'question': str(row['question']),
                'scenario': str(row['scenario']),
                'history': safe_history(row),
            })
    if len({item['item_id'] for item in items}) != len(items):
        raise ValueError('Opaque review ID collision')
    items.sort(key=lambda item: digest([STUDY, 'item-order', item['item_id']]))
    return {
        'status': 'blank_human_review_no_model_outputs',
        'study': STUDY,
        'instructions': ('Judge each item independently from its visible '
                         'snippet, question, scenario and history. Choose '
                         'Yes, No, Irrelevant, ASK or UNCLEAR and explain '
                         'your decision. Paired items and source answers '
                         'are hidden until after review is saved.'),
        'items': items,
    }


def blank_csv(pack):
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=CSV_FIELDS, lineterminator='\n')
    writer.writeheader()
    for item in pack['items']:
        writer.writerow({'item_id': item['item_id']})
    return output.getvalue().encode('utf-8')


def validate_review_rows(header, rows, pack):
    if tuple(header or ()) != CSV_FIELDS:
        raise ValueError('Unexpected review CSV columns')
    expected = {item['item_id'] for item in pack['items']}
    observed = [row['item_id'] for row in rows]
    if (len(observed) != len(expected) or len(set(observed)) != len(observed)
            or set(observed) != expected):
        raise ValueError('Review CSV has missing, repeated or foreign item IDs')
    completed = 0
    unclear = 0
    for row in rows:
        values = [row[field].strip() for field in CSV_FIELDS[1:]]
        if all(not value for value in values):
            continue
        answer, reason, reviewer, when = values
        if answer not in REVIEW_ACTIONS or not reason or not reviewer:
            raise ValueError('Review row is incomplete or has an invalid action')
        try:
            if date.fromisoformat(when).isoformat() != when:
                raise ValueError('Review date must use YYYY-MM-DD')
        except ValueError as error:
            raise ValueError('Review date must use YYYY-MM-DD') from error
        completed += 1
        unclear += answer == 'UNCLEAR'
    return {'completed': completed, 'pending': len(expected) - completed,
            'unclear': unclear, 'independence_verified': False,
            'semantic_correctness_verified': False}


def check_review_csv(path, pack):
    with path.open(encoding='utf-8-sig', newline='') as source:
        reader = csv.DictReader(source)
        return validate_review_rows(reader.fieldnames, list(reader), pack)


def prepare():
    rows = load_train_rows()
    summary = summarize(rows)
    _, _, kept = dedupe_visible(rows)
    candidates = pair_candidates(kept)
    if {key: len(value) for key, value in candidates.items()} != {
            'No/Yes': 1897, 'ASK/No': 553, 'ASK/Yes': 587}:
        raise ValueError('Pinned changed-action pool drift')
    selected = choose(candidates)
    pack = review_pack(selected)
    csv_bytes = blank_csv(pack)
    canonical_selection = [
        {'identity': identity(item), 'role': item['role']}
        for item in selected
    ]
    counts = {stratum: {'primary': PRIMARY_EACH, 'reserve': RESERVE_EACH}
              for stratum in STRATA}
    manifest = {
        'status': 'train_only_pre_human_review_no_model_inference',
        'study': STUDY,
        'official_archive_sha256': ARCHIVE_SHA256,
        'source_train_rows': summary['train_rows'],
        'source_one_answer_pairs': summary['exact_one_history_answer_pairs'],
        'selection_rule': ('Public train only; different provisional actions; '
                           '8 primary and 2 ordered reserves in each of '
                           'No/Yes, ASK/No, ASK/Yes. SHA-256 rank and '
                           'round-robin strata; no shared tree_id across '
                           'selected pairs. Reserves replace invalid items '
                           'only before inference, in frozen order.'),
        'provisional_strata': counts,
        'selected_pairs': len(selected),
        'blinded_individual_items': len(pack['items']),
        'unique_tree_ids': len({item['tree_id'] for item in selected}),
        'selection_sha256': digest(canonical_selection),
        'private_review_pack_sha256': hashlib.sha256(readable(pack)).hexdigest(),
        'private_blank_csv_sha256': hashlib.sha256(csv_bytes).hexdigest(),
        'independent_human_annotations': 0,
        'model_forwards': 0,
        'source_rows_committed': 0,
        'source_and_item_ids_committed': 0,
    }
    return manifest, readable(pack), csv_bytes


def verify_manifest(manifest):
    if MANIFEST.read_bytes().replace(b'\r\n', b'\n') != readable(manifest):
        raise ValueError('ShARC human-review selection drift')


def export_private(directory, pack_bytes, csv_bytes):
    directory = directory.resolve()
    local_path = ROOT / '.local'
    if local_path.is_symlink():
        raise ValueError('Private export root may not be a symlink')
    local = local_path.resolve()
    if directory != local and local not in directory.parents:
        raise ValueError('Private source text may only be exported inside .local')
    targets = (directory / 'review_items.json', directory / 'blank_review.csv')
    if any(path.exists() for path in targets):
        raise FileExistsError('Private review export exists; preserve it')
    directory.mkdir(parents=True, exist_ok=True)
    for path, payload in zip(targets, (pack_bytes, csv_bytes)):
        with path.open('xb') as output:
            output.write(payload)
    return targets


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('build', 'verify', 'export',
                                           'verify-export', 'check-review'))
    parser.add_argument('--output-dir', type=Path,
                        default=ROOT / '.local' / STUDY)
    parser.add_argument('--review-csv', type=Path)
    args = parser.parse_args()
    manifest, pack_bytes, csv_bytes = prepare()
    if args.command == 'build':
        if MANIFEST.exists():
            verify_manifest(manifest)
        else:
            MANIFEST.write_bytes(readable(manifest))
    else:
        verify_manifest(manifest)
    if args.command == 'export':
        targets = export_private(args.output_dir, pack_bytes, csv_bytes)
        exported = [str(path) for path in targets]
    elif args.command == 'verify-export':
        directory = args.output_dir.resolve()
        paths = (directory / 'review_items.json', directory / 'blank_review.csv')
        if [path.read_bytes() for path in paths] != [pack_bytes, csv_bytes]:
            raise ValueError('Private review export does not match frozen manifest')
        exported = [str(path) for path in paths]
    else:
        exported = []
    review_status = {}
    if args.command == 'check-review':
        if args.review_csv is None:
            parser.error('check-review requires --review-csv')
        review_status = check_review_csv(args.review_csv,
                                         json.loads(pack_bytes))
    print(json.dumps({
        'status': args.command,
        'selected_pairs': manifest['selected_pairs'],
        'blinded_individual_items': manifest['blinded_individual_items'],
        'unique_tree_ids': manifest['unique_tree_ids'],
        'human_annotations': 0,
        'model_forwards': 0,
        'private_exports': exported,
        **review_status,
    }))


if __name__ == '__main__':
    main()
