"""Prepare target-switch scenes and visible-only queries; never run a model."""
import argparse
import csv
import hashlib
import io
import json
import random
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
FACT = HERE.parent / 'fact-execution'
sys.path.insert(0, str(FACT))
sys.path.insert(0, str(HERE.parent / 'evidence-gap'))
from gap_data import direct_truth, parse_text, policy_for, sentence, world_truth
from gap_run import spec, tokenizer_for
from interface import compile_visible, instruction
from joint_route import labels, prompt as joint_prompt
from joint_route_plan import DIRECT_ORDERS
from line_evidence import visible_lines

FAMILIES = ('joint_approval', 'reversal_exception', 'route_lookup')
SEED = 'request-ownership-v0.1-20260930'
ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZ'
SOURCE_PATHS = ('prepare.py', 'PROTOCOL.md', '../fact-execution/scope_gate.py',
                '../fact-execution/interface.py', '../fact-execution/joint_route.py',
                '../fact-execution/joint_route_plan.py',
                '../fact-execution/line_evidence.py', '../evidence-gap/gap_data.py',
                '../evidence-gap/gap_run.py', '../next-study/study.py')


def digest(data):
    return hashlib.sha256(data.replace(b'\r\n', b'\n')).hexdigest()


def packed(rows):
    return ''.join(json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n'
                   for row in rows).encode('utf-8')


def pretty(obj):
    return (json.dumps(obj, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def identifiers(family, index, near):
    rng = random.Random(f'{SEED}/{family}/{index}')
    first = ''.join(rng.choice(ALPHABET) for _ in range(5))
    if near:
        position = index % 5
        replacement = rng.choice(ALPHABET.replace(first[position], ''))
        second = first[:position] + replacement + first[position + 1:]
    else:
        second = ''.join(rng.choice(ALPHABET.replace(char, '')) for char in first)
    sites = ['site-' + ''.join(rng.choice(ALPHABET) for _ in range(5)) for _ in range(2)]
    if sites[0] == sites[1]:
        raise ValueError('Site-name collision')
    return ['request-' + first, 'request-' + second], sites


def observation_values(family, action, pattern):
    """Construction only: values supporting a desired program action."""
    positive = action == 'ALLOW'
    if family == 'joint_approval':
        if action == 'INSUFFICIENT':
            return {'review_a' if pattern else 'review_b': True}
        return {'review_a': True, 'review_b': positive} if pattern else {
            'review_a': positive, 'review_b': True}
    if family == 'reversal_exception':
        base = bool(pattern)
        if action == 'INSUFFICIENT':
            return {'base': base} if pattern else {'exception': base}
        return {'base': base, 'exception': base != positive}
    route = bool(pattern)
    if action == 'INSUFFICIENT':
        return {'site_a': bool(pattern), 'site_b': not bool(pattern)}
    return {'route': route, 'site_a': positive if not route else not positive,
            'site_b': positive if route else not positive}


def material():
    """New instances of the old declared grammar, not new policy families."""
    scenes, views = [], []
    for family in FAMILIES:
        for index in range(8):
            pair_kind = 'determined_determined' if index < 4 else 'determined_insufficient'
            near = index in (0, 3, 4, 7)
            ids, sites = identifiers(family, index, near)
            if index < 4:
                actions = ['ALLOW', 'DENY'] if index % 2 == 0 else ['DENY', 'ALLOW']
            else:
                actions = (['ALLOW', 'INSUFFICIENT'], ['DENY', 'INSUFFICIENT'],
                           ['INSUFFICIENT', 'ALLOW'], ['INSUFFICIENT', 'DENY'])[index - 4]
            parent = f'ownership-{family}-{index + 1:02d}'
            observation_pattern = (index // 2) % 2
            records = [{'scope': owner, 'field': field, 'value': value}
                       for slot, owner in enumerate(ids)
                       for field, value in observation_values(family, actions[slot], observation_pattern).items()]
            random.Random(parent + '/record-order').shuffle(records)
            # Balance which owner appears first without assigning a fixed field order.
            first_slot = (0, 1, 1, 0, 1, 0, 0, 1)[index]
            first = next(i for i, record in enumerate(records) if record['scope'] == ids[first_slot])
            records[0], records[first] = records[first], records[0]
            scene = {'parent': parent, 'family': family, 'pair_kind': pair_kind,
                     'id_relation': 'one_character_near' if near else 'all_characters_distant',
                     'ids': ids, 'sites': sites, 'records': records,
                     'construction_actions': actions, 'first_owner_slot': first_slot,
                     'observation_pattern': observation_pattern,
                     'independent_human_reviewed': False}
            policy = policy_for(scene)
            block = 'Evidence:\n' + '\n'.join(sentence(record, scene) for record in records)
            scenes.append(scene)
            for slot, target in enumerate(ids):
                state = f'Request: allow action for request {target}.\n' + block
                constructed = scene | {'target': target}
                gold, legal = world_truth(constructed)
                parsed = parse_text(state, policy, family, sites)
                if gold != actions[slot] or direct_truth(parsed) != gold or world_truth(parsed) != (gold, legal):
                    raise ValueError('Program construction / visible-parser disagreement')
                views.append({'view_id': parent + f'/target-{slot}', 'parent': parent,
                              'family': family, 'pair_kind': pair_kind,
                              'id_relation': scene['id_relation'], 'target_slot': slot,
                              'state': state, 'policy': policy, 'gold': gold,
                              'legal_worlds': legal,
                              'reference_provenance': 'program construction; zero independent human annotations'})
    if len({identifier for scene in scenes for identifier in scene['ids']}) != 48:
        raise ValueError('Request identifier collision')
    return scenes, views


def filtered_state(state):
    """Filter only displayed strings; no construction object or label is accepted."""
    from scope_gate import gate_line
    header = state.splitlines()[0]
    lines = visible_lines(state)
    gates = [gate_line(header, line['text']) for line in lines]
    retained = [line['text'] for line, gate in zip(lines, gates) if gate['status'] != 'DROP']
    if not retained:
        raise ValueError('This preparation requires at least one retained record')
    return header + '\nEvidence:\n' + '\n'.join(retained), gates


def visible_plans(state, policy):
    """The entire prompt API accepts visible text only, never gold or metadata."""
    schema = compile_visible(state, policy)
    header = state.splitlines()[0]
    lines = visible_lines(state)
    filtered, gates = filtered_state(state)
    if any(gate['status'] == 'UNKNOWN' for gate in gates):
        raise ValueError('Unknown ID grammar is outside this initial preparation')
    output = []
    for line in lines:
        order = labels(schema)
        output.append({'arm': 'joint_full', 'mapping': 0, 'line_index': line['line_index'],
                       'order': order, 'prompt': joint_prompt(header, line['text'], policy, schema, order)})
    for arm, supplied in (('direct_full', state), ('direct_filtered', filtered)):
        count = len(visible_lines(supplied))
        if not 1 <= count <= len(DIRECT_ORDERS):
            raise ValueError('Unsupported direct call budget')
        for mapping, order in enumerate(DIRECT_ORDERS[:count]):
            options = '\n'.join(f'{letter}. {spec.OPTIONS[label]}'
                                for letter, label in zip('ABC', order))
            output.append({'arm': arm, 'mapping': mapping, 'line_index': None,
                           'order': list(order), 'prompt': supplied + '\n\n' +
                           instruction(schema, policy, 'direct') + '\n' + options + '\nAnswer:'})
    return output


def plans(views):
    output = []
    for view in views:
        for row in visible_plans(view['state'], view['policy']):
            suffix = row['line_index'] if row['arm'] == 'joint_full' else row['mapping']
            output.append({'query_id': f"{view['view_id']}/{row['arm']}/{suffix}",
                           'view_id': view['view_id'], 'parent': view['parent'],
                           'representation': 'new_scene_original_declared_grammar'} | row)
    if len({row['query_id'] for row in output}) != len(output):
        raise ValueError('Duplicate planned query')
    return output


def summary(scenes, views, queries):
    counts = Counter(row['arm'] for row in queries)
    expected = {'joint_full': 200, 'direct_full': 200, 'direct_filtered': 100}
    if dict(counts) != expected:
        raise ValueError(f'Unexpected grid: {dict(counts)}')
    return {'status': 'design_preparation_not_execution_freeze', 'parent_scenes': len(scenes),
            'target_switched_views': len(views), 'planned_queries': len(queries),
            'planned_queries_by_arm': dict(counts),
            'single_direct_anchor_queries_per_arm': len(views),
            'single_direct_anchors_are_subsets': True,
            'labels': dict(Counter(view['gold'] for view in views)),
            'pair_kinds': dict(Counter(scene['pair_kind'] for scene in scenes)),
            'id_relations': dict(Counter(scene['id_relation'] for scene in scenes)),
            'crossed_construction_checks': [
                {'family': family, 'pair_kind': kind, 'id_relation': relation,
                 'parents': len(group),
                 'first_owner_actions': dict(Counter(s['construction_actions'][s['first_owner_slot']] for s in group)),
                 'observation_patterns': dict(Counter(str(s['observation_pattern']) for s in group))}
                for family in FAMILIES
                for kind in ('determined_determined', 'determined_insufficient')
                for relation in ('one_character_near', 'all_characters_distant')
                for group in [[s for s in scenes if s['family'] == family
                               and s['pair_kind'] == kind and s['id_relation'] == relation]]],
            'planned_model': 'historical pinned Kev-LoRA N1 native causal logits',
            'actual_model_forwards': 0, 'independent_human_annotations': 0,
            'original_development_views_scored': 0, 'reserved_views_scored': 0,
            'paid_api_calls': 0, 'new_training': False,
            'execution_ready': False,
            'limit': ('New scene instances reuse inspected policy and language grammar. '
                      'No model results, natural-language transfer or independent confirmation.')}


def artifacts():
    scenes, views = material()
    queries = plans(views)
    data = {'data/scenes.jsonl': packed(scenes), 'data/views.jsonl': packed(views),
            'preparation/queries.jsonl': packed(queries)}
    packet = [{'view_id': v['view_id'], 'state': v['state'], 'policy': v['policy']} for v in views]
    data['review/visible_packet.json'] = pretty(packet)
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator='\n')
    writer.writerow(['view_id', 'action_ALLOW_DENY_INSUFFICIENT', 'evidence_or_reason',
                     'ambiguous_yes_no', 'reviewer', 'reviewed_at'])
    writer.writerows([[view['view_id'], '', '', '', '', ''] for view in views])
    data['review/blank.csv'] = buf.getvalue().encode('utf-8')
    manifest = summary(scenes, views, queries) | {
        'source_sha256_lf': {path: digest((HERE / path).read_bytes()) for path in SOURCE_PATHS},
        'artifact_sha256_lf': {path: digest(content) for path, content in data.items()},
        'review_blinding': 'Packet omits construction labels; public source and parent identities remain visible.'}
    data['preparation/manifest.json'] = pretty(manifest)
    return data, manifest


def encoded_artifacts(tokenizer=None):
    _, views = material()
    queries = plans(views)
    if tokenizer is None:
        rows = [json.loads(line) for line in (HERE / 'preparation/encoded_queries.jsonl').read_text(encoding='utf-8').splitlines()]
        if len(rows) != len(queries):
            raise ValueError('Encoded preparation count drift')
        for row, plan in zip(rows, queries):
            if (row['query_id'] != plan['query_id'] or row['prompt_sha256_lf'] != digest(plan['prompt'].encode())
                    or row['input_tokens'] != len(row['token_ids'])
                    or len(row['candidate_ids']) != len(plan['order'])
                    or not row['token_ids'] or any(type(token) is not int or token < 0 for token in row['token_ids'])):
                raise ValueError('Stored encoding differs from current prompt plan')
    else:
        candidates = {letter: tokenizer.encode(' ' + letter, add_special_tokens=False) for letter in 'ABCDEFGH'}
        if any(len(ids) != 1 for ids in candidates.values()) or len({ids[0] for ids in candidates.values()}) != 8:
            raise ValueError('Answer candidates are not distinct single tokens')
        rows = []
        for plan in queries:
            ids = tokenizer.encode(plan['prompt'], add_special_tokens=False)
            letters = 'ABCDEFGH'[:len(plan['order'])]
            for letter in letters:
                if tokenizer.encode(plan['prompt'] + ' ' + letter, add_special_tokens=False) != ids + candidates[letter]:
                    raise ValueError('Answer token boundary drift')
            rows.append({'query_id': plan['query_id'], 'prompt_sha256_lf': digest(plan['prompt'].encode()),
                         'input_tokens': len(ids), 'token_ids': ids,
                         'candidate_ids': [candidates[letter][0] for letter in letters]})
    counts = Counter()
    anchors = Counter()
    for plan, row in zip(queries, rows):
        counts[plan['arm']] += row['input_tokens']
        if plan['arm'].startswith('direct_') and plan['mapping'] == 0:
            anchors[plan['arm']] += row['input_tokens']
    encoded = packed(rows)
    manifest = {'status': 'tokenizer_only_design_preparation_not_execution_freeze',
                'tokenizer_model': spec.BASE, 'tokenizer_revision': spec.BASE_REV,
                'planned_queries': len(rows), 'planned_input_tokens': sum(counts.values()),
                'input_tokens_by_arm': dict(counts), 'single_anchor_input_tokens': dict(anchors),
                'max_input_tokens': max(row['input_tokens'] for row in rows),
                'queries_sha256_lf': digest(packed(queries)),
                'encoded_sha256_lf': digest(encoded), 'actual_model_forwards': 0,
                'execution_ready': False,
                'verification_limit': 'Offline verify checks stored encodings, lengths and hashes; verify-tokenizer independently re-encodes using the cached pinned tokenizer.'}
    return {'preparation/encoded_queries.jsonl': encoded,
            'preparation/token_manifest.json': pretty(manifest)}, manifest


def check_or_write(data, write):
    for name, content in data.items():
        path = HERE / name
        if write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        elif path.read_bytes().replace(b'\r\n', b'\n') != content:
            raise ValueError(f'Preparation artifact drift: {name}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('build', 'verify', 'encode', 'verify-tokenizer'))
    parser.add_argument('--cache', default='G:/jev-lab/hf-cache')
    args = parser.parse_args()
    data, manifest = artifacts()
    check_or_write(data, args.command == 'build')
    if args.command in ('encode', 'verify-tokenizer'):
        encoded, token_manifest = encoded_artifacts(tokenizer_for(args.cache))
        check_or_write(encoded, args.command == 'encode')
        manifest = token_manifest
    elif args.command == 'verify' and (HERE / 'preparation/encoded_queries.jsonl').exists():
        encoded, _ = encoded_artifacts()
        check_or_write(encoded, False)
    print(json.dumps({key: value for key, value in manifest.items()
                      if key not in ('source_sha256_lf', 'artifact_sha256_lf')}, indent=2))


if __name__ == '__main__':
    main()
