"""Verify a real ownership run and derive paired results; never run inference.

Pure helpers support explicitly synthetic, in-memory unit tests. Only analyze()
validates persisted scientific evidence; helpers alone establish no model result.
"""
import argparse
import importlib.util
import json
import math
import posixpath
import random
import re
import subprocess
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXECUTION_SPEC = importlib.util.spec_from_file_location('ownership_execution_analyzer', HERE / 'execution.py')
execution = importlib.util.module_from_spec(EXECUTION_SPEC)
EXECUTION_SPEC.loader.exec_module(execution)
prepare = execution.load_preparation()
from gap_data import parse_text, world_truth
from interface import compile_visible, execute, status_for
from joint_route import OTHER_REQUEST, NO_OBSERVATION, aggregate
from line_evidence import visible_lines
from scope_gate import gate_line

ACTION_ORDER = ('ALLOW', 'DENY', 'INSUFFICIENT')
MODEL_METHODS = ('joint_full', 'joint_gated', 'direct_full', 'direct_filtered',
                 'single_full', 'single_filtered')
METHODS = MODEL_METHODS + ('known_grammar', 'always_defer')
EXPECTED_CALLS = {'joint_full': 200, 'direct_full': 200, 'direct_filtered': 100}
EXPECTED_TOKENS = {'joint_full': 85214, 'direct_full': 71050, 'direct_filtered': 32533}


def numeric(value):
    return type(value) in (int, float) and math.isfinite(value)


def probabilities(logits, width):
    if width not in (3, 6, 8) or len(logits) != width or any(not numeric(x) for x in logits):
        raise ValueError('Invalid candidate logits')
    values = [math.exp(value - max(logits)) for value in logits]
    return [value / sum(values) for value in values]


def direct_distribution(rows):
    if not rows:
        raise ValueError('Empty direct order ensemble')
    result = dict.fromkeys(ACTION_ORDER, 0.0)
    for row in rows:
        values = row['probabilities']
        if (len(row['order']) != 3 or set(row['order']) != set(ACTION_ORDER)
                or len(values) != 3 or any(not numeric(p) or not 0 <= p <= 1 for p in values)
                or not math.isclose(sum(values), 1, rel_tol=2e-5, abs_tol=1e-7)):
            raise ValueError('Invalid direct semantic distribution')
        for action, value in zip(row['order'], values):
            result[action] += value / len(rows)
    return result


def validate_raw(raw, expected, manifest, seed=20261007):
    """Reject missing/foreign/reordered scores before deriving any endpoint."""
    if (manifest.get('scientific_forwards') != 500 or manifest.get('planned_input_tokens') != 188797
            or len(raw) != 500 or len(expected) != 500
            or len({r['query_id'] for r in raw}) != 500
            or len({r['query_id'] for r in expected}) != 500
            or Counter(r['arm'] for r in expected) != EXPECTED_CALLS):
        raise ValueError('Incomplete or duplicated ownership query grid')
    shuffled = list(expected)
    random.Random(seed).shuffle(shuffled)
    for number, (record, planned) in enumerate(zip(raw, shuffled), 1):
        if any(record.get(key) != value for key, value in planned.items()):
            raise ValueError('Raw query differs from encoded execution plan')
        width = len(planned['order'])
        if (planned['arm'] == 'joint_full' and width not in (6, 8)) or (
                planned['arm'] != 'joint_full' and width != 3):
            raise ValueError('Wrong arm candidate width')
        probs = probabilities(record.get('logits', []), width)
        recorded = record.get('probabilities', [])
        if (record.get('config_hash') != manifest['config_hash']
                or type(record.get('forward_index')) is not int or record['forward_index'] != number
                or record.get('ok') is not True
                or record.get('split') != 'new_scene_development'
                or record.get('representation') != 'new_scene_original_declared_grammar'
                or len(recorded) != width or any(not numeric(p) or not 0 <= p <= 1 for p in recorded)
                or not math.isclose(sum(recorded), 1.0, rel_tol=0.0, abs_tol=2e-6)
                or any(not math.isclose(p, q, rel_tol=2e-5, abs_tol=1e-7) for p, q in zip(probs, recorded))
                or record.get('prediction') != planned['order'][max(range(width), key=record['logits'].__getitem__)]
                or record.get('input_tokens') != len(planned['token_ids'])
                or not numeric(record.get('latency_s')) or record['latency_s'] < 0
                or not numeric(record.get('candidate_mass')) or not 0 <= record['candidate_mass'] <= 1):
            raise ValueError('Invalid score, identity, latency or candidate mass')
    if sum(r['input_tokens'] for r in raw) != 188797:
        raise ValueError('Scientific input-token total drift')
    if {arm: sum(r['input_tokens'] for r in raw if r['arm'] == arm)
            for arm in EXPECTED_TOKENS} != EXPECTED_TOKENS:
        raise ValueError('Arm input-token total drift')


def costs(rows):
    return {'model_calls': len(rows), 'input_tokens': sum(row['input_tokens'] for row in rows),
            'summed_saved_forward_latency_s': sum(row['latency_s'] for row in rows)}


def predict_view(view_id, state, policy, raw_by_view):
    """Visible-only runtime derivation. No scene records or gold are accepted."""
    schema = compile_visible(state, policy)
    lines = visible_lines(state)
    rows = raw_by_view[view_id]
    joint = sorted((r for r in rows if r['arm'] == 'joint_full'), key=lambda r: r['line_index'])
    if [r['line_index'] for r in joint] != list(range(len(lines))):
        raise ValueError('Incomplete joint lines for view')
    header = state.splitlines()[0]
    gates = {line['line_index']: gate_line(header, line['text']) for line in lines}
    full_choices = {row['line_index']: row['prediction'] for row in joint}
    gated_choices = {index: OTHER_REQUEST if gates[index]['status'] == 'DROP' else choice
                     for index, choice in full_choices.items()}
    outputs = []
    retained = [row for row in joint if gates[row['line_index']]['status'] != 'DROP']
    for method, choices in (('joint_full', full_choices), ('joint_gated', gated_choices)):
        extracted = aggregate(state, schema, choices)
        outputs.append({'method': method, 'prediction': execute(schema, extracted['facts']),
                        'facts': extracted['facts'], 'model_selected_spans': extracted['model_selected_spans'],
                        'absence_certified': False, 'conditional_action_probabilities': None,
                        'cost_provenance': 'same_saved_joint_forwards_reused' if method == 'joint_gated'
                                           else 'saved_joint_forwards',
                        'projected_prefilter_calls': len(retained) if method == 'joint_gated' else None,
                        'projected_prefilter_input_tokens': sum(r['input_tokens'] for r in retained)
                                                          if method == 'joint_gated' else None,
                        **costs(joint)})
    for arm, anchor in (('direct_full', 'single_full'), ('direct_filtered', 'single_filtered')):
        direct = sorted((r for r in rows if r['arm'] == arm), key=lambda r: r['mapping'])
        wanted = len(lines) if arm == 'direct_full' else len(retained)
        if [row['mapping'] for row in direct] != list(range(wanted)):
            raise ValueError('Incomplete distinct direct orders')
        for method, used in ((arm, direct), (anchor, direct[:1])):
            distribution = direct_distribution(used)
            outputs.append({'method': method,
                            'prediction': max(ACTION_ORDER, key=lambda action: distribution[action]),
                            'facts': None, 'model_selected_spans': None, 'absence_certified': False,
                            'conditional_action_probabilities': distribution,
                            'cost_provenance': 'saved_direct_subset' if method == anchor else 'saved_direct_forwards',
                            'projected_prefilter_calls': None, 'projected_prefilter_input_tokens': None,
                            **costs(used)})
    # The known-grammar control parses displayed strings independently of construction labels.
    parsed = parse_text(state, policy, schema['policy_id'], schema['sites'])
    for method, prediction in (('known_grammar', world_truth(parsed)[0]), ('always_defer', 'INSUFFICIENT')):
        outputs.append({'method': method, 'prediction': prediction, 'facts': None,
                        'model_selected_spans': None, 'absence_certified': False,
                        'conditional_action_probabilities': None, 'cost_provenance': 'offline_control_cpu_unmeasured',
                        'model_calls': 0, 'input_tokens': 0, 'summed_saved_forward_latency_s': None,
                        'projected_prefilter_calls': None, 'projected_prefilter_input_tokens': None})
    return outputs, {'schema': schema, 'lines': lines, 'gates': gates,
                     'joint_full': full_choices, 'joint_gated': gated_choices}


def route_error(prediction, reference):
    if prediction == reference:
        return 'correct_route'
    if prediction in (OTHER_REQUEST, NO_OBSERVATION):
        return 'safe_nonselection' if reference == OTHER_REQUEST else 'missed_relevant'
    if reference == OTHER_REQUEST:
        return 'wrong_request'
    return 'wrong_field' if prediction.split(':')[0] != reference.split(':')[0] else 'wrong_polarity'


def score(rows):
    parents = sorted({row['parent'] for row in rows})
    if any(len([r for r in rows if r['parent'] == parent]) != 2 for parent in parents):
        raise ValueError('Scoring unit must retain both target-switched views')
    uncertain = [r for r in rows if r['gold'] == 'INSUFFICIENT']
    determined = [r for r in rows if r['gold'] != 'INSUFFICIENT']
    latencies = [r['summed_saved_forward_latency_s'] for r in rows]
    return {'views': len(rows), 'parent_pairs': len(parents),
            'complete_pairs_correct': sum(all(r['correct'] for r in rows if r['parent'] == parent)
                                          for parent in parents),
            'correct_decisions': sum(r['correct'] for r in rows),
            'uncertain_views': len(uncertain), 'determined_views': len(determined),
            'false_commitments': sum(r['prediction'] != 'INSUFFICIENT' for r in uncertain),
            'determined_correct': sum(r['correct'] for r in determined),
            'needless_deferrals': sum(r['prediction'] == 'INSUFFICIENT' for r in determined),
            'wrong_determined_actions': sum(not r['correct'] and r['prediction'] != 'INSUFFICIENT'
                                           for r in determined),
            'model_calls': sum(r['model_calls'] for r in rows),
            'input_tokens': sum(r['input_tokens'] for r in rows),
            'summed_saved_forward_latency_s': sum(latencies) if all(v is not None for v in latencies) else None}


def compare(candidate, baseline):
    left = {row['view_id']: row for row in candidate}
    right = {row['view_id']: row for row in baseline}
    if len(left) != len(candidate) or len(right) != len(baseline) or set(left) != set(right):
        raise ValueError('Unpaired comparison views')
    changes = []
    transitions = Counter()
    for view_id in sorted(left):
        new, old = left[view_id], right[view_id]
        if new['parent'] != old['parent'] or new['gold'] != old['gold']:
            raise ValueError('Paired comparison reference mismatch')
        transition = ('stayed_correct' if old['correct'] and new['correct'] else
                      'regression' if old['correct'] else 'correction' if new['correct'] else 'stayed_wrong')
        transitions[transition] += 1
        if old['prediction'] != new['prediction']:
            changes.append({'candidate': new['method'], 'baseline': old['method'],
                            'view_id': view_id, 'parent': new['parent'], 'family': new['family'],
                            'id_relation': new['id_relation'], 'gold': new['gold'],
                            'before': old['prediction'], 'after': new['prediction'], 'transition': transition})
    pairs = Counter()
    for parent in sorted({row['parent'] for row in candidate}):
        ids = [row['view_id'] for row in candidate if row['parent'] == parent]
        if len(ids) != 2:
            raise ValueError('Pair must have exactly two views')
        new = all(left[view_id]['correct'] for view_id in ids)
        old = all(right[view_id]['correct'] for view_id in ids)
        pairs['gain' if new and not old else 'loss' if old and not new else 'tie'] += 1
    return {'candidate': candidate[0]['method'], 'baseline': baseline[0]['method'],
            'parent_pairs': sum(pairs.values()),
            'complete_pair_gains': pairs['gain'], 'complete_pair_losses': pairs['loss'],
            'complete_pair_ties': pairs['tie'],
            'view_transitions': {key: transitions[key] for key in
                                 ('correction', 'regression', 'stayed_correct', 'stayed_wrong')},
            'changed_actions': len(changes)}, changes


def validate_pairs(scenes, views):
    """Keep the exact parent sampling unit intact before runtime derivation."""
    if (len(scenes) != 24 or len(views) != 48
            or len({scene['parent'] for scene in scenes}) != 24
            or len({view['view_id'] for view in views}) != 48
            or {scene['parent'] for scene in scenes} != {view['parent'] for view in views}
            or Counter(view['gold'] for view in views) != {'ALLOW': 18, 'DENY': 18, 'INSUFFICIENT': 12}):
        raise ValueError('Incomplete or duplicate ownership parent/view grid')
    for scene in scenes:
        pair = [view for view in views if view['parent'] == scene['parent']]
        if len(pair) != 2:
            raise ValueError('Every parent must retain exactly two views')
        left, right = pair
        targets = {compile_visible(view['state'], view['policy'])['target'] for view in pair}
        if (len(targets) != 2 or {view['target_slot'] for view in pair} != {0, 1}
                or left['gold'] == right['gold']
                or left['state'].partition('\n')[2] != right['state'].partition('\n')[2]
                or left['policy'] != right['policy']
                or any(view[key] != scene[key] for view in pair
                       for key in ('family', 'pair_kind', 'id_relation'))):
            raise ValueError('Invalid target-switch pair identity, evidence or action contrast')


def derive(raw, scenes, views):
    """Compute in memory; caller must validate real raw provenance separately."""
    validate_pairs(scenes, views)
    by_view = {}
    for row in raw:
        by_view.setdefault(row['view_id'], []).append(row)
    # Complete visible-only derivation before any construction record is used for grading.
    predicted = {view['view_id']: predict_view(view['view_id'], view['state'], view['policy'], by_view)
                 for view in views}
    by_parent = {scene['parent']: scene for scene in scenes}
    decisions, claims, audits, gate_rows = [], [], [], []
    for view in views:
        outputs, context = predicted[view['view_id']]
        schema, scene = context['schema'], by_parent[view['parent']]
        identity = {key: view[key] for key in ('view_id', 'parent', 'family', 'pair_kind', 'id_relation', 'target_slot')}
        references = {field['name']: status_for([record['value'] for record in scene['records']
                      if record['scope'] == schema['target'] and record['field'] == field['name']])
                      for field in schema['fields']}
        for output in outputs:
            decisions.append(identity | output | {'gold': view['gold'], 'correct': output['prediction'] == view['gold']})
            if output['facts'] is not None:
                for field, status in output['facts'].items():
                    claims.append(identity | {'method': output['method'], 'field': field, 'status': status,
                                  'reference_status': references[field], 'correct': status == references[field],
                                  'model_selected_spans': output['model_selected_spans'][field],
                                  'absence_certified': False,
                                  'reference_provenance': 'program construction; not independent human annotation'})
        if len(scene['records']) != len(context['lines']):
            raise ValueError('Construction line alignment drift')
        for line, record in zip(context['lines'], scene['records']):
            index = line['line_index']
            target = record['scope'] == schema['target']
            reference = (record['field'] + (':POSITIVE' if record['value'] else ':NEGATIVE')) if target else OTHER_REQUEST
            gate_rows.append(identity | {'line_index': index, **context['gates'][index],
                                        'reference_scope': 'target' if target else 'other'})
            for method in ('joint_full', 'joint_gated'):
                choice = context[method][index]
                audits.append(identity | {'method': method, 'line_index': index,
                              'evidence_span': {key: line[key] for key in ('start', 'end', 'text')},
                              'saved_model_route': context['joint_full'][index], 'applied_route': choice,
                              'gate': context['gates'][index], 'reference_scope': 'target' if target else 'other',
                              'construction_reference_route': reference, 'program_audit': route_error(choice, reference),
                              'reference_provenance': 'program construction; not independent human annotation'})
    grouped = {method: [row for row in decisions if row['method'] == method] for method in METHODS}
    methods = {method: score(rows) for method, rows in grouped.items()}
    if (len(views) != 48 or len(scenes) != 24 or Counter(v['gold'] for v in views) !=
            {'ALLOW': 18, 'DENY': 18, 'INSUFFICIENT': 12} or len(claims) != 224
            or len(audits) != 400 or len(gate_rows) != 200):
        raise ValueError('Ownership grading denominator drift')
    strata = {dimension: {value: {method: score([row for row in rows if row[dimension] == value])
                                  for method, rows in grouped.items()}
                          for value in sorted({view[dimension] for view in views})}
              for dimension in ('family', 'id_relation', 'pair_kind')}
    paired, changes = [], []
    for method in METHODS:
        for baseline in ('joint_full', 'direct_full'):
            if method != baseline:
                comparison, changed = compare(grouped[method], grouped[baseline])
                paired.append(comparison)
                changes.extend(changed)
    paired_strata = {
        dimension: {value: [compare([r for r in grouped[method] if r[dimension] == value],
                                   [r for r in grouped[baseline] if r[dimension] == value])[0]
                           for method in METHODS for baseline in ('joint_full', 'direct_full') if method != baseline]
                    for value in sorted({view[dimension] for view in views})}
        for dimension in ('family', 'id_relation', 'pair_kind')}
    pair_outcomes = []
    for method, rows in grouped.items():
        for parent in sorted(by_parent):
            pair = sorted((row for row in rows if row['parent'] == parent), key=lambda row: row['target_slot'])
            pair_outcomes.append({'method': method, 'parent': parent, 'family': pair[0]['family'],
                                  'pair_kind': pair[0]['pair_kind'], 'id_relation': pair[0]['id_relation'],
                                  'view_ids': [row['view_id'] for row in pair], 'gold': [row['gold'] for row in pair],
                                  'predictions': [row['prediction'] for row in pair],
                                  'correct_views': sum(row['correct'] for row in pair),
                                  'complete_pair_correct': all(row['correct'] for row in pair)})
    joint_stats = {}
    for method in ('joint_full', 'joint_gated'):
        method_claims = [row for row in claims if row['method'] == method]
        method_audits = [row for row in audits if row['method'] == method]
        joint_stats[method] = {
            'fields': len(method_claims), 'correct_fields': sum(row['correct'] for row in method_claims),
            'exact_fact_vectors': sum(all(row['correct'] for row in method_claims if row['view_id'] == view['view_id'])
                                      for view in views),
            'missing_as_reported_value': sum(row['reference_status'] == 'MISSING' and row['status'] in ('TRUE', 'FALSE')
                                              for row in method_claims),
            'route_errors': dict(Counter(row['program_audit'] for row in method_audits)),
            'scope': {scope: {'lines': sum(row['reference_scope'] == scope for row in method_audits),
                             'selected_as_target_field': sum(row['reference_scope'] == scope
                                                            and row['applied_route'] not in (OTHER_REQUEST, NO_OBSERVATION)
                                                            for row in method_audits),
                             'exact_route_correct': sum(row['reference_scope'] == scope and row['program_audit'] == 'correct_route'
                                                       for row in method_audits)} for scope in ('target', 'other')}}
    gate_counts = Counter(row['status'] for row in gate_rows)
    if gate_counts != {'KEEP': 100, 'DROP': 100}:
        raise ValueError('Prepared lexical gate scope drift')
    gate_audit = {'visible_lines': 200, **{key: gate_counts[key] for key in ('KEEP', 'DROP', 'UNKNOWN')},
                  'target_lines': sum(row['reference_scope'] == 'target' for row in gate_rows),
                  'foreign_lines': sum(row['reference_scope'] == 'other' for row in gate_rows),
                  'target_retained': sum(row['reference_scope'] == 'target' and row['status'] != 'DROP' for row in gate_rows),
                  'foreign_accepted': sum(row['reference_scope'] == 'other' and row['status'] != 'DROP' for row in gate_rows)}
    summary = {'status': 'in_memory_derivation_provenance_not_yet_validated', 'arm': 'N1',
               'parent_pairs': 24, 'views': 48, 'independent_human_annotations': 0,
               'reference_provenance': 'program construction, not independent human labels',
               'methods': methods, 'strata': strata, 'paired_comparisons': paired,
               'paired_comparisons_by_stratum': paired_strata,
               'joint_diagnostics': joint_stats, 'gate_audit': gate_audit,
               'scientific_forwards': len(raw), 'unique_scientific_input_tokens': sum(r['input_tokens'] for r in raw),
               'observed_costs_by_arm': {arm: costs([r for r in raw if r['arm'] == arm]) for arm in EXPECTED_CALLS},
               'joint_gated_cost': {'underlying_saved_forwards': methods['joint_gated']['model_calls'],
                                    'underlying_saved_input_tokens': methods['joint_gated']['input_tokens'],
                                    'projected_retained_forwards': sum(r['projected_prefilter_calls'] for r in grouped['joint_gated']),
                                    'projected_retained_input_tokens': sum(r['projected_prefilter_input_tokens'] for r in grouped['joint_gated']),
                                    'projected_latency_measured': False, 'gate_cpu_time_measured': False,
                                    'new_skipped_inference_run': False},
               'directional_diagnostic': {
                   'rule': 'joint_gated complete pairs > joint_full AND false commitments <= joint_full',
                   'complete_pair_gain': methods['joint_gated']['complete_pairs_correct'] - methods['joint_full']['complete_pairs_correct'],
                   'false_commitment_change': methods['joint_gated']['false_commitments'] - methods['joint_full']['false_commitments'],
                   'passed': methods['joint_gated']['complete_pairs_correct'] > methods['joint_full']['complete_pairs_correct']
                             and methods['joint_gated']['false_commitments'] <= methods['joint_full']['false_commitments'],
                   'confirmation': False},
               'interpretation_limit': ('Constructed paired scenes reuse inspected language/policy grammar. '
                                       'No independent human review or natural-language transfer. Derived method costs '
                                       'share raw forwards and must not be summed as experiment size. '
                                       'Calls and input tokens differ; no equal total compute or calibrated probabilities. '
                                       'Stored full-vocabulary candidate mass is range-checked but cannot be '
                                       'reconstructed from the saved candidate-only logits.')}
    return {'summary': summary, 'decisions': decisions, 'fact_claims': claims, 'line_audits': audits,
            'pair_outcomes': pair_outcomes, 'case_changes': changes}


def analyze():
    """Only this path validates actual persisted evidence before publication."""
    manifest = execution.verify_frozen()
    runtime = json.loads((execution.OUT / 'runtime.json').read_text(encoding='utf-8'))
    required = {'status': 'complete', 'config_hash': manifest['config_hash'],
                'scientific_forwards': 500, 'warmup_forwards': 2, 'sdpa_kernel': 'math_only',
                'attempted_scientific_forwards': 500, 'attempted_warmup_forwards': 2,
                'backbone_dtype': 'bfloat16', 'adapter_exact_tensors': 504,
                'rewrite_model_records': 0, 'reserved_model_records': 0,
                'original_development_model_records': 0,
                'paid_api_calls': 0, 'jev_api_calls': 0, 'new_training': False}
    if any(runtime.get(key) != value for key, value in required.items()):
        raise ValueError('Incomplete or changed ownership runtime')
    if runtime.get('new_training') is not False:
        raise ValueError('Training flag drift')
    if (any(not numeric(runtime.get(key)) or runtime[key] < 0
            for key in ('elapsed_s', 'peak_allocated_mib'))
            or any(not isinstance(runtime.get(key), str) or not runtime[key].strip()
                   for key in ('python', 'gpu', 'cuda'))
            or not isinstance(runtime.get('packages'), dict)
            or any(not isinstance(runtime['packages'].get(key), str) or not runtime['packages'][key].strip()
                   for key in ('torch', 'transformers', 'peft', 'huggingface-hub', 'numpy'))):
        raise ValueError('Incomplete or invalid measured runtime metadata')
    commit = runtime.get('execution_commit', '')
    if not re.fullmatch('[0-9a-f]{40}', commit):
        raise ValueError('Invalid execution commit')
    for path, expected_hash in manifest['source_file_sha256_lf'].items():
        target = posixpath.normpath('research/request-ownership/' + path)
        if not target.startswith('research/') and not target.startswith('tests/'):
            raise ValueError('Foreign execution-source path')
        content = subprocess.check_output(['git', 'show', commit + ':' + target], cwd=HERE)
        if execution.sha(content) != expected_hash:
            raise ValueError(f'Execution source differs from freeze: {target}')
    expected_weights = json.loads((HERE.parent / 'next-study/results/weight_checksums.json').read_text(encoding='utf-8'))
    weights = json.loads((execution.OUT / 'weight_checksums.json').read_text(encoding='utf-8'))
    adapter = json.loads((execution.OUT / 'adapter_audit.json').read_text(encoding='utf-8'))
    if weights != expected_weights or adapter != {'status': 'passed', 'exact_tensors': 504, 'parameters': 33030144}:
        raise ValueError('Pinned cached weights or loaded adapter audit drift')
    raw = [json.loads(line) for line in (execution.OUT / 'N1.jsonl').read_text(encoding='utf-8').splitlines()]
    expected = execution.source_plans()
    validate_raw(raw, expected, manifest, execution.SEED)
    scenes, views = prepare.material()
    result = derive(raw, scenes, views)
    result['summary'].update(status='verified_completed_run_constructed_pairs', config_hash=manifest['config_hash'],
                             execution_commit=commit, warmup_forwards=2, rewrite_model_records=0,
                             reserved_model_records=0, original_development_model_records=0,
                             attempted_scientific_forwards=500, attempted_warmup_forwards=2,
                             paid_api_calls=0, jev_api_calls=0, new_training=False)
    return result


def serialized(result):
    return {name + ('.json' if name == 'summary' else '.jsonl'):
            prepare.pretty(value) if name == 'summary' else prepare.packed(value)
            for name, value in result.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    result = analyze()
    data = serialized(result)
    if not args.verify and any((execution.OUT / name).exists() for name in data):
        raise ValueError('Preserve existing ownership derived results')
    for name, content in data.items():
        path = execution.OUT / name
        if args.verify:
            if path.read_bytes().replace(b'\r\n', b'\n') != content:
                raise ValueError(f'Ownership derived-result drift: {name}')
        else:
            path.write_bytes(content)
    print(json.dumps({'status': 'passed', 'read_only': args.verify, 'scientific_forwards': 500,
                      'complete_pairs_joint': result['summary']['methods']['joint_full']['complete_pairs_correct'],
                      'complete_pairs_gated': result['summary']['methods']['joint_gated']['complete_pairs_correct'],
                      'directional_diagnostic_passed': result['summary']['directional_diagnostic']['passed']}))


if __name__ == '__main__':
    main()
