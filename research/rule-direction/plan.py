"""Build and verify the complete bounded grid before any inference."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from specification import cases,grammar_control

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
CACHE=ROOT/'.local/rule-direction-v1'
OLD=ROOT/'research/qa4pc-answer-interface'
sys.path.insert(0,str(OLD))
spec=importlib.util.spec_from_file_location('rule_existing_backend',OLD/'runner.py')
existing=importlib.util.module_from_spec(spec);spec.loader.exec_module(existing)
ORDERS=(('yes','no','maybe'),('maybe','no','yes'))
MODEL='jev-1.13.0'
INSTRUCTION=('Treat the supplied policy as a fictional logical constraint, not a real-world policy. '
    'Use only the stated rule and visible facts to answer the question. '
    'yes means the queried eligibility holds in every situation consistent with them; '
    'no means it fails in every consistent situation; maybe means both outcomes remain possible. '
    'An unmentioned fact is unknown, not false. Do not assume any unstated policy rule.')
LIMITS={'http_attempts':222,'http_retries':0,'local_generations':222,
    'jev_actual_input_tokens':300000,'jev_planning_bytes_plus_allowance':2000000,
    'local_input_tokens':200000,'local_generated_tokens':7104,
    'local_generation_wall_seconds':900,'local_context_tokens':32768}
SMOKES=[({'policy':'The badge is active if and only if the badge is blue.',
    'question':'Is the badge active?','scenario':s},label) for s,label in (
    ('The badge is blue.','yes'),('The badge is not blue.','no'),
    ('The badge was printed on Monday.','maybe'))]


def encoded(obj):return (json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode()
def digest(raw):return hashlib.sha256(raw).hexdigest()
def lfhash(path):return digest(Path(path).read_bytes().replace(b'\r\n',b'\n'))
def preserve(path,raw):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists() and path.read_bytes().replace(b'\r\n',b'\n')!=raw:raise ValueError('Preserve existing artifact: '+path.name)
    if not path.exists():path.write_bytes(raw)


def compile_grid(tokenizer):
    rows=cases()
    if len(rows)!=108 or any(grammar_control(r['state'])!=r['reference'] for r in rows):raise ValueError('Grammar/enumeration disagreement')
    jobs=[]
    def add(ident,state,phase,family=None,expected=None):
        for mapping,options in enumerate(ORDERS):
            common={'phase':phase,'mapping':mapping,'options':list(options),'item_id':ident,
                'tree_id':family,'expected_smoke_action':expected}
            request={'model':MODEL,'state':state,'questions':{'decision':{'type':'choice',
                'instructions':INSTRUCTION,'criteria':{l:f'The truth value is exactly {v}.' for l,v in zip('ABC',options)}}}}
            jobs.append({**common,'id':f'{ident}_m{mapping}_jev','backend':'jev','arm':'native','request':request})
            prompt=INSTRUCTION+'\nINPUT JSON:\n'+json.dumps(state,ensure_ascii=False,sort_keys=True)+\
                '\nAnswer with exactly one semantic label and no explanation.\nAllowed labels in display order:\n'+'\n'.join(options)
            rendered=tokenizer.apply_chat_template([{'role':'user','content':prompt}],tokenize=False,
                add_generation_prompt=True,enable_thinking=False)
            ids=tokenizer.encode(rendered,add_special_tokens=False)
            if not ids or len(ids)+32>LIMITS['local_context_tokens']:raise ValueError('Context limit')
            jobs.append({**common,'id':f'{ident}_m{mapping}_qwen','backend':'qwen','arm':'semantic',
                'prompt':prompt,'rendered_input':rendered,'input_ids':ids,'max_new_tokens':32,'thinking':False})
    for n,(state,label) in enumerate(SMOKES):add(f'smoke_{n}',state,'smoke',expected=label)
    for row in rows:add(row['id'],row['state'],'main',row['family_id'])
    input_tokens=sum(len(j['input_ids']) for j in jobs if j['backend']=='qwen')
    proxy=sum(len(encoded(j['request']))+4096 for j in jobs if j['backend']=='jev')
    if input_tokens>LIMITS['local_input_tokens'] or proxy>LIMITS['jev_planning_bytes_plus_allowance']:raise ValueError('Planning bound')
    plan={'study':'rule-direction-v1','limits':LIMITS,'jobs':jobs}
    manifest={'status_at_preparation':'zero model calls','study':plan['study'],
        'plan_sha256':digest(encoded(plan)),'case_sha256':digest(encoded(rows)),
        'counts':dict(Counter(j['backend']+'_'+j['phase'] for j in jobs)),
        'reference_distribution':dict(Counter(r['reference'] for r in rows)),
        'vocabulary_families':12,'logical_relation_patterns':3,'orders':[list(o) for o in ORDERS],
        'planned_local_input_tokens':input_tokens,'planned_local_output_token_cap':7104,
        'planned_jev_request_bytes_plus_allowance':proxy,'limits':LIMITS}
    return rows,plan,manifest


def pins():
    old=json.loads((OLD/'freeze.json').read_bytes())['source_hashes_lf']
    paths=set(old)|{'research/qa4pc-answer-interface/freeze.json'}
    paths|={p.relative_to(ROOT).as_posix() for p in [HERE/n for n in ('specification.py','plan.py','execute.py','PROTOCOL.md','cases.json')]}
    return {p:lfhash(ROOT/p) for p in sorted(paths)}


def prepare(model_dir):
    tokenizer,_=existing.checked_tokenizer(model_dir)
    rows,grid,manifest=compile_grid(tokenizer)
    for path,raw in ((HERE/'cases.json',encoded(rows)),(CACHE/'plan.json',encoded(grid)),(HERE/'manifest.json',encoded(manifest))):preserve(path,raw)
    freeze={'plan_sha256':manifest['plan_sha256'],'manifest_sha256':lfhash(HERE/'manifest.json'),
        'source_hashes_lf':pins(),'status_at_freeze':'zero model calls; require clean commit before execution'}
    preserve(HERE/'freeze.json',encoded(freeze))
    return grid,manifest,freeze


def verify(model_dir):
    if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT).strip():raise ValueError('Need clean committed freeze')
    grid,manifest,freeze=prepare(model_dir)
    for name in ('cases.json','manifest.json','freeze.json','PROTOCOL.md'):
        raw=subprocess.check_output(['git','show','HEAD:'+(HERE/name).relative_to(ROOT).as_posix()],cwd=ROOT)
        if raw.replace(b'\r\n',b'\n')!=(HERE/name).read_bytes().replace(b'\r\n',b'\n'):raise ValueError('Not committed')
    return grid,manifest


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=('prepare','verify'));p.add_argument('--model-dir',type=Path,required=True);a=p.parse_args()
    if a.command=='prepare':_,manifest,_=prepare(a.model_dir)
    else:_,manifest=verify(a.model_dir)
    print(json.dumps(manifest))
