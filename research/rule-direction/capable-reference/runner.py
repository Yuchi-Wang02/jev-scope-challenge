"""Durable, zero-retry Messages runner. Imports and dry-run never access the network."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import time
import urllib.error
import urllib.request

import prepare

ENDPOINT = 'https://api.anthropic.com/v1/messages'
LABEL = re.compile(r'(yes|no|maybe)\Z')


def now():
    return datetime.now(timezone.utc).isoformat()


def reservation(estimate):
    tokens = estimate + prepare.INPUT_ALLOWANCE
    return {'input_tokens': tokens, 'output_tokens': prepare.MAX_OUTPUT,
            'cost_microusd': 2 * tokens + 10 * prepare.MAX_OUTPUT}


def parse_usage(body):
    usage = body.get('usage') if isinstance(body, dict) else None
    if not isinstance(usage, dict):
        raise ValueError('missing_usage')
    for name in ('input_tokens', 'output_tokens'):
        if not prepare.integer(usage.get(name)):
            raise ValueError('invalid_usage_' + name)
    for name in ('cache_creation_input_tokens', 'cache_read_input_tokens'):
        value = usage.get(name, 0)
        if not prepare.integer(value) or value != 0:
            raise ValueError('unexpected_cache_usage')
    creation = usage.get('cache_creation')
    if creation is not None:
        if not isinstance(creation, dict) or any(not prepare.integer(v) or v != 0 for v in creation.values()):
            raise ValueError('unexpected_cache_creation')
    return {'input_tokens': usage['input_tokens'], 'output_tokens': usage['output_tokens'],
            'cost_microusd': 2 * usage['input_tokens'] + 10 * usage['output_tokens']}


def classify(raw, reserve):
    """Recomputed on journal replay; no reference label is available here."""
    fatal = []
    if raw.get('credential_redacted'):
        fatal.append('credential_echo_redacted')
    try:
        body = json.loads(raw['full_body'])
    except (ValueError, TypeError, KeyError):
        body = None
        fatal.append('invalid_json_body')
    try:
        usage = parse_usage(body)
    except ValueError as exc:
        usage = None
        fatal.append(str(exc))
    if raw.get('transport_error'):
        fatal.append('transport_error')
    if raw.get('http_status') != 200:
        fatal.append('http_error')
    label, text, stop = None, None, None
    status = 'protocol_error'
    if isinstance(body, dict):
        stop = body.get('stop_reason')
        if body.get('model') != prepare.MODEL:
            fatal.append('served_model_mismatch')
        blocks = body.get('content')
        schema_ok = (body.get('type') == 'message' and body.get('role') == 'assistant'
                     and isinstance(body.get('id'), str) and bool(body['id'])
                     and isinstance(blocks, list))
        if schema_ok:
            for block in blocks:
                if not isinstance(block, dict):
                    schema_ok = False
                    break
                kind = block.get('type')
                field = {'text': 'text', 'thinking': 'thinking', 'redacted_thinking': 'data'}.get(kind)
                if field is None or not isinstance(block.get(field), str):
                    schema_ok = False
                    break
        if not schema_ok:
            fatal.append('message_schema_error')
        else:
            text = ''.join(block['text'] for block in blocks if block['type'] == 'text').strip()
            if stop == 'max_tokens':
                status = 'truncated'
                fatal.append('truncation')
            elif stop == 'refusal':
                status = 'refusal'
            elif stop == 'end_turn':
                label = text if LABEL.fullmatch(text) else None
                status = 'ok' if label else 'invalid'
            else:
                fatal.append('unexpected_stop_reason')
    else:
        fatal.append('message_schema_error')
    if usage is not None:
        if usage['input_tokens'] > reserve['input_tokens']:
            fatal.append('actual_input_exceeds_reservation')
        if usage['output_tokens'] > reserve['output_tokens']:
            fatal.append('actual_output_exceeds_reservation')
    # A string that looks like a label in a malformed/mismatched response is not scored.
    if fatal:
        label = None
        if status != 'truncated':
            status = 'protocol_error'
    return {'label': label, 'status': status, 'final_text_stripped': text,
            'stop_reason': stop, 'served_model': body.get('model') if isinstance(body, dict) else None,
            'usage': usage, 'fatal_reasons': fatal}


def append_event(path, event):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(event, ensure_ascii=False) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


def read_events(path):
    if not path.exists():
        return []
    raw = path.read_bytes()
    if raw and not raw.endswith(b'\n'):
        raise ValueError('Unterminated journal record; preserve and audit, never auto-resume')
    return [json.loads(line) for line in raw.decode('utf-8').splitlines()]


def replay(events, jobs, estimates, freeze_hash, approval_hash=None):
    state = {'started': [], 'results': {}, 'active': None, 'halted': False,
             'input_reserved': 0, 'cost_reserved_microusd': 0,
             'actual_input': 0, 'actual_output': 0, 'actual_cost_microusd': 0,
             'unknown_usage': 0}
    by_id = {job['job_id']: job for job in jobs}
    observed_approval_hash = None
    for sequence, event in enumerate(events):
        if event.get('seq') != sequence or event.get('freeze_sha256_lf') != freeze_hash:
            raise ValueError('Journal sequence/freeze mismatch')
        job_id = event.get('job_id')
        if job_id not in by_id:
            raise ValueError('Unknown journal job')
        reserve = reservation(estimates[job_id])
        if event.get('event') == 'start':
            event_approval = event.get('approval_sha256_lf')
            if not isinstance(event_approval, str) or not event_approval:
                raise ValueError('Missing journal approval provenance')
            if approval_hash is not None and event_approval != approval_hash:
                raise ValueError('Journal approval differs from the current approval artifact')
            if observed_approval_hash is not None and event_approval != observed_approval_hash:
                raise ValueError('Approval artifact changed between attempts')
            observed_approval_hash = event_approval
            if state['active'] is not None or state['halted']:
                raise ValueError('Start after an unresolved or halted attempt')
            index = len(state['started'])
            if index >= len(jobs) or jobs[index]['job_id'] != job_id:
                raise ValueError('Duplicate/out-of-order start')
            if event.get('reservation') != reserve or event.get('payload_sha256') != prepare.payload_hash(by_id[job_id]['payload']):
                raise ValueError('Journal request/reservation mismatch')
            state['started'].append(job_id)
            state['active'] = job_id
            state['input_reserved'] += reserve['input_tokens']
            state['cost_reserved_microusd'] += reserve['cost_microusd']
        elif event.get('event') == 'result':
            if state['active'] != job_id or job_id in state['results']:
                raise ValueError('Result without its unique active start')
            observed = classify(event['raw'], reserve)
            if observed != event.get('observation'):
                raise ValueError('Saved interpretation differs from raw response')
            state['results'][job_id] = event
            state['active'] = None
            if observed['usage'] is None:
                state['unknown_usage'] += 1
            else:
                state['actual_input'] += observed['usage']['input_tokens']
                state['actual_output'] += observed['usage']['output_tokens']
                state['actual_cost_microusd'] += observed['usage']['cost_microusd']
            if observed['fatal_reasons']:
                state['halted'] = True
        else:
            raise ValueError('Unknown journal event')
        if len(state['started']) > prepare.MAX_ATTEMPTS or state['input_reserved'] > prepare.MAX_INPUT_RESERVE or state['cost_reserved_microusd'] > prepare.MAX_MICROUSD:
            raise ValueError('Journal exceeds frozen limits')
    return state


def check_next(state, reserve):
    if state['active'] is not None:
        raise ValueError('Unresolved start: unknown request outcome; automatic resume prohibited')
    if state['halted'] or state['unknown_usage']:
        raise ValueError('A terminal safety condition prohibits further requests')
    if len(state['started']) + 1 > prepare.MAX_ATTEMPTS:
        raise ValueError('Attempt cap')
    if state['input_reserved'] + reserve['input_tokens'] > prepare.MAX_INPUT_RESERVE:
        raise ValueError('Input reservation cap')
    if state['cost_reserved_microusd'] + reserve['cost_microusd'] > prepare.MAX_MICROUSD:
        raise ValueError('Dollar reservation cap')


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def transport(payload, key):
    """One HTTP attempt, no SDK retry, no redirects, no saved request headers."""
    request = urllib.request.Request(ENDPOINT, data=json.dumps(payload).encode('utf-8'),
        headers={'content-type': 'application/json', 'anthropic-version': '2023-06-01', 'x-api-key': key}, method='POST')
    opener = urllib.request.build_opener(NoRedirect())
    started = time.perf_counter()
    record = {'http_status': None, 'request_id': None, 'full_body': '',
              'transport_error': None, 'latency_seconds': None, 'credential_redacted': False}
    try:
        with opener.open(request, timeout=180) as response:
            record['http_status'] = response.status
            record['request_id'] = response.headers.get('request-id')
            record['full_body'] = response.read().decode('utf-8', errors='replace')
    except urllib.error.HTTPError as exc:
        record['http_status'] = exc.code
        record['request_id'] = exc.headers.get('request-id')
        record['full_body'] = exc.read().decode('utf-8', errors='replace')
    except Exception as exc:
        # Do not serialize exception text, request objects or headers containing secrets.
        record['transport_error'] = type(exc).__name__
    for field in ('full_body', 'request_id'):
        value = record[field]
        if isinstance(value, str) and key and key in value:
            record[field] = value.replace(key, '[REDACTED_SECRET]')
            record['credential_redacted'] = True
    record['latency_seconds'] = time.perf_counter() - started
    return record


def validate_approval(root, freeze_hash, max_usd):
    if max_usd != 20:
        raise ValueError('Execution requires explicit --max-usd 20')
    approval = prepare.load(root / 'approval.json')
    if (approval.get('status') != 'approved' or approval.get('model') != prepare.MODEL
        or approval.get('max_usd') != 20 or isinstance(approval.get('max_usd'), bool)
        or approval.get('freeze_sha256') != freeze_hash
        or not isinstance(approval.get('authorization_note'), str) or not approval['authorization_note'].strip()):
        raise ValueError('Approval must bind explicit provider/budget authorization to this freeze')


def execute_jobs(root, requests, estimates, freeze_hash, approval_hash, key, sender=transport, sleeper=time.sleep):
    """Caller holds exclusive lock and validated freeze/approval; sender injected only in tests."""
    path = root / 'results' / 'journal.jsonl'
    events = read_events(path)
    state = replay(events, requests['jobs'], estimates, freeze_hash, approval_hash)
    if state['active'] is not None or state['halted']:
        raise ValueError('Journal is blocked; preserve results, no automatic retry/resume')
    for job in requests['jobs'][len(state['started']):]:
        reserve = reservation(estimates[job['job_id']])
        check_next(state, reserve)
        if state['started']:
            sleeper(2.0)  # Fixed operational pacing, independent of answer/score.
        start = {'event': 'start', 'seq': len(events), 'time_utc': now(),
                 'freeze_sha256_lf': freeze_hash, 'approval_sha256_lf': approval_hash,
                 'job_id': job['job_id'], 'payload_sha256': prepare.payload_hash(job['payload']),
                 'reservation': reserve}
        append_event(path, start)  # Durable start always precedes the network request.
        events.append(start)
        raw = sender(job['payload'], key)
        observation = classify(raw, reserve)
        result = {'event': 'result', 'seq': len(events), 'time_utc': now(),
                  'freeze_sha256_lf': freeze_hash, 'job_id': job['job_id'],
                  'raw': raw, 'observation': observation}
        append_event(path, result)
        events.append(result)
        state = replay(events, requests['jobs'], estimates, freeze_hash, approval_hash)
        if state['halted']:
            break
    return state


def main():
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--dry-run', action='store_true')
    modes.add_argument('--execute', action='store_true')
    parser.add_argument('--max-usd', type=int)
    args = parser.parse_args()
    root = prepare.HERE
    requests, estimates, budget = prepare.verify()
    frozen_hash = prepare.lfhash(root / 'freeze.json')
    path = root / 'results' / 'journal.jsonl'
    approval_path = root / 'approval.json'
    state = replay(read_events(path), requests['jobs'], estimates, frozen_hash,
                   prepare.lfhash(approval_path) if approval_path.exists() else None)
    if args.dry_run:
        print(json.dumps({'mode': 'offline_dry_run', 'jobs': len(requests['jobs']),
            'budget': budget, 'started': len(state['started']), 'unresolved_start': state['active'],
            'halted': state['halted'], 'network_calls': 0}))
        return
    validate_approval(root, frozen_hash, args.max_usd)
    key = os.environ.get('ANTHROPIC_API_KEY')
    if not key:
        raise ValueError('ANTHROPIC_API_KEY is not available')
    lock = root / 'execution.lock'
    with lock.open('x', encoding='utf-8') as stream:
        stream.write(str(os.getpid()))
        stream.flush()
        os.fsync(stream.fileno())
    try:
        # A second process cannot start between the journal check and its first append.
        state = execute_jobs(root, requests, estimates, frozen_hash,
                             prepare.lfhash(root / 'approval.json'), key)
        prepare.verify()
    finally:
        lock.unlink()
    print(json.dumps({'attempts': len(state['started']), 'results': len(state['results']),
        'halted': state['halted'], 'unknown_usage': state['unknown_usage'],
        'actual_input_tokens': state['actual_input'], 'actual_output_tokens': state['actual_output'],
        'actual_cost_microusd': state['actual_cost_microusd'],
        'reserved_cost_microusd': state['cost_reserved_microusd']}))
    if state['halted'] or state['active'] is not None:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
