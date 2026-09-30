"""Compile a private QA4PC three-class grid and public hashes before inference."""
import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys

from cohort import ROOT, HERE, STUDY, audit

sys.path.insert(0, str(ROOT / 'research/external-validation'))
from comparison_plan import checked_tokenizer, QWEN_REVISION

MODEL = 'jev-1.13.0'
ORDERS = (('yes', 'no', 'maybe'), ('maybe', 'no', 'yes'))
LETTERS = 'ABC'
TOKEN_IDS = [32, 33, 34]
LIMITS = {'http_attempts': 262, 'http_retries': 0, 'local_generations': 262,
    'jev_planning_bytes_plus_allowance': 2000000, 'jev_actual_input_tokens': 500000,
    'local_input_tokens': 500000, 'local_generated_tokens': 0,
    'local_generation_wall_seconds': 600, 'local_context_tokens': 32768}
CACHE = ROOT / '.local' / STUDY
RULE = ('Treat the supplied policy as a historical rule, not current advice. Use only the visible '
    'scenario facts. yes means established true; no means established false; maybe means not '
    'established either way. Do not treat missing facts as false. Apply three-valued logic: '
    'NOT yes=no, NOT no=yes, NOT maybe=maybe; AND is no if any operand is no, yes if all '
    'are yes, otherwise maybe; OR is yes if any operand is yes, no if all are no, otherwise maybe.')
INSTRUCTIONS = {
    'D': RULE + ' Answer the main question under the policy.',
    'G': RULE + ' Answer the main question. The supplied condition questions and expression '
         'are the intended decomposition of this policy; combine their truth values.',
    'F': RULE + ' Judge only the selected condition question against the scenario. '
         'Return its truth value, not the overall policy decision. The other questions and '
         'expression provide the same structural context as the overall decision task.',
    'L': 'Execute the supplied expression using the supplied fact labels. ' + RULE +
         ' These fact labels are given premises. Return the resulting truth value.',
}
SMOKES = [({'expression': 'Q0 AND Q1', 'facts': {'Q0': 'yes', 'Q1': 'maybe'}}, 'maybe'),
          ({'expression': 'Q0 OR Q1', 'facts': {'Q0': 'no', 'Q1': 'no'}}, 'no'),
          ({'expression': 'NOT Q0', 'facts': {'Q0': 'no'}}, 'yes')]


def read(path): return json.loads(Path(path).read_bytes())
def readable(value): return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
def lfhash(path): return audit.digest(Path(path).read_bytes().replace(b'\r\n', b'\n'))


def preserve(path, raw):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes().replace(b'\r\n', b'\n') != raw:
            raise ValueError('Existing artifact differs; preserve evidence before any amendment')
    else: path.write_bytes(raw)


def options_checked(options):
    if tuple(options) not in ORDERS: raise ValueError('Unexpected option mapping')
    return tuple(options)


def compile_grid(trees, ent, qa, cohort, tokenizer):
    audit.inspect(trees, ent, qa)
    tree_map = {r['tree_id']: r for r in trees}
    ent_map = {r['utterance_id']: r for r in ent}
    facts = {}
    for row in qa: facts.setdefault(row['utterance_id'], {})[row['question_id']] = row['answer']
    jobs = []; references = []

    def add(ident, arm, state, mapping, phase, item_id=None, qid=None, expected=None):
        options = ORDERS[mapping]
        instruction = INSTRUCTIONS[arm]
        mapping_text = '\n'.join(f'{l}: {v}' for l,v in zip(LETTERS, options))
        request = {'model': MODEL, 'state': state, 'questions': {'decision': {
            'type': 'choice', 'instructions': instruction,
            'criteria': {l: f'The truth value is exactly {v}.' for l,v in zip(LETTERS, options)}}}}
        prompt = instruction + '\nINPUT JSON:\n' + json.dumps(state, ensure_ascii=False, sort_keys=True) + \
                 '\nAnswer with exactly one letter and no explanation.\n' + mapping_text
        rendered = tokenizer.apply_chat_template([{'role':'user','content':prompt}], tokenize=False,
                    add_generation_prompt=True, enable_thinking=False)
        ids = tokenizer.encode(rendered, add_special_tokens=False)
        if not ids or len(ids) > LIMITS['local_context_tokens']: raise ValueError('Context bound')
        for letter, token in zip(LETTERS, TOKEN_IDS):
            if tokenizer.encode(rendered + letter, add_special_tokens=False) != ids + [token]:
                raise ValueError('Letter not a stable single-token continuation')
        common = {'phase': phase, 'arm': arm, 'mapping': mapping, 'options': list(options),
                  'item_id': item_id, 'question_id': qid, 'expected_smoke_action': expected}
        jobs.append({**common, 'id': f'{ident}_m{mapping}_jev', 'backend': 'jev', 'request': request})
        jobs.append({**common, 'id': f'{ident}_m{mapping}_qwen', 'backend': 'qwen',
                     'prompt': prompt, 'rendered_input': rendered, 'input_ids': ids, 'max_new_tokens': 0})

    for mapping in range(2):
        for i,(state,expected) in enumerate(SMOKES):
            add(f'smoke_{i}', 'L', state, mapping, 'smoke', expected=expected)
    seen = set()
    for cluster in cohort['selected']:
        tid = cluster['tree_id']; tree = tree_map[tid]
        for item in cluster['scenarios']:
            uid = item['utterance_id']; row = ent_map[uid]
            if uid in seen or row['tree_id'] != tid: raise ValueError('Selected ID/tree mismatch')
            seen.add(uid)
            direct = {k: row[k] for k in ('policy', 'question', 'scenario')}
            if audit.digest(audit.encoded(direct)) != item['direct_visible_sha256']:
                raise ValueError('Selected source content drift')
            graph = {'condition_questions': tree['questions'], 'expression': tree['logic']}
            if sorted(tree['questions']) != cluster['question_ids']: raise ValueError('Question inventory drift')
            ref = {'item_id': uid, 'tree_id': tid, 'label': row['answer'], 'facts': facts[uid], 'expression': tree['logic']}
            if audit.execute(audit.parse_logic(tree['logic']), facts[uid]) != row['answer']:
                raise ValueError('Selected formula incomplete or reference inconsistent')
            references.append(ref)
            for mapping in range(2):
                add(f'{uid}_D','D',direct,mapping,'main',uid)
                add(f'{uid}_G','G',{**direct,**graph},mapping,'main',uid)
                for qid in cluster['question_ids']:
                    add(f'{uid}_F_{qid}','F',{**direct,**graph,'selected_condition_id':qid},mapping,'main',uid,qid)
                add(f'{uid}_L','L',{'expression':tree['logic'],'facts':facts[uid]},mapping,'main',uid)
    if len({j['id'] for j in jobs}) != len(jobs): raise ValueError('Duplicate jobs')
    plan = {'study':STUDY,'jev_model':MODEL,'qwen_revision':QWEN_REVISION,'limits':LIMITS,'jobs':jobs}
    manifest = {'study':STUDY,'status':'frozen compilation; zero model calls at creation',
        'cohort_sha256':lfhash(HERE/'cohort.json'), 'plan_sha256':audit.digest(readable(plan)),
        'references_sha256':audit.digest(readable(references)),
        'counts':dict(sorted(Counter(f"{j['backend']}_{j['phase']}_{j['arm']}" for j in jobs).items())),
        'planned_local_input_tokens':sum(len(j['input_ids']) for j in jobs if j['backend']=='qwen'),
        'planned_jev_request_utf8_bytes_plus_4096_per_call':sum(len(audit.encoded(j['request']))+4096 for j in jobs if j['backend']=='jev'),
        'jobs':[{'id':j['id'],'backend':j['backend'],'phase':j['phase'],'arm':j['arm'],'mapping':j['mapping'],
                 'item_id':j['item_id'],'question_id':j['question_id'],'options':j['options'],
                 'job_sha256':audit.digest(audit.encoded(j)),
                 'input_tokens':len(j['input_ids']) if j['backend']=='qwen' else None} for j in jobs]}
    if manifest['planned_local_input_tokens'] > LIMITS['local_input_tokens'] or manifest['planned_jev_request_utf8_bytes_plus_4096_per_call'] > LIMITS['jev_planning_bytes_plus_allowance']:
        raise ValueError('Planned input budget exceeded')
    if sum(j['backend']=='jev' for j in jobs)>LIMITS['http_attempts'] or sum(j['backend']=='qwen' for j in jobs)>LIMITS['local_generations']:
        raise ValueError('Attempt budget exceeded')
    return plan,references,manifest


def source_pins():
    paths = [HERE/name for name in ('plan.py','runner.py','journal.py','cohort.py','cohort.json','PROTOCOL.md')]
    paths += [ROOT/name for name in ('research/qa4pc-audit/audit.py',
        'research/external-validation/comparison_plan.py','research/external-validation/comparison_backends.py',
        'research/action-backends/adapters.py','research/payment-ownership/run_api_v02.py',
        'research/payment-ownership/study.py','research/baseline-readiness/qwen35-smoke-repaired/run.json')]
    return {p.relative_to(ROOT).as_posix():lfhash(p) for p in paths}


def prepare(source_dir, model_dir):
    data = audit.files(source_dir); tokenizer,files=checked_tokenizer(model_dir)
    plan,refs,manifest=compile_grid(*data,read(HERE/'cohort.json'),tokenizer)
    freeze={'study':STUDY,'plan_sha256':manifest['plan_sha256'],'references_sha256':manifest['references_sha256'],
            'manifest_sha256':audit.digest(readable(manifest)),'source_hashes_lf':source_pins(),'tokenizer_files':files,
            'source_revision':audit.REVISION,'source_file_pins':audit.PINS}
    for path,raw in [(CACHE/'plan.json',readable(plan)),(CACHE/'references.json',readable(refs)),
                     (HERE/'plan_manifest.json',readable(manifest)),(HERE/'freeze.json',readable(freeze))]: preserve(path,raw)
    return plan,refs,manifest


def check(source_dir,model_dir,clean=True):
    if clean and subprocess.check_output(['git','status','--porcelain'],cwd=ROOT).strip():
        raise ValueError('Need a clean committed freeze')
    freeze=read(HERE/'freeze.json')
    if source_pins()!=freeze['source_hashes_lf']: raise ValueError('Frozen source drift')
    for name in ('freeze.json','plan_manifest.json'):
        saved=subprocess.check_output(['git','show','HEAD:'+ (HERE/name).relative_to(ROOT).as_posix()],cwd=ROOT)
        if saved.replace(b'\r\n',b'\n')!=(HERE/name).read_bytes().replace(b'\r\n',b'\n'):
            raise ValueError('Uncommitted freeze artifact')
    plan,refs,manifest=prepare(source_dir,model_dir)
    if audit.digest(readable(plan))!=freeze['plan_sha256']: raise ValueError('Plan hash drift')
    return plan,refs,manifest


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=('prepare','verify'))
    p.add_argument('--source-dir',type=Path,required=True);p.add_argument('--model-dir',type=Path,required=True)
    a=p.parse_args(); plan,_,manifest=(prepare if a.command=='prepare' else check)(a.source_dir,a.model_dir)
    print(json.dumps({'jobs':len(plan['jobs']),**{k:manifest[k] for k in ('counts','planned_local_input_tokens','planned_jev_request_utf8_bytes_plus_4096_per_call','plan_sha256')}}))


if __name__=='__main__': main()
