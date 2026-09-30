"""Audit exact one-history-answer contrasts in pinned ShARC train data."""
import argparse
import hashlib
import io
import itertools
import json
import urllib.request
import zipfile
from collections import Counter, defaultdict

from inspect_sharc import ARCHIVE_SHA256, HERE, URL, REQUIRED

SUMMARY = HERE / 'sharc_pair_summary.json'
FIXED_ANSWERS = {'Yes', 'No', 'Irrelevant'}


def action(row):
    answer = str(row['answer']).strip()
    if not answer:
        raise ValueError('Empty ShARC answer')
    return answer if answer in FIXED_ANSWERS else 'ASK'


def history(row):
    if not isinstance(row['history'], list) or any(
            not isinstance(turn, dict) or
            not {'follow_up_question', 'follow_up_answer'} <= set(turn)
            for turn in row['history']):
        raise ValueError('Unexpected ShARC history structure')
    return tuple((str(turn['follow_up_question']), str(turn['follow_up_answer']))
                 for turn in row['history'])


def visible_key(row):
    return (str(row['tree_id']), str(row['snippet']), str(row['question']),
            str(row['scenario']), history(row))


def one_answer_difference(left, right):
    if visible_key(left)[:4] != visible_key(right)[:4]:
        return None
    left_h, right_h = history(left), history(right)
    if (len(left_h) != len(right_h) or
            [question for question, _ in left_h] !=
            [question for question, _ in right_h]):
        return None
    differences = [(a, b) for (_, a), (_, b) in zip(left_h, right_h)
                   if a != b]
    if len(differences) != 1 or set(differences[0]) != {'No', 'Yes'}:
        return None
    return ('No', 'Yes')


def dedupe_visible(rows):
    by_visible = defaultdict(list)
    for row in rows:
        by_visible[visible_key(row)].append(row)
    ambiguous = [group for group in by_visible.values()
                 if len({action(row) for row in group}) > 1]
    kept = [min(group, key=lambda row: str(row['utterance_id']))
            for group in by_visible.values()
            if len({action(row) for row in group}) == 1]
    return by_visible, ambiguous, kept


def iter_one_answer_pairs(kept):
    by_context = defaultdict(list)
    for row in kept:
        by_context[visible_key(row)[:4]].append(row)
    for group in by_context.values():
        for left, right in itertools.combinations(group, 2):
            if one_answer_difference(left, right) is not None:
                yield left, right


def summarize(rows):
    if len(rows) != 21890 or any(not isinstance(row, dict) or
                                 not REQUIRED <= set(row) for row in rows):
        raise ValueError('Unexpected pinned ShARC train grid')
    questions_by_tree = defaultdict(set)
    snippets_by_tree = defaultdict(set)
    for row in rows:
        questions_by_tree[str(row['tree_id'])].add(str(row['question']))
        snippets_by_tree[str(row['tree_id'])].add(str(row['snippet']))
    by_visible, ambiguous, kept = dedupe_visible(rows)
    duplicates = sum(len(group) > 1 for group in by_visible.values())
    transitions, changed_answers, trees = Counter(), Counter(), set()
    pairs = 0
    for left, right in iter_one_answer_pairs(kept):
        pairs += 1
        changed_answers[('No', 'Yes')] += 1
        labels = tuple(sorted((action(left), action(right))))
        transitions[labels] += 1
        if labels[0] != labels[1]:
            trees.add(str(left['tree_id']))
    if changed_answers != {('No', 'Yes'): pairs}:
        raise ValueError('One-answer contrasts are not all Yes/No changes')
    changed = sum(n for (a, b), n in transitions.items() if a != b)
    multiple_questions = sum(len(questions) > 1
                             for questions in questions_by_tree.values())
    question_variants = Counter(len(questions)
                                for questions in questions_by_tree.values())
    multiple_snippets = sum(len(snippets) > 1
                            for snippets in snippets_by_tree.values())
    if (len(by_visible) != 21850 or duplicates != 34 or len(ambiguous) != 1 or
            sum(map(len, ambiguous)) != 3 or len(kept) != 21849 or
            pairs != 3334 or changed != 3037 or len(trees) != 599 or
            multiple_questions != 628 or question_variants != {3: 628} or
            multiple_snippets != 0):
        raise ValueError('Pinned ShARC pair inventory drift')
    return {
        'status': 'train_only_visible_contrast_inventory_not_model_evaluation',
        'train_rows': len(rows), 'unique_visible_inputs': len(by_visible),
        'tree_ids_with_multiple_visible_questions': multiple_questions,
        'question_variants_per_tree_distribution': {
            str(n): count for n, count in sorted(question_variants.items())},
        'tree_ids_with_multiple_visible_snippets': multiple_snippets,
        'duplicated_visible_input_groups': duplicates,
        'ambiguous_action_groups_excluded': len(ambiguous),
        'ambiguous_rows_excluded': sum(map(len, ambiguous)),
        'one_representative_per_consistent_visible_input': len(kept),
        'exact_one_history_answer_pairs': pairs,
        'changed_history_answer_values': {'No/Yes': changed_answers[('No', 'Yes')]},
        'provisionally_changed_action_pairs': changed,
        'same_action_pairs': pairs - changed,
        'tree_ids_with_changed_action_pair': len(trees),
        'action_pair_counts': {a + '/' + b: n
                               for (a, b), n in sorted(transitions.items())},
        'pair_rule': ('Within identical tree_id, snippet, question and scenario, '
                      'the history questions and length match and exactly one '
                      'history answer changes from No to Yes. Duplicate visible '
                      'inputs collapse to the smallest utterance_id if actions '
                      'agree; conflicting-action groups are excluded.'),
        'action_mapping': ('Yes, No and Irrelevant stay literal; every other '
                           'answer is provisionally ASK. Human semantic review '
                           'and follow-up question quality scoring remain undone.'),
        'model_forwards': 0, 'independent_human_annotations_by_this_project': 0,
        'raw_third_party_rows_published_here': 0}


def load_train_rows():
    with urllib.request.urlopen(URL, timeout=30) as response:
        payload = response.read()
    if hashlib.sha256(payload).hexdigest() != ARCHIVE_SHA256:
        raise ValueError('Official ShARC archive changed; inspect before updating the pin')
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        rows = json.loads(archive.read(
            'sharc1-official/json/sharc_train.json').decode('utf-8'))
    return rows


def audit():
    return {'official_archive_sha256': ARCHIVE_SHA256,
            **summarize(load_train_rows())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('build', 'verify'))
    args = parser.parse_args()
    result = audit()
    payload = (json.dumps(result, indent=2, ensure_ascii=False) + '\n').encode('utf-8')
    if args.command == 'verify':
        if SUMMARY.read_bytes().replace(b'\r\n', b'\n') != payload:
            raise ValueError('Pinned ShARC pair inventory drift')
    elif SUMMARY.exists() and SUMMARY.read_bytes().replace(b'\r\n', b'\n') != payload:
        raise ValueError('Preserve previously published ShARC pair inventory')
    elif not SUMMARY.exists():
        SUMMARY.write_bytes(payload)
    print(json.dumps({'status': 'verified' if args.command == 'verify' else 'built',
                      'pairs': result['exact_one_history_answer_pairs'],
                      'changed_actions': result['provisionally_changed_action_pairs'],
                      'model_forwards': 0}))


if __name__ == '__main__':
    main()
