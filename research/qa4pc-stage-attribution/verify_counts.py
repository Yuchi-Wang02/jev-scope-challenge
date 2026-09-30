"""Independent source-based count replay; no tokenizer, weights, API or private plan."""
import argparse
import ast
from collections import Counter
import json
from pathlib import Path
import re

from cohort import HERE,audit


def compose(expression,facts):
    tree=ast.parse(re.sub(r'\b(AND|OR|NOT)\b',lambda m:m[0].lower(),expression),mode='eval').body
    def visit(node):
        if isinstance(node,ast.Name):return facts[node.id]
        if isinstance(node,ast.UnaryOp) and isinstance(node.op,ast.Not):
            return {'yes':'no','no':'yes','maybe':'maybe'}[visit(node.operand)]
        if isinstance(node,ast.BoolOp):
            values=[visit(n) for n in node.values]
            if isinstance(node.op,ast.And):
                return 'no' if 'no' in values else 'yes' if all(v=='yes' for v in values) else 'maybe'
            if isinstance(node.op,ast.Or):
                return 'yes' if 'yes' in values else 'no' if all(v=='no' for v in values) else 'maybe'
        raise ValueError('Unsupported formula')
    return visit(tree)


def verify(source_dir):
    trees,ent,qa=audit.files(source_dir)
    t={r['tree_id']:r for r in trees};e={r['utterance_id']:r for r in ent}
    cohort=json.loads((HERE/'cohort.json').read_bytes());manifest=json.loads((HERE/'plan_manifest.json').read_bytes())
    report=json.loads((HERE/'report.json').read_bytes());jobs={j['id']:j for j in manifest['jobs']}
    ids=[r['utterance_id'] for tree in cohort['selected'] for r in tree['scenarios']]
    if len(ids)!=24 or len(set(ids))!=24 or len(cohort['selected'])!=12:raise ValueError('Unexpected cohort')
    results={};counts={}
    for backend in ('jev','qwen'):
        events=[json.loads(line) for line in (HERE/'results'/f'{backend}.jsonl').read_text().splitlines()]
        started=[x['job_id'] for x in events if x['event']=='call_start']
        ends=[x for x in events if x['event']=='call_finish']
        if len(set(started))!=len(started) or [x['job_id'] for x in ends]!=started:raise ValueError('Duplicate or missing attempts')
        results[backend]={x['job_id']:x['result'] for x in ends}
        usage={k:sum(x['result'][k] for x in ends) for k in ('input_tokens','output_tokens')}
        if any(usage[k]!=report['cost'][backend][k] for k in usage):raise ValueError('Usage mismatch')
        if len(ends)!=report['cost'][backend]['completed']:raise ValueError('Coverage mismatch')
    if any(jobs[k]['phase']=='main' for k in results['qwen']):raise ValueError('Original Qwen main must remain unexecuted')
    for mapping in (0,1):
        pred={}
        for ident,r in results['jev'].items():
            job=jobs[ident]
            if job['phase']!='main' or job['mapping']!=mapping:continue
            letter=r['detail']['raw_response']['answers']['decision']['choice']
            pred[(job['item_id'],job['arm'],job['question_id'])]=job['options']['ABC'.index(letter)]
        for arm in ('D','G','F','L'):
            actions={}
            for uid in ids:
                if arm=='F':
                    tr=t[e[uid]['tree_id']]
                    actions[uid]=compose(tr['logic'],{q:pred[(uid,'F',q)] for q in tr['questions']})
                else:actions[uid]=pred[(uid,arm,None)]
            correct=sum(actions[uid]==e[uid]['answer'] for uid in ids)
            key=f'jev_mapping{mapping}_{arm}';counts[key]=correct
            if report['metrics'][key]['correct']!=correct:raise ValueError('Agreement mismatch')
        facts=[q for q in qa if q['utterance_id'] in ids]
        correct=sum(pred[(q['utterance_id'],'F',q['question_id'])]==q['answer'] for q in facts)
        if len(facts)!=56 or report['metrics'][f'jev_mapping{mapping}_facts']['correct']!=correct:
            raise ValueError('Fact-count mismatch')
        counts[f'jev_mapping{mapping}_facts']=correct
    return {'status':'independent count replay passed','counts':counts,
            'qwen_main_evaluated':0,'cluster_units':12,'scenarios':24,'condition_rows':56}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-dir',type=Path,required=True)
    print(json.dumps(verify(p.parse_args().source_dir)))
