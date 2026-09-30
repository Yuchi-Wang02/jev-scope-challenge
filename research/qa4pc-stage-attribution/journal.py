"""Durable single-attempt execution core. No network clients or model imports.

Callers supply a context-managed backend. This is accounting, not authorization
or evidence that references/model responses are scientifically valid.
"""
import json
import math
import os
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

# Adapted from this repository's frozen external-validation journal.
ACTIONS = ('yes', 'no', 'maybe')


def utc():
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def exclusive_lock(path):
    """OS-owned lock releases on process exit; the marker file is not a lease."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as handle:
        handle.seek(0, 2)
        if handle.tell() == 0:
            handle.write(b'0'); handle.flush()
        handle.seek(0)
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == 'nt':
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def read_events(path):
    path = Path(path)
    if not path.exists():
        return []
    raw = path.read_bytes()
    if raw and not raw.endswith(b'\n'):
        raise ValueError('Partial journal tail; preserve and investigate, never truncate')
    events = [json.loads(line) for line in raw.decode('utf-8').splitlines()]
    if any(not isinstance(e, dict) or type(e.get('seq')) != int or e['seq'] != i
           for i, e in enumerate(events)):
        raise ValueError('Journal sequence is missing or corrupt')
    return events


def append(path, events, event):
    record = {**event, 'seq': len(events), 'recorded_at_utc': utc()}
    encoded = (json.dumps(record, ensure_ascii=True, allow_nan=False) + '\n').encode()
    with Path(path).open('ab') as output:
        output.write(encoded); output.flush(); os.fsync(output.fileno())
    events.append(record)


def duration(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def validate_result(result):
    required = {'status', 'action', 'input_tokens', 'output_tokens', 'latency_seconds', 'detail'}
    if not isinstance(result, dict) or set(result) != required:
        raise ValueError('Backend result schema mismatch')
    if result['status'] not in ('ok', 'protocol_error', 'execution_error'):
        raise ValueError('Unknown backend status')
    action = result['action']
    if action is not None and (not isinstance(action, str) or action not in ACTIONS):
        raise ValueError('Invalid semantic action')
    if result['status'] != 'ok' and action is not None:
        raise ValueError('Failed backend must not claim an accepted action')
    for key in ('input_tokens', 'output_tokens'):
        value = result[key]
        if value is not None and (type(value) != int or value < 0):
            raise ValueError('Invalid usage')
    if result['status'] == 'ok' and any(result[k] is None for k in ('input_tokens', 'output_tokens')):
        raise ValueError('Successful call must report usage')
    if not duration(result['latency_seconds']) or not isinstance(result['detail'], dict):
        raise ValueError('Invalid latency or detail')


def replay(events, *, plan_hash, backend, jobs):
    """Reject unknown chronology; do not silently infer a completed request."""
    expected = {'event': 'header', 'version': 1, 'plan_sha256': plan_hash,
                'backend': backend, 'job_ids': [j['id'] for j in jobs]}
    state = {'started': [], 'results': {}, 'active_job': None, 'active_session': None,
             'sessions': 0, 'session_seconds': 0.0, 'input_tokens': 0,
             'output_tokens': 0, 'unknown_usage': False, 'halted': False}
    if not events:
        return state
    if any(events[0].get(k) != v for k, v in expected.items()):
        raise ValueError('Journal belongs to another plan/backend/cohort')
    for event in events[1:]:
        kind = event.get('event')
        if kind == 'session_start':
            if (state['active_session'] is not None or state['active_job'] is not None or
                    state['halted'] or state['unknown_usage']):
                raise ValueError('Session cannot start in unresolved/halted state')
            if event.get('session') != state['sessions']:
                raise ValueError('Session sequence mismatch')
            state['active_session'] = event['session']; state['sessions'] += 1
        elif kind == 'call_start':
            index = len(state['started'])
            if (state['active_session'] is None or state['active_job'] is not None or
                    state['halted'] or state['unknown_usage'] or index >= len(jobs) or
                    event.get('job_id') != jobs[index]['id']):
                raise ValueError('Repeated, unordered or unaccounted call start')
            state['active_job'] = event['job_id']; state['started'].append(event['job_id'])
        elif kind == 'call_finish':
            ident = event.get('job_id')
            if ident != state['active_job'] or ident is None:
                raise ValueError('Finish without matching unique start')
            result = event.get('result')
            validate_result(result)
            job = jobs[len(state['started']) - 1]
            if backend == 'qwen' and result['status'] == 'ok' and (
                    result['input_tokens'] != len(job['input_ids']) or
                    result['output_tokens'] > job['max_new_tokens']):
                raise ValueError('Local usage differs from planned input/output bounds')
            state['results'][ident] = result; state['active_job'] = None
            for key in ('input_tokens', 'output_tokens'):
                if result[key] is None:
                    state['unknown_usage'] = True
                else:
                    state[key] += result[key]
            state['halted'] |= result['status'] != 'ok'
        elif kind == 'session_end':
            if (state['active_session'] is None or event.get('session') != state['active_session'] or
                    not duration(event.get('elapsed_seconds'))):
                raise ValueError('Session end mismatch or invalid elapsed time')
            state['session_seconds'] += event['elapsed_seconds']
            state['active_session'] = None
        else:
            raise ValueError('Unknown journal event')
    return state


def stop_reason(state, backend, jobs, limits, elapsed):
    if state['active_job'] is not None or state['active_session'] is not None:
        return 'unresolved_interruption'
    if state['halted'] or state['unknown_usage']:
        return 'recorded_failure_requires_repair'
    if len(state['results']) == len(jobs):
        return 'complete'
    limit = limits['http_attempts'] if backend == 'jev' else limits['local_generations']
    if len(state['started']) >= limit:
        return 'attempt_budget'
    input_limit = limits['jev_actual_input_tokens'] if backend == 'jev' else limits['local_input_tokens']
    if state['input_tokens'] >= input_limit:
        return 'input_budget'
    if backend == 'qwen':
        job = jobs[len(state['started'])]
        if state['input_tokens'] + len(job['input_ids']) > input_limit:
            return 'input_budget'
        if state['output_tokens'] + job['max_new_tokens'] > limits['local_generated_tokens']:
            return 'output_budget'
        if elapsed >= limits['local_generation_wall_seconds']:
            return 'time_budget'
    return None


def outcome(reason, state, backend, limits):
    input_limit = limits['jev_actual_input_tokens'] if backend == 'jev' else limits['local_input_tokens']
    overruns = {'input_tokens': max(0, state['input_tokens'] - input_limit)}
    if backend == 'qwen':
        overruns.update(output_tokens=max(0, state['output_tokens'] - limits['local_generated_tokens']),
                        session_seconds=max(0, state['session_seconds'] - limits['local_generation_wall_seconds']))
    return {'status': reason, 'state': state, 'overruns': overruns}


def execute(directory, plan, plan_hash, backend, backend_factory, *, clock=time.monotonic):
    """Execute only unstarted jobs; no references or correctness-based stopping.

    Factory is entered under the OS lock after journal checks and yields
    (call(job, remaining_seconds), metadata). Unknown interrupted requests or
    sessions are never auto-retried. A new output directory is not a resume.
    """
    if backend not in ('jev', 'qwen'):
        raise ValueError('Unknown backend')
    jobs = [j for j in plan['jobs'] if j['backend'] == backend]
    if not jobs or len({j['id'] for j in jobs}) != len(jobs):
        raise ValueError('Empty or repeated job IDs')
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / (backend + '.jsonl')
    with exclusive_lock(directory / (backend + '.lock')):
        events = read_events(path)
        if not events:
            append(path, events, {'event': 'header', 'version': 1,
                                 'plan_sha256': plan_hash, 'backend': backend,
                                 'job_ids': [j['id'] for j in jobs]})
        state = replay(events, plan_hash=plan_hash, backend=backend, jobs=jobs)
        reason = stop_reason(state, backend, jobs, plan['limits'], state['session_seconds'])
        if reason:
            return outcome(reason, state, backend, plan['limits'])
        with backend_factory() as (call, metadata):
            session = state['sessions']
            prior_seconds = state['session_seconds']
            session_start = clock()
            append(path, events, {'event': 'session_start', 'session': session,
                                 'backend_metadata': metadata})
            try:
                while True:
                    state = replay(events, plan_hash=plan_hash, backend=backend, jobs=jobs)
                    # Current session is owned by this process; only previous
                    # unresolved sessions are rejected by the initial check.
                    state['active_session'] = None
                    elapsed = prior_seconds + clock() - session_start
                    reason = stop_reason(state, backend, jobs, plan['limits'], elapsed)
                    if reason:
                        break
                    job = jobs[len(state['started'])]
                    append(path, events, {'event': 'call_start', 'job_id': job['id']})
                    start = clock()
                    remaining = max(0, plan['limits']['local_generation_wall_seconds'] - elapsed)
                    try:
                        result = call(job, remaining)
                    except Exception as error:
                        # Deliberately no exception message; a transport exception
                        # can embed credential-bearing request data.
                        result = {'status': 'execution_error', 'action': None,
                                  'input_tokens': None, 'output_tokens': None,
                                  'latency_seconds': max(0, clock() - start),
                                  'detail': {'exception_type': type(error).__name__}}
                    # An invalid backend result leaves a durable unmatched start;
                    # never discard it or call the job again automatically.
                    validate_result(result)
                    append(path, events, {'event': 'call_finish', 'job_id': job['id'], 'result': result})
            finally:
                append(path, events, {'event': 'session_end', 'session': session,
                                     'elapsed_seconds': max(0, clock() - session_start)})
        state = replay(events, plan_hash=plan_hash, backend=backend, jobs=jobs)
        reason = stop_reason(state, backend, jobs, plan['limits'], state['session_seconds'])
        return outcome(reason or 'stopped', state, backend, plan['limits'])
