"""Build/verify the offline stage replay from complete saved source records only."""
from __future__ import annotations

import argparse
from decimal import Decimal
from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OLD = REPO / 'research/rule-direction'
NEW = OLD / 'capable-reference'
OUTPUT = REPO / 'docs/decision_boundary.html'
TEMPLATE = HERE / 'replay_template.html'
MARKER = '__REPLAY_DATA_JSON__'
QWEN_REVISION = '851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a'
FAMILY_NAMES = ('Parcel dispatch', 'Repair service', 'Booking changes', 'Warehouse equipment',
                'Preferred suppliers', 'Rental fees', 'Cold-storage release', 'Invoice billing',
                'Order packing', 'Device replacement', 'Dock access', 'Purchase rebates')
RELATIONS = ('sufficient', 'necessary', 'equivalent')
FACTS = ('positive', 'negative', 'unknown')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path, lf=False):
    raw = path.read_bytes()
    return hashlib.sha256(raw.replace(b'\r\n', b'\n') if lf else raw).hexdigest()


def verify_hashes(base, entries, lf=True):
    for name, expected in entries.items():
        path = (base / name).resolve()
        require(path.is_relative_to(REPO), 'Source hash path outside repository')
        require(sha(path, lf) == expected, 'Source hash mismatch: ' + name)


def indexed(rows, key, description):
    out = {}
    for row in rows:
        ident = key(row)
        require(ident not in out, 'Duplicate ' + description + ': ' + str(ident))
        out[ident] = row
    return out


def journal(path):
    raw = path.read_bytes()
    require(raw.endswith(b'\n'), 'Incomplete journal line: ' + path.name)
    events = [json.loads(line) for line in raw.decode('utf-8').splitlines()]
    require(all(e['seq'] == i for i, e in enumerate(events)), 'Journal sequence mismatch')
    return events


def worlds(case):
    relation, fact = case['relation'], case['fact_state']
    require(relation in RELATIONS and fact in FACTS, 'Unknown source logic pattern')
    allowed = []
    for p, q in itertools.product((False, True), repeat=2):
        rule = {'sufficient': not p or q, 'necessary': not q or p, 'equivalent': p == q}[relation]
        visible = {'positive': p, 'negative': not p, 'unknown': True}[fact]
        if rule and visible:
            allowed.append({'P': p, 'Q': q})
    values = {w['Q'] for w in allowed}
    reference = 'yes' if values == {True} else 'no' if values == {False} else 'maybe'
    require(allowed == case['possible_worlds'] and reference == case['reference'],
            'Original reference/witness mismatch: ' + case['id'])
    return allowed


def old_results(backend, plan, report, case_by_id):
    jobs = [j for j in plan['jobs'] if j['backend'] == backend]
    by_id = indexed(jobs, lambda j: j['id'], backend + ' job')
    require(len(by_id) == 222, 'Original backend must contain all 222 jobs')
    events = journal(OLD / 'results' / (backend + '.jsonl'))
    headers = [e for e in events if e['event'] == 'header']
    require(len(headers) == 1, 'Original journal header missing/duplicated')
    require(headers[0]['plan_sha256'] == sha(OLD / 'request_plan.json', True), 'Journal/plan mismatch')
    require(len(headers[0]['job_ids']) == len(jobs) and set(headers[0]['job_ids']) == set(by_id),
            'Original header does not cover complete job set')
    starts = [e for e in events if e['event'] == 'call_start']
    finished = indexed([e for e in events if e['event'] == 'call_finish'], lambda e: e['job_id'], 'finished job')
    require(len(starts) == 222 and {e['job_id'] for e in starts} == set(by_id) and set(finished) == set(by_id),
            'Original start/result coverage mismatch')
    if backend == 'qwen':
        metadata = [e['backend_metadata'] for e in events if e['event'] == 'session_start']
        require(metadata and all(m['model'] == 'Qwen/Qwen3.5-4B' and m['revision'] == QWEN_REVISION for m in metadata),
                'Historical Qwen checkpoint mismatch')
    observations = indexed([o for o in report['observations'] if o['backend'] == backend],
                           lambda o: o['job_id'], 'original reported observation')
    require(set(observations) == set(by_id), 'Original report omits/duplicates jobs')
    out = {}
    for job in jobs:
        result = finished[job['id']]['result']
        detail = result['detail']
        require(result['status'] == 'ok', 'Unexpected incomplete original result')
        if backend == 'jev':
            raw = detail['raw_response']
            require(detail['http_status'] == 200 and raw['model'] == 'jev-1.13.0', 'Original Jev identity/HTTP mismatch')
            answer = raw['answers']['decision']
            require(answer['choice'] in ('A', 'B', 'C'), 'Invalid native source choice')
            label = job['options']['ABC'.index(answer['choice'])]
            require(set(answer['probabilities']) == set('ABC'), 'Missing native probabilities')
            data = {'label': label, 'status': 'ok', 'native_choice': answer['choice'],
                    'confidence': str(answer['confidence']),
                    'probabilities': {job['options'][i]: answer['probabilities'][letter] for i, letter in enumerate('ABC')},
                    'saved_response': raw, 'final_text': None}
        else:
            require(detail['ended_eos'] is True and detail['unsupported_special'] is False,
                    'Unexpected historical Qwen completion condition')
            final_text = detail['decoded_body']
            label = final_text.strip() if final_text.strip() in ('yes', 'no', 'maybe') else None
            require(label is not None and detail['generated']['action'] == label, 'Historical Qwen parse mismatch')
            data = {'label': label, 'status': 'ok', 'final_text': final_text}
        reference = case_by_id[job['item_id']]['reference'] if job['phase'] == 'main' else job['expected_smoke_action']
        require(result['action'] == label, 'Raw/original saved label mismatch')
        obs = observations[job['id']]
        require(obs['action'] == label and obs['reference'] == reference and obs['correct'] == (label == reference),
                'Raw/original report differs: ' + job['id'])
        data.update(input_tokens=result['input_tokens'], output_tokens=result['output_tokens'],
                    latency_seconds=result['latency_seconds'], correct=label == reference,
                    source_job_id=job['id'], phase=job['phase'])
        out[job['id']] = data
    return by_id, out


def sonnet_results(requests, old_qwen_jobs, report, case_by_id, freeze):
    jobs = requests['jobs']
    require([j['job_id'] for j in jobs] == list(old_qwen_jobs), 'Supplement order differs from original Qwen')
    events = journal(NEW / 'results/journal.jsonl')
    require(len(events) == 444, 'Supplement must have 222 complete start/result pairs')
    freeze_hash = sha(NEW / 'freeze.json', True)
    approval_hash = sha(NEW / 'approval.json', True)
    require(report['complete'] is True and report['freeze_sha256_lf'] == freeze_hash
            and report['journal_sha256_lf'] == sha(NEW / 'results/journal.jsonl', True), 'Supplement report identity mismatch')
    observations = indexed(report['observations'], lambda o: o['job_id'], 'supplement reported observation')
    require(set(observations) == {j['job_id'] for j in jobs}, 'Supplement report job coverage mismatch')
    out = {}
    for i, job in enumerate(jobs):
        original = old_qwen_jobs[job['job_id']]
        expected = {'model': 'claude-sonnet-5-5', 'max_tokens': 8192,
                    'thinking': {'type': 'adaptive', 'display': 'summarized'},
                    'output_config': {'effort': 'high'},
                    'messages': [{'role': 'user', 'content': original['prompt']}]}
        require(job['payload'] == expected, 'Supplement payload differs from unchanged prompt/config')
        require(all(job[k] == original[k] for k in ('item_id', 'mapping', 'phase', 'tree_id')), 'Supplement metadata differs')
        start, event = events[i * 2:i * 2 + 2]
        require(start['event'] == 'start' and event['event'] == 'result'
                and start['job_id'] == event['job_id'] == job['job_id'], 'Supplement sequence differs')
        require(start['freeze_sha256_lf'] == event['freeze_sha256_lf'] == freeze_hash
                and start['approval_sha256_lf'] == approval_hash, 'Supplement authorization/freeze differs')
        payload_hash = hashlib.sha256((json.dumps(expected, ensure_ascii=False, indent=2) + '\n').encode()).hexdigest()
        require(start['payload_sha256'] == payload_hash, 'Supplement submitted payload hash differs')
        raw = event['raw']
        require(raw['http_status'] == 200 and not raw['transport_error'] and not raw['credential_redacted'], 'Supplement transport failure')
        body = json.loads(raw['full_body'])
        require(body['model'] == 'claude-sonnet-5-5' and body['type'] == 'message' and body['role'] == 'assistant', 'Served model/schema differs')
        require(body['stop_reason'] == 'end_turn', 'Unexpected supplement termination')
        require(all(b['type'] in ('text', 'thinking', 'redacted_thinking') for b in body['content']), 'Unexpected response content')
        final_text = ''.join(b['text'] for b in body['content'] if b['type'] == 'text')
        trimmed = final_text.strip()
        label = trimmed if trimmed in ('yes', 'no', 'maybe') else None
        status = 'ok' if label else 'invalid'
        obs = event['observation']
        require(obs['label'] == label and obs['status'] == status and obs['final_text_stripped'] == trimmed
                and not obs['fatal_reasons'], 'Supplement strict parsing differs')
        usage = body['usage']
        require(usage['input_tokens'] == obs['usage']['input_tokens'] and usage['output_tokens'] == obs['usage']['output_tokens'],
                'Supplement usage differs')
        require(usage.get('cache_read_input_tokens', 0) == usage.get('cache_creation_input_tokens', 0) == 0,
                'Unaccounted cache usage')
        require(2 * usage['input_tokens'] + 10 * usage['output_tokens'] == obs['usage']['cost_microusd'], 'Cost arithmetic mismatch')
        reference = case_by_id[job['item_id']]['reference'] if job['phase'] == 'main' else original['expected_smoke_action']
        scored = observations[job['job_id']]
        require(scored['label'] == label and scored['status'] == status and scored['reference'] == reference
                and scored['correct'] == (label == reference), 'Supplement report observation mismatch')
        out[job['job_id']] = {'label': label, 'status': status, 'final_text': final_text,
            'correct': label == reference, 'input_tokens': usage['input_tokens'], 'output_tokens': usage['output_tokens'],
            'latency_seconds': raw['latency_seconds'], 'source_job_id': job['job_id'], 'phase': job['phase']}
    return out


def confidence_audit(audit, jev_results, jev_jobs, case_by_id):
    for item in audit['provenance']['inputs'] + audit['provenance']['implementation']:
        require(sha(REPO / item['path']) == item['sha256'], 'Confidence report source changed: ' + item['path'])
    records = indexed(audit['records'], lambda r: r['job_id'], 'confidence record')
    main = {ident for ident, job in jev_jobs.items() if job['phase'] == 'main'}
    require(set(records) == main and len(main) == 216, 'Confidence report must cover complete main grid')
    # Read the original numeric lexemes with Decimal, rather than going through binary floats.
    exact = {}
    for line in (OLD / 'results/jev.jsonl').read_text(encoding='utf-8').splitlines():
        event = json.loads(line, parse_float=Decimal)
        if event['event'] == 'call_finish' and event['job_id'] in main:
            exact[event['job_id']] = event['result']['detail']['raw_response']['answers']['decision']['confidence']
    for ident in sorted(main):
        row, saved, job = records[ident], jev_results[ident], jev_jobs[ident]
        value = exact[ident]
        require(isinstance(value, (int, Decimal)) and not isinstance(value, bool), 'Non-numeric saved confidence')
        value = Decimal(value)
        require(value.is_finite() and 0 <= value <= 1 and row['confidence_status'] == 'valid', 'Invalid confidence')
        require(Decimal(row['confidence']) == value and row['correct'] == saved['correct']
                and row['action'] == saved['label'] and row['reference'] == case_by_id[job['item_id']]['reference']
                and row['mapping'] == job['mapping'], 'Confidence row differs from source decision')
        for threshold in ('0.9', '0.95', '0.99'):
            expected = {'decimal_exact': value >= Decimal(threshold),
                        'legacy_fraction_of_binary_float': Fraction(float(value)) >= Fraction(Decimal(threshold))}
            require(row['threshold_decisions'][threshold] == expected, 'Threshold decision differs')
        saved['confidence'] = str(value)
        saved['accepted_at_099'] = value >= Decimal('0.99')
        saved['at_exact_099'] = value == Decimal('0.99')
    groups = {'pooled': list(main), **{f'mapping_{m}': [i for i in main if jev_jobs[i]['mapping'] == m] for m in (0, 1)}}
    for group, ids in groups.items():
        for threshold in ('0.9', '0.95', '0.99'):
            for mode in ('decimal_exact', 'legacy_fraction_of_binary_float'):
                counts = audit['aggregates'][group]['thresholds'][threshold][mode]
                for bucket, accepted in (('accepted', True), ('rejected', False)):
                    selected = [i for i in ids if records[i]['threshold_decisions'][threshold][mode] is accepted]
                    actual = {'total': len(selected), 'correct': sum(jev_results[i]['correct'] for i in selected),
                              'wrong': sum(not jev_results[i]['correct'] for i in selected)}
                    require(counts[bucket] == actual, 'Threshold aggregate differs from all source rows')
    point = audit['aggregates']['pooled']['thresholds']['0.99']
    require(point['decimal_exact']['accepted'] == {'total': 173, 'correct': 164, 'wrong': 9}, 'Corrected threshold changed')
    require(point['legacy_fraction_of_binary_float']['accepted'] == {'total': 128, 'correct': 128, 'wrong': 0}, 'Legacy reproduction changed')
    return point


def summary(rows, backend):
    return {str(m): {'correct': sum(r[backend]['correct'] for r in rows if r['mapping'] == m),
                    'invalid': sum(r[backend]['label'] is None for r in rows if r['mapping'] == m),
                    'total': sum(r['mapping'] == m for r in rows)} for m in (0, 1)}


def build_data():
    manifest = load(OLD / 'manifest.json')
    require(sha(OLD / 'request_plan.json', True) == manifest['plan_sha256']
            and sha(OLD / 'cases.json', True) == manifest['case_sha256'], 'Historical manifest mismatch')
    freeze = load(NEW / 'freeze.json')
    verify_hashes(OLD, freeze['old_sources_sha256_lf'])
    verify_hashes(OLD, freeze['old_contracts_sha256_lf'])
    verify_hashes(NEW, freeze['files_sha256_lf'])
    cases, plan, old_report = load(OLD / 'cases.json'), load(OLD / 'request_plan.json'), load(OLD / 'report.json')
    by_case = indexed(cases, lambda c: c['id'], 'source case')
    require(len(cases) == 108 and {c['id'] for c in cases} ==
            {f'r{n:02d}_{relation}_{fact}' for n in range(1, 13) for relation in RELATIONS for fact in FACTS},
            'Case grid is incomplete')
    for case in cases:
        worlds(case)
    jev_jobs, jev = old_results('jev', plan, old_report, by_case)
    qwen_jobs, qwen = old_results('qwen', plan, old_report, by_case)
    new_report = load(NEW / 'results/report.json')
    sonnet = sonnet_results(load(NEW / 'requests.json'), qwen_jobs, new_report, by_case, freeze)
    confidence = confidence_audit(load(HERE / 'confidence_report.json'), jev, jev_jobs, by_case)
    rows = []
    for case in cases:
        for mapping in (0, 1):
            stem = f"{case['id']}_m{mapping}"
            jj, qj = jev_jobs[stem + '_jev'], qwen_jobs[stem + '_qwen']
            require(jj['request']['state'] == case['state'] and jj['options'] == qj['options'], 'Source input mismatch')
            require(jj['options'] == (['yes', 'no', 'maybe'] if mapping == 0 else ['maybe', 'no', 'yes']),
                    'Displayed option-order description differs from source')
            criteria = jj['request']['questions']['decision']['criteria']
            require(all(criteria[letter] == f'The truth value is exactly {jj["options"][i]}.' for i, letter in enumerate('ABC')),
                    'Native option mapping differs')
            prompt = (jj['request']['questions']['decision']['instructions'] + '\nINPUT JSON:\n'
                      + json.dumps(case['state'], ensure_ascii=False, sort_keys=True)
                      + '\nAnswer with exactly one semantic label and no explanation.\nAllowed labels in display order:\n'
                      + '\n'.join(qj['options']))
            require(qj['prompt'] == prompt, 'Prompt semantic contract differs from source native request')
            rows.append({'item_id': case['id'], 'mapping': mapping, 'options': qj['options'],
                'prompt': qj['prompt'], 'jev_request': jj['request'],
                'jev': jev[stem + '_jev'], 'qwen': qwen[stem + '_qwen'], 'sonnet': sonnet[stem + '_qwen']})
    summaries = {name: summary(rows, name) for name in ('jev', 'qwen', 'sonnet')}
    require(all(row['jev']['label'] == row['qwen']['label'] for row in rows),
            'Historical same-answer claim differs from source')
    for mapping in ('0', '1'):
        require(summaries['jev'][mapping]['correct'] == summaries['qwen'][mapping]['correct'] == 84, 'Historical score differs')
        require(summaries['sonnet'][mapping]['correct'] == new_report['mappings'][mapping]['correct'], 'Supplement summary differs')
    invalid = [r for r in rows if r['sonnet']['label'] is None]
    require(len(invalid) == 1 and invalid[0]['item_id'] == 'r08_sufficient_negative' and invalid[0]['mapping'] == 0,
            'Unexpected format-failure identity')
    require(summaries['sonnet']['0']['correct'] == 107 and summaries['sonnet']['1']['correct'] == 108, 'Strict supplementary score changed')
    usage = {}
    for name, records in (('jev', jev), ('qwen', qwen), ('sonnet', sonnet)):
        usage[name] = {'decisions': len(records), 'input_tokens': sum(r['input_tokens'] for r in records.values()),
            'output_tokens': sum(r['output_tokens'] for r in records.values()),
            'summed_latency_seconds': round(sum(r['latency_seconds'] for r in records.values()), 6),
            'smoke_correct': sum(r['correct'] for r in records.values() if r['phase'] == 'smoke')}
    require(usage['sonnet']['input_tokens'] == 58288 and usage['sonnet']['output_tokens'] == 1277, 'Supplement usage totals changed')
    usage['sonnet']['standard_price_usd'] = (2 * usage['sonnet']['input_tokens'] + 10 * usage['sonnet']['output_tokens']) / 1_000_000
    sources = [OLD/'cases.json', OLD/'request_plan.json', OLD/'manifest.json', OLD/'report.json',
               OLD/'results/jev.jsonl', OLD/'results/qwen.jsonl', NEW/'requests.json', NEW/'freeze.json',
               NEW/'approval.json', NEW/'results/journal.jsonl', NEW/'results/report.json',
               HERE/'confidence_report.json', HERE/'build_replay.py', TEMPLATE]
    return {'version': 1, 'publication_status': 'Stage research replay; saved outputs only.',
        'families': [{'id': f'r{n:02d}', 'name': name} for n, name in enumerate(FAMILY_NAMES, 1)],
        'cases': cases, 'decisions': rows, 'summary': summaries, 'usage': usage,
        'confidence': confidence, 'default': {'family': 'r01', 'relation': 'necessary', 'fact': 'positive', 'mapping': 0},
        'format_failure': {'family': 'r08', 'relation': 'sufficient', 'fact': 'negative', 'mapping': 0},
        'integrity': {'cases': len(cases), 'mappings': 2, 'main_records_compared': len(rows) * 3,
            'all_backend_results_checked': len(jev) + len(qwen) + len(sonnet),
            'reference_updates': 0, 'thinking_text_included': False,
            'sources': [{'path': p.relative_to(REPO).as_posix(), 'sha256_lf': sha(p, True)} for p in sources]}}


def render():
    data = build_data()
    template = TEMPLATE.read_text(encoding='utf-8')
    require(template.count(MARKER) == 1, 'Expected one data marker')
    safe = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
    html = template.replace(MARKER, safe)
    require('fetch(' not in template and '.innerHTML' not in template, 'Use local data and textContent only')
    return html.encode('utf-8'), data


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=('build', 'verify'))
    args = parser.parse_args()
    raw, data = render()
    if args.command == 'build':
        OUTPUT.write_bytes(raw)
    else:
        require(OUTPUT.read_bytes().replace(b'\r\n', b'\n') == raw, 'Replay differs from current source reconstruction')
    print(json.dumps({'command': args.command, 'status': 'passed', 'output': OUTPUT.relative_to(REPO).as_posix(),
        'cases': len(data['cases']), 'main_records_compared': data['integrity']['main_records_compared'],
        'all_backend_results_checked': data['integrity']['all_backend_results_checked'],
        'strict_sonnet_correct': sum(m['correct'] for m in data['summary']['sonnet'].values()),
        'corrected_099_kept': data['confidence']['decimal_exact']['accepted']['total'],
        'corrected_099_errors': data['confidence']['decimal_exact']['accepted']['wrong'],
        'sha256': hashlib.sha256(raw).hexdigest()}))
