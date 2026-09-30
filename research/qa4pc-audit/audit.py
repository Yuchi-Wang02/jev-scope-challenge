"""Audit pinned QA4PC development joins and three-valued graph composition.

Only original audit code runs. Source data stays in an explicitly supplied cache.
No eval, model, generated source repair, or independent semantic adjudication.
"""
import argparse
import ast
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import urllib.request

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REVISION = '2b1de7c5e588ec70afa1e753394ae25531e0d182'
BASE = f'https://huggingface.co/datasets/Marzipan/QA4PC/resolve/{REVISION}/'
PINS = {
    'trees_dev_test_qa4pc.json': ('04bf52c38d7ed98d2c926547046c37027749962755d8260c0960cac62f8e8b62', 115320),
    'dev_entailment_qa4pc.json': ('a50fa03a1abe60f385e2ba28cca12c5bf42678f938a294fd7ca9211ada7c4707', 257782),
    'dev_qa_qa4pc.json': ('326be6d53018777528455bda616f9fe5b82d8a0569259118c1f1098df7a37d60', 581381),
}
VALUES = {'no': -1, 'maybe': 0, 'yes': 1}
LABELS = {v: k for k, v in VALUES.items()}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


def parse_logic(text):
    if not isinstance(text, str) or len(text) > 10000:
        raise ValueError('Invalid logic text')
    normalized = re.sub(r'\b(AND|OR|NOT)\b', lambda m: m[0].lower(), text).strip()
    try:
        tree = ast.parse(normalized, mode='eval')
    except (SyntaxError, RecursionError) as error:
        raise ValueError('Unparseable logic') from error
    for node in ast.walk(tree):
        if type(node) not in (ast.Expression, ast.Name, ast.Load, ast.BoolOp, ast.And, ast.Or, ast.UnaryOp, ast.Not):
            raise ValueError('Unsupported expression node')
        if isinstance(node, ast.Name) and not re.fullmatch(r'Q[0-9]+', node.id):
            raise ValueError('Unsupported variable')
    return tree.body


def variables(tree):
    return {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}


def execute(tree, facts):
    """Strong Kleene AND/OR/NOT; absent variables are errors, never Maybe."""
    if variables(tree) - facts.keys():
        raise ValueError('Missing formula variable')
    if any(v not in VALUES for v in facts.values()):
        raise ValueError('Unknown fact label')

    def visit(node):
        if isinstance(node, ast.Name):
            return VALUES[facts[node.id]]
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            return -visit(node.operand)
        if isinstance(node, ast.BoolOp) and isinstance(node.op, (ast.And, ast.Or)):
            values = [visit(v) for v in node.values]
            return (min if isinstance(node.op, ast.And) else max)(values)
        raise ValueError('Unsupported expression node')

    return LABELS[visit(tree)]


def index(rows, keys, fields):
    result = {}
    for row in rows:
        if set(row) != set(fields):
            raise ValueError('Source schema changed')
        key = tuple(row[k] for k in keys)
        if key in result:
            raise ValueError('Duplicate join key')
        result[key] = row
    return result


def inspect(trees, entailments, questions, prior=None):
    tree_index = index(trees, ('tree_id',), ('tree_id', 'question', 'logic', 'difficult', 'questions', 'policy'))
    ent_index = index(entailments, ('tree_id', 'utterance_id'), ('answer', 'policy', 'question', 'scenario', 'tree_id', 'utterance_id'))
    qa_index = index(questions, ('tree_id', 'utterance_id', 'question_id'), ('answer', 'question', 'question_id', 'scenario', 'set_id', 'tree_id', 'utterance_id'))
    if len({x['utterance_id'] for x in entailments}) != len(entailments):
        raise ValueError('Utterance ID occurs in multiple trees')
    if len({x['set_id'] for x in questions}) != len(questions):
        raise ValueError('Duplicate question-row set_id')
    if any(x['answer'] not in VALUES for x in [*entailments, *questions]):
        raise ValueError('Unknown source label')
    grouped = defaultdict(dict)
    for (tid, uid, qid), row in qa_index.items():
        grouped[(tid, uid)][qid] = row
    if grouped.keys() != ent_index.keys():
        raise ValueError('Unmatched scenario groups')
    if {k[0] for k in ent_index} - {k[0] for k in tree_index}:
        raise ValueError('Unmatched tree IDs')
    parsed = {}; issues = []; shape_counts = Counter(); normalized_count = 0
    dev_counts = Counter(x['tree_id'] for x in entailments)
    for (tid,), row in sorted(tree_index.items()):
        if not isinstance(row['questions'], dict) or not row['questions'] or any(not re.fullmatch(r'Q[0-9]+', k) for k in row['questions']):
            raise ValueError('Invalid question inventory')
        graph = parse_logic(row['logic']); parsed[tid] = graph
        normalized_count += re.sub(r'\b(AND|OR|NOT)\b', lambda m: m[0].lower(), row['logic']).strip() != row['logic']
        shape_counts.update(type(n).__name__ for n in ast.walk(graph) if not isinstance(n, ast.Load))
        refs = variables(graph); inventory = set(row['questions'])
        if refs != inventory:
            issues.append({'tree_id': tid, 'missing_variables': sorted(refs - inventory),
                'unused_questions': sorted(inventory - refs), 'dev_scenarios': dev_counts[tid],
                'logic_sha256': digest(row['logic'].encode('utf-8'))})
    unavailable = []; mismatches = []; evaluable_ids = []; groups = defaultdict(list)
    final_counts = Counter(); recomputed_counts = Counter()
    for (tid, uid), ent in sorted(ent_index.items()):
        tree = tree_index[(tid,)]; facts = grouped[(tid, uid)]
        if ent['policy'] != tree['policy'] or ent['question'] != tree['question']:
            raise ValueError('Entailment/tree text mismatch')
        if facts.keys() != tree['questions'].keys():
            raise ValueError('Scenario/question inventory mismatch')
        for qid, row in facts.items():
            if row['question'] != tree['questions'][qid] or row['scenario'] != ent['scenario']:
                raise ValueError('QA text mismatch')
        visible_hash = digest(encoded({k: ent[k] for k in ('policy', 'question', 'scenario')}))
        groups[visible_hash].append({'tree_id': tid, 'utterance_id': uid, 'label': ent['answer']})
        missing = sorted(variables(parsed[tid]) - facts.keys())
        if missing:
            unavailable.append({'tree_id': tid, 'utterance_id': uid, 'missing_variables': missing})
            continue
        computed = execute(parsed[tid], {k: v['answer'] for k, v in facts.items()})
        final_counts[ent['answer']] += 1; recomputed_counts[computed] += 1
        evaluable_ids.append(uid)
        if computed != ent['answer']:
            mismatches.append({'tree_id': tid, 'utterance_id': uid, 'composed': computed, 'released': ent['answer']})
    overlaps = {}
    dev_trees = set(dev_counts); dev_ids = {k[1] for k in ent_index}
    for name, (seen_trees, seen_ids) in (prior or {}).items():
        overlaps[name] = {'tree_ids': sorted(dev_trees & set(seen_trees)),
            'utterance_ids': sorted(dev_ids & set(seen_ids)),
            'dev_scenarios_on_shared_trees': sum(dev_counts[t] for t in dev_trees & set(seen_trees))}
    conflicts = [{'visible_sha256': h, 'members': members} for h, members in sorted(groups.items()) if len({m['label'] for m in members}) > 1]
    return {
        'status': 'structural source audit; not model evaluation or semantic validation',
        'shared_dev_test_trees_inspected': len(trees), 'dev_trees': len(dev_trees),
        'dev_scenarios': len(entailments), 'dev_question_rows': len(questions),
        'unique_set_ids': len({r['set_id'] for r in questions}),
        'source_label_counts': dict(sorted(Counter(r['answer'] for r in entailments).items())),
        'fact_label_counts': dict(sorted(Counter(r['answer'] for r in questions).items())),
        'formula_representation_normalizations': normalized_count,
        'formula_node_counts': dict(sorted(shape_counts.items())), 'graph_inventory_issues': issues,
        'all_join_text_and_inventory_checks_passed': True,
        'evaluable_scenarios': len(evaluable_ids), 'evaluable_trees': len(dev_trees - {x['tree_id'] for x in unavailable}),
        'evaluable_utterance_ids_sha256': digest(encoded(sorted(evaluable_ids))),
        'evaluable_released_label_counts': dict(sorted(final_counts.items())),
        'composed_label_counts': dict(sorted(recomputed_counts.items())),
        'composition_mismatches': mismatches, 'unavailable_scenarios': unavailable,
        'distinct_direct_visible_inputs': len(groups), 'direct_visible_label_conflicts': conflicts,
        'overlap_with_inspected_materials': overlaps,
        'test_scenarios_loaded': False, 'test_shared_graphs_inspected': True,
        'model_calls': 0, 'new_human_labels': 0, 'source_labels_modified': False,
        'upstream_code_executed': False,
    }


def files(directory, fetch=False):
    values = []
    for name, (expected, size) in PINS.items():
        path = directory / name
        if fetch and not path.exists():
            with urllib.request.urlopen(BASE + name, timeout=30) as response:
                raw = response.read(size + 1)
            if len(raw) != size or digest(raw) != expected:
                raise ValueError('Upstream download differs from pin')
            directory.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
        raw = path.read_bytes()
        if len(raw) != size or digest(raw) != expected:
            raise ValueError('Local source differs from pin')
        values.append(json.loads(raw))
    return values


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('fetch', 'build', 'verify'))
    parser.add_argument('--source-dir', type=Path, required=True)
    args = parser.parse_args()
    trees, ent, qa = files(args.source_dir, args.command == 'fetch')
    prior_paths = {'source_screen': ROOT / 'research/source-label-screen/selection.json',
                   'extra': ROOT / 'research/implementation-audit/extra_release_audit.json'}
    screen = json.loads(prior_paths['source_screen'].read_bytes())['selected']
    extra = json.loads(prior_paths['extra'].read_bytes())['pair_records']
    prior = {'source_screen': ([p['tree_id'] for p in screen], [r['utterance_id'] for p in screen for r in p['rows']]),
             'extra': ([p['tree_id'] for p in extra], [p['utterance_id'] for p in extra])}
    report = inspect(trees, ent, qa, prior)
    report['source'] = {'repository': 'Marzipan/QA4PC', 'revision': REVISION,
        'files': {k: {'sha256': v[0], 'bytes': v[1], 'url': BASE + k} for k, v in PINS.items()},
        'prior_material_lf_sha256': {k: digest(p.read_bytes().replace(b'\r\n', b'\n')) for k, p in prior_paths.items()}}
    raw = (json.dumps(report, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    output = HERE / 'report.json'
    if args.command == 'build': output.write_bytes(raw)
    if args.command == 'verify' and output.read_bytes().replace(b'\r\n', b'\n') != raw:
        raise ValueError('Audit report differs from source')
    print(json.dumps({k: report[k] for k in ('dev_trees', 'dev_scenarios', 'evaluable_scenarios', 'composition_mismatches', 'graph_inventory_issues', 'overlap_with_inspected_materials')}))


if __name__ == '__main__': main()
