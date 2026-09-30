"""Freeze or run the bounded ownership diagnostic; preparation never calls a model."""
import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import math
import os
import platform
import random
import re
import subprocess
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / 'results/v0.1'
ENCODED = HERE / 'preparation/execution_queries.jsonl'
MANIFEST = HERE / 'preparation/execution_manifest.json'
SEED = 20261007
SPLIT = 'new_scene_development'
REPRESENTATION = 'new_scene_original_declared_grammar'
ARM_COUNTS = {'joint_full': 200, 'direct_full': 200, 'direct_filtered': 100}
ARM_TOKENS = {'joint_full': 85214, 'direct_full': 71050, 'direct_filtered': 32533}
ZERO_FLAGS = ('paid_api_calls', 'jev_api_calls', 'rewrite_model_records',
              'reserved_model_records', 'original_development_model_records')
SUPPORT_FILES = ('base/config.json', 'base/model.safetensors.index.json',
                 'adapter/adapter_config.json')
SOURCE_PATHS = (
    'execution.py', 'analyze.py', 'EXECUTION_PROTOCOL.md', 'prepare.py', 'PROTOCOL.md',
    'data/scenes.jsonl', 'data/views.jsonl', 'preparation/manifest.json',
    'preparation/queries.jsonl', 'preparation/encoded_queries.jsonl',
    'preparation/token_manifest.json',
    '../fact-execution/scope_gate.py', '../fact-execution/interface.py',
    '../fact-execution/joint_route.py', '../fact-execution/joint_route_plan.py',
    '../fact-execution/line_evidence.py', '../fact-execution/data_tools.py',
    '../fact-execution/line_run.py', '../fact-execution/fact_run.py',
    '../fact-execution/line_plan_tools.py',
    '../evidence-gap/gap_data.py', '../evidence-gap/gap_run.py',
    '../next-study/study.py', '../next-study/results/weight_checksums.json',
    '../../tests/test_request_ownership.py', '../../tests/test_ownership_execution.py',
    '../../tests/test_ownership_analysis.py')


def sha(payload):
    return hashlib.sha256(payload.replace(b'\r\n', b'\n')).hexdigest()


def load_preparation():
    definition = importlib.util.spec_from_file_location('ownership_preparation_runtime', HERE / 'prepare.py')
    module = importlib.util.module_from_spec(definition)
    definition.loader.exec_module(module)
    return module


def read_rows(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]


def packed(rows):
    return ''.join(json.dumps(r, ensure_ascii=False, separators=(',', ':'),
                              allow_nan=False) + '\n' for r in rows).encode('utf-8')


def pretty(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode('utf-8')


def source_plans():
    prep = load_preparation()
    artifacts, _ = prep.artifacts()
    prep.check_or_write(artifacts, False)
    artifacts, _ = prep.encoded_artifacts()
    prep.check_or_write(artifacts, False)
    queries = read_rows(HERE / 'preparation/queries.jsonl')
    encodings = read_rows(HERE / 'preparation/encoded_queries.jsonl')
    rows = []
    for query, encoded in zip(queries, encodings):
        if query['query_id'] != encoded['query_id']:
            raise ValueError('Encoding query identity drift')
        candidate_ids = encoded['candidate_ids']
        if (len(set(candidate_ids)) != len(candidate_ids) or
                any(type(t) is not int or t < 0 for t in candidate_ids) or
                len(query['order']) not in ((6, 8) if query['arm'] == 'joint_full' else (3,))):
            raise ValueError('Invalid candidate identity or width')
        rows.append(query | encoded | {'split': SPLIT})
    costs = Counter()
    for row in rows:
        costs[row['arm']] += row['input_tokens']
    if (len(rows) != 500 or len({r['query_id'] for r in rows}) != 500 or
            len({r['view_id'] for r in rows}) != 48 or len({r['parent'] for r in rows}) != 24 or
            Counter(r['arm'] for r in rows) != ARM_COUNTS or dict(costs) != ARM_TOKENS or
            any(r['representation'] != REPRESENTATION for r in rows) or
            sum(r['input_tokens'] for r in rows) != 188797):
        raise ValueError('Ownership scientific grid or budget drift')
    return rows


def cache_paths(cache):
    spec = load_preparation().spec
    root = Path(cache)
    return {'base': root / 'models--Qwen--Qwen3-4B-Base/snapshots' / spec.BASE_REV,
            'adapter': root / 'models--jaredpalmer--kev-4b/snapshots' / spec.ADAPTER_REV}


def support_hashes(cache):
    paths = cache_paths(cache)
    return {name: sha((paths[name.split('/')[0]] / name.split('/', 1)[1]).read_bytes())
            for name in SUPPORT_FILES}


def expected_manifest(rows, support):
    spec = load_preparation().spec
    if (set(support) != set(SUPPORT_FILES) or
            any(not isinstance(value, str) or not re.fullmatch('[a-f0-9]{64}', value)
                for value in support.values())):
        raise ValueError('Incomplete pinned cache configuration hashes')
    manifest = {
        'study': 'request-ownership-N1-native-new-scene-development-v0.1',
        'status': 'pre_inference_freeze', 'seed': SEED, 'arm': 'N1',
        'base': spec.BASE, 'base_revision': spec.BASE_REV,
        'adapter': spec.ADAPTER, 'adapter_revision': spec.ADAPTER_REV,
        'allowed_splits': [SPLIT], 'allowed_representations': [REPRESENTATION],
        'parent_scenes': 24, 'views': 48, 'scientific_forwards': 500,
        'warmup_forwards': 2, 'warmup_token_ids': [151643],
        'planned_input_tokens': 188797, 'warmup_input_tokens': 2,
        'forwards_by_arm': ARM_COUNTS, 'input_tokens_by_arm': ARM_TOKENS,
        'max_input_tokens': max(r['input_tokens'] for r in rows),
        'encoded_plan_sha256_lf': sha(packed(rows)),
        'source_file_sha256_lf': {p: sha((HERE / p).read_bytes()) for p in SOURCE_PATHS},
        'cached_support_files_sha256_lf': support,
        'new_training': False, **dict.fromkeys(ZERO_FLAGS, 0),
        'independent_human_annotations': 0,
        'uses_inspected_language_and_policy_grammar': True,
        'primary_endpoint': 'complete_target_switch_pairs_correct_out_of_24',
        'directional_rule': 'joint_gated_pairs_gt_joint_full_and_false_commitments_le_joint_full'}
    manifest['config_hash'] = sha(json.dumps(manifest, sort_keys=True,
                                           separators=(',', ':')).encode('utf-8'))
    return manifest


def freeze(cache):
    """Create once; refuse drift. Reads cached configs but no model weights."""
    rows = source_plans()
    manifest = expected_manifest(rows, support_hashes(cache))
    artifacts = {ENCODED: packed(rows), MANIFEST: pretty(manifest)}
    for path, expected in artifacts.items():
        if path.exists() and path.read_bytes().replace(b'\r\n', b'\n') != expected:
            raise ValueError(f'Existing execution freeze differs: {path.name}')
    for path, expected in artifacts.items():
        if not path.exists():
            with path.open('xb') as stream:
                stream.write(expected)
    return manifest


def verify_frozen():
    """Exact read-only verification with no torch, tokenizer, cache or inference."""
    rows = source_plans()
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    expected = expected_manifest(rows, manifest['cached_support_files_sha256_lf'])
    if manifest != expected or ENCODED.read_bytes().replace(b'\r\n', b'\n') != packed(rows):
        raise ValueError('Execution freeze source, scope, encoding or cost drift')
    return manifest


def reserve_output(approved_config_hash, out=None):
    """Validate before loading dependencies; atomically reserve a never-used run path."""
    manifest = verify_frozen()
    if not approved_config_hash or approved_config_hash != manifest['config_hash']:
        raise ValueError('Explicit approved config hash is required; old approvals do not transfer')
    if subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT):
        raise ValueError('Commit the complete source freeze before inference')
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    destination = OUT if out is None else Path(out)
    destination.parent.mkdir(parents=True, exist_ok=True)
    # exist_ok=False also rejects an empty directory left by an interrupted run.
    destination.mkdir(exist_ok=False)
    return manifest, commit, destination


def checkpoint(out, env):
    temporary = out / 'runtime.pending.json'
    with temporary.open('wb') as stream:
        stream.write(pretty(env))
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, out / 'runtime.json')


def validate_values(logits, probs, mass, latency):
    if (not logits or len(logits) != len(probs) or
            any(not math.isfinite(x) for x in logits + probs + [mass, latency]) or
            any(p < 0 or p > 1 for p in probs) or
            not math.isclose(sum(probs), 1, abs_tol=2e-6) or
            not 0 <= mass <= 1 or latency < 0):
        raise ValueError('Invalid model numeric output; preserve attempt and stop')


def run(cache, approved_config_hash):
    manifest, commit, out = reserve_output(approved_config_hash)
    env = {'status': 'loading', 'config_hash': manifest['config_hash'],
           'execution_commit': commit, 'python': platform.python_version(),
           'scientific_forwards': 0, 'attempted_scientific_forwards': 0,
           'warmup_forwards': 0, 'attempted_warmup_forwards': 0,
           **dict.fromkeys(ZERO_FLAGS, 0), 'new_training': False,
           'attempt_accounting': 'checkpointed before invocation; crash-safe upper bound',
           'start_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    checkpoint(out, env)
    started = time.perf_counter()
    try:
        for name in ('HF_HUB_OFFLINE', 'TRANSFORMERS_OFFLINE', 'HF_DATASETS_OFFLINE'):
            os.environ[name] = '1'
        import torch
        from peft import PeftModel
        from transformers import AutoModelForCausalLM
        from safetensors.torch import load_file
        from line_run import _check_weights
        if not torch.cuda.is_available():
            raise ValueError('Approved local CUDA environment is unavailable')
        if support_hashes(cache) != manifest['cached_support_files_sha256_lf']:
            raise ValueError('Cached model configuration drift')
        base, adapter, weights = _check_weights(cache)
        (out / 'weight_checksums.json').write_bytes(pretty(weights))
        env.update(gpu=torch.cuda.get_device_name(0), cuda=torch.version.cuda,
                   packages={p: importlib.metadata.version(p) for p in
                             ('torch', 'transformers', 'peft', 'huggingface-hub', 'numpy')},
                   sdpa_kernel='math_only', backbone_dtype='bfloat16')
        torch.manual_seed(SEED)
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        torch.backends.cuda.enable_flash_sdp(False)
        torch.backends.cuda.enable_mem_efficient_sdp(False)
        torch.backends.cuda.enable_cudnn_sdp(False)
        torch.backends.cuda.enable_math_sdp(True)
        torch.cuda.reset_peak_memory_stats()
        lm = AutoModelForCausalLM.from_pretrained(
            base, torch_dtype=torch.bfloat16, attn_implementation='sdpa',
            local_files_only=True).to('cuda').eval()
        lm.model = PeftModel.from_pretrained(lm.model, adapter, is_trainable=False,
                                            local_files_only=True)
        lm.eval()
        if lm.config.eos_token_id != manifest['warmup_token_ids'][0]:
            raise ValueError('Pinned EOS warmup token drift')
        saved = load_file(adapter / 'adapter_model.safetensors')
        actual = dict(lm.model.named_parameters())
        for name, value in saved.items():
            key = name.replace('.lora_A.weight', '.lora_A.default.weight').replace(
                '.lora_B.weight', '.lora_B.default.weight')
            if key not in actual or not torch.equal(actual[key].detach().cpu().float(), value.float()):
                raise ValueError('Loaded adapter tensor mismatch')
        if len(saved) != 504 or sum(t.numel() for t in saved.values()) != 33030144:
            raise ValueError('Adapter inventory mismatch')
        env['adapter_exact_tensors'] = 504
        (out / 'adapter_audit.json').write_bytes(pretty(
            {'status': 'passed', 'exact_tensors': 504, 'parameters': 33030144}))
        for number in range(1, 3):
            env.update(status='warming', attempted_warmup_forwards=number)
            checkpoint(out, env)
            with torch.inference_mode():
                lm(input_ids=torch.tensor([manifest['warmup_token_ids']], device='cuda'))
            torch.cuda.synchronize()
            env['warmup_forwards'] = number
            checkpoint(out, env)
        jobs = source_plans()
        random.Random(SEED).shuffle(jobs)
        with (out / 'N1.jsonl').open('x', encoding='utf-8', newline='\n') as stream:
            for number, job in enumerate(jobs, 1):
                env.update(status='running', attempted_scientific_forwards=number,
                           current_query_id=job['query_id'])
                checkpoint(out, env)
                torch.cuda.synchronize()
                tick = time.perf_counter()
                with torch.inference_mode():
                    full = lm(input_ids=torch.tensor([job['token_ids']], device='cuda')).logits[0, -1].float()
                    z = full[job['candidate_ids']]
                    probs = torch.softmax(z, -1)
                    mass = torch.softmax(full, -1)[job['candidate_ids']].sum().item()
                torch.cuda.synchronize()
                latency = time.perf_counter() - tick
                logits, probabilities = z.cpu().tolist(), probs.cpu().tolist()
                validate_values(logits, probabilities, mass, latency)
                record = job | dict(config_hash=manifest['config_hash'], forward_index=number,
                                    ok=True, latency_s=latency, candidate_mass=mass, logits=logits,
                                    probabilities=probabilities,
                                    prediction=job['order'][max(range(len(logits)), key=logits.__getitem__)])
                stream.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + '\n')
                stream.flush()
                os.fsync(stream.fileno())
                env['scientific_forwards'] = number
                checkpoint(out, env)
                if number % 50 == 0:
                    print(f'N1 ownership diagnostic: {number}/500', flush=True)
        env.update(status='complete', elapsed_s=time.perf_counter() - started,
                   end_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                   peak_allocated_mib=torch.cuda.max_memory_allocated() / 1024**2)
        checkpoint(out, env)
        return env
    except BaseException as error:
        env.update(status='failed', error_type=type(error).__name__, error=str(error),
                   elapsed_s=time.perf_counter() - started)
        checkpoint(out, env)
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('build', 'verify-freeze', 'run'))
    parser.add_argument('--cache', default='G:/jev-lab/hf-cache')
    parser.add_argument('--approved-config-hash')
    args = parser.parse_args()
    result = (freeze(args.cache) if args.command == 'build' else
              verify_frozen() if args.command == 'verify-freeze' else
              run(args.cache, args.approved_config_hash))
    print(json.dumps(result if args.command == 'run' else {
        'status': 'execution_freeze_verified_no_inference',
        'config_hash': result['config_hash'], 'planned_forwards': 500,
        'planned_input_tokens': 188797, 'planned_warmups': 2,
        'model_forwards_this_command': 0}, indent=2))
