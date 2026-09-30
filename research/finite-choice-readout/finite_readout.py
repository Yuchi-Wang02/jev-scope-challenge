"""Frozen single-prefill letter control. Importing loads no weights or keys."""
import argparse
import json
import math
import os
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'research/external-validation'))
from comparison_plan import INSTRUCTIONS, ORDERS, QWEN_REVISION, checked_tokenizer, canonical, readable, sha, visible_state
from comparison_backends import file_hash
from execution_journal import execute, read_events, replay, outcome, stop_reason, exclusive_lock
from paired_metrics import score_condition

PARENT = ROOT / 'research/source-label-screen'
STUDY = 'sharc-finite-letter-prefill-v1'
LETTERS = 'ABCD'
TOKEN_IDS = [32, 33, 34, 35]
LIMITS = {'http_attempts': 0, 'http_retries': 0, 'local_generations': 56,
          'local_input_tokens': 50000, 'local_generated_tokens': 0,
          'local_generation_wall_seconds': 300, 'local_context_tokens': 32768}


def read(path):
    return json.loads(Path(path).read_bytes())


def lfhash(path):
    return sha(Path(path).read_bytes().replace(b'\r\n', b'\n'))


def preserve(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes().replace(b'\r\n', b'\n') != data:
            raise ValueError('Existing artifact differs; preserve prior evidence')
    else:
        path.write_bytes(data)


def source_pins():
    names = set(read(PARENT / 'freeze.json')['source_hashes_lf'])
    names.update(('research/finite-choice-readout/finite_readout.py',
                  'research/finite-choice-readout/PROTOCOL.md'))
    return {name: lfhash(ROOT / name) for name in sorted(names)}


def parent_pins():
    return {name: lfhash(PARENT / name) for name in ('freeze.json', 'plan.json', 'references.json',
            'results/comparison.json', 'results/qwen.jsonl')}


def extract(values, full_logsumexp, top_id, top_logit, options):
    if (len(values) != 4 or list(options) not in [list(o) for o in ORDERS] or
            any(type(x) not in (int, float) or not math.isfinite(x)
                for x in [*values, full_logsumexp, top_logit]) or
            type(top_id) != int or top_id < 0):
        raise ValueError('Invalid finite logit record')
    maximum = max(values)
    if full_logsumexp < top_logit - 1e-9 or top_logit < maximum - 1e-9:
        raise ValueError('Impossible full-vocabulary metadata')
    if top_id in TOKEN_IDS and top_logit != values[TOKEN_IDS.index(top_id)]:
        raise ValueError('Top-token logit mismatch')
    total = sum(math.exp(x - maximum) for x in values)
    norm = maximum + math.log(total)
    mass = math.exp(norm - full_logsumexp)
    if mass > 1 + 1e-9:
        raise ValueError('Candidate mass exceeds full vocabulary')
    winners = [i for i, x in enumerate(values) if x == maximum]
    index = winners[0] if len(winners) == 1 else None
    return {'action': options[index] if index is not None else None,
        'letter': LETTERS[index] if index is not None else None, 'exact_tie': index is None,
        'conditional_probabilities': {l: math.exp(x - maximum) / total for l, x in zip(LETTERS, values)},
        'full_vocabulary_candidate_mass': mass, 'unconstrained_top_is_candidate': top_id in TOKEN_IDS}


def build(tokenizer, files):
    parent = read(PARENT / 'plan.json')
    jobs = []
    def add(ident, prompt, options, phase, expected=None, state=None):
        rendered = tokenizer.apply_chat_template([{'role': 'user', 'content': prompt}],
            tokenize=False, add_generation_prompt=True, enable_thinking=False)
        ids = tokenizer.encode(rendered, add_special_tokens=False)
        if not ids or len(ids) > LIMITS['local_context_tokens']:
            raise ValueError('Bad input length')
        for letter, token in zip(LETTERS, TOKEN_IDS):
            if tokenizer.encode(rendered + letter, add_special_tokens=False) != ids + [token]:
                raise ValueError('Letter is not one stable continuation token')
        jobs.append({'id': ident, 'backend': 'qwen', 'phase': phase, 'prompt': prompt,
            'options': list(options), 'rendered_input': rendered, 'input_ids': ids,
            'max_new_tokens': 0, 'expected_smoke_action': expected, 'state': state})
    for order, options in enumerate(ORDERS):
        mapping = '\n'.join(f'{letter}: {action}' for letter, action in zip(LETTERS, options))
        for letter, expected in zip(LETTERS, options):
            add(f'smoke_order{order}_{letter}',
                f'Interface copy test. Return exactly the letter {letter}, with no explanation or punctuation.\n'
                f'The action mapping is:\n{mapping}', options, 'smoke', expected=expected)
    main = []
    for prior in parent['jobs']:
        if prior['condition'] not in ('jev_order0', 'jev_order1'):
            continue
        state, options = prior['request']['state'], prior['options']
        if state != visible_state(state):
            raise ValueError('Unexpected task-state fields')
        mapping = '\n'.join(f'{letter}: {action}' for letter, action in zip(LETTERS, options))
        prompt = INSTRUCTIONS + '\nReturn exactly one letter from A, B, C, D. No explanation or punctuation.\n'
        prompt += 'Action mapping:\n' + mapping + '\nVisible state:\n' + canonical(state)
        ident = prior['item_id'] + '_prefill_order' + prior['condition'][-1]
        add(ident, prompt, options, 'main', state=state)
        main.append(jobs.pop())
        main[-1].update(item_id=prior['item_id'], condition='prefill_order' + prior['condition'][-1])
    jobs += sorted(main, key=lambda j: sha(canonical([STUDY, j['id']]).encode()))
    if len(jobs) != 56 or sum(len(j['input_ids']) for j in jobs) > LIMITS['local_input_tokens']:
        raise ValueError('Grid/budget mismatch')
    return {'study': STUDY, 'jobs': jobs, 'limits': LIMITS, 'tokenizer_files': files,
        'token_ids': TOKEN_IDS, 'new_model_calls_at_freeze': 0,
        'reference_basis': 'same public source labels, no new human review',
        'planned_input_tokens': sum(len(j['input_ids']) for j in jobs)}


def prepare(model_dir):
    tokenizer, files = checked_tokenizer(model_dir)
    plan = build(tokenizer, files)
    freeze = {'study': STUDY, 'status': 'frozen_for_prefill', 'plan_sha256': sha(readable(plan)),
              'source_hashes_lf': source_pins(), 'parent_hashes_lf': parent_pins()}
    preserve(HERE / 'plan.json', readable(plan)); preserve(HERE / 'freeze.json', readable(freeze))
    return plan, freeze


def check(clean=False):
    freeze, plan = read(HERE / 'freeze.json'), read(HERE / 'plan.json')
    if (freeze['study'] != STUDY or freeze['status'] != 'frozen_for_prefill' or
            freeze['plan_sha256'] != lfhash(HERE / 'plan.json') or
            freeze['source_hashes_lf'] != source_pins() or freeze['parent_hashes_lf'] != parent_pins()):
        raise ValueError('Freeze or parent evidence changed')
    if clean:
        if subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT).strip():
            raise ValueError('Need a clean committed freeze')
        for name in ('freeze.json', 'plan.json', 'PROTOCOL.md'):
            path = HERE / name
            saved = subprocess.check_output(['git', 'show', 'HEAD:' + path.relative_to(ROOT).as_posix()], cwd=ROOT)
            if saved.replace(b'\r\n', b'\n') != path.read_bytes().replace(b'\r\n', b'\n'):
                raise ValueError('Uncommitted freeze')
    return plan, freeze


@contextmanager
def backend(model_dir, plan):
    for key in ('HF_HUB_OFFLINE', 'TRANSFORMERS_OFFLINE', 'HF_HUB_DISABLE_TELEMETRY', 'HF_HUB_DISABLE_PROGRESS_BARS'):
        os.environ[key] = '1'
    import torch
    import transformers
    import peft
    if (torch.__version__ != '2.8.0+cu128' or transformers.__version__ != '5.3.0' or peft.__version__ != '0.18.1'):
        raise ValueError('Runtime version mismatch')
    start = time.monotonic()
    tokenizer, files = checked_tokenizer(model_dir)
    if build(tokenizer, files) != plan:
        raise ValueError('Plan no longer reconstructs')
    model_files = read(ROOT / 'research/baseline-readiness/qwen35-smoke-repaired/run.json')['model_files']
    for f in model_files:
        p = model_dir / f['name']
        if p.stat().st_size != f['bytes'] or file_hash(p) != f['sha256']:
            raise ValueError('Model file mismatch')
    verify_seconds = time.monotonic() - start
    start = time.monotonic(); torch.cuda.reset_peak_memory_stats()
    model = transformers.Qwen3_5ForConditionalGeneration.from_pretrained(model_dir,
        dtype=torch.bfloat16, device_map={'': 'cuda:0'}, attn_implementation='sdpa',
        local_files_only=True, trust_remote_code=False)
    model.eval(); torch.cuda.synchronize()
    if ({str(p.device) for p in model.parameters()} != {'cuda:0'} or
            {str(p.dtype) for p in model.parameters()} != {'torch.bfloat16'}):
        raise ValueError('Placement/precision mismatch')
    count = [0]
    def hook(module, inputs):
        count[0] += 1
    handle = model.register_forward_pre_hook(hook)
    metadata = {'model': 'Qwen/Qwen3.5-4B', 'revision': QWEN_REVISION, 'python': sys.version,
        'torch': torch.__version__, 'transformers': transformers.__version__, 'peft': peft.__version__,
        'gpu': torch.cuda.get_device_name(0), 'model_files': model_files,
        'verification_seconds': verify_seconds, 'load_seconds': time.monotonic() - start,
        'warmup_forwards': 0, 'execution_commit': subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()}
    def call(job, remaining_seconds):
        start = time.monotonic(); before = count[0]
        ids = torch.tensor([job['input_ids']], device='cuda:0')
        torch.cuda.synchronize()
        with torch.inference_mode():
            out = model(input_ids=ids, attention_mask=torch.ones_like(ids),
                        use_cache=True, logits_to_keep=1, return_dict=True)
        torch.cuda.synchronize()
        logits = out.logits[0, -1].double()
        forwards = count[0] - before
        if forwards != 1 or not bool(torch.isfinite(logits).all().item()):
            return {'status':'protocol_error','action':None,'input_tokens':len(job['input_ids']),
                'output_tokens':0,'latency_seconds':time.monotonic()-start,
                'detail':{'error':'nonfinite_logits_or_forward_count','physical_forwards':forwards}}
        values = logits[TOKEN_IDS].tolist()
        top_id = int(logits.argmax().item()); top_logit = float(logits[top_id].item())
        norm = float(torch.logsumexp(logits,dim=0).item())
        parsed = extract(values, norm, top_id, top_logit, job['options'])
        detail = {'candidate_logits':values,'full_logsumexp':norm,'top_token_id':top_id,
            'top_logit':top_logit,'top_token_text':tokenizer.decode([top_id]),'parsed':parsed,
            'physical_forwards':forwards, 'use_cache':True,'logits_to_keep':1,
            'stage_peak_allocated_bytes':torch.cuda.max_memory_allocated(),
            'stage_peak_reserved_bytes':torch.cuda.max_memory_reserved()}
        status, action = 'ok', parsed['action']
        if job['phase']=='smoke' and action != job['expected_smoke_action']:
            status, action = 'protocol_error', None
            detail['error'] = 'smoke_gate_miss'
        return {'status':status,'action':action,'input_tokens':len(job['input_ids']),
                'output_tokens':0,'latency_seconds':time.monotonic()-start,'detail':detail}
    try:
        yield call, metadata
    finally:
        handle.remove(); del model; torch.cuda.empty_cache()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=('prepare','verify','run'))
    p.add_argument('--model-dir',type=Path,required=True)
    args=p.parse_args()
    if args.command=='prepare':
        plan,freeze=prepare(args.model_dir)
        print(json.dumps({'status':'prepared_no_forwards','jobs':len(plan['jobs']),
                          'input_tokens':plan['planned_input_tokens']})); return
    plan,freeze=check(clean=True)
    tokenizer,files=checked_tokenizer(args.model_dir)
    if build(tokenizer,files)!=plan: raise ValueError('Frozen plan differs')
    if args.command=='verify':
        print(json.dumps({'status':'verified_no_forwards','jobs':len(plan['jobs'])})); return
    directory=ROOT/'.local'/STUDY/('execution-'+freeze['plan_sha256'])
    result=execute(directory,plan,freeze['plan_sha256'],'qwen',lambda:backend(args.model_dir,plan))
    print(json.dumps({'status':result['status'],'attempts':len(result['state']['started']),
                      'finished':len(result['state']['results']),'input_tokens':result['state']['input_tokens'],
                      'overruns':result['overruns']}))


if __name__=='__main__': main()
