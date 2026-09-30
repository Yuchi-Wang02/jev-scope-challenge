"""Compile the fixed four-route interface grid without loading model weights."""
import argparse
from collections import Counter
import importlib.util
from itertools import permutations
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('interface_cohort', HERE/'cohort.py')
cohort=importlib.util.module_from_spec(spec);spec.loader.exec_module(cohort)
ROOT=cohort.ROOT;STUDY=cohort.STUDY;audit=cohort.audit
readable=cohort.readable;lfhash=cohort.lfhash
sys.path.insert(0,str(ROOT/'research/external-validation'))
from comparison_plan import checked_tokenizer, QWEN_REVISION

ORDERS=tuple(permutations(('yes','no','maybe')))
LETTERS='ABC';TOKEN_IDS=(32,33,34)
MODEL='jev-1.13.0'
# Copied verbatim from the frozen preceding plan, so this is an interface
# contrast rather than an outcome-selected new reasoning instruction.
RULE=('Treat the supplied policy as a historical rule, not current advice. Use only the visible '
    'scenario facts. yes means established true; no means established false; maybe means not '
    'established either way. Do not treat missing facts as false. Apply three-valued logic: '
    'NOT yes=no, NOT no=yes, NOT maybe=maybe; AND is no if any operand is no, yes if all '
    'are yes, otherwise maybe; OR is yes if any operand is yes, no if all are no, otherwise maybe.')
INSTRUCTION=RULE+' Answer the main question under the policy.'
LIMITS={'http_attempts':162,'http_retries':0,'local_generations':486,
    'jev_planning_bytes_plus_allowance':2000000,'jev_actual_input_tokens':500000,
    'local_input_tokens':500000,'local_generated_tokens':10368,
    'local_generation_wall_seconds':1800,'local_context_tokens':32768}
CACHE=ROOT/'.local'/STUDY
SMOKES=[({'policy':'The rule is satisfied exactly when the parcel is blue.',
          'question':'Is the rule satisfied?', 'scenario':text}, label) for text,label in (
          ('The parcel is blue.','yes'),('The parcel is red, not blue.','no'),
          ('There is a parcel. Its color is not stated.','maybe'))]


def preserve(path,raw):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if path.read_bytes().replace(b'\r\n',b'\n')!=raw:
            raise ValueError('Existing artifact differs; preserve before amendment')
    else: path.write_bytes(raw)


def prompts(state,options):
    if tuple(options) not in ORDERS: raise ValueError('Invalid mapping')
    prefix=INSTRUCTION+'\nINPUT JSON:\n'+json.dumps(state,ensure_ascii=False,sort_keys=True)
    letter=prefix+'\nAnswer with exactly one letter and no explanation.\n'+\
        '\n'.join(f'{l}: {v}' for l,v in zip(LETTERS,options))
    semantic=prefix+'\nAnswer with exactly one semantic label and no explanation.\n'+\
        'Allowed labels in display order:\n'+'\n'.join(options)
    return letter,semantic


def compile_grid(rows,selection,tokenizer):
    rm={r['utterance_id']:r for r in rows}
    if len(rm)!=len(rows): raise ValueError('Duplicate source IDs')
    jobs=[];refs=[]
    def add(ident,state,phase,tree_id=None,expected=None):
        for mapping,options in enumerate(ORDERS):
            common={'phase':phase,'mapping':mapping,'options':list(options),
                'item_id':ident if phase=='main' else None,'tree_id':tree_id,
                'expected_smoke_action':expected}
            request={'model':MODEL,'state':state,'questions':{'decision':{
                'type':'choice','instructions':INSTRUCTION,
                'criteria':{l:f'The truth value is exactly {v}.' for l,v in zip(LETTERS,options)}}}}
            jobs.append({**common,'id':f'{ident}_m{mapping}_native','backend':'jev','arm':'native','request':request})
            letter,semantic=prompts(state,options)
            for arm,prompt,max_tokens in (('finite',letter,0),('letter',letter,32),('semantic',semantic,32)):
                rendered=tokenizer.apply_chat_template([{'role':'user','content':prompt}],tokenize=False,
                    add_generation_prompt=True,enable_thinking=False)
                ids=tokenizer.encode(rendered,add_special_tokens=False)
                if not ids or len(ids)+max_tokens>LIMITS['local_context_tokens']: raise ValueError('Context bound')
                if arm=='finite':
                    for l,t in zip(LETTERS,TOKEN_IDS):
                        if tokenizer.encode(rendered+l,add_special_tokens=False)!=ids+[t]:
                            raise ValueError('Unstable letter continuation')
                jobs.append({**common,'id':f'{ident}_m{mapping}_{arm}','backend':'qwen','arm':arm,
                    'prompt':prompt,'rendered_input':rendered,'input_ids':ids,'max_new_tokens':max_tokens,
                    'thinking':False})
    for n,(state,label) in enumerate(SMOKES):add(f'smoke_{n}',state,'smoke',expected=label)
    seen=set()
    for tree in selection['selected']:
        for item in tree['scenarios']:
            uid=item['utterance_id'];r=rm[uid]
            if uid in seen or r['tree_id']!=tree['tree_id']:raise ValueError('Selection join mismatch')
            seen.add(uid);state={k:r[k] for k in ('policy','question','scenario')}
            if audit.digest(audit.encoded(state))!=item['direct_visible_sha256']:raise ValueError('Content drift')
            refs.append({'item_id':uid,'tree_id':tree['tree_id'],'label':r['answer']})
            add(uid,state,'main',tree['tree_id'])
    if len({j['id'] for j in jobs})!=len(jobs):raise ValueError('Duplicate jobs')
    plan={'study':STUDY,'jev_model':MODEL,'qwen_revision':QWEN_REVISION,'limits':LIMITS,'jobs':jobs}
    for backend,limit in (('jev','http_attempts'),('qwen','local_generations')):
        if sum(j['backend']==backend for j in jobs)>LIMITS[limit]:raise ValueError('Call budget')
    input_tokens=sum(len(j['input_ids']) for j in jobs if j['backend']=='qwen')
    output_cap=sum(j['max_new_tokens'] for j in jobs if j['backend']=='qwen')
    proxy=sum(len(audit.encoded(j['request']))+4096 for j in jobs if j['backend']=='jev')
    if input_tokens>LIMITS['local_input_tokens'] or output_cap>LIMITS['local_generated_tokens'] or proxy>LIMITS['jev_planning_bytes_plus_allowance']:
        raise ValueError('Token/planning budget exceeded')
    manifest={'study':STUDY,'status':'compiled before inference; runner freeze still required',
        'plan_sha256':audit.digest(readable(plan)),'references_sha256':audit.digest(readable(refs)),
        'orders':[list(o) for o in ORDERS],
        'counts':dict(sorted(Counter(f"{j['backend']}_{j['phase']}_{j['arm']}" for j in jobs).items())),
        'planned_local_input_tokens':input_tokens,'maximum_local_generated_tokens':output_cap,
        'planned_jev_request_bytes_plus_allowance':proxy,
        'jobs':[{'id':j['id'],'backend':j['backend'],'arm':j['arm'],'phase':j['phase'],
            'mapping':j['mapping'],'options':j['options'],'item_id':j['item_id'],'tree_id':j['tree_id'],
            'job_sha256':audit.digest(audit.encoded(j)),
            'input_tokens':len(j['input_ids']) if j['backend']=='qwen' else None,
            'input_ids_sha256':audit.digest(audit.encoded(j['input_ids'])) if j['backend']=='qwen' else None}
            for j in jobs]}
    return plan,refs,manifest


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=('prepare','verify'));p.add_argument('--source-dir',type=Path,required=True)
    p.add_argument('--model-dir',type=Path,required=True);a=p.parse_args()
    selection=cohort.build(a.source_dir)
    if (HERE/'cohort.json').read_bytes().replace(b'\r\n',b'\n')!=readable(selection):raise ValueError('Cohort drift')
    tokenizer,files=checked_tokenizer(a.model_dir)
    _,rows,_=audit.files(a.source_dir)
    plan,refs,manifest=compile_grid(rows,selection,tokenizer)
    manifest['tokenizer_files']=files
    manifest['preparation_source_hashes_lf']={p.relative_to(ROOT).as_posix():lfhash(p) for p in (
        Path(__file__),HERE/'cohort.py',HERE/'cohort.json',HERE/'DESIGN.md',
        ROOT/'research/external-validation/comparison_plan.py')}
    outputs=[(CACHE/'plan.json',readable(plan)),(CACHE/'references.json',readable(refs)),
             (HERE/'plan_manifest.json',readable(manifest))]
    for path,raw in outputs:
        if a.command=='prepare':preserve(path,raw)
        elif path.read_bytes().replace(b'\r\n',b'\n')!=raw:raise ValueError('Compiled plan drift')
    print(json.dumps({k:manifest[k] for k in ('counts','planned_local_input_tokens',
        'maximum_local_generated_tokens','planned_jev_request_bytes_plus_allowance','plan_sha256')}))


if __name__=='__main__':main()
