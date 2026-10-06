"""Bounded Jev pilot runner. Import/verify does not load credentials or call APIs.

Accounting and redaction patterns reuse this repository's payment-ownership and
qa4pc-stage-attribution runners; this module has no old study-global imports.
Native choice is the decision; displayed probabilities remain unnormalized data.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import time

HERE = Path(__file__).resolve().parent
MODEL = 'jev-1.13.0'
LABELS = ('RESUME_EXISTING', 'START_ADDITIONAL', 'CLARIFY')
LETTERS = 'ABC'
ENDPOINT = 'https://api.typesafe.ai/v1/systemone'
TRANSIENT = {408, 429, 500, 502, 503, 504, 529}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def decode_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate_json_key')
            result[key] = value
        return result
    def bad_constant(value):
        raise ValueError('nonfinite_json')
    return json.loads(raw, object_pairs_hook=unique, parse_constant=bad_constant)


def sanitize(value, key):
    if isinstance(value, dict):
        return {k: sanitize(v, key) for k, v in value.items()
                if k.lower() not in ('authorization', 'headers', 'api_key', 'apikey', 'x-api-key')}
    if isinstance(value, list):
        return [sanitize(v, key) for v in value]
    if isinstance(value, str):
        return re.sub(r'apikey_[A-Za-z0-9_]+', '[REDACTED]', value.replace(key, '[REDACTED]'))
    return value


def options_checked(options):
    if not isinstance(options, (list, tuple)) or len(options) != 3 or set(options) != set(LABELS):
        raise ValueError('invalid_option_mapping')
    return tuple(options)


def probability(value):
    return type(value) in (int, float) and math.isfinite(value) and 0 <= value <= 1


def validate_result(result):
    required = {'ok', 'prediction', 'input_tokens', 'output_tokens', 'error', 'raw_response',
                'metadata_quality', 'http_status', 'latency_s', 'ts_utc', 'retry_after_s'}
    if not isinstance(result, dict) or set(result) != required or type(result['ok']) is not bool:
        raise ValueError('invalid_result_schema')
    if (result['ok'] and result['prediction'] not in LABELS) or (not result['ok'] and result['prediction'] is not None):
        raise ValueError('invalid_result_prediction')
    for name in ('input_tokens', 'output_tokens'):
        value = result[name]
        if (value is not None and (type(value) is not int or value < 0)) or (result['ok'] and value is None):
            raise ValueError('invalid_result_usage')
    latency = result['latency_s']
    if type(latency) not in (int, float) or not math.isfinite(latency) or latency < 0:
        raise ValueError('invalid_result_latency')
    if type(result['retry_after_s']) is not int or result['retry_after_s'] < 0:
        raise ValueError('invalid_retry_delay')
    status = result['http_status']
    if status is not None and (type(status) is not int or not 100 <= status <= 599):
        raise ValueError('invalid_http_status')
    if result['ok'] and status != 200:
        raise ValueError('successful_non200_response')
    if not isinstance(result['ts_utc'], str) or (result['error'] is not None and not isinstance(result['error'], str)):
        raise ValueError('invalid_result_metadata')


def adapt_response(raw, http_status, options):
    options = options_checked(options)
    result = {'ok': False, 'prediction': None, 'input_tokens': None, 'output_tokens': None,
              'error': None, 'raw_response': raw, 'metadata_quality': None}
    usage = raw.get('usage', {}) if isinstance(raw, dict) else {}
    if isinstance(usage, dict):
        for name in ('input_tokens', 'output_tokens'):
            if type(usage.get(name)) is int and usage[name] >= 0:
                result[name] = usage[name]
    try:
        if http_status != 200:
            raise ValueError('http_failure')
        if not isinstance(raw, dict) or raw.get('model') != MODEL:
            raise ValueError('served_model_mismatch')
        answers = raw.get('answers')
        if not isinstance(answers, dict) or set(answers) != {'decision'}:
            raise ValueError('answer_keys')
        answer = answers['decision']
        if not isinstance(answer, dict) or answer.get('type') != 'choice':
            raise ValueError('answer_type')
        choice = answer.get('choice')
        if not isinstance(choice, str) or choice not in tuple(LETTERS):
            raise ValueError('choice')
        if result['input_tokens'] is None or result['output_tokens'] is None:
            raise ValueError('usage')
        probabilities = answer.get('probabilities')
        keys_valid = isinstance(probabilities, dict) and set(probabilities) == set(LETTERS)
        values_valid = keys_valid and all(probability(p) for p in probabilities.values())
        total = sum(probabilities.values()) if values_valid else None
        top = [k for k, p in probabilities.items() if p == max(probabilities.values())] if values_valid and total else []
        result['metadata_quality'] = {
            'probability_keys_valid': keys_valid, 'probability_values_valid': values_valid,
            'raw_sum': total, 'within_sum_tolerance': abs(total - 1) <= 1e-4 if total is not None else None,
            'normalization_applied': False, 'calibration_quality_established': False,
            'choice_is_displayed_argmax': choice in top if top else None,
            'displayed_top_tie': len(top) > 1 if top else None,
            'confidence_valid': probability(answer.get('confidence')),
        }
        result.update(ok=True, prediction=options[LETTERS.index(choice)])
    except ValueError as error:
        result['error'] = str(error)
    return result


def read_rows(path):
    path = Path(path)
    if not path.exists():
        return []
    raw = path.read_bytes()
    if raw and not raw.endswith(b'\n'):
        raise ValueError('partial_jsonl_tail_preserve_and_reconcile')
    return [decode_json(line) for line in raw.decode('utf-8').splitlines()]


def append(path, record):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('ab') as output:
        output.write((canonical(record) + '\n').encode('utf-8'))
        output.flush()
        os.fsync(output.fileno())


@contextmanager
def exclusive_lock(path):
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


def verify(root=HERE):
    root = Path(root).resolve()
    raw = (root / 'freeze.json').read_bytes()
    freeze = decode_json(raw)
    if freeze.get('model') != MODEL:
        raise ValueError('freeze_model')
    for name, maximum in (('attempt_limit', 156), ('retry_limit', 9), ('planned_input_limit', 1000000)):
        if type(freeze.get(name)) is not int or not (0 if name == 'retry_limit' else 1) <= freeze[name] <= maximum:
            raise ValueError('freeze_limit')
    hashes = freeze.get('sha256')
    if not isinstance(hashes, dict) or not {'plans/jev.jsonl', 'run_jev.py'} <= set(hashes):
        raise ValueError('freeze_missing_required_hashes')
    for name, expected in hashes.items():
        path = (root / name).resolve()
        if root not in path.parents or digest(path.read_bytes()) != expected:
            raise ValueError('frozen_file_mismatch')
    jobs = read_rows(root / 'plans/jev.jsonl')
    if not jobs or len({j['job_id'] for j in jobs}) != len(jobs):
        raise ValueError('empty_or_duplicate_jobs')
    primary_seen = False
    for job in jobs:
        options_checked(job['option_order'])
        if job['phase'] not in ('smoke', 'primary'):
            raise ValueError('job_phase')
        if job['phase'] == 'primary':
            primary_seen = True
        elif primary_seen or job.get('smoke_reference') not in LABELS:
            raise ValueError('smoke_order_or_reference')
        body = job['body']
        if body.get('model') != MODEL or digest(canonical(body).encode()) != job['request_sha256']:
            raise ValueError('request_hash_or_model')
        questions = body.get('questions', {})
        if set(questions) != {'decision'} or questions['decision'].get('type') != 'choice':
            raise ValueError('request_choice_contract')
        if set(questions['decision'].get('criteria', {})) != set(LETTERS):
            raise ValueError('request_criteria')
        units = job['planned_input_units']
        if type(units) is not int or units < len(canonical(body).encode('utf-8')) + 256:
            raise ValueError('underreserved_planning_units')
    if not any(j['phase'] == 'smoke' for j in jobs):
        raise ValueError('missing_smoke')
    if len(jobs) > freeze['attempt_limit'] or sum(j['planned_input_units'] for j in jobs) > freeze['planned_input_limit']:
        raise ValueError('plan_exceeds_caps')
    return jobs, freeze, digest(raw)


def accounting(events, jobs, freeze_hash):
    index = {j['job_id']: j for j in jobs}
    starts, finishes = {}, {}
    active = None
    per_job = {}
    for event in events:
        attempt = event.get('attempt_id')
        if event.get('event') == 'started':
            if active is not None or type(attempt) is not int or attempt != len(starts) + 1:
                raise ValueError('invalid_attempt_sequence')
            job = index.get(event.get('job_id'))
            if job is None or event.get('freeze_sha256') != freeze_hash or event.get('request_sha256') != job['request_sha256']:
                raise ValueError('attempt_plan_mismatch')
            previous = per_job.get(job['job_id'], [])
            retry = len(previous)
            if retry > 1 or event.get('retry_index') != retry or event.get('planned_input_units') != job['planned_input_units']:
                raise ValueError('invalid_retry_or_reservation')
            if previous and (finishes[previous[-1]]['result']['ok'] or not finishes[previous[-1]]['retry_allowed']):
                raise ValueError('retry_after_terminal')
            starts[attempt] = event
            per_job.setdefault(job['job_id'], []).append(attempt)
            active = attempt
        elif event.get('event') == 'finished':
            if active is None or attempt != active or attempt in finishes or event.get('job_id') != starts[attempt]['job_id']:
                raise ValueError('invalid_finish_sequence')
            result = event.get('result')
            validate_result(result)
            if type(event.get('retry_allowed')) is not bool or (event['retry_allowed'] and (result['ok'] or starts[attempt]['retry_index'] != 0)):
                raise ValueError('invalid_retry_marker')
            finishes[attempt] = event
            active = None
        else:
            raise ValueError('unknown_attempt_event')
    return {'attempts': len(starts), 'retries': sum(s['retry_index'] for s in starts.values()),
            'planned_input_units': sum(s['planned_input_units'] for s in starts.values()),
            'known_input_tokens': sum(e['result'].get('input_tokens') or 0 for e in finishes.values()),
            'known_output_tokens': sum(e['result'].get('output_tokens') or 0 for e in finishes.values()),
            'unknown_usage_attempts': sum(any(e['result'][k] is None for k in ('input_tokens', 'output_tokens')) for e in finishes.values()),
            'unfinished': active, 'starts': starts, 'finishes': finishes, 'per_job': per_job}


def check_budget(stats, job, retry_index, limits):
    if stats['unfinished'] is not None:
        raise RuntimeError('unfinished_attempt_requires_reconciliation')
    if stats['attempts'] >= limits['attempt_limit']:
        raise RuntimeError('attempt_cap')
    if retry_index and stats['retries'] >= limits['retry_limit']:
        raise RuntimeError('retry_cap')
    reserve = job['planned_input_units']
    if max(stats['planned_input_units'], stats['known_input_tokens']) + reserve > limits['planned_input_limit']:
        raise RuntimeError('input_cap')


def terminal_record(event, job):
    return {'attempt_id': event['attempt_id'], 'job_id': job['job_id'], 'phase': job['phase'],
            'item_id': job['item_id'], 'option_order': job['option_order'],
            'request_sha256': job['request_sha256'], **event['result'],
            'smoke_correct': event['result']['prediction'] == job['smoke_reference'] if job['phase'] == 'smoke' else None}


def reconcile(stats, responses, jobs, path):
    if stats['unfinished'] is not None:
        raise RuntimeError('unfinished_attempt_requires_reconciliation')
    indexed = {r['job_id']: r for r in responses}
    if len(indexed) != len(responses):
        raise ValueError('duplicate_terminal_record')
    expected = {}
    for job in jobs:
        attempts = stats['per_job'].get(job['job_id'], [])
        if attempts:
            last = stats['finishes'][attempts[-1]]
            if last['result']['ok'] or not last['retry_allowed']:
                expected[job['job_id']] = terminal_record(last, job)
    if any(ident not in expected or row != expected[ident] for ident, row in indexed.items()):
        raise ValueError('terminal_record_mismatch')
    for ident, row in expected.items():
        if ident not in indexed:
            append(path, row)
            indexed[ident] = row
    return indexed


@contextmanager
def live_client():
    # Deliberately env-only: no implicit credential-file reads or provider fallback.
    key = os.environ.get('TYPESAFE_API_KEY')
    if not key:
        raise RuntimeError('missing_TYPESAFE_API_KEY')
    import httpx
    with httpx.Client(timeout=60, follow_redirects=False, trust_env=False,
                      transport=httpx.HTTPTransport(retries=0)) as client:
        def call(job):
            start = time.monotonic()
            status, raw, error, retry_after = None, None, None, 1
            try:
                response = client.post(ENDPOINT, json=job['body'], headers={'Authorization': 'Bearer ' + key})
                status = response.status_code
                try:
                    raw = sanitize(decode_json(response.text), key)
                except ValueError:
                    raw = {'invalid_json_body': sanitize(response.text, key)}
                    error = 'invalid_json_body'
                value = response.headers.get('Retry-After', '1')
                retry_after = int(value) if value.isdigit() else 31
            except Exception as exc:
                error = 'transport_' + type(exc).__name__
            result = adapt_response(raw, status, job['option_order'])
            if error:
                result['error'] = error
            result.update(http_status=status, latency_s=time.monotonic() - start,
                          ts_utc=utc(), retry_after_s=retry_after)
            return result
        yield call


def run(phase, root=HERE, factory=live_client, sleep=time.sleep):
    if phase not in ('smoke', 'primary'):
        raise ValueError('invalid_phase')
    root = Path(root)
    jobs, limits, freeze_hash = verify(root)
    directory = root / 'results'
    ledger = directory / 'jev_attempts.jsonl'
    response_path = directory / 'jev_responses.jsonl'
    with exclusive_lock(directory / 'jev.lock'):
        stats = accounting(read_rows(ledger), jobs, freeze_hash)
        completed = reconcile(stats, read_rows(response_path), jobs, response_path)
        if any(not r['ok'] for r in completed.values()):
            raise RuntimeError('terminal_failure_requires_reconciliation')
        if phase == 'primary' and any(j['job_id'] not in completed or not completed[j['job_id']]['smoke_correct'] for j in jobs if j['phase'] == 'smoke'):
            raise RuntimeError('smoke_gate_not_passed')
        todo = [j for j in jobs if j['phase'] == phase and j['job_id'] not in completed]
        if todo:
            with factory() as call:
                for job in todo:
                    while True:
                        stats = accounting(read_rows(ledger), jobs, freeze_hash)
                        retry = len(stats['per_job'].get(job['job_id'], []))
                        check_budget(stats, job, retry, limits)
                        if retry:
                            previous = stats['finishes'][stats['per_job'][job['job_id']][-1]]
                            sleep(max(0, previous['result']['retry_after_s']))
                        attempt = stats['attempts'] + 1
                        append(ledger, {'event': 'started', 'attempt_id': attempt, 'job_id': job['job_id'],
                            'retry_index': retry, 'planned_input_units': job['planned_input_units'],
                            'request_sha256': job['request_sha256'], 'freeze_sha256': freeze_hash, 'ts_utc': utc()})
                        # A crash or invalid backend result leaves an unmatched durable start.
                        result = call(job)
                        retry_allowed = (not result['ok'] and retry == 0 and
                            (result['http_status'] in TRANSIENT or result['http_status'] is None) and
                            type(result['retry_after_s']) is int and 0 <= result['retry_after_s'] <= 30 and
                            stats['retries'] < limits['retry_limit'])
                        event = {'event': 'finished', 'attempt_id': attempt, 'job_id': job['job_id'],
                                 'retry_allowed': retry_allowed, 'result': result, 'ts_utc': utc()}
                        # Validate before persisting; do not silently accept malformed custom backends.
                        accounting(read_rows(ledger) + [event], jobs, freeze_hash)
                        append(ledger, event)
                        if retry_allowed:
                            continue
                        record = terminal_record(event, job)
                        append(response_path, record)
                        if not result['ok']:
                            raise RuntimeError('persisted_terminal_failure')
                        print(canonical({'job_id': job['job_id'], 'ok': True, 'attempts': attempt}), flush=True)
                        break
        stats = accounting(read_rows(ledger), jobs, freeze_hash)
        completed = reconcile(stats, read_rows(response_path), jobs, response_path)
        return {'phase': phase, 'complete': all(j['job_id'] in completed for j in jobs if j['phase'] == phase),
                'attempts': stats['attempts'], 'retries': stats['retries'],
                'known_input_tokens': stats['known_input_tokens'], 'known_output_tokens': stats['known_output_tokens'],
                'planned_input_units': stats['planned_input_units'], 'unknown_usage_attempts': stats['unknown_usage_attempts'],
                'terminal_responses': len(completed)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('verify', 'smoke', 'primary'))
    parser.add_argument('--root', type=Path, default=HERE)
    args = parser.parse_args()
    try:
        if args.command == 'verify':
            jobs, _, _ = verify(args.root)
            print(canonical({'verified': True, 'jobs': len(jobs), 'new_calls': 0}))
        else:
            print(canonical(run(args.command, args.root)))
    except Exception as error:
        # Never expose request/exception reprs, credential values, or traceback locals.
        print(canonical({'status': 'stopped', 'error_type': type(error).__name__}))
        raise SystemExit(1)


if __name__ == '__main__':
    main()
