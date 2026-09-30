"""Build a self-contained replay from the published, verified screen evidence."""
import argparse
import json
from pathlib import Path

import report
from screen import HERE, ROOT, rank
from comparison_plan import visible_state
from execution_journal import read_events

OUTPUT = ROOT / 'docs/source_label_screen.html'


def payload():
    _, plan, refs = report.frozen_inputs()
    comparison = report.load('results/comparison.json')
    api = {r['job_id']: r for r in report.load('results/jev_audit.json')['records']}
    local = {e['job_id']: e['result'] for e in read_events(HERE / 'results/qwen.jsonl')
             if e['event'] == 'call_finish'}
    pairs = {p['pair_id']: p for p in report.load('selection.json')['selected']}
    jobs = {j['id']: j for j in plan['jobs']}
    output = []
    for ref in refs:
        pair = pairs[ref['pair_id']]
        items = []
        for ident, source, action in zip(ref['item_ids'], pair['rows'], ref['reference_actions']):
            if ident != rank('item', pair['tree_id'], str(source['utterance_id']))[:24]:
                raise ValueError('Source row and item identity differ')
            views = []
            for order in (0, 1):
                key = f'{ident}_jev_order{order}'
                a = api[key]
                view = {'options': jobs[key]['options'], 'jev': a, 'local': {}}
                for mode in ('direct', 'thinking'):
                    key = f'{ident}_qwen_{mode}_order{order}'
                    r = local.get(key)
                    if r is None:
                        view['local'][mode] = {'state': 'No recorded result', 'action': None}
                    else:
                        adapted = r.get('detail', {}).get('adapted', {})
                        view['local'][mode] = {'state': r['status'], 'action': r['action'],
                            'completion': adapted.get('completion'), 'final_text': adapted.get('final_text'),
                            'boundary_error': adapted.get('boundary_error'),
                            'output_tokens': r['output_tokens'], 'latency_seconds': r['latency_seconds']}
                views.append(view)
            items.append({'id': ident, 'state': visible_state(source), 'source_action': action,
                          'views': views})
        output.append({'id': ref['pair_id'], 'group': pair['group'], 'items': items})
    return {'pairs': output, 'comparison': comparison}


def render(data):
    # Source strings are inert JSON, then assigned through textContent, never HTML.
    encoded = json.dumps(data, ensure_ascii=True, separators=(',', ':')).replace('<', '\\u003c')
    template = (HERE / 'replay_template.html').read_text(encoding='utf-8')
    if template.count('__EVIDENCE_JSON__') != 1:
        raise ValueError('Expected one evidence placeholder')
    return template.replace('__EVIDENCE_JSON__', encoded).encode()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    data = payload()
    page = render(data)
    if args.verify:
        if OUTPUT.read_bytes().replace(b'\r\n', b'\n') != page:
            raise ValueError('Replay differs from published evidence')
    else:
        OUTPUT.write_bytes(page)
    print(json.dumps({'pairs': len(data['pairs']), 'items': sum(len(p['items']) for p in data['pairs']),
                      'new_model_calls': 0, 'output': str(OUTPUT)}))
