"""Build/verify the complete offline line-evidence case explorer from raw records."""
import argparse
import json

from data_tools import HERE, original_cases
from line_analyze import analyze
from line_evidence import visible_lines
from line_run import OUT

TEMPLATE = HERE / 'line_explorer_template.html'
DEST = HERE / 'docs/line_explorer.html'


def payload():
    summary, decisions, claims = analyze()
    raw = [json.loads(line) for line in (OUT / 'N1.jsonl').read_text(encoding='utf-8').splitlines()]
    pred = {(r['source_id'], r['field'], r['line_index']): r['prediction'] for r in raw}
    by_decision = {r['source_id']: r for r in decisions}
    by_claim = {(r['source_id'], r['field']): r for r in claims}
    cases = []
    for case in original_cases():
        decision = by_decision[case['id']]
        fields = []
        names = list(decision['facts'])
        for field in names:
            claim = by_claim[(case['id'], field)]
            lines = []
            for line, record in zip(visible_lines(case['state']), case['records']):
                model = pred[(case['id'], field, line['line_index'])]
                reference = ('IRRELEVANT' if record['scope'] != case['target'] or
                             record['field'] != field else
                             'POSITIVE' if record['value'] else 'NEGATIVE')
                error = ('other_request' if model != 'IRRELEVANT' and
                         record['scope'] != case['target'] else
                         'other_field' if model != 'IRRELEVANT' and
                         record['field'] != field else
                         'opposite_value' if model != 'IRRELEVANT' and model != reference else
                         'missed_relevant' if model == 'IRRELEVANT' and reference != 'IRRELEVANT' else
                         'correct_line_choice')
                lines.append({'index': line['line_index'] + 1, 'text': line['text'],
                              'model': model, 'construction_reference': reference,
                              'error': error})
            fields.append({'name': field, 'predicted_status': claim['status'],
                           'reference_status': claim['reference_status'],
                           'audit_gate': claim['known_grammar_audit']['gate'],
                           'audit_reason': claim['known_grammar_audit']['reason'],
                           'lines': lines})
        cases.append({'id': case['id'], 'parent': case['parent'],
                      'family': case['family'], 'variant': case['variant'],
                      'state': case['state'], 'policy': case['instruction'],
                      'gold': decision['gold'], 'prediction': decision['prediction'],
                      'correct': decision['correct'], 'model_calls': decision['model_calls'],
                      'input_tokens': decision['input_tokens'], 'fields': fields})
    if len(cases) != 72 or sum(len(f['lines']) for c in cases for f in c['fields']) != 548:
        raise ValueError('Explorer does not cover the complete scored grid')
    errors = {kind: sum(line['error'] == kind for c in cases for f in c['fields']
                        for line in f['lines']) for kind in
              ('other_request', 'other_field', 'opposite_value')}
    if errors != {'other_request': 73, 'other_field': 172, 'opposite_value': 4}:
        raise ValueError('Explorer error categories disagree with verified result')
    selected = sum(line['model'] != 'IRRELEVANT' for c in cases for f in c['fields']
                   for line in f['lines'])
    if selected != 407:
        raise ValueError('Explorer selected-line denominator drift')
    return {'summary': summary, 'cases': cases,
            'default_case': 'joint_approval-1-decisive_missing',
            'selected_line_judgments': selected,
            'source': 'saved N1/native primary-order forwards; program-derived construction references'}


def render():
    data = json.dumps(payload(), ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')
    template = TEMPLATE.read_text(encoding='utf-8')
    if template.count('__LINE_DATA__') != 1:
        raise ValueError('Explorer template data slot drift')
    return template.replace('__LINE_DATA__', data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    page = render().encode('utf-8')
    if args.verify:
        if DEST.read_bytes().replace(b'\r\n', b'\n') != page:
            raise ValueError('Line explorer drift')
    else:
        DEST.parent.mkdir(exist_ok=True)
        if DEST.exists() and DEST.read_bytes().replace(b'\r\n', b'\n') != page:
            raise ValueError('Preserve existing explorer; update intentionally')
        if not DEST.exists():
            DEST.write_bytes(page)
    print(json.dumps({'status': 'verified' if args.verify else 'built',
                      'inputs': 72, 'line_field_queries': 548,
                      'new_model_forwards': 0}))
