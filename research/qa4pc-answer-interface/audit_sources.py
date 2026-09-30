"""Join an exhaustive qualitative source audit to saved outcomes without rescoring."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def encoded(x):return (json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
def digest(p):return hashlib.sha256(Path(p).read_bytes().replace(b'\r\n',b'\n')).hexdigest()


def compile_audit(source_dir):
    selection=json.loads((HERE/'cohort.json').read_bytes())
    notes=json.loads((HERE/'source_notes.json').read_bytes())
    result=json.loads((HERE/'report.json').read_bytes())
    for name,(sha,size) in selection['source']['qa4pc_file_pins'].items():
        raw=(source_dir/name).read_bytes()
        if len(raw)!=size or hashlib.sha256(raw).hexdigest()!=sha:raise ValueError('Pinned source mismatch')
    rows={r['utterance_id']:r for r in json.loads((source_dir/'dev_entailment_qa4pc.json').read_bytes())}
    trees={r['tree_id']:r for r in json.loads((source_dir/'trees_dev_test_qa4pc.json').read_bytes())}
    facts={}
    for r in json.loads((source_dir/'dev_qa_qa4pc.json').read_bytes()):facts.setdefault(r['utterance_id'],{})[r['question_id']]=r['answer']
    ordered=[(t['tree_id'],r['utterance_id']) for t in selection['selected'] for r in t['scenarios']]
    if [n['item_id'] for n in notes['rows']]!=[uid for _,uid in ordered]:raise ValueError('Notes must cover every selected scenario once in cohort order')
    if notes['reference_updates']!=0 or notes['replacement_scores_authorized'] is not False:raise ValueError('Not an adjudication/rescoring artifact')
    out=[]
    for (tid,uid),note in zip(ordered,notes['rows']):
        if any(f not in ('decisive_evidence_gap','rule_scope') for f in note['final_flags']):raise ValueError('Unknown final flag')
        if len(note['final_flags'])>1:raise ValueError('Primary review category must be unique')
        row=rows[uid];tree=trees[tid]
        if row['tree_id']!=tid or row['policy']!=tree['policy']:raise ValueError('Source join mismatch')
        model={}
        for arm in ('native','finite','letter','semantic'):
            obs=sorted([o for o in result['observations'] if o['item_id']==uid and o['arm']==arm],key=lambda o:o['mapping'])
            if len(obs)!=6 or [o['mapping'] for o in obs]!=list(range(6)) or any(not o['executed'] or o['reference']!=row['answer'] for o in obs):raise ValueError('Incomplete outcome join')
            actions=[o['action'] for o in obs]
            model[arm]={'actions':actions,'source_matches':sum(a==row['answer'] for a in actions),
                'histogram':dict(Counter(a if a is not None else 'INVALID' for a in actions)),
                'all_six_same_valid':all(a is not None for a in actions) and len(set(actions))==1}
        out.append({**note,'tree_id':tid,'source_label':row['answer'],'source_fact_labels':facts[uid],
            'model_observations':model})
    flags=Counter(f for r in out for f in r['final_flags'])
    unanimous=[]
    for r in out:
        acts=[a for o in r['model_observations'].values() for a in o['actions']]
        if all(a is not None for a in acts) and len(set(acts))==1 and acts[0]!=r['source_label']:
            unanimous.append(r['item_id'])
    stable_native=[r for r in out if r['model_observations']['native']['all_six_same_valid'] and r['model_observations']['native']['source_matches']==0]
    return {'review_type':notes['review_type'],'source_revision':selection['source']['qa4pc_revision'],
        'coverage_scenarios':len(out),'coverage_trees':len({r['tree_id'] for r in out}),
        'final_review_categories':dict(flags),'no_specific_final_flag_in_this_pass':sum(not r['final_flags'] for r in out),
        'intermediate_flagged_scenarios':sum(bool(r['intermediate_flags']) for r in out),
        'all_routes_all_mappings_same_source_mismatch':unanimous,
        'native_stable_source_mismatches':len(stable_native),
        'native_stable_source_mismatches_with_final_review_flag':sum(bool(r['final_flags']) for r in stable_native),
        'reference_updates':0,'new_model_calls':0,'new_human_reviews':0,'rescored_or_filtered_metrics':False,
        'input_hashes_lf':{name:digest(HERE/name) for name in ('source_notes.json','cohort.json','report.json','audit_sources.py')},
        'items':out}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=('build','verify'))
    p.add_argument('--source-dir',type=Path,required=True);a=p.parse_args()
    report=compile_audit(a.source_dir);path=HERE/'source_audit.json';raw=encoded(report)
    if a.command=='build':path.write_bytes(raw)
    elif path.read_bytes().replace(b'\r\n',b'\n')!=raw:raise ValueError('Source audit drift')
    print(json.dumps({k:v for k,v in report.items() if k not in ('items','input_hashes_lf')}))
