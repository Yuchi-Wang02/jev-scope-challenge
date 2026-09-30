"""Final bounded suffix: native choice plus diagnostics; never resend prior calls."""
import argparse
import json
import subprocess
from contextlib import contextmanager

import repair_jev
from screen import ROOT, HERE, readable, sha, preserve
from execution_journal import exclusive_lock, read_events, replay, execute
from native_choice import adapt

STUDY = 'sharc-dev-source-label-screen-native-choice-final-v1'
FILES = ('research/source-label-screen/native_choice.py',
         'research/source-label-screen/final_repair.py',
         'research/source-label-screen/FINAL_READOUT.md')


def material():
    parent_freeze, full_plan, jobs, first_state, first_payload = repair_jev.parent()
    manifest, suffix_plan, payload = repair_jev.repair_material()
    if manifest != json.loads((HERE / 'repair_freeze.json').read_bytes()):
        raise ValueError('First repair freeze changed')
    for name, digest in manifest['source_hashes_lf'].items():
        if sha((ROOT / name).read_bytes().replace(b'\r\n', b'\n')) != digest:
            raise ValueError('First repair source changed')
    directory = repair_jev.location(manifest)
    with exclusive_lock(directory / 'jev.lock'):
        second_payload = (directory / 'jev.jsonl').read_bytes()
        events = read_events(directory / 'jev.jsonl')
    second = replay(events, plan_hash=manifest['repair_plan_sha256'], backend='jev', jobs=suffix_plan['jobs'])
    if (len(second['results']) != 7 or second['started'] != [j['id'] for j in jobs[23:30]] or
            not second['halted'] or second['unknown_usage'] or second['active_job'] is not None or
            second['active_session'] is not None):
        raise ValueError('Expected terminal seven-attempt first-repair suffix missing')
    all_results = {**first_state['results'], **second['results']}
    failed = 0
    for job in jobs[:30]:
        old = all_results[job['id']]
        new = adapt(old['detail']['raw_response'], old['detail']['http_status'], job['options'], old['latency_seconds'])
        if new['status'] != 'ok':
            raise ValueError('Prior response lacks a usable native choice/usage')
        if old['status'] == 'ok' and new['action'] != old['action']:
            raise ValueError('Previously accepted native action changed')
        failed += old['status'] != 'ok'
    last = all_results[jobs[29]['id']]
    last_view = adapt(last['detail']['raw_response'], last['detail']['http_status'], jobs[29]['options'], last['latency_seconds'])
    if failed != 2 or last_view['detail']['metadata_quality']['choice_is_displayed_argmax'] is not False:
        raise ValueError('Unexpected repair-trigger pattern')
    spent = first_state['input_tokens'] + second['input_tokens']
    plan = {**full_plan, 'study': STUDY, 'status': 'frozen_final_unstarted_suffix',
        'jobs': jobs[30:], 'counts': {'http_attempts': 18, 'local_generations': 0},
        'limits': {**full_plan['limits'], 'http_attempts': 18, 'jev_actual_input_tokens': 100000 - spent}}
    freeze = {'study': STUDY, 'status': 'final_native_choice_policy_no_further_readout_repairs',
        'first_journal_sha256': sha(first_payload), 'second_journal_sha256': sha(second_payload),
        'first_repair_freeze_sha256_lf': sha(readable(manifest)), 'prior_attempts': 30,
        'prior_input_tokens': spent, 'remaining_attempts': 18,
        'total_attempt_cap': 48, 'total_input_cap': 100000,
        'plan_sha256': sha(readable(plan)),
        'source_hashes_lf': {name: sha((ROOT / name).read_bytes().replace(b'\r\n', b'\n')) for name in FILES}}
    return freeze, plan, second_payload


def check():
    if subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT).strip():
        raise ValueError('Final suffix requires a clean committed checkout')
    repair_jev.check()
    freeze, plan, payload = material()
    artifacts = {'final_readout_freeze.json': readable(freeze), 'final_readout_plan.json': readable(plan),
                 'results/jev_first_repair_stopped.jsonl': payload}
    for name, expected in artifacts.items():
        path = HERE / name
        committed = subprocess.check_output(['git', 'show', 'HEAD:' + path.relative_to(ROOT).as_posix()], cwd=ROOT)
        if (path.read_bytes().replace(b'\r\n', b'\n') != expected or
                committed.replace(b'\r\n', b'\n') != expected):
            raise ValueError('Final suffix freeze changed or is not committed')
    return freeze, plan


def location(freeze):
    return ROOT / '.local' / STUDY / ('execution-' + freeze['plan_sha256'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('prepare', 'verify', 'run'))
    args = parser.parse_args()
    try:
        if args.command == 'prepare':
            freeze, plan, payload = material()
            for path, value in ((HERE / 'final_readout_freeze.json', readable(freeze)),
                (HERE / 'final_readout_plan.json', readable(plan)),
                (HERE / 'results/jev_first_repair_stopped.jsonl', payload)):
                preserve(path, value)
            print(json.dumps({'status': 'prepared_final_readout', 'remaining': 18, 'new_calls': 0}))
            return
        freeze, plan = check()
        if args.command == 'verify':
            print(json.dumps({'status': 'verified_final_readout', 'new_calls': 0}))
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
                yield wrapped, {**metadata, 'study': STUDY, 'execution_commit': commit}
        result = execute(location(freeze), plan, freeze['plan_sha256'], 'jev', factory)
        print(json.dumps({'status': result['status'], 'suffix_attempts': len(result['state']['started']),
            'suffix_finished': len(result['state']['results']),
            'all_phase_attempts': 30 + len(result['state']['started']),
            'all_phase_input_tokens': freeze['prior_input_tokens'] + result['state']['input_tokens'],
            'usage_incomplete': result['state']['unknown_usage']}, indent=2))
    except (Exception, KeyboardInterrupt) as error:
        print(json.dumps({'status': 'stopped', 'error_type': type(error).__name__}))
        raise SystemExit(1)


if __name__ == '__main__':
    main()
