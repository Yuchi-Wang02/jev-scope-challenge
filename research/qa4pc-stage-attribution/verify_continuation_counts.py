"""Independent raw-logit/native-choice replay of the completed amended comparison."""
import argparse
from collections import Counter
import json
from pathlib import Path

from cohort import HERE,audit
from verify_counts import compose


def verify(source_dir):
    trees,ent,qa=audit.files(source_dir)
    t={x['tree_id']:x for x in trees};e={x['utterance_id']:x for x in ent}
    selected=json.loads((HERE/'cohort.json').read_bytes())['selected']
    ids=[r['utterance_id'] for c in selected for r in c['scenarios']]
    manifest=json.loads((HERE/'plan_manifest.json').read_bytes());jobs={j['id']:j for j in manifest['jobs']}
    report=json.loads((HERE/'continuation_report.json').read_bytes());records={};cost={}
    for backend,files in [('jev',['jev.jsonl']),('qwen',['qwen.jsonl','qwen_continuation.jsonl'])]:
        ends=[];starts=[]
        for name in files:
            events=[json.loads(x) for x in (HERE/'results'/name).read_text().splitlines()]
            starts.extend(x['job_id'] for x in events if x['event']=='call_start')
            ends.extend(x for x in events if x['event']=='call_finish')
        expected=[j['id'] for j in manifest['jobs'] if j['backend']==backend]
        if starts!=expected or [x['job_id'] for x in ends]!=expected or len(set(starts))!=262:
            raise ValueError('Combined physical grid is not complete/disjoint/ordered')
        records[backend]={x['job_id']:x['result'] for x in ends}
        cost[backend]={k:sum(x['result'][k] for x in ends) for k in ('input_tokens','output_tokens')}
        if any(cost[backend][k]!=report['cost'][backend][k] for k in cost[backend]):raise ValueError('Cost mismatch')
    counts={};ties=[]
    for backend in ('jev','qwen'):
        for mapping in (0,1):
            pred={}
            for ident,r in records[backend].items():
                j=jobs[ident]
                if j['phase']!='main' or j['mapping']!=mapping:continue
                if backend=='jev':
                    letter=r['detail']['raw_response']['answers']['decision']['choice'];value=j['options']['ABC'.index(letter)]
                else:
                    logits=r['detail']['candidate_logits'];winners=[i for i,v in enumerate(logits) if v==max(logits)]
                    value=j['options'][winners[0]] if len(winners)==1 else None
                    if value is None:ties.append(ident)
                pred[(j['item_id'],j['arm'],j['question_id'])]=value
            for arm in ('D','G','F','L'):
                values={}
                for uid in ids:
                    tr=t[e[uid]['tree_id']]
                    if arm=='F':
                        facts={qid:pred[(uid,'F',qid)] for qid in tr['questions']}
                        value=compose(tr['logic'],facts) if all(v is not None for v in facts.values()) else None
                    else:value=pred[(uid,arm,None)]
                    values[uid]=value
                k=f'{backend}_mapping{mapping}_{arm}'
                counts[k]={'correct':sum(values[u]==e[u]['answer'] for u in ids),'invalid':sum(v is None for v in values.values()),'total':len(ids)}
                if any(report['metrics'][k][n]!=v for n,v in counts[k].items()):raise ValueError('Main count mismatch')
            facts=[x for x in qa if x['utterance_id'] in ids]
            k=f'{backend}_mapping{mapping}_facts'
            counts[k]={'correct':sum(pred[(x['utterance_id'],'F',x['question_id'])]==x['answer'] for x in facts),
                      'invalid':sum(pred[(x['utterance_id'],'F',x['question_id'])] is None for x in facts),'total':len(facts)}
            if any(report['metrics'][k][n]!=v for n,v in counts[k].items()):raise ValueError('Fact count mismatch')
    return {'status':'independent amended count replay passed','counts':counts,'qwen_exact_ties':sorted(ties),'cost':cost}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-dir',type=Path,required=True)
    print(json.dumps(verify(p.parse_args().source_dir)))
