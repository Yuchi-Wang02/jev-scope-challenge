"""Read-only structural audit of the pinned official ShARC archive; no model calls."""
import argparse
import hashlib
import io
import json
import statistics
import urllib.request
import zipfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
SUMMARY = HERE / 'sharc_source_summary.json'
URL = 'https://sharc-data.github.io/data/sharc1-official.zip'
ARCHIVE_SHA256 = '72dca3f4f3ba73b1d796b40e952a80d53cd2011ef90b2168b8bcaa818f5edd1e'
REQUIRED = {'utterance_id', 'tree_id', 'source_url', 'snippet', 'question',
            'scenario', 'history', 'answer', 'evidence'}
FIXED_ANSWERS = ('Yes', 'No', 'Irrelevant')


def describe(rows):
    if (not isinstance(rows, list) or not rows or
            any(not isinstance(row, dict) or not REQUIRED <= set(row)
                for row in rows)):
        raise ValueError('Unexpected ShARC row structure')
    utterances = [str(row['utterance_id']) for row in rows]
    if len(set(utterances)) != len(utterances):
        raise ValueError('Duplicate ShARC utterance ID within a split')
    answers = Counter(str(row['answer']) for row in rows)
    trees = Counter(str(row['tree_id']) for row in rows)
    lengths = [len(str(row['snippet']).split()) for row in rows]
    return {
        'rows': len(rows), 'unique_tree_ids': len(trees),
        'trees_with_multiple_rows': sum(count > 1 for count in trees.values()),
        'fixed_answers': {answer: answers[answer] for answer in FIXED_ANSWERS},
        'other_answer_rows': len(rows) - sum(answers[a] for a in FIXED_ANSWERS),
        'nonempty_history_rows': sum(bool(row['history']) for row in rows),
        'empty_scenario_rows': sum(not str(row['scenario']).strip() for row in rows),
        'median_snippet_words': statistics.median(lengths),
        'max_snippet_words': max(lengths)}


def audit():
    with urllib.request.urlopen(URL, timeout=30) as response:
        payload = response.read()
    digest = hashlib.sha256(payload).hexdigest()
    if digest != ARCHIVE_SHA256:
        raise ValueError('Official ShARC archive changed; inspect before updating the pin')
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        rows = {split: json.loads(archive.read(
            f'sharc1-official/json/sharc_{split}.json').decode('utf-8'))
            for split in ('train', 'dev')}
        has_license_file = any('licen' in name.lower() for name in archive.namelist()
                               if not name.startswith('__MACOSX/'))
    tree_overlap = len({str(r['tree_id']) for r in rows['train']} &
                       {str(r['tree_id']) for r in rows['dev']})
    if tree_overlap:
        raise ValueError('Train/development rule-question tree overlap')
    return {
        'status': 'source_structure_only_no_model_inference',
        'official_archive_url': URL, 'archive_sha256': digest,
        'archive_bytes': len(payload), 'train': describe(rows['train']),
        'dev': describe(rows['dev']), 'train_dev_tree_id_overlap': tree_overlap,
        'license_file_in_archive': has_license_file,
        'test_labels_parsed_by_this_script': False, 'model_forwards': 0,
        'independent_human_annotations_by_this_project': 0,
        'interpretation_limit': ('Public external data, not a pristine held-out test. '
                                 'Nonstandard answers require an explicit follow-up-action '
                                 'mapping and review; answer text quality is not scored here.')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('build', 'verify'))
    args = parser.parse_args()
    result = audit()
    encoded = (json.dumps(result, indent=2, ensure_ascii=False) + '\n').encode('utf-8')
    if args.command == 'verify':
        if SUMMARY.read_bytes().replace(b'\r\n', b'\n') != encoded:
            raise ValueError('Pinned ShARC structural summary drift')
    elif SUMMARY.exists() and SUMMARY.read_bytes().replace(b'\r\n', b'\n') != encoded:
        raise ValueError('Preserve previously published ShARC structural summary')
    elif not SUMMARY.exists():
        SUMMARY.write_bytes(encoded)
    print(json.dumps({'status': 'verified' if args.command == 'verify' else 'built',
                      'archive_sha256': result['archive_sha256'],
                      'train_trees': result['train']['unique_tree_ids'],
                      'dev_trees': result['dev']['unique_tree_ids'],
                      'model_forwards': 0}))


if __name__ == '__main__':
    main()
