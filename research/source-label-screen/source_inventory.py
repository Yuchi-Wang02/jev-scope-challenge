"""Inventory a separate public-source diagnostic; no predictions or selected grid."""
import hashlib
import io
import json
import sys
import urllib.request
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'research/external-validation'))
from inspect_sharc import URL, ARCHIVE_SHA256
from inspect_sharc_pairs import action, dedupe_visible, iter_one_answer_pairs


def normalized(text):
    return ' '.join(text.casefold().split())


def load_source():
    with urllib.request.urlopen(URL, timeout=30) as response:
        payload = response.read()
    if hashlib.sha256(payload).hexdigest() != ARCHIVE_SHA256:
        raise ValueError('Pinned official source changed')
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        splits = {split: json.loads(archive.read('sharc1-official/json/sharc_' + split + '.json'))
                  for split in ('train', 'dev')}
    return splits['train'], splits['dev']


def eligible_rows(train, dev):
    train_trees = {r['tree_id'] for r in train}
    train_snippets = {normalized(r['snippet']) for r in train}
    excluded = {r['tree_id'] for r in dev if r['tree_id'] in train_trees or
                normalized(r['snippet']) in train_snippets}
    return [r for r in dev if r['tree_id'] not in excluded]


def inventory(train, dev):
    train_trees = {r['tree_id'] for r in train}
    train_snippets = {normalized(r['snippet']) for r in train}
    overlaps = {r['tree_id'] for r in dev if normalized(r['snippet']) in train_snippets}
    eligible = eligible_rows(train, dev)
    _, ambiguous, kept = dedupe_visible(eligible)
    counts, trees = Counter(), defaultdict(set)
    for left, right in iter_one_answer_pairs(kept):
        kind = '/'.join(sorted((action(left), action(right))))
        counts[kind] += 1
        trees[kind].add(left['tree_id'])
    return {
        'status': 'source_feasibility_only_no_model_calls_or_selected_grid',
        'archive_sha256': ARCHIVE_SHA256,
        'train_trees': len(train_trees), 'dev_trees': len({r['tree_id'] for r in dev}),
        'tree_id_overlap': len(train_trees & {r['tree_id'] for r in dev}),
        'dev_trees_with_exact_normalized_snippet_overlap_with_train': len(overlaps),
        'eligible_dev_trees_after_excluding_entire_overlapping_trees': len({r['tree_id'] for r in eligible}),
        'eligible_dev_rows': len(eligible),
        'conflicting_visible_action_groups_excluded': len(ambiguous),
        'pair_counts_by_source_action': dict(sorted(counts.items())),
        'tree_counts_by_source_action': {k: len(v) for k, v in sorted(trees.items())},
        'source_labels_independently_verified': False,
        'semantic_or_near_duplicate_overlap_checked': False,
        'new_model_calls': 0, 'public_test_parsed': False,
    }


if __name__ == '__main__':
    print(json.dumps(inventory(*load_source()), indent=2))
