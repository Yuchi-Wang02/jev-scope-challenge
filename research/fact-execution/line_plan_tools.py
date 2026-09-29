"""Build/verify public, unscored line-evidence prompts before any inference."""
import argparse
import hashlib
import json

from data_tools import HERE, original_cases
from line_evidence import audit_plan, plan_queries

OUT = HERE / 'preparation'
PLANS = OUT / 'line_query_plans.jsonl'
MANIFEST = OUT / 'line_query_manifest.json'


def digest(payload):
    return hashlib.sha256(payload.replace(b'\r\n', b'\n')).hexdigest()


def expected():
    plans = plan_queries(original_cases())
    identity = {(p['source_id'], p['field'], p['line_index'], p['mapping']) for p in plans}
    if len(plans) != 1096 or len(identity) != len(plans):
        raise ValueError('Missing or duplicate query')
    if any(p['representation'] != 'original' or p['split'] != 'development' for p in plans):
        raise ValueError('Foreign input in plan')
    payload = ''.join(json.dumps(p, ensure_ascii=False, separators=(',', ':')) + '\n'
                      for p in plans).encode('utf-8')
    source = (HERE / 'data/original_cases.jsonl').read_bytes()
    protocol = (HERE / 'LINE_EVIDENCE_PROTOCOL.md').read_bytes()
    implementation = (HERE / 'line_evidence.py').read_bytes()
    manifest = {'status': 'unscored_preparation_not_execution_freeze',
                'source_original_cases_sha256_lf': digest(source),
                'protocol_sha256_lf': digest(protocol),
                'implementation_sha256_lf': digest(implementation),
                'query_plans_sha256_lf': digest(payload),
                'query_plans': len(plans), 'primary_order_plans': len(plans) // 2,
                'planned_primary_arm': 'N1_historical_kev_lora_native',
                'actual_model_forwards': 0,
                'rewrite_or_reserved_queries': 0,
                'human_annotations_produced': 0,
                'note': 'Model prompts are in the prompt key; IDs and spans are audit metadata, not model input. No inference has run.'}
    return payload, (json.dumps(manifest, indent=2, ensure_ascii=False) + '\n').encode('utf-8')


def run(command):
    payload, manifest = expected()
    if command == 'build':
        OUT.mkdir(exist_ok=True)
        for path, content in ((PLANS, payload), (MANIFEST, manifest)):
            if path.exists() and path.read_bytes().replace(b'\r\n', b'\n') != content:
                raise ValueError(f'Existing preparation drift: {path.name}')
            if not path.exists():
                path.write_bytes(content)
    else:
        for path, content in ((PLANS, payload), (MANIFEST, manifest)):
            if path.read_bytes().replace(b'\r\n', b'\n') != content:
                raise ValueError(f'Preparation drift: {path.name}')
    return {'status': 'verified' if command == 'verify' else 'built',
            'planned_queries': audit_plan()['two_order_planned_queries'],
            'model_forwards': 0, 'rewrite_or_reserved_queries': 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('build', 'verify'))
    args = parser.parse_args()
    print(json.dumps(run(args.command)))
