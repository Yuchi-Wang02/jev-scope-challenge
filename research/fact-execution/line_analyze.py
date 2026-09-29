"""Recompute the N1 line-evidence pilot from raw forwards; never infer in CI."""
import argparse
import json
import math
import posixpath
import re
import subprocess
from collections import Counter

from data_tools import HERE, original_cases
from fact_run import read_rows
from gap_analyze import equal
from interface import compile_visible, execute
from line_evidence import aggregate_line_choices, audit_claim_known_grammar, visible_lines
from line_run import ENCODED, OUT, SEED, sha, verify_frozen


def probabilities(logits):
    if len(logits) != 3 or any(not isinstance(x, (float, int)) or
                               not math.isfinite(x) for x in logits):
        raise ValueError('Invalid three-way logits')
    values = [math.exp(x - max(logits)) for x in logits]
    return [x / sum(values) for x in values]


def validate_raw(raw, plans, manifest):
    import random
    ordered = list(plans)
    random.Random(SEED).shuffle(ordered)
    if len(raw) != 548 or len(ordered) != 548:
        raise ValueError('Incomplete line pilot grid')
    for number, (record, planned) in enumerate(zip(raw, ordered), 1):
        for key, value in planned.items():
            if record.get(key) != value:
                raise ValueError(f'Raw forward differs from frozen query: {key}')
        if (record.get('arm') != 'N1' or record.get('config_hash') != manifest['config_hash'] or
                record.get('forward_index') != number or record.get('ok') is not True or
                record.get('mapping') != 0 or record.get('split') != 'development' or
                record.get('representation') != 'original'):
            raise ValueError('Raw forward identity or scope drift')
        p = probabilities(record['logits'])
        if (len(record.get('probabilities', [])) != 3 or any(
                not math.isclose(a, b, rel_tol=2e-5, abs_tol=1e-7)
                for a, b in zip(p, record['probabilities'])) or
                record['prediction'] != planned['order'][max(range(3), key=p.__getitem__)] or
                record['input_tokens'] != len(planned['token_ids']) or
                not isinstance(record.get('latency_s'), (float, int)) or
                not math.isfinite(record['latency_s']) or record['latency_s'] < 0 or
                not isinstance(record.get('candidate_mass'), (float, int)) or
                not math.isfinite(record['candidate_mass']) or
                not 0 <= record['candidate_mass'] <= 1):
            raise ValueError('Raw score, choice or cost drift')


def analyze():
    manifest = verify_frozen()
    runtime = json.loads((OUT / 'runtime.json').read_text(encoding='utf-8'))
    if (runtime['status'] != 'complete' or
            runtime['config_hash'] != manifest['config_hash'] or
            runtime['scientific_forwards'] != 548 or runtime['warmup_forwards'] != 2 or
            runtime['rewrite_model_records'] != 0 or runtime['reserved_model_records'] != 0 or
            runtime['paid_api_calls'] != 0 or runtime['new_training'] is not False or
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
            raise ValueError(f'Source not frozen at execution commit: {target}')
    expected_weights = json.loads((HERE.parent / 'next-study/results/weight_checksums.json').read_text())
    equal(expected_weights, json.loads((OUT / 'weight_checksums.json').read_text()))
    equal({'status': 'passed', 'exact_tensors': 504, 'parameters': 33030144},
          json.loads((OUT / 'adapter_audit.json').read_text()))
    raw = read_rows(OUT / 'N1.jsonl')
    plans = read_rows(ENCODED)
    validate_raw(raw, plans, manifest)
    if sum(r['input_tokens'] for r in raw) != manifest['planned_input_tokens']:
        raise ValueError('Actual input token budget differs from freeze')
    lookup = {(r['source_id'], r['field'], r['line_index']): r for r in raw}
    if len(lookup) != 548:
        raise ValueError('Duplicate query identity')
    references = {(r['source_id'], r['field']): r for r in
                  read_rows(HERE / 'data/reference_facts.jsonl')}
    cases = original_cases()
    decisions, claims = [], []
    for case in cases:
        schema = compile_visible(case['state'], case['instruction'])
        line_count = len(visible_lines(case['state']))
        vector, used, case_claims = {}, [], []
        for field in schema['fields']:
            name = field['name']
            selected = [lookup[(case['id'], name, i)] for i in range(line_count)]
            used.extend(selected)
            choices = {r['line_index']: r['prediction'] for r in selected}
            claim = aggregate_line_choices(case['state'], name, choices)
            audit = audit_claim_known_grammar(case['state'], case['instruction'], claim)
            truth = references[(case['id'], name)]['status']
            wrong_scope = wrong_field = wrong_value = 0
            for row in selected:
                if row['prediction'] == 'IRRELEVANT':
                    continue
                source = case['records'][row['line_index']]
                if source['scope'] != schema['target']:
                    wrong_scope += 1
                elif source['field'] != name:
                    wrong_field += 1
                elif source['value'] != (row['prediction'] == 'POSITIVE'):
                    wrong_value += 1
            entry = {'source_id': case['id'], 'parent': case['parent'],
                     'family': case['family'], 'variant': case['variant'],
                     'field': name, 'status': claim['status'],
                     'reference_status': truth, 'correct': claim['status'] == truth,
                     'evidence_spans': claim['evidence_spans'],
                     'provenance': claim['provenance'],
                     'inspected_scope': claim['inspected_scope'],
                     'known_grammar_audit': audit,
                     'wrong_request_selected_lines': wrong_scope,
                     'wrong_field_selected_lines': wrong_field,
                     'wrong_value_selected_lines': wrong_value,
                     'selected_lines': len(claim['evidence_spans'])}
            vector[name] = claim['status']
            claims.append(entry)
            case_claims.append(entry)
        decision = execute(schema, vector)
        entry = {'source_id': case['id'], 'parent': case['parent'],
                 'family': case['family'], 'variant': case['variant'],
                 'gold': case['gold'], 'prediction': decision,
                 'correct': decision == case['gold'], 'facts': vector,
                 'facts_exact': all(c['correct'] for c in case_claims),
                 'model_calls': len(used),
                 'input_tokens': sum(r['input_tokens'] for r in used),
                 'summed_forward_latency_s': sum(r['latency_s'] for r in used)}
        if entry['facts_exact'] and not entry['correct']:
            raise ValueError('Correct facts produced wrong executor decision')
        decisions.append(entry)
    uncertain = [r for r in decisions if r['gold'] == 'INSUFFICIENT']
    determined = [r for r in decisions if r['gold'] != 'INSUFFICIENT']
    parents = {r['parent'] for r in decisions}
    baseline = json.loads((HERE / 'results/summary.json').read_text(encoding='utf-8'))['methods']['N1']
    prior = {name: {key: baseline[name]['all'][key] for key in
                    ('correct', 'false_commitments', 'determined_decisions',
                     'model_calls', 'input_tokens')}
             for name in ('facts_0', 'direct_0')}
    summary = {
        'status': 'post_hoc_original_development_only',
        'config_hash': manifest['config_hash'], 'arm': 'N1',
        'original_inputs': len(decisions), 'parent_clusters': len(parents),
        'reference_fields': len(claims), 'independent_human_annotations': 0,
        'rewrite_model_records': 0, 'reserved_model_records': 0,
        'scientific_forwards': len(raw), 'warmup_forwards': 2,
        'correct_decisions': sum(r['correct'] for r in decisions),
        'complete_parents': sum(all(r['correct'] for r in decisions if r['parent'] == parent)
                                for parent in parents),
        'uncertain_decisions': len(uncertain),
        'false_commitments': sum(r['prediction'] != 'INSUFFICIENT' for r in uncertain),
        'determined_decisions': len(determined),
        'determined_correct': sum(r['correct'] for r in determined),
        'wrong_supported_actions': sum(r['prediction'] != 'INSUFFICIENT' and not r['correct']
                                       for r in determined),
        'false_insufficient': sum(r['prediction'] == 'INSUFFICIENT' for r in determined),
        'correct_fields': sum(r['correct'] for r in claims),
        'exact_fact_vectors': sum(r['facts_exact'] for r in decisions),
        'missing_fields': sum(r['reference_status'] == 'MISSING' for r in claims),
        'missing_as_reported_value': sum(r['reference_status'] == 'MISSING' and
                                         r['status'] in ('TRUE', 'FALSE') for r in claims),
        'missed_conflicts': sum(r['reference_status'] == 'CONFLICT' and
                                r['status'] != 'CONFLICT' for r in claims),
        'wrong_request_selected_lines': sum(r['wrong_request_selected_lines'] for r in claims),
        'wrong_field_selected_lines': sum(r['wrong_field_selected_lines'] for r in claims),
        'wrong_value_selected_lines': sum(r['wrong_value_selected_lines'] for r in claims),
        'known_grammar_audit_gates': dict(Counter(
            r['known_grammar_audit']['gate'] for r in claims)),
        'model_calls': sum(r['model_calls'] for r in decisions),
        'input_tokens': sum(r['input_tokens'] for r in decisions),
        'summed_forward_latency_s': sum(r['summed_forward_latency_s'] for r in decisions),
        'by_family': {family: {'correct': sum(r['correct'] for r in decisions if r['family'] == family),
                               'decisions': sum(r['family'] == family for r in decisions)}
                      for family in sorted({r['family'] for r in decisions})},
        'by_variant': {variant: {'correct': sum(r['correct'] for r in decisions if r['variant'] == variant),
                                'decisions': sum(r['variant'] == variant for r in decisions)}
                       for variant in sorted({r['variant'] for r in decisions})},
        'fixed_screening_rule': {'max_false_commitments': 7, 'min_determined_correct': 34,
                                 'passed': None},
        'old_N1_comparators': prior,
        'interpretation_limit': 'Original public development grammar; no independent labels, budget-matched direct control, rewrite test or Jev run.'}
    if len(decisions) != 72 or len(claims) != 168 or len(uncertain) != 24 or len(determined) != 48:
        raise ValueError('Unexpected source grid or label balance')
    summary['fixed_screening_rule']['passed'] = (
        summary['false_commitments'] <= 7 and summary['determined_correct'] >= 34)
    return summary, decisions, claims


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    summary, decisions, claims = analyze()
    files = (('summary.json', json.dumps(summary, indent=2, ensure_ascii=False) + '\n'),
             ('decisions.jsonl', ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in decisions)),
             ('fact_claims.jsonl', ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in claims)))
    for name, payload in files:
        path = OUT / name
        if args.verify:
            if path.read_bytes().replace(b'\r\n', b'\n') != payload.encode('utf-8'):
                raise ValueError(f'Derived result drift: {name}')
        else:
            if path.exists():
                raise ValueError(f'Preserve existing derived result: {name}')
            path.write_text(payload, encoding='utf-8', newline='\n')
    print(json.dumps({'status': 'passed', 'read_only': args.verify,
                      'scientific_forwards': summary['scientific_forwards'],
                      'correct_decisions': summary['correct_decisions'],
                      'false_commitments': summary['false_commitments'],
                      'screening_passed': summary['fixed_screening_rule']['passed']}))


if __name__ == '__main__':
    main()
