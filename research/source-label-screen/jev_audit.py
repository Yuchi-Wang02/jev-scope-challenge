"""Offline reproduction of all 48 API attempts and their three preserved readouts."""
import argparse
import json
from collections import Counter
from decimal import Decimal

from screen import HERE, readable, sha, preserve
from execution_journal import read_events, replay
from comparison_backends import adapt_jev
from decision_readout import adapt as first_repair
from native_choice import adapt as final_readout


def load(name):
    return json.loads((HERE / name).read_bytes())


def audit():
    original, repaired, final = (load(n) for n in ('freeze.json', 'repair_freeze.json', 'final_readout_freeze.json'))
    full_jobs = [j for j in load('plan.json')['jobs'] if j['backend'] == 'jev']
    phases = (
        ('original_strict', 'plan.json', original['artifact_sha256_lf']['plan.json'],
         'jev_original_stopped.jsonl', final['first_journal_sha256'], adapt_jev),
        ('first_repair', 'repair_plan.json', repaired['repair_plan_sha256'],
         'jev_first_repair_stopped.jsonl', final['second_journal_sha256'], first_repair),
        ('final_native', 'final_readout_plan.json', final['plan_sha256'],
         'jev_final_suffix.jsonl', None, final_readout),
    )
    records, phase_reports, all_starts = [], {}, []
    for name, plan_file, plan_hash, filename, expected, adapter in phases:
        plan_bytes = (HERE / plan_file).read_bytes().replace(b'\r\n', b'\n')
        if sha(plan_bytes) != plan_hash:
            raise ValueError('Phase plan hash mismatch')
        plan = json.loads(plan_bytes)
        jobs = [j for j in plan['jobs'] if j['backend'] == 'jev']
        path = HERE / 'results' / filename
        digest = sha(path.read_bytes())
        if expected is not None and digest != expected:
            raise ValueError('Preserved failed journal changed')
        events = read_events(path)
        state = replay(events, plan_hash=plan_hash, backend='jev', jobs=jobs)
        if state['active_job'] is not None or state['active_session'] is not None or state['unknown_usage']:
            raise ValueError('Incomplete phase accounting')
        all_starts.extend(state['started'])
        phase_reports[name] = {'planned': len(jobs), 'attempts': len(state['started']),
            'finished': len(state['results']), 'original_status_counts': dict(Counter(r['status'] for r in state['results'].values())),
            'input_tokens': state['input_tokens'], 'output_tokens': state['output_tokens'],
            'session_seconds': state['session_seconds'], 'journal_sha256': digest,
            'execution_commit': next(e['backend_metadata']['execution_commit'] for e in events if e['event'] == 'session_start')}
        for job in jobs:
            if job['id'] not in state['results']:
                continue
            saved = state['results'][job['id']]
            raw, http = saved['detail']['raw_response'], saved['detail']['http_status']
            if adapter(raw, http, job['options'], saved['latency_seconds']) != saved:
                raise ValueError('Stored phase output differs from its original adapter')
            native = final_readout(raw, http, job['options'], saved['latency_seconds'])
            if native['status'] != 'ok':
                raise ValueError('Final native-choice grid remains incomplete')
            if saved['status'] == 'ok' and native['action'] != saved['action']:
                raise ValueError('Previously accepted native choice changed')
            records.append({'job_id': job['id'], 'item_id': job['item_id'], 'condition': job['condition'],
                'phase': name, 'original_status': saved['status'], 'native_action': native['action'],
                'quality': native['detail']['metadata_quality'], 'input_tokens': saved['input_tokens'],
                'output_tokens': saved['output_tokens'], 'latency_seconds': saved['latency_seconds']})
    if all_starts != [j['id'] for j in full_jobs] or len(records) != 48:
        raise ValueError('Attempts do not form the unique original fixed 48-job grid')
    count = lambda predicate: sum(predicate(r['quality']) for r in records)
    total_input = sum(r['input_tokens'] for r in records)
    return {'status': 'all_48_native_choices_audited', 'new_model_calls_during_audit': 0,
        'source_agreement_scored_here': False, 'independent_human_reviews': 0,
        'original_strict_run_complete': False, 'readout_repairs': 2,
        'total_http_attempts': 48, 'repeated_job_ids': 0,
        'input_tokens': total_input, 'output_tokens': sum(r['output_tokens'] for r in records),
        'list_price_usd_per_million_input_tokens': '0.042', 'price_checked_date': '2026-09-30',
        'estimated_input_list_price_usd': str(Decimal(total_input) * Decimal('0.042') / Decimal(1000000)),
        'latency_seconds_sum': sum(r['latency_seconds'] for r in records),
        'metadata_anomaly_counts': {
            'any_original_metadata_check_failed': count(lambda q: not q['all_original_metadata_checks_pass']),
            'nonunit_probability_sum': count(lambda q: not q['within_original_sum_tolerance']),
            'native_choice_not_displayed_maximum': count(lambda q: q['choice_is_displayed_argmax'] is False),
            'no_unique_displayed_argmax': count(lambda q: q['unique_argmax_action'] is None),
            'invalid_confidence': count(lambda q: not q['confidence_valid'])},
        'phases': phase_reports, 'records': records}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    report = audit()
    path = HERE / 'results/jev_audit.json'
    if args.verify:
        if path.read_bytes().replace(b'\r\n', b'\n') != readable(report):
            raise ValueError('Published audit differs from raw journals')
    else:
        preserve(path, readable(report))
    print(json.dumps({k: v for k, v in report.items() if k not in ('records', 'phases')}, indent=2))
