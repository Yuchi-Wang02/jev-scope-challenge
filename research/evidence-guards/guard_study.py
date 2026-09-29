"""Development-only, no-inference follow-up over immutable real saved scores."""
import argparse
import csv
import itertools
import json
import math
import platform
import subprocess
import sys
import time
from pathlib import Path
HERE=Path(__file__).resolve().parent
GAP=HERE.parent/'evidence-gap'
sys.path.insert(0,str(GAP))
from gap_run import ARMS, read_rows, write_json, sha, canonical
from gap_methods import softmax
from gap_analyze import metrics, equal
from gap_data import keys, world_truth
from verify_gap import verify as verify_prior
from guards import methods, parse_visible, gates, decide


def prepare():
    if (HERE/'manifest.json').exists():freeze();print('Existing design freeze verified read-only.');return
    verify_prior()
    cases=[c for c in read_rows(GAP/'data/cases.jsonl') if c['split']=='development']
    check_cases(cases)
    path=HERE/'development_cases.jsonl'
    payload=''.join(json.dumps(c,ensure_ascii=False)+'\n' for c in cases)
    if path.exists() and path.read_text(encoding='utf-8')!=payload:raise ValueError('Preserve existing extraction')
    path.write_text(payload,encoding='utf-8',newline='\n')
    print(json.dumps(freeze(),indent=2))


def check_cases(cases):
    if len(cases)!=72 or len({c['id'] for c in cases})!=72 or any(c['split']!='development' or c['family']=='composed_route' for c in cases):
        raise ValueError('Foreign/reserved/duplicate development cases')
    if len({c['parent'] for c in cases})!=12:raise ValueError('Wrong parent count')


def freeze():
    paths=['PROTOCOL.md','guards.py','guard_study.py','development_cases.jsonl',
           '../evidence-gap/manifest.json','../evidence-gap/gap_data.py','../evidence-gap/gap_run.py',
           '../evidence-gap/gap_methods.py','../evidence-gap/gap_analyze.py','../evidence-gap/verify_gap.py',
           '../evidence-gap/results/runtime.json','../evidence-gap/results/summary.json']+[
           f'../evidence-gap/results/{a}.jsonl' for a in ARMS]
    obj={'study':'evidence-guards-development-v0.1','prior_source_commit':'434703989b08d003a44a95b0528765d2b94e11d3',
         'design_status':'post_hoc_after_development_results','allowed_splits':['development'],
         'methods':methods(),'new_model_forwards':0,'reused_main_records':648,'derived_predictions':8424,
         'code_reference_predictions':216,'reserved_model_records':0,'label_fitted_parameters':0,
         'independent_human_annotations':0,'paid_api_calls':0,'training_steps':0,
         'file_sha256_lf':{p:sha((HERE/p).read_bytes().replace(b'\r\n',b'\n')) for p in paths}}
    obj['config_hash']=sha(canonical(obj).encode());path=HERE/'manifest.json'
    if path.exists():
        if json.loads(path.read_text(encoding='utf-8'))!=obj:raise ValueError('Frozen follow-up changed; version it')
    else:write_json(path,obj)
    return obj


def grid(rows,cases,arm):
    expected={(c['id'],m) for c in cases for m in range(3)}
    selected=[r for r in rows if r['kind']=='main']
    if len(selected)!=216 or {(r['id'],r['mapping']) for r in selected}!=expected:
        raise ValueError('Incomplete/duplicate/foreign main record grid')
    if any(r['split']!='development' or r['arm']!=arm for r in selected):raise ValueError('Reserved/foreign model record')
    return sorted(selected,key=lambda r:(r['id'],r['mapping']))


def audit_logic():
    checked=0
    for family in ('joint_approval','reversal_exception','route_lookup'):
        names=keys(family)
        for observations in itertools.product(((),(False,),(True,),(False,True)),repeat=len(names)):
            case={'family':family,'target':'request-X','records':[
                {'scope':'request-X','field':k,'value':v} for k,vs in zip(names,observations) for v in vs]}
            if gates(case)[1]['may_commit']!=(world_truth(case)[0]!='INSUFFICIENT'):
                raise ValueError('Policy determinate flag disagrees with finite worlds')
            checked+=1
    return {'status':'passed','structured_states_checked':checked,'natural_language_human_validation':False}


def panel(rows,cases,raw_index):
    m=metrics(rows,cases);uncertain=[];supported=[];actions=[]
    corrected=regressed=0
    for r in rows:
        gold=cases[r['id']]['gold'];base=raw_index[r['id'],r['mapping']]['prediction']
        (uncertain if gold=='INSUFFICIENT' else supported).append(r)
        if r['prediction']!='INSUFFICIENT':actions.append(r)
        corrected+=base!=gold and r['prediction']==gold
        regressed+=base==gold and r['prediction']!=gold
    action_errors=sum(r['prediction']!=cases[r['id']]['gold'] for r in actions)
    m.update(supported_decisions=len(supported),false_insufficient=sum(r['prediction']=='INSUFFICIENT' for r in supported),
             supported_wrong_actions=sum(r['prediction'] not in (cases[r['id']]['gold'],'INSUFFICIENT') for r in supported),
             actions=len(actions),action_errors=action_errors,action_coverage=len(actions)/len(rows),
             action_risk=action_errors/len(actions) if actions else None,
             corrected_vs_raw=corrected,regressed_vs_raw=regressed)
    return m


def derive():
    manifest=freeze();verify_prior();case_list=read_rows(HERE/'development_cases.jsonl');check_cases(case_list)
    original=[c for c in read_rows(GAP/'data/cases.jsonl') if c['split']=='development']
    if case_list!=original:raise ValueError('Development extraction differs from immutable source')
    cases={c['id']:c for c in case_list};cache={};gate_records=[];code=[]
    audit=audit_logic()
    for c in case_list:
        parsed=parse_visible(c['state'],c['instruction']);schema,policy=gates(parsed)
        # Label is used only below for reference evaluation, never for gate construction.
        cache[c['id']]=(schema,policy)
        gate_records.append({'id':c['id'],'schema':schema,'policy':policy,'input_fields':['state','instruction']})
        prediction=world_truth(parsed)[0]
        for mapping in range(3):code.append({'id':c['id'],'parent':c['parent'],'family':c['family'],
            'variant':c['variant'],'mapping':mapping,'prediction':prediction,'method':'known_grammar_solver',
            'nominal_model_calls':0,'uses_known_grammar':True})
    results={};predictions=[]
    for arm in ARMS:
        raw=grid(read_rows(GAP/f'results/{arm}.jsonl'),case_list,arm)
        lookup={(r['id'],r['mapping']):r for r in raw};panels={}
        for method in methods():
            selected=[]
            for r in raw:
                probabilities=softmax(r['logits']);pred=r['order'][max(range(3),key=probabilities.__getitem__)]
                if pred!=r['prediction']:raise ValueError('Historical raw prediction mismatch')
                schema,policy=cache[r['id']]
                row={k:r[k] for k in ('id','parent','family','variant','mapping','arm','split')}
                row.update(method=method,raw_prediction=pred,source_forward_id=None if method=='always_insufficient' else r['forward_id'],
                           **decide(pred,probabilities,r['order'],schema,policy,method))
                selected.append(row)
            panels[method]={'all':panel(selected,cases,lookup),'families':{
                f:panel([r for r in selected if r['family']==f],{k:c for k,c in cases.items() if c['family']==f},lookup)
                for f in sorted({c['family'] for c in case_list})}}
            predictions.extend(selected)
        results[arm]=panels
    reference=metrics(code,cases)
    if reference['correct']!=216:raise ValueError('Known grammar reference differs from existing development truth')
    summary={'status':'post_hoc_development_only','config_hash':manifest['config_hash'],'new_model_forwards':0,
             'reused_main_records':648,'unused_prior_null_records':108,'derived_predictions':len(predictions),
             'code_reference_predictions':len(code),'gate_text_inputs':len(cache),'structured_logic_audit':audit,
             'reserved_model_records':0,'independent_human_annotations':0,'label_fitted_parameters':0,
             'results':results,'known_grammar_solver':reference,
             'model_cost_note':'Model-dependent paths nominally reuse one real forward per decision; grammar work is extra.',
             'score_note':'Fixed grids, no selected/calibrated threshold; no risk guarantee.'}
    return summary,predictions,gate_records,code


def write_rows(path,rows):
    path.write_text(''.join(json.dumps(r,ensure_ascii=False,allow_nan=False)+'\n' for r in rows),encoding='utf-8',newline='\n')


def run():
    out=HERE/'results'
    if out.exists() and any(out.iterdir()):raise ValueError('Existing output: preserve, do not rerun/select')
    out.mkdir(exist_ok=True);tick=time.perf_counter()
    runtime={'status':'running','new_model_forwards':0,'reserved_model_records':0,'paid_api_calls':0,'training_steps':0,
             'python':platform.python_version(),'execution_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=HERE,text=True).strip()}
    write_json(out/'runtime.json',runtime)
    try:
        summary,rows,gates_out,code=derive()
        write_json(out/'summary.json',summary);write_rows(out/'predictions.jsonl',rows)
        write_rows(out/'gates.jsonl',gates_out);write_rows(out/'code_reference.jsonl',code)
        with (out/'decisions.csv').open('w',encoding='utf-8',newline='') as stream:
            fields=['arm','method','id','parent','variant','mapping','raw_prediction','prediction','changed','nominal_model_calls','uses_known_grammar']
            w=csv.DictWriter(stream,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
        runtime.update(status='complete',config_hash=summary['config_hash'],derived_predictions=len(rows),
                       parsed_unique_texts=72,gate_decisions_computed=144,elapsed_s=time.perf_counter()-tick)
        write_json(out/'runtime.json',runtime);print(json.dumps(runtime,indent=2))
    except BaseException as error:
        runtime.update(status='failed',error_type=type(error).__name__,error=str(error),elapsed_s=time.perf_counter()-tick)
        write_json(out/'runtime.json',runtime);raise


def verify():
    summary,rows,gates_out,code=derive();out=HERE/'results'
    for path,expected in [('summary.json',summary),('predictions.jsonl',rows),('gates.jsonl',gates_out),('code_reference.jsonl',code)]:
        actual=read_rows(out/path) if path.endswith('jsonl') else json.loads((out/path).read_text(encoding='utf-8'))
        equal(actual,expected,path)
    runtime=json.loads((out/'runtime.json').read_text(encoding='utf-8'))
    if runtime['status']!='complete' or runtime['config_hash']!=summary['config_hash']:
        raise ValueError('Incomplete/foreign follow-up runtime')
    expected={'new_model_forwards':0,'reserved_model_records':0,'paid_api_calls':0,'training_steps':0,
              'derived_predictions':8424,'parsed_unique_texts':72,'gate_decisions_computed':144}
    if any(runtime[k]!=v for k,v in expected.items()):raise ValueError('Foreign runtime counts')
    if not math.isfinite(runtime['elapsed_s']) or runtime['elapsed_s']<0:raise ValueError('Invalid runtime duration')
    return {'status':'passed','read_only':True,**expected,'independent_human_annotations':0}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['prepare','run','verify'])
    args=parser.parse_args()
    if args.command=='prepare':prepare()
    elif args.command=='run':run()
    else:print(json.dumps(verify()))
