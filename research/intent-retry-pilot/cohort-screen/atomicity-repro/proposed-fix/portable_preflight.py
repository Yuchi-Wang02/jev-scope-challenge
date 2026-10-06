"""Source/result hash preflight only. Does not run or adapt the frozen regression."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PREFIX = 'upstream/dataset/environments/personal_profile_and_contacts/__pycache__/'
EXCLUDED = {PREFIX+n for n in ('__init__.cpython-313.pyc', 'environment.cpython-313.pyc', 'schema.cpython-313.pyc')}


def verify(base, entries, missing=()):
    for name, expected in entries.items():
        if name in missing:
            raise FileNotFoundError('Simulated absent file: '+name)
        assert hashlib.sha256((base/name).read_bytes()).hexdigest() == expected, name


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    output = parser.parse_args().output.resolve()
    assert output.is_relative_to(ROOT/'portability-checks')
    assert not output.exists(), 'Preserve previous preflight results.'
    frozen_bytes = (ROOT/'freeze.json').read_bytes()
    assert hashlib.sha256(frozen_bytes).hexdigest() == 'c6bf2c705fed802ed4bbe5f02ac8a50de55dc383298106caeb9b5e525e951c50'
    verify(ROOT, json.loads(frozen_bytes)['sha256'])
    original = json.loads((ROOT/'preserved-original-files.json').read_text(encoding='utf-8'))['sha256']
    assert len(original) == 29 and EXCLUDED.issubset(original)
    portable = {name: digest for name, digest in original.items() if name not in EXCLUDED}
    verify(ROOT.parent, portable)
    verify(ROOT.parent, portable, missing=EXCLUDED)
    original_rejects_cache_absence = False
    try:
        verify(ROOT.parent, original, missing=EXCLUDED)
    except FileNotFoundError:
        original_rejects_cache_absence = True
    assert original_rejects_cache_absence
    required_source_rejected = False
    try:
        verify(ROOT.parent, portable, missing={'upstream/dataset/environments/personal_profile_and_contacts/schema.py'})
    except FileNotFoundError:
        required_source_rejected = True
    assert required_source_rejected
    output.mkdir(parents=True)
    result = {'status': 'portable source/result preflight passed', 'original_manifest_entries': 29,
              'source_and_result_files_verified': len(portable), 'excluded_ignored_bytecode': sorted(EXCLUDED),
              'simulated_absent_bytecode_passes_preflight': True,
              'original_full_manifest_rejects_simulated_absence': original_rejects_cache_absence,
              'missing_required_source_rejected': required_source_rejected,
              'simulation': 'raise FileNotFoundError for specified absent paths; all other hashes computed from actual source bytes',
              'files_deleted_or_hashes_fabricated': False, 'environment_calls': 0, 'model_calls': 0,
              'full_portable_regression_executed': False, 'frozen_runner_adapted': False,
              'preflight_script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (output/'preflight.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
