"""Bounded public-metadata preflight. Never downloads weights or runs a model.

capture: inspect four explicit Hub repositories and the existing local runtime.
verify: check the recorded snapshot/report offline. Does not refresh live facts.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
MODELS = ('Qwen/Qwen3-4B', 'Qwen/Qwen3-8B', 'Qwen/Qwen3-8B-FP8', 'Qwen/Qwen3.5-4B')
OLD_REVISION = '1cfa9a7208912126459214e8b04321603b3df60c'
ALLOWED_FILES = ('config.json', 'generation_config.json', 'model.safetensors.index.json', 'README.md')
MAX_FETCHES = 20
MAX_BODY_BYTES = 8 * 1024 * 1024


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n', encoding='utf-8', newline='\n')


def metadata_url(model, revision=None, filename=None):
    if model not in MODELS:
        raise ValueError('Repository outside this bounded preflight')
    if filename is None:
        revision_path = '/revision/'+revision if revision else ''
        if revision and not re.fullmatch('[0-9a-f]{40}', revision):
            raise ValueError('Use a pinned SHA')
        return f'https://huggingface.co/api/models/{model}{revision_path}?blobs=true'
    if filename not in ALLOWED_FILES or not re.fullmatch('[0-9a-f]{40}', revision or ''):
        raise ValueError('Only pinned metadata files are allowed; no weights')
    return f'https://huggingface.co/{model}/resolve/{revision}/{filename}'


def runtime(python):
    program = (
        "import json,platform,transformers,torch; "
        "from transformers.models.auto.configuration_auto import CONFIG_MAPPING; "
        "print(json.dumps({'python':platform.python_version(),'transformers':transformers.__version__,"
        "'torch':torch.__version__,'cuda':torch.version.cuda,'gpu':torch.cuda.get_device_name(0),"
        "'total_gpu_memory_bytes':torch.cuda.get_device_properties(0).total_memory,"
        "'registered_model_types':{k:k in CONFIG_MAPPING for k in ['qwen3','qwen3_5','qwen3_5_text','qwen3_5_moe']}}))"
    )
    result = subprocess.run([str(python), '-c', program], capture_output=True, text=True, check=True, timeout=60)
    return json.loads(result.stdout)


def capture(python, recover_cache=False):
    target = ROOT/'snapshot.json'
    if target.exists():
        raise RuntimeError('Snapshot exists; preserve history and use a separately versioned capture')
    import httpx
    cache = REPO/'.local/baseline-readiness'; cache.mkdir(parents=True, exist_ok=True)
    entries = []; budget = {'logical_fetches': 0, 'redirect_hops': 0, 'final_response_body_bytes': 0,
                            'recovered_payload_files': 0, 'recovered_payload_bytes': 0}
    with httpx.Client(timeout=30, follow_redirects=True, max_redirects=5, trust_env=False) as client:
        def fetch(url, cache_name):
            if recover_cache and (cache/cache_name).exists():
                raw = (cache/cache_name).read_bytes()
                budget['recovered_payload_files'] += 1; budget['recovered_payload_bytes'] += len(raw)
                if budget['recovered_payload_bytes'] + budget['final_response_body_bytes'] > MAX_BODY_BYTES:
                    raise RuntimeError('Recovered and new payload cap reached')
                return raw
            if budget['logical_fetches'] >= MAX_FETCHES:
                raise RuntimeError('Metadata-fetch cap reached')
            budget['logical_fetches'] += 1
            chunks = []
            with client.stream('GET', url) as response:
                response.raise_for_status(); budget['redirect_hops'] += len(response.history)
                for chunk in response.iter_bytes():
                    budget['final_response_body_bytes'] += len(chunk)
                    if budget['final_response_body_bytes'] + budget['recovered_payload_bytes'] > MAX_BODY_BYTES:
                        raise RuntimeError('Metadata payload cap reached')
                    chunks.append(chunk)
            raw = b''.join(chunks); (cache/cache_name).write_bytes(raw)
            return raw
        for model in MODELS:
            slug = model.split('/')[-1]
            info_url = metadata_url(model, OLD_REVISION if model == MODELS[0] else None)
            info_raw = fetch(info_url, slug+'_hub.json'); info = json.loads(info_raw)
            revision = info['sha']; docs = {}; source_hashes = {}
            listed = {item['rfilename'] for item in info['siblings']}
            for filename in ALLOWED_FILES:
                url = metadata_url(model, revision, filename)
                if filename == 'generation_config.json' and filename not in listed:
                    source_hashes[filename] = {'url': url, 'status': 'absent_from_pinned_file_listing', 'bytes': 0, 'sha256': None}
                    continue
                raw = fetch(url, slug+'_'+filename)
                docs[filename] = raw.decode('utf-8')
                source_hashes[filename] = {'url': url, 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
            config = json.loads(docs['config.json'])
            generation = json.loads(docs['generation_config.json']) if 'generation_config.json' in docs else None
            index = json.loads(docs['model.safetensors.index.json'])
            weights = []
            names = sorted(set(index['weight_map'].values()))
            byname = {s['rfilename']: s for s in info['siblings']}
            for name in names:
                item = byname[name]; lfs = item.get('lfs', {})
                weights.append({'name': name, 'file_bytes': item.get('size', lfs.get('size')),
                                'lfs_sha256': lfs.get('sha256') or lfs.get('oid')})
            entries.append({'model': model, 'revision': revision,
                'hub_info_url': info_url, 'hub_info_sha256': hashlib.sha256(info_raw).hexdigest(),
                'license_reported_by_hub': info.get('cardData', {}).get('license'),
                'model_type': config.get('model_type'), 'architectures': config.get('architectures'),
                'checkpoint_transformers_version': config.get('transformers_version'),
                'config_dtype': config.get('dtype', config.get('torch_dtype')),
                'text_model_type': config.get('text_config', {}).get('model_type'),
                'quantization_config': config.get('quantization_config'),
                'generation_config': generation,
                'tensor_storage_bytes_from_index': index['metadata']['total_size'],
                'weight_file_bytes': sum(w['file_bytes'] for w in weights),
                'index_minus_weight_files_bytes': index['metadata']['total_size'] - sum(w['file_bytes'] for w in weights),
                'weight_files': weights, 'sources': source_hashes,
                'readme_has_explicit_greedy_warning': 'DO NOT use greedy decoding' in docs['README.md'],
                'readme_mentions_32768_output_recommendation': '32,768 tokens for most queries' in docs['README.md'],
                'weights_downloaded': False, 'runtime_load_tested': False})
    rt = runtime(python)
    for entry in entries:
        entry['model_type_registered_in_existing_runtime'] = rt['registered_model_types'].get(entry['model_type'], False)
        entry['weight_file_gib'] = round(entry['weight_file_bytes']/1024**3, 3)
        entry['tensor_storage_gib'] = round(entry['tensor_storage_bytes_from_index']/1024**3, 3)
    snapshot = {'captured_at_utc': datetime.now(timezone.utc).isoformat(),
        'purpose': 'Resource and interface audit, not an inference comparison',
        'local_runtime': rt, 'models': entries, 'network': budget,
        'limits': {'logical_fetches': MAX_FETCHES, 'final_response_body_bytes': MAX_BODY_BYTES},
        'model_forwards': 0, 'weight_download_bytes': 0,
        'capture_recovery': {'used_saved_payloads': recover_cache,
            'prior_failure': 'Initial capture stopped on the unlisted Qwen3.5-4B generation_config.json (404); 17 successful payloads retained, plus one failed fetch. No weights or inference. Redirect count and failed response size were not retained for that initial attempt.' if recover_cache else None},
        'notes': ['Weight storage is not peak runtime memory.',
                  'Registry support is not a tested load, forward, generation, or quantization kernel.',
                  'Vendor scores are not reproduced or used to declare a stronger model on our task.',
                  'No tokenizers, model source code or weights are executed by this capture.']}
    write(target, snapshot)
    (ROOT/'README.md').write_text(report(snapshot), encoding='utf-8', newline='\n')
    verify()


def report(s):
    r = s['local_runtime']; gpu_gib = r['total_gpu_memory_bytes']/1024**3
    lines = ['# Ordinary-model comparator readiness', '',
        'Historical metadata-only stage. The subsequent [Qwen3.5 technical smoke](QWEN35_SMOKE_RESULTS.md) '
        'adds a real local load and six generic generation calls; it is not a research evaluation. '
        'The snapshot and counts below retain their original scope.', '',
        f'Captured {s["captured_at_utc"]}. **Metadata and installed-runtime inspection only: zero inference, zero weight downloads.**', '',
        '## What is available versus what remains untested', '',
        f'The existing environment uses Transformers {r["transformers"]}, PyTorch {r["torch"]}, CUDA {r["cuda"]}, '
        f'and {r["gpu"]} with {gpu_gib:.2f} GiB total memory. GPU display/other allocations further reduce free memory. '
        'The inspected caches contain Qwen3-4B instruction, smaller Qwen checkpoints and the historical Base/Kev pair, '
        'but none of the three uncached alternatives below. This is a focused cache check, not a scan of every user folder.', '',
        '|Candidate|Pinned revision|Weight files, GiB|Architecture registered in existing runtime|Decision|',
        '|---|---|---:|---|---|']
    decisions = [
        'Existing measured comparator; not a capable-model ceiling.',
        'BF16 weights alone leave little total GPU headroom and exceed current free memory; offload/quantization changes the comparator.',
        'Smaller stored weights, but FP8 loader/kernel/peak memory are untested. Not a BF16 parity result.',
        'Potential new-generation small comparator; requires a separate supported environment and load test. Capability on our task unmeasured.']
    for m, d in zip(s['models'], decisions):
        lines.append(f'|[{m["model"]}](https://huggingface.co/{m["model"]}/tree/{m["revision"]})|`{m["revision"]}`|'
                     f'{m["weight_file_gib"]:.3f}|{m["model_type_registered_in_existing_runtime"]}|{d}|')
    lines += ['', 'All four Hub metadata records report Apache-2.0. No weights are redistributed. '
        'Storage totals come from the pinned index and Hub file metadata, not a memory estimator. '
        'Configuration support does not establish that a model will load or execute, especially with FP8. '
        'See [snapshot.json](snapshot.json) for exact bytes, configurations and source hashes.', '',
        'Metadata discrepancy: the FP8 index declares 9,438,648,320 tensor bytes, while the listed weight files sum '
        'to 9,436,628,784 bytes (2,019,536 fewer). Both raw declarations are retained. The initial consistency check '
        'incorrectly assumed the index was always a lower bound and failed. Download estimates here use listed '
        'file sizes; neither declaration proves actual loaded tensor memory. The discrepancy was not resolved '
        'by downloading weights or silently replacing upstream metadata.', '',
        '## Material correction to the interpretation of our 512-token control', '',
        f'The [Qwen3-4B model card at our exact checkpoint revision](https://huggingface.co/Qwen/Qwen3-4B/blob/{OLD_REVISION}/README.md) '
        'advises sampling in thinking mode and explicitly warns against greedy decoding. It also recommends much longer '
        'output allowance for general benchmarking. Our frozen control deliberately used a 512-token greedy budget and a '
        'forced final native readout. That is a bounded engineering configuration, not the vendor-recommended reasoning baseline.', '',
        'Its measured 58/72 and 59/72 remain unchanged and its truncated outputs remain counted. '
        'The original six sampled smoke outputs still do not implement the frozen greedy protocol; preserving them was correct. '
        'However, repairing the implementation to match a protocol does not make that protocol a strong or recommended comparator. '
        'The card cannot establish that sampling or a larger budget would fix any particular error. '
        'Do not silently pool, rescore or rerun the closed 72-input grids.', '',
        '## A fair next comparison needs two separate questions', '',
        '1. **Capability reference:** on new reviewed material, use a supported ordinary-model interface with predeclared '
        'sampling, output format and adequate finite output budget. Record incomplete outputs, seeds and all work. '
        'If it samples, use a small fixed set of seeds and report variation at the parent level; never choose the best seed.',
        '2. **Budget-constrained component:** compare named configurations at fixed calls/tokens/latency or cost levels. '
        'Different tokenizers and hidden hosted compute make these different budget axes, not interchangeable fairness guarantees. '
        'A 512-token control belongs here, alongside the no-thinking readout.', '',
        'For both, freeze the same visible evidence, policy, tools and external help. Keep the known-grammar code baseline. '
        'Report final-answer parsing failures separately; a forced A/B/C logit readout is not natural generated-answer accuracy. '
        'Model family/size, precision, template, runtime version, generation settings and readout are separate factors.', '',
        'No new model has been selected or acquired by this audit. A prospective Qwen3.5-4B setup would require '
        'roughly the listed weight bytes plus dependencies, isolated from the frozen Transformers 4.55.4 environment. '
        'The download scope, disk destination and smoke budget must be recorded before acquisition. '
        'The user has also been asked whether another capable API/local model is already available; no such resource is assumed.', '',
        '## Reproduce the audit', '',
        '```powershell', 'python research/baseline-readiness/preflight.py verify', '```', '',
        'Verification is offline snapshot consistency, not a fresh availability, license or compatibility check. '
        'The capture implementation allows only four named models and four metadata filenames, caps 20 logical fetches '
        'and 8 MiB final response bodies, and refuses to overwrite the historical snapshot. Raw fetched metadata is '
        'kept in ignored local storage; only the derived snapshot and source hashes are published. '
        'The capture imports the installed runtime to inspect its registry/GPU but never loads model weights. '
        'No credential is required or collected.', '',
        f'Completion pass: {s["network"]["logical_fetches"]} new logical fetches, {s["network"]["redirect_hops"]} redirects, '
        f'{s["network"]["final_response_body_bytes"]:,} new final-response bytes; '
        f'{s["network"]["recovered_payload_files"]} saved payloads / {s["network"]["recovered_payload_bytes"]:,} bytes reused. Zero model forwards.', '',
        'The initial capture stopped on a 404: Qwen3.5-4B has no generation_config.json in its pinned file listing. '
        'Seventeen successful payloads were retained, and the failed fetch adds one initial attempt. '
        'The recovery reads those payloads and fetches the two remaining metadata files; it does not restart model acquisition. '
        'The missing configuration is recorded as absent, not invented as defaults. Initial redirect counts and failed-body bytes '
        'were not retained. This software repair has no model outputs or inference cost.', '']
    return '\n'.join(lines)


def verify():
    s = json.loads((ROOT/'snapshot.json').read_text(encoding='utf-8'))
    assert tuple(m['model'] for m in s['models']) == MODELS
    assert s['models'][0]['revision'] == OLD_REVISION
    assert s['model_forwards'] == s['weight_download_bytes'] == 0
    assert s['network']['logical_fetches'] <= MAX_FETCHES
    assert s['network']['final_response_body_bytes'] + s['network']['recovered_payload_bytes'] <= MAX_BODY_BYTES
    assert s['models'][0]['readme_has_explicit_greedy_warning']
    for m in s['models']:
        assert re.fullmatch('[0-9a-f]{40}', m['revision'])
        assert m['weight_file_bytes'] == sum(w['file_bytes'] for w in m['weight_files'])
        assert m['index_minus_weight_files_bytes'] == m['tensor_storage_bytes_from_index'] - m['weight_file_bytes']
        assert m['weight_file_gib'] == round(m['weight_file_bytes']/1024**3, 3)
        assert m['model_type_registered_in_existing_runtime'] == s['local_runtime']['registered_model_types'].get(m['model_type'], False)
        assert not m['weights_downloaded'] and not m['runtime_load_tested']
        assert set(m['sources']) == set(ALLOWED_FILES)
        for filename, source in m['sources'].items():
            assert source['url'] == metadata_url(m['model'], m['revision'], filename)
            if source.get('status') == 'absent_from_pinned_file_listing':
                assert filename == 'generation_config.json' and m['generation_config'] is None
                assert source['sha256'] is None and source['bytes'] == 0
            else:
                assert re.fullmatch('[0-9a-f]{64}', source['sha256'])
    assert (ROOT/'README.md').read_text(encoding='utf-8') == report(s)
    print(json.dumps({'snapshot_verified': True, 'model_forwards': 0, 'weight_download_bytes': 0}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('command', choices=('capture', 'verify'))
    parser.add_argument('--runtime-python', type=Path)
    parser.add_argument('--recover-cache', action='store_true', help='Reuse saved metadata after an interrupted capture; records recovery')
    args = parser.parse_args()
    if args.command == 'capture':
        if not args.runtime_python:
            parser.error('--runtime-python is required to inspect the existing environment')
        capture(args.runtime_python, args.recover_cache)
    else:
        verify()
