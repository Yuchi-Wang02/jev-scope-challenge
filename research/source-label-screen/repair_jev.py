"""Frozen repair branch: preserve 23 original attempts, request only 25 unstarted jobs."""
import argparse
import json
import subprocess
from contextlib import contextmanager
from pathlib import Path

import screen
from screen import ROOT, HERE, readable, sha, preserve
from decision_readout import adapt
from execution_journal import read_events, replay, exclusive_lock, execute

PARENT_COMMIT = 'e90f051459370ad99be8ddfaf29e65c013d2eda1'
STUDY = 'sharc-dev-source-label-screen-jev-readout-repair-v1'
PATH = HERE / 'repair_freeze.json'
SOURCE_NAMES = ('research/source-label-screen/repair_jev.py',
    'research/source-label-screen/decision_readout.py',
    'research/source-label-screen/READOUT_REPAIR.md')


def parent():
    freeze = json.loads((HERE / 'freeze.json').read_bytes())
    names = ['research/source-label-screen/' + n for n in ('freeze.json', *freeze['artifact_sha256_lf'])]
    for name in (*names, *freeze['source_hashes_lf']):
        historical = subprocess.check_output(['git', 'show', PARENT_COMMIT + ':' + name], cwd=ROOT)
        if historical.replace(b'\r\n', b'\n') != (ROOT / name).read_bytes().replace(b'\r\n', b'\n'):
            raise ValueError('Parent evidence/source differs from execution commit')
    plan = json.loads((HERE / 'plan.json').read_bytes())
    jobs = [j for j in plan['jobs'] if j['backend'] == 'jev']
    directory = screen.directory(freeze)
    with exclusive_lock(directory / 'jev.lock'):
        payload = (directory / 'jev.jsonl').read_bytes()
        events = read_events(directory / 'jev.jsonl')
    state = replay(events, plan_hash=freeze['artifact_sha256_lf']['plan.json'], backend='jev', jobs=jobs)
    if (len(state['results']) != 23 or state['started'] != [j['id'] for j in jobs[:23]] or
            not state['halted'] or state['unknown_usage'] or state['active_job'] is not None or
            state['active_session'] is not None):
        raise ValueError('Expected terminal 23-attempt parent ledger not found')
    errors = 0
    for job in jobs[:23]:
        old = state['results'][job['id']]
        new = adapt(old['detail']['raw_response'], old['detail']['http_status'],
                    job['options'], old['latency_seconds'])
        if new['status'] != 'ok':
            raise ValueError('Parent has a failure not resolved by the declared readout')
        if old['status'] != 'ok':
            errors += 1
            if old['status'] != 'protocol_error' or new['detail']['probability_quality']['within_original_sum_tolerance']:
                raise ValueError('Parent failure is not the isolated sum-check issue')
        elif new['action'] != old['action']:
            raise ValueError('Valid historical decision changed')
    if errors != 1:
        raise ValueError('Unexpected parent failure count')
    return freeze, plan, jobs, state, payload


def repair_material():
    freeze, plan, jobs, state, payload = parent()
    limits = {**plan['limits'], 'http_attempts': 25,
              'jev_actual_input_tokens': plan['limits']['jev_actual_input_tokens'] - state['input_tokens']}
    repaired = {**plan, 'study': STUDY, 'status': 'frozen_unstarted_suffix_only',
                'jobs': jobs[23:], 'limits': limits,
                'counts': {'http_attempts': 25, 'local_generations': 0}}
    manifest = {'study': STUDY, 'status': 'frozen_for_readout_repair',
        'parent_execution_commit': PARENT_COMMIT,
        'parent_plan_sha256': freeze['artifact_sha256_lf']['plan.json'],
        'parent_journal_sha256': sha(payload), 'parent_attempts': 23,
        'parent_input_tokens': state['input_tokens'], 'remaining_attempts': 25,
        'original_total_attempt_cap': 48, 'original_total_input_cap': 100000,
        'repair_plan_sha256': sha(readable(repaired)),
        'source_hashes_lf': {name: sha((ROOT / name).read_bytes().replace(b'\r\n', b'\n')) for name in SOURCE_NAMES}}
    return manifest, repaired, payload


def check():
    if subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT).strip():
        raise ValueError('Repair requires a clean committed checkout')
    manifest, plan, payload = repair_material()
    for path, expected in ((PATH, readable(manifest)), (HERE / 'repair_plan.json', readable(plan)),
                           (HERE / 'results/jev_original_stopped.jsonl', payload)):
        if path.read_bytes().replace(b'\r\n', b'\n') != expected:
            raise ValueError('Repair inputs changed')
        historical = subprocess.check_output(['git', 'show', 'HEAD:' + path.relative_to(ROOT).as_posix()], cwd=ROOT)
        if historical.replace(b'\r\n', b'\n') != expected:
            raise ValueError('Repair freeze is not committed')
    return manifest, plan


def location(manifest):
    return ROOT / '.local' / STUDY / ('execution-' + manifest['repair_plan_sha256'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('prepare', 'verify', 'run'))
    args = parser.parse_args()
    try:
        if args.command == 'prepare':
            manifest, plan, payload = repair_material()
            targets = [(PATH, readable(manifest)), (HERE / 'repair_plan.json', readable(plan)),
                       (HERE / 'results/jev_original_stopped.jsonl', payload)]
            # Original parent transcript is copied byte-for-byte, never edited.
            for path, data in targets:
                preserve(path, data)
            print(json.dumps({'status': 'prepared_readout_repair', 'new_calls': 0,
                              'remaining_planned': 25, 'parent_journal_sha256': sha(payload)}))
            return
        manifest, plan = check()
        if args.command == 'verify':
            print(json.dumps({'status': 'verified_readout_repair', 'new_calls': 0}))
            return
        from comparison_backends import jev_backend
        @contextmanager
        def factory():
            with jev_backend() as (call, metadata):
                def wrapped(job, remaining):
                    result = call(job, remaining)
                    return adapt(result['detail']['raw_response'], result['detail']['http_status'],
                                 job['options'], result['latency_seconds'])
                commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
                yield wrapped, {**metadata, 'execution_commit': commit,
                    'study': STUDY, 'parent_journal_sha256': manifest['parent_journal_sha256']}
        result = execute(location(manifest), plan, manifest['repair_plan_sha256'], 'jev', factory)
        print(json.dumps({'status': result['status'], 'suffix_attempts': len(result['state']['started']),
            'suffix_finished': len(result['state']['results']),
            'suffix_input_tokens': result['state']['input_tokens'],
            'all_phase_attempts': 23 + len(result['state']['started']),
            'all_phase_input_tokens': manifest['parent_input_tokens'] + result['state']['input_tokens'],
            'usage_incomplete': result['state']['unknown_usage']}, indent=2))
    except (Exception, KeyboardInterrupt) as error:
        print(json.dumps({'status': 'stopped', 'error_type': type(error).__name__}))
        raise SystemExit(1)


if __name__ == '__main__':
    main()
