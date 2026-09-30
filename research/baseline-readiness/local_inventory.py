"""Inspect known project caches without downloads, credential reads or model loading."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
LOCATIONS = {
    'project_models': Path('G:/jev-lab/models'),
    'historical_base_adapter_cache': Path('G:/jev-lab/hf-cache'),
    'earlier_instruction_cache': Path.home() / 'Downloads/p1/hf_cache/hub',
    'default_hub_cache': Path.home() / '.cache/huggingface/hub',
}


def inspect_model(path, relative):
    config_path = path / 'config.json'
    adapter_path = path / 'adapter_config.json'
    chosen = config_path if config_path.exists() else adapter_path
    raw = chosen.read_bytes()
    config = json.loads(raw)
    indices = list(path.glob('*.safetensors.index.json'))
    required = set()
    for index in indices:
        required.update(json.loads(index.read_bytes()).get('weight_map', {}).values())
    if not required:
        required.update(p.name for p in path.glob('*.safetensors'))
    present = sorted(n for n in required if (path / n).is_file())
    missing = sorted(required - set(present))
    return {
        'relative_directory': relative,
        'kind': 'model' if config_path.exists() else 'adapter',
        'config_file': chosen.name,
        'config_sha256': hashlib.sha256(raw).hexdigest(),
        'model_type': config.get('model_type'),
        'architectures': config.get('architectures'),
        'base_model_name_or_path': config.get('base_model_name_or_path'),
        'declared_weight_files': len(required),
        'present_weight_files': len(present),
        'missing_weight_files': missing,
        'present_weight_bytes': sum((path / n).stat().st_size for n in present),
        'weight_contents_hashed': False,
        'loaded_by_this_inventory': False,
    }


def capture():
    roots = []
    for name, base in LOCATIONS.items():
        models = []
        if base.exists():
            # Configs only: do not traverse unrelated user files or load weights.
            paths = set(base.rglob('config.json')) | set(base.rglob('adapter_config.json'))
            # Hub .no_exist files are absence sentinels, not checkpoint configs.
            parents = sorted({p.parent for p in paths if '.no_exist' not in p.parts})
            for path in parents:
                models.append(inspect_model(path, path.relative_to(base).as_posix()))
        roots.append({'location_label': name, 'exists': base.exists(), 'entries': models})
    gpu = subprocess.check_output([
        'nvidia-smi', '--query-gpu=name,memory.total,memory.used', '--format=csv,noheader'
    ], text=True).strip()
    return {
        'captured_at_utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'Focused known-cache inventory; not an exhaustive machine search or capability test',
        'new_model_calls': 0, 'weight_downloads': 0,
        'gpu_snapshot_csv': gpu, 'roots': roots,
        'limitations': [
            'Config and file presence do not establish a correct or runnable checkpoint.',
            'Weights are not rehashed, loaded or benchmarked in this inventory.',
            'Directory names and parameter counts do not establish stronger capability.',
            'GPU allocation is transient and not a peak-memory estimate.',
        ],
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Refusing to overwrite an existing inventory snapshot')
    result = capture()
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'roots': len(result['roots']),
        'entries': sum(len(r['entries']) for r in result['roots']),
        'new_model_calls': 0, 'weight_downloads': 0}))
