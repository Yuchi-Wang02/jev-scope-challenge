"""Frozen N1/native line-evidence pilot; never runs rewrites or reserved inputs."""
import argparse
import hashlib
import importlib.metadata
import json
import platform
import random
import subprocess
import time
from pathlib import Path

from data_tools import HERE
from fact_run import freeze as old_study_freeze
from gap_run import read_rows, spec, tokenizer_for, write_json
from line_plan_tools import run as verify_query_plan

SEED = 20261004
PREP = HERE / 'preparation'
ENCODED = PREP / 'line_native_primary.jsonl'
MANIFEST = PREP / 'line_execution_manifest.json'
OUT = HERE / 'line_results/v0.1'
SOURCE_PATHS = (
    'LINE_EVIDENCE_PROTOCOL.md', 'line_evidence.py', 'line_plan_tools.py',
    'line_run.py', 'line_analyze.py', 'data/original_cases.jsonl',
    'preparation/line_query_plans.jsonl', 'preparation/line_query_manifest.json',
    'manifest.json', '../next-study/results/weight_checksums.json',
    '../evidence-gap/gap_run.py', '../next-study/study.py')


def sha(payload):
    return hashlib.sha256(payload.replace(b'\r\n', b'\n')).hexdigest()


def json_lines(rows):
    return ''.join(json.dumps(row, ensure_ascii=False, separators=(',', ':'),
                              allow_nan=False) + '\n' for row in rows).encode('utf-8')


def planned_encoded(cache):
    verify_query_plan('verify')
    old_study_freeze()
    tok = tokenizer_for(cache)
    candidates = [tok.encode(' ' + letter, add_special_tokens=False) for letter in 'ABC']
    if any(len(ids) != 1 for ids in candidates) or len({ids[0] for ids in candidates}) != 3:
        raise ValueError('Answer letters are not distinct single tokens')
    source = read_rows(PREP / 'line_query_plans.jsonl')
    selected = [p for p in source if p['mapping'] == 0]
    if len(source) != 1096 or len(selected) != 548 or any(
            p['split'] != 'development' or p['representation'] != 'original' for p in selected):
        raise ValueError('Unapproved query plan')
    rows = []
    for p in selected:
        ids = tok.encode(p['prompt'], add_special_tokens=False)
        for letter, candidate in zip('ABC', candidates):
            if tok.encode(p['prompt'] + ' ' + letter,
                          add_special_tokens=False) != ids + candidate:
                raise ValueError('Answer token boundary drift')
        rows.append(p | {'token_ids': ids, 'candidate_ids': [c[0] for c in candidates]})
    return rows


def freeze(cache):
    rows = planned_encoded(cache)
    payload = json_lines(rows)
    digests = {path: sha((HERE / path).read_bytes()) for path in SOURCE_PATHS}
    manifest = {'study': 'line-evidence-N1-native-original-development-v0.1',
                'status': 'pre_inference_freeze', 'arm': 'N1',
                'base': spec.BASE, 'base_revision': spec.BASE_REV,
                'adapter': spec.ADAPTER, 'adapter_revision': spec.ADAPTER_REV,
                'seed': SEED, 'allowed_splits': ['development'],
                'allowed_representations': ['original'], 'allowed_mappings': [0],
                'planned_forwards': 548, 'planned_input_tokens': sum(len(r['token_ids']) for r in rows),
                'max_input_tokens': max(len(r['token_ids']) for r in rows),
                'encoded_plan_sha256_lf': sha(payload),
                'source_file_sha256_lf': digests, 'new_training': False,
                'paid_api_calls': 0, 'rewrite_model_records': 0,
                'reserved_model_records': 0, 'post_hoc_development': True}
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
    """Check a committed preparation without requiring a local tokenizer cache."""
    verify_query_plan('verify')
    old_study_freeze()
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    rows = read_rows(ENCODED)
    source = [p for p in read_rows(PREP / 'line_query_plans.jsonl') if p['mapping'] == 0]
    if len(rows) != 548 or len(source) != 548 or manifest['planned_forwards'] != 548:
        raise ValueError('Encoded pilot grid count drift')
    for row, original in zip(rows, source):
        if any(row.get(key) != value for key, value in original.items()):
            raise ValueError('Encoded pilot source query drift')
        if (not isinstance(row.get('token_ids'), list) or
                not all(isinstance(t, int) and t >= 0 for t in row['token_ids']) or
                len(row.get('candidate_ids', [])) != 3 or
                len(set(row['candidate_ids'])) != 3):
            raise ValueError('Invalid encoded candidate plan')
    if (manifest['encoded_plan_sha256_lf'] != sha(ENCODED.read_bytes()) or
            manifest['planned_input_tokens'] != sum(len(r['token_ids']) for r in rows) or
            manifest['max_input_tokens'] != max(len(r['token_ids']) for r in rows)):
        raise ValueError('Encoded plan digest or token cost drift')
    if manifest['source_file_sha256_lf'] != {
            path: sha((HERE / path).read_bytes()) for path in SOURCE_PATHS}:
        raise ValueError('Pre-inference source drift')
    config = dict(manifest)
    saved_hash = config.pop('config_hash')
    if sha(json.dumps(config, sort_keys=True, separators=(',', ':')).encode('utf-8')) != saved_hash:
        raise ValueError('Execution manifest config hash drift')
    if (manifest['arm'] != 'N1' or manifest['allowed_splits'] != ['development'] or
            manifest['allowed_representations'] != ['original'] or
            manifest['allowed_mappings'] != [0] or manifest['paid_api_calls'] != 0 or
            manifest['rewrite_model_records'] != 0 or manifest['reserved_model_records'] != 0):
        raise ValueError('Unapproved execution scope')
    return manifest


def _check_weights(cache):
    base = Path(cache) / 'models--Qwen--Qwen3-4B-Base/snapshots' / spec.BASE_REV
    adapter = Path(cache) / 'models--jaredpalmer--kev-4b/snapshots' / spec.ADAPTER_REV
    expected = json.loads((HERE.parent / 'next-study/results/weight_checksums.json').read_text())
    for key, digest in expected.items():
        if key.startswith(spec.BASE + '@' + spec.BASE_REV + '/'):
            path = base / key.split(spec.BASE_REV + '/', 1)[1]
        elif key.startswith(spec.ADAPTER + '@' + spec.ADAPTER_REV + '/'):
            path = adapter / key.split(spec.ADAPTER_REV + '/', 1)[1]
        else:
            raise ValueError('Foreign cached weight')
        h = hashlib.sha256()
        with path.open('rb') as stream:
            for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
                h.update(chunk)
        if h.hexdigest() != digest:
            raise ValueError(f'Cached weight checksum mismatch: {key}')
    return base, adapter, expected


def run(cache):
    manifest = freeze(cache)
    verify_frozen()
    if subprocess.check_output(['git', 'status', '--porcelain'], cwd=HERE):
        raise ValueError('Commit the complete execution freeze before inference')
    if OUT.exists() and any(OUT.iterdir()):
        raise ValueError('Existing line pilot outputs; never overwrite or resume-select')
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
           'paid_api_calls': 0, 'new_training': False,
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
        if len(jobs) != 548 or sum(len(j['token_ids']) for j in jobs) != manifest['planned_input_tokens']:
            raise ValueError('Encoded job count or token budget drift')
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
            for number, p in enumerate(jobs, 1):
                torch.cuda.synchronize()
                tick = time.perf_counter()
                with torch.inference_mode():
                    full = lm(input_ids=torch.tensor([p['token_ids']], device='cuda')).logits[0, -1].float()
                    z = full[p['candidate_ids']]
                    probs = torch.softmax(z, -1)
                    mass = torch.softmax(full, -1)[p['candidate_ids']].sum().item()
                torch.cuda.synchronize()
                record = {k: p[k] for k in ('source_id', 'parent', 'family', 'variant',
                                            'split', 'representation', 'field', 'line_index',
                                            'evidence_span', 'mapping', 'order', 'prompt',
                                            'token_ids', 'candidate_ids')}
                record.update(arm='N1', config_hash=manifest['config_hash'],
                              forward_index=number, ok=True, input_tokens=len(p['token_ids']),
                              latency_s=time.perf_counter() - tick, candidate_mass=mass,
                              logits=z.cpu().tolist(), probabilities=probs.cpu().tolist(),
                              prediction=p['order'][int(probs.argmax())])
                stream.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + '\n')
                stream.flush()
                env['scientific_forwards'] = number
                if number % 48 == 0:
                    write_json(OUT / 'runtime.json', env)
                    print(f'N1 line evidence: {number}/548', flush=True)
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
                          'planned_forwards': report['planned_forwards'],
                          'planned_input_tokens': report['planned_input_tokens'],
                          'model_forwards': 0}))
