"""Select fresh policy clusters; no inference and no selection by label/output."""
import argparse
from collections import Counter, defaultdict
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
STUDY = 'qa4pc-answer-interface-dev-v1'
spec = importlib.util.spec_from_file_location('interface_source_audit', ROOT/'research/qa4pc-audit/audit.py')
audit = importlib.util.module_from_spec(spec); spec.loader.exec_module(audit)


def readable(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def lfhash(path):
    return audit.digest(Path(path).read_bytes().replace(b'\r\n', b'\n'))


def choose(trees, rows, exclusions, count=12, per_tree=2):
    # Same established hash-selection approach as stage-attribution/cohort.py,
    # with a new study salt and whole-tree exclusion of that completed cohort.
    if count <= 0 or per_tree <= 0: raise ValueError('Invalid selection size')
    tm = {t['tree_id']:t for t in trees}
    if len(tm) != len(trees): raise ValueError('Duplicate tree')
    if len({r['utterance_id'] for r in rows}) != len(rows): raise ValueError('Duplicate scenario')
    grouped = defaultdict(list)
    for r in rows:
        if r['tree_id'] not in tm: raise ValueError('Missing tree')
        if r['policy'] != tm[r['tree_id']]['policy']: raise ValueError('Policy join mismatch')
        grouped[r['tree_id']].append(r)
    blocked = set().union(*exclusions.values())
    eligible = [t for t in grouped if t not in blocked and len(grouped[t]) >= per_tree]
    if len({tm[t]['policy'] for t in eligible}) != len(eligible): raise ValueError('Repeated policy')
    if len(eligible) < count: raise ValueError('Insufficient eligible trees')
    def rank(kind, ident): return audit.digest(audit.encoded([STUDY, kind, ident]))
    selected = []
    for tid in sorted(eligible, key=lambda t:(rank('tree',t),t))[:count]:
        scenarios = sorted(grouped[tid], key=lambda r:(rank('scenario',r['utterance_id']),r['utterance_id']))[:per_tree]
        selected.append({'tree_id':tid, 'tree_rank':rank('tree',tid), 'scenarios':[
            {'utterance_id':r['utterance_id'], 'scenario_rank':rank('scenario',r['utterance_id']),
             'direct_visible_sha256':audit.digest(audit.encoded({k:r[k] for k in ('policy','question','scenario')}))}
            for r in scenarios]})
    selected_ids = {r['utterance_id'] for t in selected for r in t['scenarios']}
    return {'study':STUDY, 'status':'selected before new model inference',
        'selection_rule':'Whole-tree exclusions, study-salted SHA256 tree rank, then scenario rank; no label or output selection.',
        'dev_trees':len(grouped), 'dev_scenarios':len(rows),
        'exclusions':{k:{'trees':len(v & grouped.keys()), 'scenarios':sum(len(grouped[t]) for t in v & grouped.keys())} for k,v in exclusions.items()},
        'excluded_union_trees':len(blocked & grouped.keys()),
        'excluded_union_scenarios':sum(len(grouped[t]) for t in blocked & grouped.keys()),
        'eligible_trees':len(eligible), 'eligible_tree_ids_sha256':audit.digest(audit.encoded(sorted(eligible))),
        'selected_trees':len(selected), 'selected_scenarios':len(selected_ids),
        'selected_label_counts':dict(sorted(Counter(r['answer'] for r in rows if r['utterance_id'] in selected_ids).items())),
        'selected':selected, 'model_calls_at_selection':0, 'project_human_labels':0,
        'claim': 'Disjoint policy IDs from prior project model cohorts and pending review queue; not unseen policies, training-contamination freedom, or independent semantic confirmation.'}


def build(source_dir):
    trees, rows, qa = audit.files(source_dir)
    inspected = audit.inspect(trees, rows, qa)
    if inspected['composition_mismatches'] or inspected['direct_visible_label_conflicts']:
        raise ValueError('Source consistency failed')
    sys.path.insert(0, str(ROOT/'research/external-validation'))
    import prepare_sharc_review as review
    manifest, _, _, queue = review.prepare_with_selection()
    review.verify_manifest(manifest)
    paths = {'prior_source_screen':'research/source-label-screen/selection.json',
             'inspected_extra':'research/implementation-audit/extra_release_audit.json',
             'prior_stage_attribution':'research/qa4pc-stage-attribution/cohort.json'}
    saved = {k:json.loads((ROOT/v).read_bytes()) for k,v in paths.items()}
    exclusions = {'incomplete_graph':{r['tree_id'] for r in inspected['unavailable_scenarios']},
        'pending_training_review_queue':{r['tree_id'] for r in queue},
        'prior_source_screen':{r['tree_id'] for r in saved['prior_source_screen']['selected']},
        'inspected_extra':{r['tree_id'] for r in saved['inspected_extra']['pair_records']},
        'prior_stage_attribution':{r['tree_id'] for r in saved['prior_stage_attribution']['selected']}}
    report = choose(trees, rows, exclusions)
    prior_ids = {r['utterance_id'] for t in saved['prior_stage_attribution']['selected'] for r in t['scenarios']}
    queue_ids = {i for r in queue for i in r['ids']}
    chosen_ids = {r['utterance_id'] for t in report['selected'] for r in t['scenarios']}
    if chosen_ids & (prior_ids | queue_ids): raise ValueError('Forbidden scenario overlap')
    dependencies = [Path(__file__), ROOT/'research/qa4pc-audit/audit.py',
        *[ROOT/v for v in paths.values()], *[ROOT/'research/external-validation'/n for n in (
        'prepare_sharc_review.py','inspect_sharc_pairs.py','inspect_sharc.py','sharc_review_manifest.json')]]
    report['source'] = {'qa4pc_revision':audit.REVISION,'qa4pc_file_pins':audit.PINS,
        'pending_queue_selection_sha256':manifest['selection_sha256'],
        'sharc_archive_sha256':manifest['official_archive_sha256'],
        'dependencies_lf_sha256':{p.relative_to(ROOT).as_posix():lfhash(p) for p in dependencies}}
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=('build','verify')); p.add_argument('--source-dir',type=Path,required=True)
    a=p.parse_args(); report=build(a.source_dir); path=HERE/'cohort.json'; raw=readable(report)
    if a.command=='build' and not path.exists(): path.write_bytes(raw)
    elif path.read_bytes().replace(b'\r\n',b'\n') != raw: raise ValueError('Cohort drift; preserve original selection')
    print(json.dumps({k:report[k] for k in ('eligible_trees','excluded_union_trees','selected_trees','selected_scenarios','selected_label_counts')}))


if __name__=='__main__': main()
