"""Select a bounded QA4PC development cohort before model execution.

No model prompts or predictions. Pending review queue IDs are used only to
exclude whole trees and are not exported as a queue-to-source mapping.
"""
import argparse
from collections import Counter, defaultdict
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
STUDY = 'qa4pc-stage-attribution-dev-v1'
spec = importlib.util.spec_from_file_location('qa4pc_source_audit', ROOT / 'research/qa4pc-audit/audit.py')
audit = importlib.util.module_from_spec(spec); spec.loader.exec_module(audit)


def rank(*parts):
    return audit.digest(audit.encoded([STUDY, *parts]))


def choose(trees, scenarios, exclusions, n_trees=12, per_tree=2):
    """Hash rank ignores labels, question counts, difficulty and all predictions."""
    if n_trees <= 0 or per_tree <= 0:
        raise ValueError('Selection sizes must be positive')
    tree_map = {x['tree_id']: x for x in trees}
    if len(tree_map) != len(trees): raise ValueError('Duplicate trees')
    if len({x['utterance_id'] for x in scenarios}) != len(scenarios):
        raise ValueError('Duplicate scenario IDs')
    grouped = defaultdict(list)
    for row in scenarios:
        if row['tree_id'] not in tree_map: raise ValueError('Missing tree')
        grouped[row['tree_id']].append(row)
    blocked = set().union(*[set(v) for v in exclusions.values()])
    eligible = [tid for tid, rows in grouped.items() if tid not in blocked and len(rows) >= per_tree]
    ordered = sorted(eligible, key=lambda tid: (rank('tree', tid), tid))
    if len(ordered) < n_trees: raise ValueError('Insufficient trees; do not relax exclusions')
    selected = []; used_policies = set()
    for tid in ordered:
        policy = tree_map[tid]['policy']
        if policy in used_policies: raise ValueError('Duplicate policy text requires explicit grouping')
        used_policies.add(policy)
    for tid in ordered[:n_trees]:
        rows = sorted(grouped[tid], key=lambda r: (rank('scenario', r['utterance_id']), r['utterance_id']))[:per_tree]
        selected.append({'tree_id': tid, 'tree_rank': rank('tree', tid),
            'question_ids': sorted(tree_map[tid]['questions']),
            'scenarios': [{'utterance_id': r['utterance_id'],
                'scenario_rank': rank('scenario', r['utterance_id']),
                'direct_visible_sha256': audit.digest(audit.encoded({k: r[k] for k in ('policy', 'question', 'scenario')}))}
                for r in rows]})
    selected_ids = {r['utterance_id'] for t in selected for r in t['scenarios']}
    return {'study': STUDY, 'status': 'selected before inference; prompts and runner not frozen',
        'selection_rule': f'Exclude whole blocked trees; SHA-256 rank trees then scenarios; first {n_trees} trees and first {per_tree} scenarios per tree; no label stratification.',
        'dev_trees': len(grouped), 'dev_scenarios': len(scenarios),
        'exclusions': {name: {'dev_trees': len(set(ids) & grouped.keys()),
            'dev_scenarios': sum(len(grouped[t]) for t in set(ids) & grouped.keys())}
            for name, ids in exclusions.items()},
        'excluded_union_trees': len(blocked & grouped.keys()),
        'excluded_union_scenarios': sum(len(grouped[t]) for t in blocked & grouped.keys()),
        'insufficient_scenario_trees': sum(tid not in blocked and len(rows) < per_tree for tid, rows in grouped.items()),
        'eligible_trees': len(eligible),
        'eligible_tree_ids_sha256': audit.digest(audit.encoded(sorted(eligible))),
        'selected_trees': len(selected), 'selected_scenarios': len(selected_ids),
        'selected_question_decisions_per_model_mapping': sum(len(t['question_ids'])*len(t['scenarios']) for t in selected),
        'selected_label_counts': dict(sorted(Counter(r['answer'] for r in scenarios if r['utterance_id'] in selected_ids).items())),
        'selected': selected, 'model_calls': 0, 'new_human_labels': 0,
        'paired_counterfactuals': False, 'label_stratified': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('build', 'verify'))
    parser.add_argument('--source-dir', type=Path, required=True)
    args = parser.parse_args()
    trees, ent, qa = audit.files(args.source_dir)
    source_audit = audit.inspect(trees, ent, qa)
    if source_audit['composition_mismatches'] or source_audit['direct_visible_label_conflicts']:
        raise ValueError('Source consistency gate failed')
    sys.path.insert(0, str(ROOT / 'research/external-validation'))
    import prepare_sharc_review as review
    manifest, _, _, queued = review.prepare_with_selection()
    review.verify_manifest(manifest)
    screen_path = ROOT / 'research/source-label-screen/selection.json'
    extra_path = ROOT / 'research/implementation-audit/extra_release_audit.json'
    screen = json.loads(screen_path.read_bytes())['selected']
    extra = json.loads(extra_path.read_bytes())['pair_records']
    exclusions = {'incomplete_graph': {x['tree_id'] for x in source_audit['unavailable_scenarios']},
        'prior_source_screen': {x['tree_id'] for x in screen},
        'inspected_extra': {x['tree_id'] for x in extra},
        'pending_training_review_queue': {x['tree_id'] for x in queued}}
    report = choose(trees, ent, exclusions)
    selected_ids = {r['utterance_id'] for t in report['selected'] for r in t['scenarios']}
    queue_ids = {i for row in queued for i in row['ids']}
    if selected_ids & queue_ids: raise ValueError('Selected scenario overlaps pending queue')
    report['queue_overlap_check'] = {'dev_shared_trees': len(exclusions['pending_training_review_queue'] & {r['tree_id'] for r in ent}),
        'dev_shared_utterance_ids': len(queue_ids & {r['utterance_id'] for r in ent}),
        'selected_shared_trees': 0, 'selected_shared_utterance_ids': 0,
        'queue_selection_sha256': manifest['selection_sha256'], 'queue_labels_or_predictions_exported': False}
    paths = [Path(__file__), ROOT / 'research/qa4pc-audit/audit.py', screen_path, extra_path,
             ROOT / 'research/external-validation/sharc_review_manifest.json',
             ROOT / 'research/external-validation/prepare_sharc_review.py',
             ROOT / 'research/external-validation/inspect_sharc_pairs.py',
             ROOT / 'research/external-validation/inspect_sharc.py']
    report['source'] = {'qa4pc_revision': audit.REVISION,
        'qa4pc_file_sha256': {k: v[0] for k,v in audit.PINS.items()},
        'sharc_archive_sha256': manifest['official_archive_sha256'],
        'local_dependency_lf_sha256': {p.relative_to(ROOT).as_posix(): audit.digest(p.read_bytes().replace(b'\r\n', b'\n')) for p in paths}}
    raw = (json.dumps(report, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    output = HERE / 'cohort.json'
    if args.command == 'build': output.write_bytes(raw)
    elif output.read_bytes().replace(b'\r\n', b'\n') != raw:
        raise ValueError('Cohort manifest drift')
    print(json.dumps({k: report[k] for k in ('exclusions', 'excluded_union_trees', 'eligible_trees', 'selected_trees', 'selected_scenarios', 'selected_question_decisions_per_model_mapping', 'selected_label_counts', 'queue_overlap_check')}))


if __name__ == '__main__': main()
