"""Inspect pinned EXtrA released pairs; no model or upstream code execution."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import urllib.request

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REVISION = '71dfc330a22983ca869b665845c4bb5c5a08d43e'
BASE = f'https://raw.githubusercontent.com/jeromeramos70/extra-sharc/{REVISION}/data/'
PINS = {
    'original_samples.json': ('69d4f3f690c4e75bd362a775af5cc94e969981df1c6684ad92833cd669dbb91e', 108130),
    'counterfactual_samples.json': ('7782f58e6bae542f337485c8babb389ee14cb6bc6b51fe558c420f4c72227f56', 108435),
}
VISIBLE = ('snippet', 'question', 'scenario', 'history')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def action(text):
    if not isinstance(text, str) or not text.strip():
        raise ValueError('Missing source answer')
    return text if text in ('Yes', 'No', 'Irrelevant') else 'ASK'


def indexed(rows):
    out = {}
    for row in rows:
        ident = row['utterance_id']
        if ident in out:
            raise ValueError('Duplicate utterance ID')
        if any(k not in row for k in (*VISIBLE, 'tree_id', 'answer', 'evidence')):
            raise ValueError('Missing required field')
        out[ident] = row
    return out


def inspect(original, counterfactual, prior_trees=(), prior_items=()):
    left, right = indexed(original), indexed(counterfactual)
    if left.keys() != right.keys():
        raise ValueError('Unmatched pair IDs')
    pairs = []; groups = defaultdict(list)
    for ident in sorted(left):
        a, b = left[ident], right[ident]
        if a['tree_id'] != b['tree_id']:
            raise ValueError('Tree changed within pair')
        changed = sorted(k for k in set(a) | set(b) if (k in a) != (k in b) or a.get(k) != b.get(k))
        visible_changed = [k for k in VISIBLE if a[k] != b[k]]
        hashes = [digest(encoded({k: x[k] for k in VISIBLE})) for x in (a, b)]
        labels = [action(x['answer']) for x in (a, b)]
        pairs.append({'utterance_id': ident, 'tree_id': a['tree_id'], 'changed_fields': changed,
            'visible_changed_fields': visible_changed, 'visible_sha256': hashes,
            'source_actions': labels, 'source_answer_text_changed': a['answer'] != b['answer'],
            'semantic_action_changed': labels[0] != labels[1],
            'unchanged_visible_conflicting_action': not visible_changed and labels[0] != labels[1]})
        for side, h, label in zip(('original', 'counterfactual'), hashes, labels):
            groups[h].append({'utterance_id': ident, 'side': side, 'source_action': label})
    conflicts = [{'visible_sha256': h, 'records': records} for h, records in sorted(groups.items())
                 if len({r['source_action'] for r in records}) > 1]
    # A fixed deterministic function can select only one label for identical input.
    maximum = sum(max(Counter(r['source_action'] for r in records).values()) for records in groups.values())
    trees = {p['tree_id'] for p in pairs}
    return {'pairs': len(pairs), 'records': 2 * len(pairs), 'tree_units': len(trees),
        'visible_fields': list(VISIBLE), 'comparison': 'exact parsed JSON values; no text normalization',
        'changed_field_counts': dict(sorted(Counter(k for p in pairs for k in p['changed_fields']).items())),
        'visible_change_patterns': dict(sorted(Counter('+'.join(p['visible_changed_fields']) or 'none' for p in pairs).items())),
        'semantic_transitions': dict(sorted(Counter(' -> '.join(p['source_actions']) for p in pairs).items())),
        'changed_semantic_actions': sum(p['semantic_action_changed'] for p in pairs),
        'unchanged_full_records': sum(not p['changed_fields'] for p in pairs),
        'unchanged_visible_conflicts': sum(p['unchanged_visible_conflicting_action'] for p in pairs),
        'distinct_visible_inputs': len(groups), 'conflicting_visible_groups': conflicts,
        'deterministic_source_agreement_ceiling': {'numerator': maximum, 'denominator': 2 * len(pairs),
            'scope': 'fixed deterministic action from exactly the four visible fields, on all records'},
        'overlap_with_previous_public_screen': {'tree_ids': sorted(trees & set(prior_trees)),
                                                'utterance_ids': sorted(set(left) & set(prior_items))},
        'pair_records': pairs, 'model_calls': 0, 'new_human_labels': 0,
        'source_labels_adjudicated': False, 'upstream_code_executed': False}


def files(directory, fetch=False):
    data = []
    for name, (expected, size) in PINS.items():
        path = directory / name
        if fetch and not path.exists():
            with urllib.request.urlopen(BASE + name, timeout=30) as response:
                raw = response.read(size + 1)
            if len(raw) != size or digest(raw) != expected:
                raise ValueError('Upstream download differs from pin')
            directory.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        raw = path.read_bytes()
        if len(raw) != size or digest(raw) != expected:
            raise ValueError('Local source differs from pin')
        data.append(json.loads(raw))
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('fetch', 'build', 'verify'))
    parser.add_argument('--source-dir', type=Path, required=True)
    args = parser.parse_args()
    a, b = files(args.source_dir, fetch=args.command == 'fetch')
    selected_path = ROOT / 'research/source-label-screen/selection.json'
    selected = json.loads(selected_path.read_bytes())['selected']
    result = inspect(a, b, [p['tree_id'] for p in selected],
                     [r['utterance_id'] for p in selected for r in p['rows']])
    result['source'] = {'repository': 'jeromeramos70/extra-sharc', 'revision': REVISION,
        'files': {k: {'sha256': v[0], 'bytes': v[1], 'url': BASE + k} for k, v in PINS.items()},
        'prior_selection_lf_sha256': digest(selected_path.read_bytes().replace(b'\r\n', b'\n'))}
    output = HERE / 'extra_release_audit.json'
    raw = (json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    if args.command == 'build':
        output.write_bytes(raw)
    elif args.command == 'verify' and output.read_bytes().replace(b'\r\n', b'\n') != raw:
        raise ValueError('Audit report differs from pinned source files')
    print(json.dumps({k: result[k] for k in ('pairs', 'tree_units', 'unchanged_visible_conflicts', 'model_calls')}))


if __name__ == '__main__':
    main()
