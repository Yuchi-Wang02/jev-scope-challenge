"""Read-only post-run verifier around the preserved frozen study analyzer.

The original freeze helper writes identical manifest text on each call, which
can change Windows line endings. Verify its fingerprint/hashes here and inject
the verified manifest into that preserved analyzer without any file writes.
"""
import json
import math
import analyze_study
from study import HERE,canonical,sha


def check_summary(actual, expected, path='summary'):
    """Allow only last-bit float drift across Python versions; pin all other fields."""
    if type(actual) is not type(expected):
        raise ValueError(path+' type mismatch')
    if isinstance(expected, dict):
        if actual.keys() != expected.keys():
            raise ValueError(path+' keys mismatch')
        for key in expected:
            check_summary(actual[key], expected[key], path+'.'+str(key))
    elif isinstance(expected, list):
        if len(actual) != len(expected):
            raise ValueError(path+' length mismatch')
        for index, (value, saved) in enumerate(zip(actual, expected)):
            check_summary(value, saved, path+f'[{index}]')
    elif isinstance(expected, float):
        if not math.isclose(actual, expected, rel_tol=0, abs_tol=1e-12):
            raise ValueError(path+' numeric mismatch')
    elif actual != expected:
        raise ValueError(path+' exact mismatch')


def verified_manifest():
    manifest=json.loads((HERE/'manifest.json').read_text(encoding='utf-8'))
    payload={k:v for k,v in manifest.items() if k!='config_hash'}
    if sha(canonical(payload).encode()) != manifest['config_hash']:
        raise ValueError('Study manifest self-fingerprint mismatch')
    for path,expected in manifest['file_sha256_lf'].items():
        if sha((HERE/path).read_bytes().replace(b'\r\n',b'\n')) != expected:
            raise ValueError('Frozen study file changed: '+path)
    runtime=json.loads((HERE/'results/runtime.json').read_text(encoding='utf-8'))
    if runtime['config_hash'] != manifest['config_hash'] or runtime['status'] != 'complete' or runtime['sdpa_kernel'] != 'math_only':
        raise ValueError('Incomplete/foreign runtime')
    parity=json.loads((HERE/'results/pointer_parity.json').read_text(encoding='utf-8'))
    if parity['status'] != 'passed' or parity['max_probability_delta'] >= 1e-4:
        raise ValueError('Pointer engineering gate failed')
    return manifest


def verify():
    old=analyze_study.freeze
    # Only the manifest provider is replaced; record/scoring functions and real
    # files are unchanged. No model response or scientific result is mocked.
    analyze_study.freeze=verified_manifest
    try:
        summary=analyze_study.analyze(write=False)
    finally:
        analyze_study.freeze=old
    check_summary(summary,
                  json.loads((HERE/'results/summary.json').read_text(encoding='utf-8')))
    return summary


if __name__=='__main__':
    summary=verify()
    print(json.dumps({'status':'passed','config_hash':summary['config_hash'],
                      'actual_model_records':summary['model_forward_records'],'read_only':True}))
