"""Build/verify a small, unscored human-review starter from the frozen rewrite pack."""
import argparse
import csv
import hashlib
import io
import json

from review_pair_tools import FIELDS, HERE, fingerprint, inspect_csv

SELECTED = {f'{family}-1-{variant}' for family in
            ('joint_approval', 'reversal_exception', 'route_lookup')
            for variant in ('decisive_missing', 'conflict')}
OUTPUTS = ('starter_blind_pairs.json', 'starter_blank.csv', 'starter_manifest.json')


def build():
    pairs = json.loads((HERE / 'review/blind_pairs.json').read_text(encoding='utf-8'))
    mapping = [json.loads(line) for line in
               (HERE / 'review/candidate_rewrites.jsonl').read_text(encoding='utf-8').splitlines()]
    by_id = {row['review_id']: row for row in mapping}
    if len(by_id) != len(pairs) or len(pairs) != 144:
        raise ValueError('Frozen review pack changed')
    visible = ('review_id', 'original_state', 'candidate_state', 'policy')
    if any(row != {key: by_id[row['review_id']][key] for key in visible} for row in pairs):
        raise ValueError('Blind/source pack mismatch')
    selected = [row for row in pairs if by_id[row['review_id']]['source_id'] in SELECTED]
    counts = {source: sum(by_id[row['review_id']]['source_id'] == source for row in selected)
              for source in SELECTED}
    if len(selected) != 12 or any(count != 2 for count in counts.values()):
        raise ValueError('Expected two rewrite styles for six selected originals')
    if any(set(row) != {'review_id', 'original_state', 'candidate_state', 'policy'}
           for row in selected):
        raise ValueError('Blind pack has unexpected fields')
    blind = json.dumps(selected, indent=2, ensure_ascii=False) + '\n'
    out = io.StringIO()
    writer = csv.writer(out, lineterminator='\n')
    writer.writerow(FIELDS)
    for row in selected:
        writer.writerow([row['review_id']] + [''] * (len(FIELDS) - 1))
    csv_text = out.getvalue()
    checked = inspect_csv(csv_text, fingerprint())
    if checked['submitted_rows'] != 0 or checked['rewrite_inference_open']:
        raise ValueError('Starter must remain unannotated and unscored')
    manifest = {'status': 'human_review_starter_only',
                'selection': 'first development parent in each of three families; decisive_missing and conflict; both rewrite styles',
                'source_pack_sha256_lf': fingerprint(),
                'starter_blind_sha256_lf': hashlib.sha256(blind.encode('utf-8')).hexdigest(),
                'pairs': len(selected), 'original_cases': len(SELECTED),
                'independent_human_annotations': 0, 'model_scored_rewrites': 0,
                'statistical_sample': False,
                'note': 'Selection is procedural and parent-clustered; it is not a confirmation sample or semantic validation.'}
    return dict(zip(OUTPUTS, (blind, csv_text,
                              json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    outputs = build()
    for name, contents in outputs.items():
        path = HERE / 'review' / name
        if args.verify:
            if path.read_bytes().replace(b'\r\n', b'\n') != contents.encode('utf-8'):
                raise ValueError(f'Starter drift: {name}')
        else:
            path.write_text(contents, encoding='utf-8', newline='\n')
    print(json.dumps({'status': 'verified' if args.verify else 'written',
                      'pairs': 12, 'independent_human_annotations': 0,
                      'model_scored_rewrites': 0}))
