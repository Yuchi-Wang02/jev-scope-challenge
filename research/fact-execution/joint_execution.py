"""Frozen N1/native joint-route pilot and both direct controls; no rewrites."""
import argparse
import importlib.metadata
import json
import platform
import random
import subprocess
import time

from data_tools import HERE, original_cases
from fact_run import freeze as old_fact_freeze
from gap_run import read_rows, spec, tokenizer_for, write_json
from joint_route_plan import JOINT, PREP, run as verify_joint_plan
from joint_token_control import SELECTED, run as verify_token_control
from line_evidence import visible_lines
from line_run import _check_weights, sha

SEED = 20261006
ENCODED = PREP / 'joint_native_scientific.jsonl'
MANIFEST = PREP / 'joint_execution_manifest.json'
OUT = HERE / 'joint_results/v0.1'
SOURCE_PATHS = (
    'JOINT_EXECUTION_PROTOCOL.md', 'joint_route.py', 'joint_route_plan.py',
    'joint_token_control.py', 'joint_execution.py', 'joint_analyze.py',
    'interface.py', 'line_evidence.py', 'data_tools.py',
    'data/original_cases.jsonl', 'data/reference_facts.jsonl',
    'preparation/joint_route_queries.jsonl',
    'preparation/joint_route_query_manifest.json',
    'preparation/joint_direct_queries.jsonl',
    'preparation/joint_direct_all_token_costs.jsonl',
    'preparation/joint_direct_token_matched.jsonl',
    'preparation/joint_direct_token_manifest.json',
    '../evidence-gap/gap_data.py', '../evidence-gap/gap_run.py',
    '../evidence-gap/gap_analyze.py', '../next-study/study.py',
    'line_run.py', 'line_analyze.py',
    '../next-study/results/weight_checksums.json')


def json_lines(rows):
    return ''.join(json.dumps(row, ensure_ascii=False, separators=(',', ':'),
                              allow_nan=False) + '\n' for row in rows).encode('utf-8')


def plan_id(row):
    if row['arm'] == 'joint':
        return f"joint/{row['source_id']}/{row['line_index']}"
    if row['arm'] == 'direct':
        return f"direct/{row['source_id']}/{row['mapping']}"
    raise ValueError('Foreign plan arm')


def source_plans():
    verify_joint_plan('verify')
    verify_token_control('verify', 'unused-cache')
    old_fact_freeze()
    joint = [row | {'arm': 'joint'} for row in read_rows(JOINT) if row['mapping'] == 0]
    direct = [row | {'arm': 'direct'} for row in read_rows(SELECTED)]
    rows = joint + direct
    if (len(joint) != 228 or len(direct) != 286 or
            len({plan_id(row) for row in rows}) != 514 or
            len({row['source_id'] for row in joint}) != 72 or
            any(row['split'] != 'development' or row['representation'] != 'original'
                for row in rows)):
        raise ValueError('Scientific query scope or count drift')
    return rows


def planned_encoded(cache):
    tokenizer = tokenizer_for(cache)
    candidates = {letter: tokenizer.encode(' ' + letter, add_special_tokens=False)
                  for letter in 'ABCDEFGH'}
    if any(len(ids) != 1 for ids in candidates.values()) or len(
            {ids[0] for ids in candidates.values()}) != 8:
        raise ValueError('Native answer letters A-H are not distinct single tokens')
    rows = []
    for source in source_plans():
        ids = tokenizer.encode(source['prompt'], add_special_tokens=False)
        letters = 'ABCDEFGH'[:len(source['order'])]
        for letter in letters:
            if tokenizer.encode(source['prompt'] + ' ' + letter,
                                add_special_tokens=False) != ids + candidates[letter]:
                raise ValueError('Native answer-token boundary drift')
        if source['arm'] == 'direct' and len(ids) != source['planned_input_tokens']:
            raise ValueError('Direct token-control count drift')
        rows.append(source | {'query_id': plan_id(source), 'token_ids': ids,
                              'candidate_ids': [candidates[x][0] for x in letters]})
    if (sum(len(r['token_ids']) for r in rows if r['arm'] == 'joint') != 95889 or
            sum(len(r['token_ids']) for r in rows if r['arm'] == 'direct') != 95849):
        raise ValueError('Primary input-token budget drift')
    return rows


def freeze(cache):
    rows = planned_encoded(cache)
    payload = json_lines(rows)
    manifest = {
        'study': 'joint-route-N1-native-original-development-v0.1',
        'status': 'pre_inference_freeze', 'seed': SEED,
        'arm': 'N1', 'base': spec.BASE, 'base_revision': spec.BASE_REV,
        'adapter': spec.ADAPTER, 'adapter_revision': spec.ADAPTER_REV,
        'allowed_splits': ['development'],
        'allowed_representations': ['original'],
        'joint_primary_forwards': 228, 'direct_union_forwards': 286,
        'call_matched_direct_forwards': 228,
        'token_matched_direct_forwards': 286,
        'scientific_forwards': 514, 'warmup_forwards': 2,
        'joint_input_tokens': 95889, 'direct_union_input_tokens': 95849,
        'call_matched_direct_input_tokens': 76855,
        'total_scientific_input_tokens': 191738,
        'max_input_tokens': max(len(r['token_ids']) for r in rows),
        'encoded_plan_sha256_lf': sha(payload),
        'source_file_sha256_lf': {path: sha((HERE / path).read_bytes())
                                  for path in SOURCE_PATHS},
        'new_training': False, 'paid_api_calls': 0,
        'jev_api_calls': 0, 'rewrite_model_records': 0,
        'reserved_model_records': 0,
        'independent_human_annotations': 0,
        'post_hoc_public_development': True}
    manifest['config_hash'] = sha(json.dumps(manifest, sort_keys=True,
                                           separators=(',', ':')).encode('utf-8'))
    manifest_bytes = (json.dumps(manifest, indent=2) + '\n').encode('utf-8')
    PREP.mkdir(exist_ok=True)
    for path, expected in ((ENCODED, payload), (MANIFEST, manifest_bytes)):
        if path.exists():
            if path.read_bytes().replace(b'\r\n', b'\n') != expected:
                raise ValueError(f'Frozen encoded plan drift: {path.name}')
        else:
            path.write_bytes(expected)
    return manifest


def verify_frozen():
    """Read-only source and encoded-grid verification, no tokenizer required."""
    planned = source_plans()
    rows = read_rows(ENCODED)
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    if len(rows) != 514 or len(planned) != 514:
        raise ValueError('Incomplete encoded scientific grid')
    for row, source in zip(rows, planned):
        if any(row.get(key) != value for key, value in source.items()):
            raise ValueError(f'Encoded source query drift: {plan_id(source)}')
        if (row.get('query_id') != plan_id(source) or
                not isinstance(row.get('token_ids'), list) or
                not row['token_ids'] or
                not all(isinstance(t, int) and t >= 0 for t in row['token_ids']) or
                len(row.get('candidate_ids', [])) != len(source['order']) or
                len(set(row['candidate_ids'])) != len(source['order']) or
                not all(isinstance(t, int) and t >= 0 for t in row['candidate_ids']) or
                (source['arm'] == 'direct' and
                 len(row['token_ids']) != source['planned_input_tokens'])):
            raise ValueError('Invalid encoded query, token or candidate identity')
    line_counts = {case['id']: len(visible_lines(case['state']))
                   for case in original_cases()}
    call_matched = [r for r in rows if r['arm'] == 'direct' and
                    r['mapping'] < line_counts[r['source_id']]]
    if (manifest['encoded_plan_sha256_lf'] != sha(ENCODED.read_bytes()) or
            manifest['source_file_sha256_lf'] != {
                path: sha((HERE / path).read_bytes()) for path in SOURCE_PATHS} or
            manifest['joint_input_tokens'] != sum(len(r['token_ids']) for r in rows
                                                  if r['arm'] == 'joint') or
            manifest['direct_union_input_tokens'] != sum(len(r['token_ids']) for r in rows
                                                         if r['arm'] == 'direct') or
            manifest['call_matched_direct_input_tokens'] != sum(
                len(r['token_ids']) for r in call_matched) or
            len(call_matched) != manifest['call_matched_direct_forwards'] or
            manifest['total_scientific_input_tokens'] != sum(len(r['token_ids'])
                                                             for r in rows) or
            manifest['max_input_tokens'] != max(len(r['token_ids']) for r in rows)):
        raise ValueError('Execution manifest source, plan or cost drift')
    check = dict(manifest)
    digest = check.pop('config_hash')
    if sha(json.dumps(check, sort_keys=True, separators=(',', ':')).encode('utf-8')) != digest:
        raise ValueError('Execution manifest config hash drift')
    if (manifest['study'] != 'joint-route-N1-native-original-development-v0.1' or
            manifest['allowed_splits'] != ['development'] or
            manifest['allowed_representations'] != ['original'] or
            manifest['arm'] != 'N1' or manifest['scientific_forwards'] != 514 or
            manifest['joint_primary_forwards'] != 228 or
            manifest['direct_union_forwards'] != 286 or
            manifest['token_matched_direct_forwards'] != 286 or
            manifest['call_matched_direct_forwards'] != 228 or
            manifest['warmup_forwards'] != 2 or
            manifest['new_training'] is not False or
            manifest['paid_api_calls'] != 0 or manifest['jev_api_calls'] != 0 or
            manifest['rewrite_model_records'] != 0 or
            manifest['reserved_model_records'] != 0):
        raise ValueError('Unapproved execution scope')
    return manifest


def run(cache):
    """Local scientific inference entry point. Never called during preparation."""
    manifest = freeze(cache)
    verify_frozen()
    if subprocess.check_output(['git', 'status', '--porcelain'], cwd=HERE):
        raise ValueError('Commit the full source freeze before inference')
    if OUT.exists() and any(OUT.iterdir()):
        raise ValueError('Existing joint-route outputs; never overwrite or cherry-pick')
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM

    OUT.mkdir(parents=True, exist_ok=True)
    env = {'status': 'loading', 'config_hash': manifest['config_hash'],
           'execution_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'],
                                                       cwd=HERE, text=True).strip(),
           'python': platform.python_version(), 'gpu': torch.cuda.get_device_name(0),
           'cuda': torch.version.cuda,
           'packages': {p: importlib.metadata.version(p) for p in
                        ('torch', 'transformers', 'peft', 'huggingface-hub', 'numpy')},
           'scientific_forwards': 0, 'warmup_forwards': 0,
           'rewrite_model_records': 0, 'reserved_model_records': 0,
           'paid_api_calls': 0, 'jev_api_calls': 0, 'new_training': False,
           'start_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    write_json(OUT / 'runtime.json', env)
    started = time.perf_counter()
    try:
        torch.manual_seed(SEED)
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        torch.backends.cuda.enable_flash_sdp(False)
        torch.backends.cuda.enable_mem_efficient_sdp(False)
        torch.backends.cuda.enable_cudnn_sdp(False)
        torch.backends.cuda.enable_math_sdp(True)
        torch.cuda.reset_peak_memory_stats()
        base, adapter, weights = _check_weights(cache)
        write_json(OUT / 'weight_checksums.json', weights)
        jobs = read_rows(ENCODED)
        random.Random(SEED).shuffle(jobs)
        lm = AutoModelForCausalLM.from_pretrained(
            base, torch_dtype=torch.bfloat16, attn_implementation='sdpa',
            local_files_only=True).to('cuda').eval()
        lm.model = PeftModel.from_pretrained(lm.model, adapter,
                                            is_trainable=False)
        lm.eval()
        from safetensors.torch import load_file
        saved = load_file(adapter / 'adapter_model.safetensors')
        actual = dict(lm.model.named_parameters())
        for name, value in saved.items():
            key = name.replace('.lora_A.weight', '.lora_A.default.weight').replace(
                '.lora_B.weight', '.lora_B.default.weight')
            if key not in actual or not torch.equal(actual[key].detach().cpu().float(),
                                                     value.float()):
                raise ValueError('Adapter tensor mismatch')
        if len(saved) != 504 or sum(t.numel() for t in saved.values()) != 33030144:
            raise ValueError('Adapter inventory mismatch')
        write_json(OUT / 'adapter_audit.json',
                   {'status': 'passed', 'exact_tensors': len(saved),
                    'parameters': sum(t.numel() for t in saved.values())})
        eos_id = tokenizer_for(cache).eos_token_id
        for _ in range(2):
            with torch.inference_mode():
                lm(input_ids=torch.tensor([[eos_id]], device='cuda'))
            env['warmup_forwards'] += 1
        with (OUT / 'N1.jsonl').open('w', encoding='utf-8', newline='\n') as stream:
            for number, job in enumerate(jobs, 1):
                torch.cuda.synchronize()
                tick = time.perf_counter()
                with torch.inference_mode():
                    full = lm(input_ids=torch.tensor([job['token_ids']],
                                                      device='cuda')).logits[0, -1].float()
                    z = full[job['candidate_ids']]
                    probs = torch.softmax(z, -1)
                    mass = torch.softmax(full, -1)[job['candidate_ids']].sum().item()
                torch.cuda.synchronize()
                record = dict(job)
                record.update(config_hash=manifest['config_hash'], forward_index=number,
                              ok=True, input_tokens=len(job['token_ids']),
                              latency_s=time.perf_counter() - tick,
                              candidate_mass=mass, logits=z.cpu().tolist(),
                              probabilities=probs.cpu().tolist(),
                              prediction=job['order'][int(probs.argmax())])
                stream.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + '\n')
                stream.flush()
                env['scientific_forwards'] = number
                if number % 48 == 0:
                    write_json(OUT / 'runtime.json', env)
                    print(f'N1 joint/direct: {number}/514', flush=True)
        env.update(status='complete', elapsed_s=time.perf_counter() - started,
                   peak_allocated_mib=torch.cuda.max_memory_allocated() / 1024**2,
                   sdpa_kernel='math_only', backbone_dtype='bfloat16',
                   adapter_exact_tensors=504)
        write_json(OUT / 'runtime.json', env)
        print(json.dumps(env, indent=2), flush=True)
    except BaseException as error:
        env.update(status='failed', error_type=type(error).__name__, error=str(error),
                   elapsed_s=time.perf_counter() - started)
        write_json(OUT / 'runtime.json', env)
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('build', 'verify-freeze', 'run'))
    parser.add_argument('--cache', default='G:/jev-lab/hf-cache')
    args = parser.parse_args()
    report = (freeze(args.cache) if args.command == 'build' else
              verify_frozen() if args.command == 'verify-freeze' else run(args.cache))
    if args.command in ('build', 'verify-freeze'):
        print(json.dumps({'status': 'pre_inference_freeze_verified',
                          'planned_forwards': report['scientific_forwards'],
                          'planned_input_tokens': report['total_scientific_input_tokens'],
                          'model_forwards': 0}))
