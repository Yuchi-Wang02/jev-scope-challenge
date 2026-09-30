"""Post-hoc visible-ID replay and software contract checks; no model invocation."""
import argparse
import hashlib
import json
import re
from collections import Counter

from data_tools import HERE, original_cases
from fact_run import read_rows
from gap_analyze import equal
from interface import compile_visible, execute
from joint_analyze import analyze, score_method
from joint_execution import OUT
from joint_route import OTHER_REQUEST, aggregate
from line_evidence import visible_lines
from scope_gate import gate_line

DEST = HERE / 'data/scope_gate'
REPORT = HERE / 'VISIBLE_ID_GATE_AUDIT.md'


def sha(path):
    return hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest()


def replay(state, policy, selected_routes):
    """No case metadata, reference records or labels are accepted by runtime."""
    schema = compile_visible(state, policy)
    lines = visible_lines(state)
    if set(selected_routes) != {line['line_index'] for line in lines}:
        raise ValueError('Incomplete saved route vector')
    output, gates = {}, []
    for line in lines:
        gate = gate_line(state.splitlines()[0], line['text'])
        index = line['line_index']
        output[index] = OTHER_REQUEST if gate['status'] == 'DROP' else selected_routes[index]
        gates.append(dict(line_index=index, text=line['text'], **gate,
                          saved_route=selected_routes[index], replay_route=output[index]))
    extracted = aggregate(state, schema, output)
    return dict(prediction=execute(schema, extracted['facts']), facts=extracted['facts'],
                gates=gates, routes=output)


def contract_cases():
    header = 'Request: allow action for request request-ABC.'
    examples = [
        ('same_id', header, 'Reviewer A approves request request-ABC.', 'KEEP'),
        ('same_namespace_foreign', header, 'Reviewer A approves request request-XYZ.', 'DROP'),
        ('longer_id_is_foreign', header, 'Reviewer A approves request request-ABCD.', 'DROP'),
        ('shorter_id_is_foreign', header, 'Reviewer A approves request request-AB.', 'DROP'),
        ('foreign_prefix_can_be_target', 'Request: allow action for request other-ABC.',
         'Reviewer A approves request other-ABC.', 'KEEP'),
        ('numeric_id', 'Request: allow action for request ticket-104.',
         'Reviewer A approves request ticket-104.', 'KEEP'),
        ('mixed_owner_line', header,
         'Reviewer A approves request request-ABC. Reviewer B rejects request request-XYZ.', 'UNKNOWN'),
        ('two_target_facts', header,
         'Reviewer A approves request request-ABC. Reviewer B approves request request-ABC.', 'UNKNOWN'),
        ('copied_into_target_file', header,
         'Reviewer A rejects request request-XYZ; copied into request request-ABC.', 'UNKNOWN'),
        ('quoted_target', header, 'A quote says: Reviewer A approves request request-ABC.', 'UNKNOWN'),
        ('negated_observation', header, 'It is not true that Reviewer A approves request request-ABC.', 'UNKNOWN'),
        ('implicit_reference', header, 'Reviewer A approves that request.', 'UNKNOWN'),
        ('unfamiliar_id_syntax', header, 'Reviewer A approves request request/ABC.', 'UNKNOWN'),
        ('unfamiliar_header', 'Target: request-ABC', 'Reviewer A approves request request-ABC.', 'UNKNOWN'),
        ('numbered_line', header, '[1] Reviewer A approves request request-ABC.', 'UNKNOWN'),
        ('no_record', header, '', 'UNKNOWN'),
    ]
    result = []
    for name, shown_header, line, expected in examples:
        actual = gate_line(shown_header, line)
        if actual['status'] != expected:
            raise ValueError(f'Gate contract drift: {name}')
        result.append(dict(id=name, header=shown_header, line=line, expected=expected,
                           gate=actual, model_output=None,
                           provenance='constructed software test, no model evaluation'))
    return result


def name_checks(cases):
    """Transform visible names only; never copy model outputs to new text."""
    result = []
    for case in cases:
        lines = visible_lines(case['state'])
        header = case['state'].splitlines()[0]
        base_gates = [gate_line(header, line['text']) for line in lines]
        target = base_gates[0]['target_id']
        owners = sorted({g['owner_id'] for g in base_gates})
        other = [owner for owner in owners if owner != target]
        if len(other) > 1 or any(g['status'] == 'UNKNOWN' for g in base_gates):
            raise ValueError('Original gate coverage changed')
        for name, target_new, other_new in (
            ('same_namespace', 'request-NEUTRAL', 'request-DISTANT'),
            ('swapped_prefix', 'other-NEUTRAL', 'request-DISTANT'),
            ('prefix_collision', 'request-ABC', 'request-ABCD')):
            mapping = {target: target_new} | ({other[0]: other_new} if other else {})
            pattern = re.compile(r'(?<![A-Za-z0-9_-])(?:' + '|'.join(
                re.escape(k) for k in sorted(mapping, key=len, reverse=True)) + r')(?![A-Za-z0-9_-])')
            state = pattern.sub(lambda m: mapping[m.group(0)], case['state'])
            transformed_lines = visible_lines(state)
            gates = [gate_line(state.splitlines()[0], line['text']) for line in transformed_lines]
            expected = [g['status'] for g in base_gates]
            if [g['status'] for g in gates] != expected:
                raise ValueError('Exact equality changed under injective renaming')
            prefix = ['KEEP' if g['owner_id'].startswith('request-') else 'DROP' for g in gates]
            substring = ['KEEP' if target_new in line['text'] else 'DROP' for line in transformed_lines]
            result.append(dict(source_id=case['id'], parent=case['parent'], transform=name,
                               state=state, instruction=case['instruction'],
                               expected_scope=expected, exact_id_scope=[g['status'] for g in gates],
                               prefix_shortcut_scope=prefix, substring_shortcut_scope=substring,
                               model_output=None, independent_human_annotations=0))
    return result


def audit():
    old_summary, old_decisions, old_claims, old_audits = analyze()
    for name, fresh in (('summary.json', old_summary), ('decisions.jsonl', old_decisions),
                        ('fact_claims.jsonl', old_claims), ('line_audits.jsonl', old_audits)):
        saved = json.loads((OUT / name).read_text(encoding='utf-8')) if name.endswith('.json') else read_rows(OUT / name)
        equal(fresh, saved, name)
    raw = read_rows(OUT / 'N1.jsonl')
    routes = [r for r in raw if r['arm'] == 'joint']
    lookup = {(r['source_id'], r['line_index']): r for r in routes}
    old = {r['source_id']: r for r in old_decisions if r['method'] == 'joint'}
    cases = original_cases()
    rows, gates, field_checks = [], [], []
    references = {(r['source_id'], r['field']): r['reference_status'] for r in old_claims}
    for case in cases:
        selected = {line['line_index']: lookup[case['id'], line['line_index']]['prediction']
                    for line in visible_lines(case['state'])}
        result = replay(case['state'], case['instruction'], selected)
        base = old[case['id']]
        rows.append(dict(base, method='post_hoc_visible_id_gate', prediction=result['prediction'],
                         correct=result['prediction'] == case['gold'], facts=result['facts'],
                         original_prediction=base['prediction'], original_correct=base['correct'],
                         original_facts=base['facts'],
                         new_model_forwards=0, prospective_screen_applicable=False))
        # Construction references enter only AFTER runtime predictions are finished.
        for field, value in result['facts'].items():
            reference = references[case['id'], field]
            field_checks.append(dict(source_id=case['id'], field=field, value=value,
                                     reference=reference, correct=value == reference))
        for g in result['gates']:
            record = case['records'][g['line_index']]
            reference = 'KEEP' if record['scope'] == case['target'] else 'DROP'
            gates.append(dict(source_id=case['id'], parent=case['parent'], **g,
                              reference_scope=reference,
                              scope_correct=g['status'] == reference,
                              reference_provenance='program construction, not human review'))
    score = score_method('post_hoc_visible_id_gate', rows)
    transitions = Counter(('correct' if r['original_correct'] else 'wrong') + '_to_' +
                          ('correct' if r['correct'] else 'wrong') for r in rows)
    parents = []
    for parent in sorted({r['parent'] for r in rows}):
        group = [r for r in rows if r['parent'] == parent]
        parents.append(dict(parent=parent, views=len(group),
                            original_correct=sum(r['original_correct'] for r in group),
                            replay_correct=sum(r['correct'] for r in group)))
    transformed = name_checks(cases)
    name_summary = {}
    for name in sorted({r['transform'] for r in transformed}):
        group = [r for r in transformed if r['transform'] == name]
        name_summary[name] = dict(views=len(group), lines=sum(len(r['expected_scope']) for r in group))
        for method in ('exact_id', 'prefix_shortcut', 'substring_shortcut'):
            pairs = [(actual, expected) for r in group for actual, expected in
                     zip(r[method + '_scope'], r['expected_scope'])]
            name_summary[name][method] = dict(correct=sum(a == b for a, b in pairs),
                false_keep=sum(a == 'KEEP' and b == 'DROP' for a, b in pairs),
                false_drop=sum(a == 'DROP' and b == 'KEEP' for a, b in pairs))
    kept = { (r['source_id'], r['line_index']) for r in gates if r['status'] != 'DROP'}
    summary = dict(status='post_hoc_visible_text_gate_replay_not_new_inference',
        original_inputs=72, parent_groups=12, new_model_forwards=0, independent_human_annotations=0,
        original_joint_screen_passed=old_summary['fixed_development_screening_rule']['passed'],
        replay_has_prospective_screen=False, original_method=old_summary['methods']['joint'],
        replay_method=score, transitions=dict(sorted(transitions.items())), parents=parents,
        gate_counts=dict(Counter(r['status'] for r in gates)),
        gate_correct_lines=sum(r['scope_correct'] for r in gates),
        correct_fields=sum(r['correct'] for r in field_checks),
        exact_fact_vectors=sum(all(f['correct'] for f in field_checks if f['source_id'] == r['source_id']) for r in rows),
        missing_fields_asserted=sum(r['reference'] == 'MISSING' and r['value'] in ('TRUE','FALSE') for r in field_checks),
        original_prefix_scope_agreement=sum((r['owner_id'].startswith('request-')) == (r['reference_scope'] == 'KEEP') for r in gates),
        projected_unchanged_query_subset=dict(forwards=len(kept),
            input_tokens=sum(r['input_tokens'] for r in routes if (r['source_id'],r['line_index']) in kept),
            measured_new_deployment=False, parser_cpu_seconds=None, end_to_end_latency_seconds=None),
        name_checks=name_summary, software_contract_tests=len(contract_cases()),
        source_sha256_lf={p.relative_to(HERE).as_posix():sha(p) for p in (
            HERE/'scope_gate.py', HERE/'scope_gate_audit.py', HERE/'data/original_cases.jsonl',
            OUT/'N1.jsonl', OUT/'summary.json')})
    if (score['correct_decisions'], score['false_commitments'], score['determined_correct'],
        score['complete_parents'], dict(transitions)) != (70, 1, 47, 11,
            {'wrong_to_correct':38,'correct_to_correct':32,'correct_to_wrong':2}):
        raise ValueError('Post-hoc result changed; inspect evidence before changing claims')
    return summary, rows, gates, field_checks, transformed


def report(s, rows):
    before, after = s['original_method'], s['replay_method']
    text = [
        '# Explicit request IDs: a post-hoc gate, two exposed errors', '',
        '**A visible-ID program gate changes saved joint-route decisions from 34/72 to 70/72.**',
        'This is a post-hoc composition of ordinary parsing and already recorded model outputs.',
        'It adds zero model forwards and does not change the failed frozen joint pilot.',
        'The same 72 public development views in 12 parent groups remain program-labeled,',
        'with zero independent human annotations. There is no new Jev result.', '',
        '## What was computed', '',
        'The [gate](scope_gate.py) reads only the visible request header and one visible',
        'record line. Five anchored sentence shapes locate the request-ID slot. Exact',
        'identity keeps the saved route; an explicit foreign ID replaces it with',
        '`OTHER_REQUEST`. Unsupported text is `UNKNOWN` and retains the saved route',
        'in this replay. It is never silently certified as foreign or absent.',
        'The gate returns no field or polarity. The existing aggregator and executor',
        'then run unchanged. Construction records and gold labels enter only afterward',
        'for scoring. This is grammar-specific validation, not a new extraction algorithm.', '',
        '|Pipeline|Correct /72|False commitments /24|Determined correct /48|Needless deferrals /48|Complete parents /12|',
        '|---|---:|---:|---:|---:|---:|']
    for name,m in (('Frozen joint result',before),('Post-hoc visible-ID replay',after)):
        text.append(f"|{name}|{m['correct_decisions']}|{m['false_commitments']}|{m['determined_correct']}|{m['false_insufficient']}|{m['complete_parents']}|")
    text += ['', 'The existing full known-grammar parser remains **72/72**, and always-defer',
        'remains **24/72**, both with zero model calls. Those controls are reported in',
        '[the completed study](JOINT_RESULTS.md). The gate does not beat the full parser.',
        'A new filtered-direct model comparison has not run; 70/72 must not be marketed',
        'as proof that fact decomposition beats equally filtered direct inference.', '',
        '## Two wrongs can conceal each other', '',
        '**38 wrong decisions become correct, but two correct decisions become wrong.**',
        'The other 32 stay correct. Both remaining failures are these regressions:', '',
        '|View|Reference|Original joint|Gated replay|', '|---|---|---|---|']
    for r in rows:
        if not r['correct']:
            text.append(f"|`{r['source_id']}`|{r['gold']}|{r['original_prediction']}|{r['prediction']}|")
    text += ['', 'Both affected cases contain a wrong-field route on a target record. Removing',
        'foreign-request evidence exposes the effect of that remaining extraction error.',
        'In both regressions the original fact vector also matched the program reference:',
        'the foreign route happened to supply the value missed on the target line.',
        'Even a correct action and fact vector can conceal incorrect supporting records.',
        'This is a saved-output computation, not an inference about model internals.', '',
        f"The gate keeps 162 target lines and drops 66 foreign lines, with 228/228 scope",
        f"matches and no UNKNOWN in this grammar. Replayed field statuses are correct for",
        f"{s['correct_fields']}/168 fields; {s['exact_fact_vectors']}/72 entire vectors match.",
        f"{s['missing_fields_asserted']}/18 truly missing fields become asserted values.", '',
        '## A perfect naming shortcut limits the original experiment', '',
        'The original generator assigns `request-…` to every target and `other-…` to',
        'every distractor. Merely accepting the first prefix agrees with all 228',
        'reference scopes. Existing results cannot distinguish actual ID comparison',
        'from that shortcut. Before applying view variants, the generator adds a',
        'foreign record on a key field with opposite polarity. Record ordering and',
        'formatting variation are also limited.', '',
        'The following checks rename only visible request IDs in the 72 texts.',
        'They test code, with no transferred model predictions or new model scores.',
        'Each row has 228 correlated lines; all three rows reuse the same 12 parents.', '',
        '|Software-only renaming|Exact-ID gate correct /228|Prefix shortcut correct /228|Substring shortcut correct /228|',
        '|---|---:|---:|---:|']
    for name,m in s['name_checks'].items():
        text.append(f"|{name}|{m['exact_id']['correct']}|{m['prefix_shortcut']['correct']}|{m['substring_shortcut']['correct']}|")
    text += ['', 'Same-namespace uses `request-NEUTRAL` and `request-DISTANT`; swapped-prefix',
        'makes `other-NEUTRAL` the requested target; prefix-collision uses',
        '`request-ABC` versus `request-ABCD`. Exact equality survives these injective',
        'renamings by construction. That is a software property, not language transfer.', '',
        'The [16 contract cases](data/scope_gate/contract_cases.jsonl) also include',
        'mixed owners, two target facts, quotation, negation, implicit reference,',
        'unfamiliar IDs and numbered lines. Unsupported shapes return UNKNOWN.',
        'The gate does not establish that a record is true, current or authoritative,',
        'and it does not solve [the one-line/two-fact limit](MULTIFACT_LINE_STRESS.md).', '',
        '## Historical cost and the unexecuted deployment projection', '',
        'This replay depends on **228 recorded joint forwards / 95,889 input tokens**.',
        '**Zero additional forwards** were executed. Each historical joint query sees',
        'only one record plus the same target/policy/definitions, so rejecting a record',
        'before querying would leave every retained serialized prompt unchanged.',
        f"The corresponding saved subset has **{s['projected_unchanged_query_subset']['forwards']} queries / "
        f"{s['projected_unchanged_query_subset']['input_tokens']:,} input tokens**. That is a",
        'deployment projection, not a newly timed run. Parser CPU cost and end-to-end',
        'latency were not measured. Different prompts or filtered full-context direct',
        'decisions cannot reuse these scores and require new authorized inference.', '',
        'The old screen stays failed. Applying its thresholds to a method selected',
        'after viewing the data would not make that method prospectively validated.', '',
        '## Evidence and next falsifiable step', '',
        '[Summary](data/scope_gate/summary.json), [all 72 decisions](data/scope_gate/decisions.jsonl),',
        '[all 228 line gates](data/scope_gate/lines.jsonl), [168 field checks](data/scope_gate/fields.jsonl),',
        '[216 unscored renamings](data/scope_gate/name_checks.jsonl), and',
        '[replay implementation](scope_gate_audit.py) preserve the complete derivation.', '',
        '```bash', 'python research/fact-execution/scope_gate_audit.py verify', '```', '',
        'The next preparation is a [target-switch challenge](../request-ownership/PROTOCOL.md):',
        'hold a two-request record block fixed and change only the target header.',
        'Both IDs use the same namespace. Compare full joint, gated joint, direct',
        'and equally filtered direct decisions; count pairs with both answers correct.',
        'The public original corpus is diagnostic material, not fresh confirmation.',
        'Program-generated scenes with familiar wording remain synthetic preparation;',
        'independent language review and later confirmation are still outstanding.', '',
        'Entity binding and robustness to name variation have direct prior art:',
        '[Feng and Steinhardt, ICLR 2024](https://arxiv.org/abs/2310.17191) and',
        '[Meng et al., Findings ACL 2024](https://aclanthology.org/2024.findings-acl.969/).',
        'Those papers motivate controls; no code, data or results from them are copied.',
        'See the earlier [bounded extraction audit](JOINT_ROUTE_SCOPE_AUDIT.md) and',
        '[Kev/Laya/Qwen attribution](../../THIRD_PARTY_NOTICES.md).', '']
    return '\n'.join(text)


def artifacts():
    s, rows, lines, fields, transformed = audit()
    result = {DEST/'summary.json':json.dumps(s,indent=2,ensure_ascii=False)+'\n', REPORT:report(s,rows)}
    for name, values in (('decisions',rows),('lines',lines),('fields',fields),
                         ('name_checks',transformed),('contract_cases',contract_cases())):
        result[DEST/f'{name}.jsonl']=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in values)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('build','verify'))
    args=parser.parse_args()
    expected=artifacts()
    for path, content in expected.items():
        if args.mode=='verify':
            if path.read_bytes().replace(b'\r\n',b'\n') != content.encode('utf-8'):
                raise ValueError(f'Post-hoc artifact drift: {path.name}')
        else:
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(content.encode('utf-8'))
    print(json.dumps(dict(status=args.mode, original_inputs=72, replay_correct=70,
                         additional_model_forwards=0, transformed_model_forwards=0)))


if __name__=='__main__':
    main()
