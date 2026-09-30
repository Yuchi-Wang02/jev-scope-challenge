"""Run an exact, committed execution freeze after revalidating human review.

No execution freeze exists yet. Missing freeze fails before key/weight loading.
"""
import argparse
import json
import subprocess
from pathlib import Path

from comparison_plan import (ROOT, HERE, PLAN_ID, STUDY, compile_reviewed,
                              private_directory, readable, sha)
from execution_journal import execute

FREEZE_PATH = HERE / 'EXECUTION_FREEZE.json'
PROTOCOL_PATH = HERE / 'EXECUTION_PROTOCOL.md'
SOURCE_FILES = (
    'research/external-validation/run_comparison.py',
    'research/external-validation/comparison_backends.py',
    'research/external-validation/execution_journal.py',
    'research/external-validation/comparison_plan.py',
    'research/external-validation/shortcut_controls.py',
    'research/external-validation/paired_metrics.py',
    'research/external-validation/action_interface.py',
    'research/external-validation/prepare_sharc_review.py',
    'research/external-validation/review_reconcile.py',
    'research/external-validation/review_finalize.py',
    'research/external-validation/inspect_sharc.py',
    'research/external-validation/inspect_sharc_pairs.py',
    'research/external-validation/COMPARISON_DRAFT.md',
    'research/action-backends/adapters.py',
    'research/generation-calibration/settings.py',
    'research/generation-calibration/interface.py',
    'research/payment-ownership/run_api_v02.py',
    'research/payment-ownership/study.py',
    'research/baseline-readiness/qwen35-smoke-repaired/run.json',
)


def check_freeze():
    if not FREEZE_PATH.is_file() or not PROTOCOL_PATH.is_file():
        raise ValueError('Inference closed: reviewed-cohort execution freeze is not published')
    if subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT).strip():
        raise ValueError('Execution requires a clean committed checkout')
    for path in (FREEZE_PATH, PROTOCOL_PATH):
        name = path.relative_to(ROOT).as_posix()
        committed = subprocess.check_output(['git', 'show', 'HEAD:' + name], cwd=ROOT)
        if committed.replace(b'\r\n', b'\n') != path.read_bytes().replace(b'\r\n', b'\n'):
            raise ValueError('Freeze or execution protocol is not the committed version')
    freeze = json.loads(FREEZE_PATH.read_text(encoding='utf-8'))
    if freeze.get('status') != 'frozen_for_execution' or freeze.get('study') != PLAN_ID:
        raise ValueError('Unknown execution freeze')
    expected = {name: sha((ROOT / name).read_bytes().replace(b'\r\n', b'\n')) for name in SOURCE_FILES}
    if freeze.get('source_hashes_lf') != expected:
        raise ValueError('Execution source pins do not match')
    if freeze.get('protocol_sha256_lf') != sha(PROTOCOL_PATH.read_bytes().replace(b'\r\n', b'\n')):
        raise ValueError('Execution protocol hash mismatch')
    return freeze


def verified_plan(args, freeze):
    directory = private_directory(args.plan_dir)
    saved_plan = (directory / 'comparison_plan.json').read_bytes()
    saved_refs = (directory / 'scoring_references.json').read_bytes()
    if sha(saved_plan) != freeze.get('plan_sha256') or sha(saved_refs) != freeze.get('references_sha256'):
        raise ValueError('Private plan/reference bytes differ from the published freeze')
    plan, refs = compile_reviewed(args.review_a, args.review_b, args.adjudication,
                                   args.review_dir, args.model_dir)
    if saved_plan != readable(plan) or saved_refs != readable(refs):
        raise ValueError('Plan cannot be reproduced from the preserved reviewed cohort')
    return plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('backend', choices=('jev', 'qwen'))
    parser.add_argument('--plan-dir', type=Path, default=ROOT / '.local' / PLAN_ID)
    parser.add_argument('--review-dir', type=Path, default=ROOT / '.local' / STUDY)
    parser.add_argument('--review-a', type=Path, required=True)
    parser.add_argument('--review-b', type=Path, required=True)
    parser.add_argument('--adjudication', type=Path, required=True)
    parser.add_argument('--model-dir', type=Path, required=True)
    parser.add_argument('--validate-only', action='store_true')
    args = parser.parse_args()
    stage = 'freeze'
    try:
        freeze = check_freeze()
        stage = 'review_and_plan'
        plan = verified_plan(args, freeze)
        if args.validate_only:
            print(json.dumps({'status': 'freeze_and_review_chain_verified', 'model_calls': 0}))
            return
        from comparison_backends import jev_backend, qwen_backend
        stage = 'execution'
        factory = jev_backend if args.backend == 'jev' else lambda: qwen_backend(
            args.model_dir, [j for j in plan['jobs'] if j['backend'] == 'qwen'])
        # One deterministic location per exact plan; no arbitrary --output route
        # that could accidentally create a fresh journal for the same jobs.
        directory = private_directory(ROOT / '.local' / ('execution-' + freeze['plan_sha256']))
        result = execute(directory, plan, freeze['plan_sha256'], args.backend, factory)
        state = result['state']
        print(json.dumps({'status': result['status'], 'backend': args.backend,
            'attempts_started': len(state['started']), 'results_recorded': len(state['results']),
            'known_input_tokens': state['input_tokens'], 'known_output_tokens': state['output_tokens'],
            'unknown_usage': state['unknown_usage'], 'generation_session_seconds': state['session_seconds'],
            'overruns': result['overruns']}, indent=2))
    except (Exception, KeyboardInterrupt) as error:
        # Do not print exception text from a possible backend/transport path.
        print(json.dumps({'status': 'stopped', 'stage': stage, 'error_type': type(error).__name__,
                          'instruction': 'Preserve records; inspect freeze, review chain and journal before resuming.'}))
        raise SystemExit(1)


if __name__ == '__main__':
    main()
