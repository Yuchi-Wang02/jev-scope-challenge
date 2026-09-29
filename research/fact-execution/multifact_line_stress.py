"""Software-only line-packing stress on original development evidence."""
import argparse
import json
from collections import Counter
from itertools import product

from data_tools import HERE, original_cases
from gap_data import constraints, sentence
from interface import compile_visible, execute, status_for
from joint_route import OTHER_REQUEST, aggregate
from line_evidence import visible_lines

OUT = HERE / 'data/multifact_line_stress.jsonl'
SUMMARY = HERE / 'data/multifact_line_stress_summary.json'


def route(record, target):
    if record['scope'] != target:
        return OTHER_REQUEST
    return record['field'] + (':POSITIVE' if record['value'] else ':NEGATIVE')


def pack(case, indexes):
    """Replace one newline with a space; keep every source sentence verbatim."""
    first, second = sorted(indexes)
    original = visible_lines(case['state'])
    if len(original) != len(case['records']) or any(
            line['text'] != sentence(record, case)
            for line, record in zip(original, case['records'])):
        raise ValueError('Original record-to-visible-line alignment drift')
    body, sources = [], []
    for index, line in enumerate(original):
        if index == first:
            body.append(line['text'] + ' ' + original[second]['text'])
            sources.append([first, second])
        elif index != second:
            body.append(line['text'])
            sources.append([index])
    state = '\n'.join(case['state'].splitlines()[:2] + body)
    if ([line['text'] for line in visible_lines(state)] != body or
            Counter(index for group in sources for index in group) !=
            Counter(range(len(original)))):
        raise ValueError('Packing changed or omitted a source sentence')
    return state, sources


def faithful_possibilities(case, state, sources, reference):
    """Try only labels warranted by a constituent record, never hallucinated labels."""
    schema = compile_visible(state, case['instruction'])
    allowed = [list(dict.fromkeys(route(case['records'][i], case['target'])
                                  for i in group)) for group in sources]
    vectors, decisions = [], set()
    for selections in product(*allowed):
        facts = aggregate(state, schema, dict(enumerate(selections)))['facts']
        vectors.append(facts == reference)
        decisions.add(execute(schema, facts))
    return allowed, any(vectors), case['gold'] in decisions, sorted(decisions)


def build():
    rows = []
    for case in original_cases():
        target = [i for i, r in enumerate(case['records'])
                  if r['scope'] == case['target']]
        cross = next(((a, b) for a in target for b in target
                      if a < b and case['records'][a]['field'] !=
                      case['records'][b]['field']), None)
        other = next((i for i, r in enumerate(case['records'])
                      if r['scope'] != case['target']), None)
        if cross is None or other is None:
            continue
        reference = {field: status_for(values)
                     for field, values in constraints(case).items()}
        if execute(compile_visible(case['state'], case['instruction']), reference) != case['gold']:
            raise ValueError('Original program truth drift')
        for packing, pair in (('cross_field', cross),
                              ('mixed_scope_control', (target[0], other))):
            state, sources = pack(case, pair)
            allowed, exact, decision, outcomes = faithful_possibilities(
                case, state, sources, reference)
            rows.append({
                'stress_id': case['id'] + '/' + packing,
                'source_id': case['id'], 'parent': case['parent'],
                'family': case['family'], 'variant': case['variant'],
                'source_split': 'development', 'representation': 'derived_line_packing',
                'packing': packing, 'state': state, 'policy': case['instruction'],
                'program_gold': case['gold'], 'program_reference_facts': reference,
                'line_source_indexes': sources, 'faithful_route_options': allowed,
                'faithful_exact_fact_vector_reachable': exact,
                'faithful_gold_decision_reachable': decision,
                'faithful_possible_decisions': outcomes,
                'model_scored': False, 'independent_human_reviewed': False})
    if (len(rows) != 112 or len({r['stress_id'] for r in rows}) != 112 or
            len({r['source_id'] for r in rows}) != 56 or
            len({r['parent'] for r in rows}) != 12 or
            Counter(r['packing'] for r in rows) !=
            {'cross_field': 56, 'mixed_scope_control': 56}):
        raise ValueError('Paired stress grid drift')
    by_packing = {}
    for packing in ('cross_field', 'mixed_scope_control'):
        subset = [r for r in rows if r['packing'] == packing]
        by_packing[packing] = {
            'items': len(subset),
            'exact_fact_vector_reachable': sum(
                r['faithful_exact_fact_vector_reachable'] for r in subset),
            'gold_decision_reachable': sum(
                r['faithful_gold_decision_reachable'] for r in subset)}
    if by_packing['mixed_scope_control']['exact_fact_vector_reachable'] != 56:
        raise ValueError('Mixed-scope software control unexpectedly loses facts')
    summary = {
        'status': 'software_only_program_reference_not_model_evaluation',
        'original_development_sources': 56, 'paired_derived_items': len(rows),
        'parent_clusters': 12, 'independent_new_examples': 0,
        'model_forwards': 0, 'independent_human_annotations': 0,
        'by_packing': by_packing,
        'interpretation': ('Reachability allows only a constituent record label per '
                           'packed line. It measures this exclusive interface with '
                           'perfect semantic routing, not model accuracy or language transfer.')}
    return rows, summary


def artifacts():
    rows, summary = build()
    return ((OUT, ''.join(json.dumps(r, ensure_ascii=False, allow_nan=False) + '\n'
                          for r in rows)),
            (SUMMARY, json.dumps(summary, ensure_ascii=False, indent=2) + '\n'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('build', 'verify'))
    args = parser.parse_args()
    for path, payload in artifacts():
        encoded = payload.encode('utf-8')
        if args.command == 'verify':
            if path.read_bytes().replace(b'\r\n', b'\n') != encoded:
                raise ValueError(f'Derived line-packing artifact drift: {path.name}')
        elif path.exists() and path.read_bytes().replace(b'\r\n', b'\n') != encoded:
            raise ValueError(f'Preserve existing line-packing artifact: {path.name}')
        elif not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(encoded)
    print(json.dumps({'status': 'verified' if args.command == 'verify' else 'built',
                      'model_forwards': 0, 'paired_items': 112}))


if __name__ == '__main__':
    main()
