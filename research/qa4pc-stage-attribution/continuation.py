"""Named continuation of only unexecuted Qwen jobs; preserves original stop."""
import argparse
from contextlib import contextmanager
import json
import importlib.util
from pathlib import Path
import subprocess

from plan import HERE,ROOT,CACHE,read,readable,audit,lfhash,check,preserve
from journal import read_events,replay,execute
from runner import qwen_backend,extract
_spec=importlib.util.spec_from_file_location('qa4pc_original_analysis',HERE/'analyze.py')
_analysis=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_analysis)
equivalent=_analysis.equivalent

NAME='qa4pc-qwen-semantic-gate-continuation-v1'
ORIGINAL=HERE/'results/qwen.jsonl'
LIMITS={'http_attempts':0,'http_retries':0,'local_generations':260,
    'jev_actual_input_tokens':0,'local_input_tokens':77150,'local_generated_tokens':0,
    'local_generation_wall_seconds':600,'local_context_tokens':32768}


def predecessor(parent,events):
    jobs=[j for j in parent['jobs'] if j['backend']=='qwen']
    state=replay(events,plan_hash=audit.digest(readable(parent)),backend='qwen',jobs=jobs)
    if (state['active_job'] is not None or state['active_session'] is not None or
        state['unknown_usage'] or not state['halted'] or len(state['started'])!=2 or
        list(state['results'])!=[j['id'] for j in jobs[:2]]):
        raise ValueError('Predecessor is not the resolved original two-smoke stop')
    first,last=[state['results'][j['id']] for j in jobs[:2]]
    if first['status']!='ok' or first['action']!=jobs[0]['expected_smoke_action']:
        raise ValueError('Unexpected first smoke')
    d=last['detail'];parsed=extract(d['candidate_logits'],d['full_logsumexp'],d['top_token_id'],d['top_logit'],jobs[1]['options'])
    if (last['status']!='protocol_error' or last['action'] is not None or not d.get('smoke_gate_failed') or
        parsed['action']!=d.get('smoke_observed_action') or not equivalent(parsed,d['parsed']) or
        d['physical_forwards']!=1 or parsed['action']==jobs[1]['expected_smoke_action']):
        raise ValueError('Predecessor is not the declared semantic miss')
    return state,jobs[2:]


def make_plan(parent,events):
    state,jobs=predecessor(parent,events)
    if len(jobs)!=260 or sum(j['phase']=='main' for j in jobs)!=256:
        raise ValueError('Unexpected suffix size')
    if sum(len(j['input_ids']) for j in jobs)!=LIMITS['local_input_tokens']:
        raise ValueError('Suffix input count differs')
    if set(state['started']) & {j['id'] for j in jobs}:raise ValueError('Attempt replay')
    return {'study':NAME,'parent_plan_sha256':audit.digest(readable(parent)),
            'predecessor_journal_lf_sha256':lfhash(ORIGINAL),'limits':LIMITS,'jobs':jobs}


def source_pins():
    paths=[HERE/n for n in ('continuation.py','CONTINUATION_PROTOCOL.md','analyze.py',
        'freeze.json','plan_manifest.json','results/qwen.jsonl','results/jev.jsonl')]
    return {p.relative_to(ROOT).as_posix():lfhash(p) for p in paths}


def prepare(source_dir,model_dir,clean=False):
    parent,_,_=check(source_dir,model_dir,clean=clean)
    plan=make_plan(parent,read_events(ORIGINAL));ph=audit.digest(readable(plan))
    manifest={'study':NAME,'status':'frozen before successor outputs','plan_sha256':ph,
        'parent_plan_sha256':plan['parent_plan_sha256'],'predecessor_journal_lf_sha256':lfhash(ORIGINAL),
        'main':256,'smoke':4,'input_tokens':77150,'jobs':[{'id':j['id'],'phase':j['phase'],
            'job_sha256':audit.digest(audit.encoded(j)),'input_tokens':len(j['input_ids'])} for j in plan['jobs']]}
    original_jobs={j['id']:j for j in read(HERE/'plan_manifest.json')['jobs']}
    if any(j['job_sha256']!=original_jobs[j['id']]['job_sha256'] for j in manifest['jobs']):
        raise ValueError('Successor changed a job')
    freeze={'study':NAME,'plan_sha256':ph,'manifest_sha256':audit.digest(readable(manifest)),
        'source_hashes_lf':source_pins(),'parent_source_hashes_lf':read(HERE/'freeze.json')['source_hashes_lf']}
    for path,value in [(CACHE/'continuation_plan.json',plan),(HERE/'continuation_manifest.json',manifest),
                       (HERE/'continuation_freeze.json',freeze)]:preserve(path,readable(value))
    return plan,manifest


def amended_call(call,job,remaining):
    internal={**job,'phase':'diagnostic_smoke'} if job['phase']=='smoke' else job
    result=call(internal,remaining)
    if job['phase']=='smoke':
        result['detail']['amended_smoke_policy']={'expected':job['expected_smoke_action'],
            'observed':result['action'],'correct':result['status']=='ok' and result['action']==job['expected_smoke_action'],
            'semantic_accuracy_is_gate':False}
    return result


@contextmanager
def backend(model_dir):
    with qwen_backend(model_dir) as (call,metadata):
        yield lambda job,remaining:amended_call(call,job,remaining),{**metadata,'amendment':NAME}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=('prepare','verify','run'))
    p.add_argument('--source-dir',type=Path,required=True);p.add_argument('--model-dir',type=Path,required=True);a=p.parse_args()
    plan,manifest=prepare(a.source_dir,a.model_dir,clean=a.command!='prepare')
    if a.command!='prepare':
        for name in ('continuation_manifest.json','continuation_freeze.json','CONTINUATION_PROTOCOL.md','continuation.py'):
            saved=subprocess.check_output(['git','show','HEAD:'+(HERE/name).relative_to(ROOT).as_posix()],cwd=ROOT)
            if saved.replace(b'\r\n',b'\n')!=(HERE/name).read_bytes().replace(b'\r\n',b'\n'):
                raise ValueError('Uncommitted successor freeze')
    if a.command=='run':
        directory=CACHE/('continuation-'+manifest['plan_sha256'])
        r=execute(directory,plan,manifest['plan_sha256'],'qwen',lambda:backend(a.model_dir))
        print(json.dumps({'status':r['status'],'attempts':len(r['state']['started']),
            'completed':len(r['state']['results']),'input_tokens':r['state']['input_tokens'],
            'output_tokens':r['state']['output_tokens'],'overruns':r['overruns']}))
    else:print(json.dumps({'status':a.command,'jobs':len(plan['jobs']),'input_tokens':manifest['input_tokens'],'plan_sha256':manifest['plan_sha256']}))


if __name__=='__main__':main()
