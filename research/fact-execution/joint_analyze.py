"""Recompute joint-route and both direct controls from saved raw N1 forwards."""
import argparse
import json
import math
import posixpath
import random
import re
import subprocess
from collections import Counter

from data_tools import HERE, original_cases
from fact_run import read_rows
from gap_analyze import equal
from interface import compile_visible, execute
from joint_execution import ENCODED, OUT, SEED, plan_id, sha, verify_frozen
from joint_route import OTHER_REQUEST, NO_OBSERVATION, aggregate
from joint_token_control import SELECTED
from line_analyze import probabilities
from line_evidence import visible_lines

ACTION_ORDER = ('ALLOW', 'DENY', 'INSUFFICIENT')


def direct_distribution(rows):
    """Mean conditional candidate probabilities aligned by semantic action."""
    if not rows:
        raise ValueError('Empty direct ensemble')
    mean = {action: 0.0 for action in ACTION_ORDER}
    for row in rows:
        if set(row['order']) != set(ACTION_ORDER) or len(row['probabilities']) != 3:
            raise ValueError('Invalid direct candidate mapping')
        for label, value in zip(row['order'], row['probabilities']):
            if (not isinstance(value, (float, int)) or not math.isfinite(value) or
                    not 0 <= value <= 1):
                raise ValueError('Nonfinite direct candidate probability')
            mean[label] += value / len(rows)
    if not math.isclose(sum(mean.values()), 1.0, rel_tol=1e-5, abs_tol=1e-5):
        raise ValueError('Direct conditional probabilities do not sum to one')
    return mean


def direct_choice(rows):
    probs = direct_distribution(rows)
    return max(ACTION_ORDER, key=lambda label: probs[label])


def validate_raw(raw, encoded, manifest):
    expected = list(encoded)
    random.Random(SEED).shuffle(expected)
    if len(raw) != 514 or len(expected) != 514:
        raise ValueError('Incomplete joint/direct scientific grid')
    for number, (record, planned) in enumerate(zip(raw, expected), 1):
        for key, value in planned.items():
            if record.get(key) != value:
                raise ValueError(f'Raw record differs from frozen query: {key}')
        if (record.get('config_hash') != manifest['config_hash'] or
                record.get('forward_index') != number or
                record.get('ok') is not True or
                record.get('split') != 'development' or
                record.get('representation') != 'original' or
                record.get('query_id') != plan_id(planned)):
            raise ValueError('Raw record identity or scope drift')
        p = (probabilities(record['logits']) if planned['arm'] == 'direct' else
             conditional_probabilities(record['logits'], len(planned['order'])))
        if (len(record.get('probabilities', [])) != len(planned['order']) or
                any(not math.isclose(a, b, rel_tol=2e-5, abs_tol=1e-7)
                    for a, b in zip(p, record['probabilities'])) or
                record.get('prediction') != planned['order'][max(
                    range(len(p)), key=p.__getitem__)] or
                record.get('input_tokens') != len(planned['token_ids']) or
                not isinstance(record.get('latency_s'), (float, int)) or
                not math.isfinite(record['latency_s']) or record['latency_s'] < 0 or
                not isinstance(record.get('candidate_mass'), (float, int)) or
                not math.isfinite(record['candidate_mass']) or
                not 0 <= record['candidate_mass'] <= 1):
            raise ValueError('Raw score, candidate, prediction or cost drift')


def conditional_probabilities(logits, width):
    if (len(logits) != width or width not in (6, 8) or
            any(not isinstance(x, (float, int)) or not math.isfinite(x)
                for x in logits)):
        raise ValueError('Invalid joint-route logits')
    values = [math.exp(x - max(logits)) for x in logits]
    return [x / sum(values) for x in values]


def route_audit(case, row):
    source = case['records'][row['line_index']]
    reference = (OTHER_REQUEST if source['scope'] != case['target'] else
                 source['field'] + (':POSITIVE' if source['value'] else ':NEGATIVE'))
    model = row['prediction']
    if model == reference:
        error = 'correct_route'
    elif model in (OTHER_REQUEST, NO_OBSERVATION):
        error = ('safe_nonselection' if source['scope'] != case['target'] else
                 'missed_relevant')
    elif source['scope'] != case['target']:
        error = 'wrong_request'
    elif model.split(':')[0] != source['field']:
        error = 'wrong_field'
    else:
        error = 'wrong_polarity'
    return {'source_id': case['id'], 'parent': case['parent'],
            'family': case['family'], 'variant': case['variant'],
            'line_index': row['line_index'], 'evidence_span': row['evidence_span'],
            'model_route': model, 'construction_reference_route': reference,
            'program_audit': error,
            'reference_provenance': 'program construction, not human annotation'}


def score_method(method, rows):
    uncertain = [r for r in rows if r['gold'] == 'INSUFFICIENT']
    determined = [r for r in rows if r['gold'] != 'INSUFFICIENT']
    parents = {r['parent'] for r in rows}
    if len(rows) != 72 or len(uncertain) != 24 or len(determined) != 48 or len(parents) != 12:
        raise ValueError('Method decision denominator drift')
    return {'method': method, 'correct_decisions': sum(r['correct'] for r in rows),
            'false_commitments': sum(r['prediction'] != 'INSUFFICIENT' for r in uncertain),
            'determined_correct': sum(r['correct'] for r in determined),
            'false_insufficient': sum(r['prediction'] == 'INSUFFICIENT' for r in determined),
            'wrong_supported_actions': sum(r['prediction'] != 'INSUFFICIENT' and
                                           not r['correct'] for r in determined),
            'complete_parents': sum(all(r['correct'] for r in rows if r['parent'] == p)
                                    for p in parents),
            'model_calls': sum(r['model_calls'] for r in rows),
            'input_tokens': sum(r['input_tokens'] for r in rows),
            'summed_forward_latency_s': sum(r['summed_forward_latency_s'] for r in rows),
            'by_variant': {v: {'correct': sum(r['correct'] for r in rows
                                              if r['variant'] == v),
                               'decisions': sum(r['variant'] == v for r in rows)}
                           for v in sorted({r['variant'] for r in rows})}}


def analyze():
    manifest = verify_frozen()
    runtime = json.loads((OUT / 'runtime.json').read_text(encoding='utf-8'))
    if (runtime['status'] != 'complete' or
            runtime['config_hash'] != manifest['config_hash'] or
            runtime['scientific_forwards'] != 514 or runtime['warmup_forwards'] != 2 or
            runtime['rewrite_model_records'] != 0 or
            runtime['reserved_model_records'] != 0 or
            runtime['paid_api_calls'] != 0 or runtime['jev_api_calls'] != 0 or
            runtime['new_training'] is not False or
            runtime['sdpa_kernel'] != 'math_only' or
            runtime['backbone_dtype'] != 'bfloat16' or
            runtime['adapter_exact_tensors'] != 504):
        raise ValueError('Incomplete or changed execution runtime')
    commit = runtime['execution_commit']
    if not re.fullmatch('[0-9a-f]{40}', commit):
        raise ValueError('Invalid execution commit')
    for path, digest in manifest['source_file_sha256_lf'].items():
        target = posixpath.normpath('research/fact-execution/' + path)
        content = subprocess.check_output(['git', 'show', commit + ':' + target], cwd=HERE)
        if sha(content) != digest:
            raise ValueError(f'Unfrozen execution source: {target}')
    expected_weights = json.loads((HERE.parent / 'next-study/results/weight_checksums.json').read_text())
    equal(expected_weights, json.loads((OUT / 'weight_checksums.json').read_text()))
    equal({'status': 'passed', 'exact_tensors': 504, 'parameters': 33030144},
          json.loads((OUT / 'adapter_audit.json').read_text()))
    encoded = read_rows(ENCODED)
    raw = read_rows(OUT / 'N1.jsonl')
    validate_raw(raw, encoded, manifest)
    if sum(r['input_tokens'] for r in raw) != manifest['total_scientific_input_tokens']:
        raise ValueError('Scientific input-token total drift')
    lookup = {r['query_id']: r for r in raw}
    if len(lookup) != 514:
        raise ValueError('Duplicate scientific query identity')
    references = {(r['source_id'], r['field']): r for r in
                  read_rows(HERE / 'data/reference_facts.jsonl')}
    cases = original_cases()
    direct_plan = read_rows(SELECTED)
    by_direct = {}
    for row in direct_plan:
        by_direct.setdefault(row['source_id'], []).append(lookup[
            f"direct/{row['source_id']}/{row['mapping']}"])
    decisions, claims, line_audits = [], [], []
    for case in cases:
        schema = compile_visible(case['state'], case['instruction'])
        line_count = len(visible_lines(case['state']))
        joint_rows = [lookup[f"joint/{case['id']}/{i}"] for i in range(line_count)]
        choices = {r['line_index']: r['prediction'] for r in joint_rows}
        extracted = aggregate(case['state'], schema, choices)
        joint_decision = execute(schema, extracted['facts'])
        for field in schema['fields']:
            name = field['name']
            reference = references[(case['id'], name)]['status']
            claims.append({'source_id': case['id'], 'parent': case['parent'],
                           'family': case['family'], 'variant': case['variant'],
                           'field': name, 'status': extracted['facts'][name],
                           'reference_status': reference,
                           'correct': extracted['facts'][name] == reference,
                           'model_selected_spans': extracted['model_selected_spans'][name],
                           'provenance': extracted['provenance'],
                           'absence_certified': False})
        line_audits.extend(route_audit(case, row) for row in joint_rows)
        direct_all = by_direct[case['id']]
        direct_call = [r for r in direct_all if r['mapping'] < line_count]
        direct_single = [r for r in direct_all if r['mapping'] == 0]
        if len(direct_call) != line_count or len(direct_single) != 1:
            raise ValueError('Incomplete direct subset for an input')
        for method, used, prediction in (
                ('joint', joint_rows, joint_decision),
                ('direct_single', direct_single, direct_choice(direct_single)),
                ('direct_call_matched', direct_call, direct_choice(direct_call)),
                ('direct_token_matched', direct_all, direct_choice(direct_all))):
            decisions.append({'method': method, 'source_id': case['id'],
                              'parent': case['parent'], 'family': case['family'],
                              'variant': case['variant'], 'gold': case['gold'],
                              'prediction': prediction,
                              'correct': prediction == case['gold'],
                              'model_calls': len(used),
                              'input_tokens': sum(r['input_tokens'] for r in used),
                              'summed_forward_latency_s': sum(r['latency_s'] for r in used),
                              'facts': extracted['facts'] if method == 'joint' else None})
    methods = {method: score_method(method, [r for r in decisions if r['method'] == method])
               for method in ('joint', 'direct_single', 'direct_call_matched',
                              'direct_token_matched')}
    if (methods['joint']['model_calls'] != 228 or methods['joint']['input_tokens'] != 95889 or
            methods['direct_call_matched']['model_calls'] != 228 or
            methods['direct_call_matched']['input_tokens'] != 76855 or
            methods['direct_token_matched']['model_calls'] != 286 or
            methods['direct_token_matched']['input_tokens'] != 95849 or
            len(claims) != 168 or len(line_audits) != 228):
        raise ValueError('Method cost or audit denominator drift')
    joint_decisions = [r for r in decisions if r['method'] == 'joint']
    summary = {
        'status': 'post_hoc_public_original_development_only',
        'config_hash': manifest['config_hash'], 'arm': 'N1',
        'original_inputs': 72, 'parent_clusters': 12,
        'reference_fields': 168, 'visible_lines': 228,
        'independent_human_annotations': 0,
        'rewrite_model_records': 0, 'reserved_model_records': 0,
        'scientific_forwards': 514, 'warmup_forwards': 2,
        'unique_scientific_input_tokens': 191738,
        'methods': methods,
        'joint_correct_fields': sum(r['correct'] for r in claims),
        'joint_exact_fact_vectors': sum(all(r['correct'] for r in claims
                                            if r['source_id'] == d['source_id'])
                                        for d in joint_decisions),
        'joint_missing_as_reported_value': sum(r['reference_status'] == 'MISSING' and
                                               r['status'] in ('TRUE', 'FALSE') for r in claims),
        'joint_missed_conflicts': sum(r['reference_status'] == 'CONFLICT' and
                                     r['status'] != 'CONFLICT' for r in claims),
        'joint_route_audit': dict(Counter(r['program_audit'] for r in line_audits)),
        'fixed_development_screening_rule': {
            'max_false_commitments': 7, 'min_determined_correct': 34,
            'passed': (methods['joint']['false_commitments'] <= 7 and
                       methods['joint']['determined_correct'] >= 34)},
        'interpretation_limit': ('Known synthetic development grammar and program labels; '
                                 'no independent human review, rewrite transfer, reserved '
                                 'confirmation or Jev run. Calls and input tokens trade off '
                                 'across the two direct controls; not equal total compute.')}
    return summary, decisions, claims, line_audits


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    summary, decisions, claims, line_audits = analyze()
    files = (('summary.json', json.dumps(summary, indent=2, ensure_ascii=False) + '\n'),
             ('decisions.jsonl', ''.join(json.dumps(r, ensure_ascii=False) + '\n'
                                         for r in decisions)),
             ('fact_claims.jsonl', ''.join(json.dumps(r, ensure_ascii=False) + '\n'
                                           for r in claims)),
             ('line_audits.jsonl', ''.join(json.dumps(r, ensure_ascii=False) + '\n'
                                          for r in line_audits)))
    if not args.verify and any((OUT / name).exists() for name, _ in files):
        raise ValueError('Preserve existing derived joint-route results')
    for name, payload in files:
        path = OUT / name
        if args.verify:
            if path.read_bytes().replace(b'\r\n', b'\n') != payload.encode('utf-8'):
                raise ValueError(f'Derived joint-route result drift: {name}')
        else:
            path.write_text(payload, encoding='utf-8', newline='\n')
    print(json.dumps({'status': 'passed', 'read_only': args.verify,
                      'scientific_forwards': 514,
                      'joint_correct': summary['methods']['joint']['correct_decisions'],
                      'screening_passed': summary['fixed_development_screening_rule']['passed']}))


if __name__ == '__main__':
    main()
