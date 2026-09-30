"""Build/verify a prepared-input explorer without reading model predictions."""
import argparse
import importlib.util
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / 'research/request-ownership'
TEMPLATE = ROOT / 'docs/request_switch_template.html'
OUTPUT = ROOT / 'docs/request_switch.html'
MARKER = '__REQUEST_SWITCH_DATA__'
DEFINITION = importlib.util.spec_from_file_location('ownership_execution_explorer', STUDY / 'execution.py')
execution = importlib.util.module_from_spec(DEFINITION)
DEFINITION.loader.exec_module(execution)
preparation = execution.load_preparation()
from scope_gate import gate_line


def read_rows(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]


def payload():
    """Expose visible inputs and independently recomputed program references only."""
    manifest = execution.verify_frozen()
    views = read_rows(STUDY / 'data/views.jsonl')
    scenes = read_rows(STUDY / 'data/scenes.jsonl')
    queries = read_rows(execution.ENCODED)
    parents = {scene['parent'] for scene in scenes}
    view_ids = {view['view_id'] for view in views}
    if (len(scenes) != 24 or len(parents) != 24 or len(views) != 48 or len(view_ids) != 48
            or {view['parent'] for view in views} != parents
            or len(queries) != 500 or len({row['query_id'] for row in queries}) != 500
            or {row['view_id'] for row in queries} != view_ids
            or Counter(row['arm'] for row in queries) != {'joint_full': 200, 'direct_full': 200, 'direct_filtered': 100}
            or sum(row['input_tokens'] for row in queries) != 188797
            or manifest['scientific_forwards'] != 500 or manifest['planned_input_tokens'] != 188797):
        raise ValueError('Prepared explorer scope or budget drift')
    output = []
    gate_counts = Counter()
    references = Counter()
    for scene in scenes:
        pair = sorted((view for view in views if view['parent'] == scene['parent']),
                      key=lambda view: view['target_slot'])
        if (len(pair) != 2 or {view['target_slot'] for view in pair} != {0, 1}
                or pair[0]['state'].partition('\n')[2] != pair[1]['state'].partition('\n')[2]
                or pair[0]['policy'] != pair[1]['policy']
                or any(view[key] != scene[key] for view in pair for key in ('family', 'id_relation', 'pair_kind'))):
            raise ValueError('Target-switch pair evidence or metadata drift')
        shown_views = []
        for view in pair:
            schema = preparation.compile_visible(view['state'], view['policy'])
            if schema['policy_id'] != scene['family']:
                raise ValueError('Displayed policy family differs from scene')
            parsed = preparation.parse_text(view['state'], view['policy'], scene['family'], scene['sites'])
            reference, _ = preparation.world_truth(parsed)
            if reference != preparation.direct_truth(parsed):
                raise ValueError('Displayed-text program solvers disagree')
            # Reference is computed above; prepared gold and construction records are not consulted.
            references[reference] += 1
            header = view['state'].splitlines()[0]
            lines = []
            for line in preparation.visible_lines(view['state']):
                gate = gate_line(header, line['text'])
                if gate['status'] not in ('KEEP', 'DROP') or gate['target_id'] != schema['target']:
                    raise ValueError('Unexpected prepared visible-ID gate result')
                gate_counts[gate['status']] += 1
                lines.append({'line_index': line['line_index'], 'text': line['text'],
                              'status': gate['status'], 'owner_id': gate['owner_id']})
            selected = [row for row in queries if row['view_id'] == view['view_id']]
            expected = {'joint_full': len(lines), 'direct_full': len(lines),
                        'direct_filtered': sum(line['status'] == 'KEEP' for line in lines)}
            if Counter(row['arm'] for row in selected) != expected:
                raise ValueError('Prepared per-view query coverage drift')
            if any(row['parent'] != scene['parent'] or row['input_tokens'] != len(row['token_ids'])
                   or row['split'] != 'new_scene_development'
                   or row['representation'] != 'new_scene_original_declared_grammar' for row in selected):
                raise ValueError('Prepared query identity, encoding or scope drift')
            shown_views.append({'view_id': view['view_id'], 'target': schema['target'],
                                'state': view['state'], 'policy': view['policy'],
                                'program_reference': reference, 'lines': lines,
                                'queries': [{key: row[key] for key in ('query_id', 'arm', 'mapping', 'line_index',
                                                                      'order', 'prompt', 'input_tokens')}
                                            for row in selected]})
        if (len({view['target'] for view in shown_views}) != 2
                or len({view['program_reference'] for view in shown_views}) != 2):
            raise ValueError('Target switch must change target and program action')
        output.append({key: scene[key] for key in ('parent', 'family', 'id_relation', 'pair_kind')}
                      | {'views': shown_views})
    if gate_counts != {'KEEP': 100, 'DROP': 100} or references != {'ALLOW': 18, 'DENY': 18, 'INSUFFICIENT': 12}:
        raise ValueError('Prepared gate or program-reference denominator drift')
    return {'status': 'prepared_inputs_and_program_references_only', 'config_hash': manifest['config_hash'],
            'scientific_forwards': 500, 'scientific_input_tokens': 188797,
            'parent_pairs': 24, 'views': 48, 'scenes': output}


def render(template=None, data=None):
    """Optional arguments are for in-memory template/escaping tests only."""
    if template is None:
        template = TEMPLATE.read_text(encoding='utf-8')
    if template.count(MARKER) != 1:
        raise ValueError('Expected exactly one request-switch data marker')
    encoded = json.dumps(payload() if data is None else data, ensure_ascii=False,
                         separators=(',', ':'), allow_nan=False)
    encoded = encoded.replace('<', '\\u003c').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
    return template.replace(MARKER, encoded).encode('utf-8')


def run(command):
    if command not in ('build', 'verify'):
        raise ValueError('Expected build or verify')
    content = render()
    if command == 'build':
        OUTPUT.write_bytes(content)
    elif OUTPUT.read_bytes() != content:
        raise ValueError('Published request-switch explorer differs from frozen inputs/template')
    return {'status': command, 'parent_pairs': 24, 'views': 48, 'planned_queries': 500,
            'model_outputs_read': 0, 'model_calls': 0, 'output': str(OUTPUT)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('build', 'verify'))
    print(json.dumps(run(parser.parse_args().command), indent=2))
