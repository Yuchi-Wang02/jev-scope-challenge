"""Post-run, read-only evidence checks. Does not alter the frozen experiment."""
import argparse
import json
import math
import re
from gap_run import HERE, ARMS, GATE, read_rows, freeze, spec, encode_plans, tokenizer_for
from gap_analyze import analyze, equal
from gap_data import parse_text, world_truth, exhaustive_solver_audit, validate, build_rows


def text_reference(state, policy):
    """Recover the declared synthetic schema from policy text, without case metadata."""
    route = re.search(r'The target route names either (site-[A-Z]+) or (site-[A-Z]+)\.', policy)
    if route:
        family = 'composed_route' if 'Reviewer A rejection denies' in policy else 'route_lookup'
        sites = list(route.groups())
    elif 'Allow exactly when both reviewer A and reviewer B approve.' in policy:
        family, sites = 'joint_approval', ['site-UNUSED_A', 'site-UNUSED_B']
    elif 'Use the target base decision, except reverse ALLOW and DENY' in policy:
        family, sites = 'reversal_exception', ['site-UNUSED_A', 'site-UNUSED_B']
    else:
        raise ValueError('Unsupported synthetic policy grammar')
    return world_truth(parse_text(state, policy, family, sites))[0]


def extra_record_checks(row, plan):
    """Reject non-finite metadata, false probability masses and wrong pointer options."""
    for key in ('latency_s',):
        if not isinstance(row[key], (float, int)) or not math.isfinite(row[key]) or row[key] < 0:
            raise ValueError('Invalid timing evidence')
    if len(row['logits']) != 3 or len(row['probabilities']) != 3:
        raise ValueError('Wrong score width')
    if any(not math.isfinite(v) or not 0 <= v <= 1 for v in row['probabilities']):
        raise ValueError('Invalid probabilities')
    if not math.isclose(sum(row['probabilities']), 1, abs_tol=2e-6):
        raise ValueError('Unnormalized probabilities')
    if row['arm'] == 'K1':
        if row['options'] != [spec.OPTIONS[k] for k in plan['order']]:
            raise ValueError('Wrong pointer option text')
        delta = row['parity']['max_probability_delta']
        if not math.isfinite(delta) or not 0 <= delta < GATE:
            raise ValueError('Invalid parity delta')
    elif not math.isfinite(row['candidate_mass']) or not 0 <= row['candidate_mass'] <= 1:
        raise ValueError('Invalid native candidate mass')


def verify(cache=None):
    freeze()
    s, predictions, code = analyze()
    equal(s, json.loads((HERE/'results/summary.json').read_text(encoding='utf-8')))
    equal(predictions, read_rows(HERE/'results/predictions.jsonl'))
    equal(code, json.loads((HERE/'results/code_reference.json').read_text(encoding='utf-8')))
    cases = read_rows(HERE/'data/cases.jsonl')
    validate(cases)
    if cases != build_rows():
        raise ValueError('Frozen generator/corpus mismatch')
    audit = exhaustive_solver_audit()
    equal(audit, json.loads((HERE/'data/solver_audit.json').read_text(encoding='utf-8')))
    for c in cases:
        if text_reference(c['state'], c['instruction']) != c['gold']:
            raise ValueError('Text-only known-grammar reference mismatch')
    plans = read_rows(HERE/'data/inputs.jsonl')
    lookup = {(p['id'], p['mapping']):p for p in plans}
    if len(plans) != 1008 or len(lookup) != 1008:
        raise ValueError('Duplicate or incomplete input plans')
    runtime = json.loads((HERE/'results/runtime.json').read_text(encoding='utf-8'))
    if runtime['execution_commit'] != '4809a5b2ea9aa8aef803f2875ad064998f60dd0b':
        raise ValueError('Execution source commit mismatch')
    for arm in ARMS:
        if runtime[arm] != {'main':216, 'null':36, 'status':'complete'}:
            raise ValueError('Incomplete arm runtime')
        for row in read_rows(HERE/f'results/{arm}.jsonl'):
            extra_record_checks(row, lookup[row['id'],row['mapping']])
    tokenized = False
    if cache is not None:
        if encode_plans(tokenizer_for(cache)) != plans:
            raise ValueError('Pinned tokenizer/encoder mismatch')
        tokenized = True
    return {'status':'passed', 'read_only':True, 'scientific_records':756,
            'reserved_model_records':0, 'structured_states_checked':audit['partial_or_conflicting_states'],
            'known_grammar_text_inputs_checked':len(cases), 'independent_human_annotations':0,
            'tokenizer_rechecked':tokenized}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', help='Optional existing pinned tokenizer cache; no download or inference')
    args = parser.parse_args()
    print(json.dumps(verify(args.cache)))
