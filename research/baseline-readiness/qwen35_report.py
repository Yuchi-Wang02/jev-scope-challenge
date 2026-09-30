"""Offline audit/report of the technical smoke, not an inference rerun."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read(name):
    return json.loads((ROOT/name).read_text(encoding='utf-8'))


def audit():
    first = read('qwen35-smoke-run/run.json')
    run = read('qwen35-smoke-repaired/run.json')
    acquisition = read('qwen35_acquisition.json')
    assert first['status'] == 'failed' and first['error_type'] == 'ImportError'
    assert first['generation_attempts'] == 0 and first['records'] == []
    assert 'HybridCache' in first['error']
    assert run['status'] == 'completed' and run['generation_attempts'] == 6
    assert first['model_files'] == run['model_files']
    for attempt in [first, run]:
        for filename, field in [('qwen35_smoke.py', 'runner_sha256'),
                                ('QWEN35_SMOKE_PROTOCOL.md', 'protocol_sha256')]:
            source = subprocess.check_output(['git', 'show', attempt['freeze_commit']+
                     ':research/baseline-readiness/'+filename], cwd=ROOT)
            assert hashlib.sha256(source).hexdigest() == attempt[field], filename
    weight_files = [f for f in run['model_files'] if f['name'].endswith('.safetensors')]
    assert len(weight_files) == 2
    assert sum(f['bytes'] for f in weight_files) == 9319828096
    assert all(f['sha256'] == f['upstream_lfs_sha256'] for f in weight_files)
    assert run['model_file_bytes'] == sum(f['bytes'] for f in run['model_files'])
    assert acquisition['unique_wheel_payload_bytes'] == sum(d['bytes'] for d in acquisition['dependencies'])
    total = run['model_file_bytes'] + acquisition['unique_wheel_payload_bytes']
    assert total < 15 * 1024**3
    assert run['parameter_devices'] == ['cuda:0']
    assert run['parameter_dtypes'] == ['torch.bfloat16']
    assert run['runtime']['fast_delta_kernels'] is False
    namespace = {}
    # Read constants without importing a GPU dependency or running the probe.
    import ast
    tree = ast.parse((ROOT/'qwen35_smoke.py').read_text(encoding='utf-8'))
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id == 'PROMPTS':
            namespace['prompts'] = ast.literal_eval(node.value)
    assert len(run['records']) == 6
    for i, r in enumerate(run['records']):
        thinking = i >= 3
        assert r['thinking'] == thinking and r['status'] == 'completed'
        assert r['messages'] == [{'role': 'user', 'content': namespace['prompts'][i % 3]}]
        c = r['effective_generation_config']
        assert c['do_sample'] is True and c['max_new_tokens'] == 256
        assert c['temperature'] == (1.0 if thinking else 0.7)
        assert c['top_p'] == (0.95 if thinking else 0.8) and c['top_k'] == 20
        assert c['min_p'] == 0.0 and c['repetition_penalty'] == 1.0
        assert r['presence_penalty'] == 0.0 and r['seed'] == 20260930
        assert 0 < len(r['output_ids']) == r['generated_tokens'] <= 256
        assert r['ended_with_eos'] == (r['output_ids'][-1] == c['eos_token_id'])
        assert r['hit_token_cap'] == (r['generated_tokens'] == 256 and not r['ended_with_eos'])
        assert not r['deadline_reached']
        assert r['generation_seconds'] > 0
    assert run['generated_tokens'] == sum(r['generated_tokens'] for r in run['records']) <= 1536
    assert 0 < run['inference_wall_seconds'] < 600
    return run, acquisition, total


def render(run, acquisition, total):
    rows = []
    for r in run['records']:
        text = r['decoded_output']
        if r['thinking']:
            final = text.split('</think>', 1)[1] if '</think>' in text else None
        else:
            final = text
        final = final.replace('<|im_end|>', '').strip() if final is not None else None
        shown = '`'+final.replace('\n', ' ')+'`' if final is not None else 'No final answer; thought truncated'
        rows.append(f'|{r["id"]}|{r["generated_tokens"]}|{r["generation_seconds"]:.3f}|'
                    f'{"EOS" if r["ended_with_eos"] else "256-token cap"}|{shown}|')
    return '\n'.join([
        '# Qwen3.5-4B: local runtime verified, capability comparison still pending', '',
        'Completed 2026-09-30. **One successful BF16 GPU load and six technical generation calls.** '
        'These generic prompts do not establish task accuracy, comparative capability or a research finding. '
        'The prior 72-input research grids were not reopened.', '',
        '## Observed execution', '',
        '|Call|Generated tokens|Generate seconds|Termination|Final-answer portion|',
        '|---|---:|---:|---|---|', *rows, '',
        f'Total: {run["generated_tokens"]:,} generated tokens; '
        f'{run["inference_wall_seconds"]:.3f} seconds from first generate start through final record; '
        f'load {run["load_seconds"]:.3f} seconds. Peak PyTorch allocated memory '
        f'{run["peak_allocated_bytes"]/1024**3:.3f} GiB, reserved '
        f'{run["peak_reserved_bytes"]/1024**3:.3f} GiB. These are short single-sequence '
        'measurements, not long-context, concurrency or end-to-end serving guarantees. '
        'Other GPU/display allocations are outside PyTorch peak counters.', '',
        'Non-thinking output has the requested content in all three interface checks. '
        'Two thinking calls emit a final-answer portion; the JSON call reaches the cap '
        'inside its reasoning text. A JSON example inside a thought is not a completed '
        'final answer. No parser extracts a favorable answer from that truncated trace. '
        'These hand-authored trivial checks are not summarized as benchmark accuracy.', '',
        '## Model and runtime', '',
        '- Qwen/Qwen3.5-4B, revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`.',
        '- Python 3.10.18, torch 2.8.0+cu128 / CUDA 12.8, Transformers 5.3.0, '
        'tokenizers 0.22.2, huggingface-hub 1.33.0, PEFT 0.18.1.',
        '- NVIDIA RTX 5070 Ti; all parameters reported on cuda:0 in BF16. No quantization/offload.',
        '- SDPA with native torch DeltaNet fallback; optimized flash-linear-attention '
        'and causal-conv1d kernels were unavailable. No kernel download or remote code.',
        '- Sampling on; seed 20260930 per call, top-k 20, min-p 0, repetition penalty 1. '
        'Direct temperature/top-p 0.7/0.8; thinking 1.0/0.95. Presence penalty 0. '
        'The latter and the short cap depart from the vendor general-task recommendation.', '',
        '## Acquisition and preserved failures', '',
        f'The eleven retained model/tokenizer/license files total {run["model_file_bytes"]:,} bytes; '
        'weights account for 9,319,828,096 bytes. Both weight SHA-256 values match pinned '
        'Hub LFS digests. Four dependency wheel payloads total '
        f'{acquisition["unique_wheel_payload_bytes"]:,} bytes. Combined unique payload: '
        f'{total:,} bytes ({total/1024**3:.3f} GiB), below the 15 GiB allowance. '
        'This is payload accounting, not packet-level HTTP overhead/retransmit measurement. '
        'Paid API calls: zero. Weights remain outside this repository under Apache-2.0.', '',
        'The first full runner attempt failed before loading weights because inherited '
        'PEFT 0.17.1 imported removed HybridCache. Its [raw record](qwen35-smoke-run/run.json) '
        'and traceback are retained. Installing PEFT 0.18.1 only in the isolated venv '
        'resolved the complete import check. The old environment was rechecked: '
        'Transformers 4.55.4, torch 2.8.0+cu128 and PEFT 0.17.1 remain available.', '',
        'Before that failed attempt, source inspection found removed use_model_defaults '
        'support in Transformers 5.3.0. A CPU-only check and pre-load amendment corrected '
        'the runner without changing the intended sampling policy. A terminal Unicode '
        'display error during token inspection was fixed with -X utf8, with zero model work. '
        'The dependency amendment initially misstated the wheel size by eight bytes; '
        'the acquisition record verifies 556,960 bytes for PEFT 0.18.1.', '',
        '## Reproduction and evidence boundary', '',
        'Read the [pre-acquisition protocol](QWEN35_SMOKE_PROTOCOL.md), '
        '[API compatibility amendment](QWEN35_COMPATIBILITY_AMENDMENT.md), '
        '[dependency amendment](QWEN35_DEPENDENCY_AMENDMENT.md), '
        '[acquisition manifest](qwen35_acquisition.json) and '
        '[successful raw record](qwen35-smoke-repaired/run.json). The raw record '
        'includes exact rendered inputs, token IDs, outputs, settings, durations '
        'and source-commit hashes. It is not a blinded review package.', '',
        'Offline: `python research/baseline-readiness/qwen35_report.py --verify`. '
        'This checks saved record consistency and runner/protocol hashes against full '
        'Git history. It does not reload weights or prove semantic validity. '
        'Live replication requires the separately downloaded pinned model and the '
        'isolated environment; pass a new output directory to qwen35_smoke.py. '
        'Do not silently rerun this published destination.', '',
        'For live replication, create a Python 3.10 environment with CUDA-compatible '
        'torch 2.8.0+cu128; install transformers==5.3.0, tokenizers==0.22.2, '
        'huggingface-hub==1.33.0 and peft==0.18.1. Read the original protocol budget first. '
        'The local setup reused an existing torch environment with --system-site-packages; '
        'it was not a fully hermetic fresh installation.', '',
        'Fetch pinned Hub metadata from '
        '[this public endpoint](https://huggingface.co/api/models/Qwen/Qwen3.5-4B/revision/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a?blobs=true) '
        'into hub.json. Download the eleven files listed in the run manifest with '
        '`hf download Qwen/Qwen3.5-4B --revision 851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a '
        '--local-dir MODEL_DIR` and explicit filenames from that manifest. Then:', '',
        '```bash',
        'python -X utf8 research/baseline-readiness/qwen35_smoke.py --model-dir MODEL_DIR --hub-metadata hub.json --output NEW_RUN_DIR',
        '```', '',
        'The runner checks artifact sizes/LFS hashes before loading and refuses an '
        'existing output directory. Keep the pinned environment and record all '
        'results; sampled outputs can vary across software/hardware configurations.', '',
        '## Milestone audit and next decision', '',
        'Goal: turn a metadata-only candidate into an executable ordinary-model '
        'resource. Achieved: local BF16 loading and bounded generation. Gap: no '
        'new research inputs, no independent labels, no evidence that this model is '
        'a stronger task comparator, and no adequate thinking-budget calibration. '
        'The original environment remains usable.', '',
        'Next: freeze a separate development-only interface/budget calibration before '
        'a new reviewed comparison, including final-answer parsing and truncated-output '
        'accounting. Review the existing 72-input candidate-coverage wording separately; '
        'the two old payment reviews do not cover it. Any confirmatory material must '
        'be new and independently reviewed. Preserve the code baseline and the '
        'question of whether natural-language modeling is necessary at all. '
        'Present this release as reproducible setup evidence, not a new leaderboard.', ''])


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--verify', action='store_true')
    args = p.parse_args()
    run, acquisition, total = audit()
    text = render(run, acquisition, total)
    target = ROOT/'QWEN35_SMOKE_RESULTS.md'
    if args.verify:
        assert target.read_text(encoding='utf-8') == text
    else:
        target.write_text(text, encoding='utf-8', newline='\n')
    print(json.dumps({'verified': True, 'technical_calls': 6, 'generated_tokens': run['generated_tokens'],
                      'research_calls': 0, 'unique_payload_bytes': total}))
