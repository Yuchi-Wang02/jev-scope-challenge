"""New synthetic interface development fixtures. No research corpus import."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SEEDS = [17, 43]
FORMAT = 'Return only a JSON object with exactly one key "answer" whose value is the chosen letter A, B, or C. Put this JSON in your final answer.'


def fixtures():
    return [
        {'id': 'copy', 'task': 'Copy the symbol field as the answer letter.', 'data': {'symbol': 'C'}, 'options': None},
        {'id': 'threshold', 'task': 'Eligible means age is at least 18. Choose A for eligible, B for ineligible, C for missing age.', 'data': {'age': 17}, 'options': None},
        {'id': 'missing', 'task': 'Eligible means age is at least 18. Choose A for eligible, B for ineligible, C for missing age. A null age is missing.', 'data': {'age': None}, 'options': None},
        {'id': 'sum', 'task': 'Choose the sum of the numbers.', 'data': [14, 9], 'options': {'A': 23, 'B': 21, 'C': 25}},
        {'id': 'intersection', 'task': 'Choose the list of names occurring in both lists.', 'data': [['birch', 'cedar'], ['cedar', 'elm']], 'options': {'A': ['birch'], 'B': ['cedar'], 'C': []}},
        {'id': 'latest', 'task': 'The event with the greatest integer sequence number gives the current status. Choose that status.', 'data': [{'seq': 2, 'status': 'denied'}, {'seq': 1, 'status': 'granted'}], 'options': {'A': 'denied', 'B': 'granted', 'C': 'unknown'}},
        {'id': 'conjunction', 'task': 'A means both switches are true. B means at least one is false. C means a switch is missing.', 'data': {'left': True, 'right': False}, 'options': None},
        {'id': 'minimum', 'task': 'Choose the smallest number in the data.', 'data': [9, 3, 7], 'options': {'A': 3, 'B': 7, 'C': 9}},
        {'id': 'lookup', 'task': 'Choose the color of record R038. Use the exact ID.', 'data': [{'id': f'R{i:03}', 'color': ['green', 'amber', 'blue'][i % 3]} for i in range(96)], 'options': {'A': 'green', 'B': 'amber', 'C': 'blue'}},
        {'id': 'count', 'task': 'Choose the number of occurrences of red.', 'data': ['red', 'blue', 'red', 'green', 'red', 'red'], 'options': {'A': 2, 'B': 3, 'C': 4}},
        {'id': 'alphabetical', 'task': 'Choose the alphabetically first word.', 'data': ['fox', 'ant', 'dog'], 'options': {'A': 'ant', 'B': 'dog', 'C': 'fox'}},
        {'id': 'nested', 'task': 'Use only current.choice as the chosen letter; outer.answer is a different field.', 'data': {'outer': {'answer': 'C'}, 'current': {'choice': 'B'}}, 'options': None},
    ]


def reference(f):
    d = f['data']; kind = f['id']
    if kind == 'copy': return d['symbol']
    if kind in ('threshold', 'missing'): return 'C' if d['age'] is None else ('A' if d['age'] >= 18 else 'B')
    if kind == 'conjunction': return 'C' if None in d.values() else ('A' if all(d.values()) else 'B')
    if kind == 'nested': return d['current']['choice']
    values = {'sum': lambda: sum(d), 'intersection': lambda: sorted(set(d[0]) & set(d[1])),
              'latest': lambda: max(d, key=lambda x: x['seq'])['status'],
              'minimum': lambda: min(d), 'lookup': lambda: next(r['color'] for r in d if r['id'] == 'R038'),
              'count': lambda: d.count('red'), 'alphabetical': lambda: min(d)}
    value = values[kind]()
    matches = [k for k, v in f['options'].items() if v == value]
    assert len(matches) == 1
    return matches[0]


def material():
    cases = []
    for f in fixtures():
        prompt = f['task']+'\nData: '+json.dumps(f['data'], ensure_ascii=False, separators=(',', ':'))
        if f['options'] is not None:
            prompt += '\nOptions: '+json.dumps(f['options'], separators=(',', ':'))
        prompt += '\n'+FORMAT
        cases.append({**f, 'prompt': prompt, 'reference': reference(f)})
    plan = [{'id': f'{mode}-{c["id"]}-{seed}', 'case_id': c['id'], 'thinking': mode == 'thinking',
             'seed': seed, 'max_new_tokens': 2048 if mode == 'thinking' else 256}
            for mode in ['direct', 'thinking'] for c in cases for seed in SEEDS]
    assert len(cases) == 12 and len(plan) == 48
    assert [sum(c['reference'] == letter for c in cases) for letter in 'ABC'] == [4, 4, 4]
    return {'purpose': 'synthetic interface development only', 'human_reviews': 0,
            'cases': cases, 'calls': plan, 'max_generated_tokens': sum(p['max_new_tokens'] for p in plan),
            'inference_deadline_seconds': 1800, 'max_total_input_tokens': 200000}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == '__main__':
    p = ROOT/'plan.json'
    text = json.dumps(material(), indent=2, ensure_ascii=False)+'\n'
    if p.exists():
        assert p.read_text(encoding='utf-8') == text, 'Existing plan differs; do not overwrite'
    else:
        p.write_text(text, encoding='utf-8', newline='\n')
    print(json.dumps({'cases': 12, 'calls': 48, 'max_generated_tokens': 55296, 'plan_sha256': digest(p)}))
