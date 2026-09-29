"""Read-only recomputation of all fixed pipelines, extraction errors and actual costs."""
import argparse
import json
import math
import posixpath
import re
import subprocess
from collections import Counter
from fact_run import HERE, ARMS, GATE, freeze, read_rows, write_json, queries, executor_audit, sha
from interface import compile_visible, execute, STATUSES
from data_tools import original_cases, material, files
from gap_analyze import equal
from verify_gap import text_reference

DIRECT={'direct_0':[0],'direct_1':[1],'direct_2':[2],'direct_two_01':[0,1],'direct_three':[0,1,2]}
EXTRACT={'facts_0':[0],'facts_1':[1],'facts_two':[0,1]}


def softmax(z):
    if len(z) not in (3,4) or any(not isinstance(x,(int,float)) or not math.isfinite(x) for x in z):raise ValueError('Invalid logits')
    ex=[math.exp(x-max(z)) for x in z];return [x/sum(ex) for x in ex]


def choose(rows,labels):
    means={x:sum(softmax(r['logits'])[r['order'].index(x)] for r in rows)/len(rows) for x in labels}
    return max(labels,key=means.__getitem__),means


def metrics(rows):
    if not rows:raise ValueError('Empty panel')
    parents={}
    for r in rows:parents.setdefault(r['parent'],{})[r['variant']]=r
    uncertain=[r for r in rows if r['gold']=='INSUFFICIENT'];determined=[r for r in rows if r['gold']!='INSUFFICIENT']
    actions=[r for r in rows if r['prediction']!='INSUFFICIENT'];wrong_actions=sum(not r['correct'] for r in actions)
    return {'decisions':len(rows),'correct':sum(r['correct'] for r in rows),'parents':len(parents),
        'complete_parents':sum(len(p)==6 and all(r['correct'] for r in p.values()) for p in parents.values()),
        'deletion_pair_correct':sum(p['decisive_missing']['correct'] and p['nondecisive_missing']['correct'] for p in parents.values()),
        'paired_units':len(parents),'false_commitments':sum(r['prediction']!='INSUFFICIENT' for r in uncertain),
        'uncertain_decisions':len(uncertain),'false_insufficient':sum(r['prediction']=='INSUFFICIENT' for r in determined),
        'determined_decisions':len(determined),'wrong_supported_actions':sum(r['prediction']!='INSUFFICIENT' and not r['correct'] for r in determined),
        'actions':len(actions),'action_errors':wrong_actions,'action_error_rate':wrong_actions/len(actions) if actions else None,
        'variants':{v:{'correct':sum(r['correct'] for r in rows if r['variant']==v),'decisions':sum(r['variant']==v for r in rows)} for v in sorted({r['variant'] for r in rows})},
        'model_calls':sum(r['model_calls'] for r in rows),'input_tokens':sum(r['input_tokens'] for r in rows),
        'summed_forward_latency_s':sum(r['summed_forward_latency_s'] for r in rows)}


def validate_records(rows,plans,arm,config):
    index={(r['id'],r['mapping']):r for r in rows};plook={(p['id'],p['mapping']):p for p in plans}
    if len(rows)!=552 or len(index)!=552 or set(index)!=set(plook):raise ValueError('Incomplete/duplicate/foreign grid')
    for key,r in index.items():
        p=plook[key];n=len(p['order']);ps=softmax(r['logits'])
        if r['arm']!=arm or r['config_hash']!=config or not r['ok'] or r['forward_id']!=f"{arm}/{r['id']}/{r['mapping']}":raise ValueError('Record identity')
        for f in ('id','source_id','parent','family','variant','split','representation','kind','field','mapping','order'):
            if r[f]!=p[f]:raise ValueError('Plan metadata mismatch')
        if len(r['probabilities'])!=n or any(not math.isfinite(a) or not math.isclose(a,b,rel_tol=2e-5,abs_tol=1e-7) for a,b in zip(r['probabilities'],ps)):raise ValueError('Probability evidence')
        if r['prediction']!=p['order'][max(range(n),key=ps.__getitem__)]:raise ValueError('Prediction evidence')
        if r['input_tokens']!=len(r['token_ids']) or not math.isfinite(r['latency_s']) or r['latency_s']<0:raise ValueError('Cost evidence')
        if arm!='K1':
            if any(r[f]!=p[k] for f,k in (('prompt','prompt'),('token_ids','native_token_ids'),('candidate_ids','candidate_ids'))):raise ValueError('Native input')
            if not math.isfinite(r['candidate_mass']) or not 0<=r['candidate_mass']<=1:raise ValueError('Candidate mass')
        else:
            enc=p['pointer_encoding']
            for f,k in (('token_ids','ids'),('position_ids','pos'),('segments','seg'),('decide_idx','decide_idx'),('option_idx','opt_idx')):
                if r[f]!=enc[k]:raise ValueError('Pointer input')
            if any(r[f]!=p[f] for f in ('state','instruction','options')):raise ValueError('Pointer text')
            q=softmax(r['parity']['causal_logits']);delta=max(abs(a-b) for a,b in zip(q,r['probabilities']));saved=r['parity']['max_probability_delta']
            if not math.isfinite(saved) or not 0<=saved<GATE or delta>=GATE or abs(delta-saved)>1e-6 or not r['parity']['prediction_matches'] or max(range(n),key=q.__getitem__)!=max(range(n),key=ps.__getitem__):raise ValueError('Pointer parity evidence')
    return index


def analyze():
    manifest=freeze();cases=original_cases();clook={c['id']:c for c in cases};_,refs,_=material();ref={(r['source_id'],r['field']):r for r in refs}
    for name,payload in files().items():
        if (HERE/name).read_text(encoding='utf-8')!=payload:raise ValueError('Preparation artifact changed')
    equal(executor_audit(),json.loads((HERE/'data/executor_audit.json').read_text(encoding='utf-8')))
    plans=read_rows(HERE/'data/inputs.jsonl')
    if [{k:p[k] for k in q} for p,q in zip(plans,queries(cases))]!=queries(cases) or len(plans)!=552:raise ValueError('Query source mismatch')
    for p in plans:
        from fact_run import native_prompt
        if p['prompt']!=native_prompt(p):raise ValueError('Prompt changed')
        enc=p['pointer_encoding']
        if enc['state_truncated'] or enc['pos']!=list(range(len(enc['ids']))):raise ValueError('Encoding contract')
    runtime=json.loads((HERE/'results/runtime.json').read_text(encoding='utf-8'))
    if runtime['status']!='complete' or runtime['config_hash']!=manifest['config_hash'] or runtime['allowed_splits']!=['development']:raise ValueError('Runtime identity')
    commit=runtime['execution_commit']
    if not re.fullmatch('[0-9a-f]{40}',commit):raise ValueError('Invalid source commit')
    for path,digest in manifest['file_sha256_lf'].items():
        target=posixpath.normpath('research/fact-execution/'+path)
        content=subprocess.check_output(['git','show',commit+':'+target],cwd=HERE)
        if sha(content.replace(b'\r\n',b'\n'))!=digest:raise ValueError('Source was not frozen at execution commit')
    for key in ('scientific_forwards','direct_forwards','fact_forwards','parity_forwards','warmup_forwards','reserved_model_records','rewrite_model_records','new_training','paid_api_calls'):
        if runtime[key]!=manifest[key]:raise ValueError('Runtime counts')
    if runtime['sdpa_kernel']!='math_only' or runtime['backbone_dtype']!='bfloat16' or runtime['head_dtype']!='float32':raise ValueError('Execution precision')
    expected=json.loads((HERE.parent/'next-study/results/weight_checksums.json').read_text(encoding='utf-8'))
    equal(expected,json.loads((HERE/'results/weight_checksums.json').read_text(encoding='utf-8')))
    equal({'status':'passed','exact_tensors':504,'parameters':33030144},json.loads((HERE/'results/adapter_audit.json').read_text(encoding='utf-8')))
    derived=[];claims=[];panels={};audit={}
    for arm in ARMS:
        equal({'direct':216,'fact':336,'status':'complete'},runtime[arm])
        raw=read_rows(HERE/f'results/{arm}.jsonl');index=validate_records(raw,plans,arm,manifest['config_hash']);panels[arm]={}
        legacy={(r['id'],r['mapping']):r for r in read_rows(HERE.parent/f'evidence-gap/results/{arm}.jsonl') if r['kind']=='main'}
        for method,mappings in list(DIRECT.items())+list(EXTRACT.items())+[('legacy_direct_0',[0])]:
            predictions=[];field_claims=[]
            for c in cases:
                schema=compile_visible(c['state'],c['instruction']);vector=None
                if method=='legacy_direct_0':
                    used=[legacy[c['id'],0]];prediction=used[0]['prediction']
                elif method in DIRECT:
                    used=[index[c['id']+'/direct',m] for m in mappings];prediction,_=choose(used,('ALLOW','DENY','INSUFFICIENT'))
                else:
                    used=[];vector={}
                    for f in schema['fields']:
                        name=f['name'];chosen=[index[c['id']+'/fact/'+name,m] for m in mappings];used+=chosen
                        status,probs=choose(chosen,STATUSES);vector[name]=status;truth=ref[c['id'],name]['status']
                        claim={'source_id':c['id'],'parent':c['parent'],'family':c['family'],'variant':c['variant'],
                            'arm':arm,'method':method,'field':name,'status':status,'reference_status':truth,'correct':status==truth,
                            'evidence_spans':None,'provenance':'model_choice_without_spans','semantic_probabilities':probs}
                        claims.append(claim);field_claims.append(claim)
                    prediction=execute(schema,vector)
                r={'source_id':c['id'],'parent':c['parent'],'family':c['family'],'variant':c['variant'],'arm':arm,
                    'method':method,'gold':c['gold'],'prediction':prediction,'correct':prediction==c['gold'],
                    'model_calls':len(used),'input_tokens':sum(x['input_tokens'] for x in used),
                    'summed_forward_latency_s':sum(x['latency_s'] for x in used),'facts':vector}
                if vector is not None:
                    bad=[k for k,v in vector.items() if v!=ref[c['id'],k]['status']]
                    r['incorrect_fields']=bad;r['facts_exact']=not bad
                    r['attribution']='exact_facts_correct_action' if not bad and r['correct'] else 'executor_defect' if not bad else 'wrong_facts_masked' if r['correct'] else 'wrong_facts_wrong_action'
                    if r['attribution']=='executor_defect':raise ValueError('Correct facts produced incorrect execution')
                predictions.append(r);derived.append(r)
            panel={'all':metrics(predictions),'families':{f:metrics([r for r in predictions if r['family']==f]) for f in sorted({r['family'] for r in predictions})}}
            if field_claims:
                confusion={truth:{pred:sum(r['reference_status']==truth and r['status']==pred for r in field_claims) for pred in STATUSES} for truth in STATUSES}
                panel['extraction']={'fields':168,'correct_fields':sum(r['correct'] for r in field_claims),
                    'exact_vectors':sum(r['facts_exact'] for r in predictions),'vectors':72,'confusion':confusion,
                    'missing_as_reported_value':sum(r['reference_status']=='MISSING' and r['status'] in ('TRUE','FALSE') for r in field_claims),
                    'missing_as_conflict':sum(r['reference_status']=='MISSING' and r['status']=='CONFLICT' for r in field_claims),
                    'missing_fields':sum(r['reference_status']=='MISSING' for r in field_claims),
                    'missed_conflicts':sum(r['reference_status']=='CONFLICT' and r['status']!='CONFLICT' for r in field_claims),
                    'conflict_fields':sum(r['reference_status']=='CONFLICT' for r in field_claims),
                    'attribution':dict(Counter(r['attribution'] for r in predictions)),
                    'by_field':{f:{'correct':sum(r['correct'] for r in field_claims if r['field']==f),'fields':sum(r['field']==f for r in field_claims)} for f in sorted({r['field'] for r in field_claims})},
                    'by_family':{f:{'correct':sum(r['correct'] for r in field_claims if r['family']==f),'fields':sum(r['family']==f for r in field_claims)} for f in sorted({r['family'] for r in field_claims})},
                    'by_variant':{v:{'correct':sum(r['correct'] for r in field_claims if r['variant']==v),'fields':sum(r['variant']==v for r in field_claims)} for v in sorted({r['variant'] for r in field_claims})}}
            primary=[r for r in derived if r['arm']==arm and r['method']=='direct_0']
            panel['vs_scaffolded_direct_0']={'corrected':sum(not b['correct'] and r['correct'] for b,r in zip(primary,predictions)),
                'regressed':sum(b['correct'] and not r['correct'] for b,r in zip(primary,predictions))}
            panels[arm][method]=panel
        audit[arm]={'records':len(raw),'direct':sum(r['kind']=='direct' for r in raw),'fact':sum(r['kind']=='fact' for r in raw),
            'input_tokens':sum(r['input_tokens'] for r in raw),'summed_forward_latency_s':sum(r['latency_s'] for r in raw)}
    if any(text_reference(c['state'],c['instruction'])!=c['gold'] for c in cases):raise ValueError('Known grammar disagreement')
    maximum=max(r['parity']['max_probability_delta'] for r in read_rows(HERE/'results/K1.jsonl'))
    if maximum!=runtime['max_parity_delta']:raise ValueError('Parity runtime mismatch')
    summary={'config_hash':manifest['config_hash'],'status':'exploratory_original_development_only',
        'original_inputs':72,'parents':12,'reference_fields':168,'human_annotations':0,'rewrite_model_records':0,'reserved_model_records':0,
        'scientific_forwards':1656,'parity_forwards':552,'warmups':6,'executor_states_checked':96,
        'known_grammar_reference':{'correct':72,'decisions':72,'model_calls':0,'scope':'declared exact synthetic grammar'},
        'actual_execution':audit,'methods':panels}
    return summary,derived,claims


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify',action='store_true');a=p.parse_args();s,rows,claims=analyze()
    if a.verify:
        equal(s,json.loads((HERE/'results/summary.json').read_text(encoding='utf-8')));equal(rows,read_rows(HERE/'results/decisions.jsonl'));equal(claims,read_rows(HERE/'results/fact_claims.jsonl'))
    else:
        write_json(HERE/'results/summary.json',s)
        for name,data in (('decisions',rows),('fact_claims',claims)):
            (HERE/f'results/{name}.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,allow_nan=False)+'\n' for r in data),encoding='utf-8',newline='\n')
    print(json.dumps({'status':'passed','read_only':a.verify,'scientific_records':1656,'decisions':len(rows),'fact_claims':len(claims),'human_annotations':0,'rewrite_model_records':0,'reserved_model_records':0}))


if __name__=='__main__':main()
