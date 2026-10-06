"""Offline, decimal-exact audit of saved Jev rule-direction confidence.

Original implementation: external retrospective code is inspected, never imported.
No model calls, label updates, epsilon, statistical fitting, or calibration claims.
"""
from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import zipfile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
THRESHOLDS = ('0.9', '0.95', '0.99')
MODES = ('decimal_exact', 'legacy_fraction_of_binary_float')
MISSING = object()
ZIP_MEMBERS = (
    'research/series-retrospective/retrospective.py',
    'research/series-retrospective/loaders/common.py',
    'research/series-retrospective/loaders/rule_direction.py',
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_json(text):
    return json.loads(text, parse_float=Decimal)


def confidence_value(value=MISSING):
    """Only actual JSON numeric values qualify; do not repair strings or floats."""
    if value is MISSING:
        return None, 'missing'
    if type(value) is int:
        value = Decimal(value)
    if not isinstance(value, Decimal) or not value.is_finite() or not 0 <= value <= 1:
        return None, 'invalid'
    return value, 'valid'


def accepted(confidence, threshold, mode='decimal_exact'):
    require(mode in MODES, 'Unknown comparison mode')
    require(isinstance(threshold, Decimal) and threshold.is_finite() and 0 <= threshold <= 1,
            'Threshold must be a finite Decimal in [0, 1]')
    if confidence is None:
        return False
    value, status = confidence_value(confidence)
    require(status == 'valid', 'Confidence must be a validated Decimal or None')
    if mode == 'decimal_exact':
        return value >= threshold
    # This deliberately reproduces the reference's *wrong* binary-float boundary.
    return Fraction(float(value)) >= Fraction(threshold)


def bucket(rows):
    require(all(type(row['correct']) is bool for row in rows), 'Correctness must be boolean')
    return {'total': len(rows), 'correct': sum(row['correct'] for row in rows),
            'wrong': sum(not row['correct'] for row in rows)}


def threshold_counts(rows, threshold, mode):
    kept = [r for r in rows if accepted(r['confidence'], threshold, mode)]
    rejected = [r for r in rows if not accepted(r['confidence'], threshold, mode)]
    equal = [r for r in rows if r['confidence'] is not None and r['confidence'] == threshold]
    result = {'accepted': bucket(kept), 'rejected': bucket(rejected),
              'exact_decimal_boundary': {**bucket(equal),
                  'accepted': sum(accepted(r['confidence'], threshold, mode) for r in equal),
                  'rejected': sum(not accepted(r['confidence'], threshold, mode) for r in equal)},
              'missing_or_invalid_confidence_rejected': sum(r['confidence'] is None for r in rejected)}
    for key, total in bucket(rows).items():
        require(result['accepted'][key] + result['rejected'][key] == total, 'Partition does not reconcile')
    return result


def file_evidence(path, label):
    raw = path.read_bytes()
    return {'path': label, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def reference_evidence(path):
    info = file_evidence(path, path.name)
    with zipfile.ZipFile(path) as archive:
        sources = {name: archive.read(name) for name in ZIP_MEMBERS}
    code = sources[ZIP_MEMBERS[0]].decode('utf-8')
    require('Fraction(r[key]) >= t' in code, 'External reference formula changed')
    require('Fraction(99, 100)' in code, 'Expected exact 99/100 reference threshold missing')
    info['members'] = [
        {'path': name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
        for name, raw in sources.items()]
    info['formula_line'] = next(i for i, line in enumerate(code.splitlines(), 1) if 'Fraction(r[key]) >= t' in line)
    info['treatment'] = 'Read-only reference; no code imported, applied, or copied as the implementation.'
    info['threshold_scope'] = '0.9 and 0.99 were in the zip; 0.95 is an explicitly added audit threshold, not a claimed zip output.'
    return info


def verification_reference(saved_report, reference_zip=None):
    """A missing archive permits analysis verification, not archive re-verification."""
    prior = saved_report['provenance']['external_reference_zip']
    if reference_zip is None:
        return prior, {'external_reference_reopened': False,
                       'external_reference_verification': 'Prior saved provenance retained; ZIP and member bytes were not rechecked.'}
    current = reference_evidence(reference_zip)
    require(current['sha256'] == prior['sha256'] and current['bytes'] == prior['bytes'] and
            current['members'] == prior['members'], 'External ZIP or member hashes differ from saved provenance')
    return prior, {'external_reference_reopened': True,
                   'external_reference_verification': 'ZIP and all recorded member hashes rechecked against saved provenance.'}


def load_rows(repo):
    study = repo/'research/rule-direction'
    plan_bytes = (study/'request_plan.json').read_bytes()
    plan = load_json(plan_bytes)
    case_bytes = (study/'cases.json').read_bytes()
    cases = load_json(case_bytes)
    manifest_bytes = (study/'manifest.json').read_bytes()
    manifest = load_json(manifest_bytes)
    frozen = load_json((study/'freeze.json').read_text(encoding='utf-8'))
    lfhash = lambda raw: hashlib.sha256(raw.replace(b'\r\n', b'\n')).hexdigest()
    require(lfhash(plan_bytes) == manifest['plan_sha256'] == frozen['plan_sha256'], 'Original plan freeze mismatch')
    require(lfhash(case_bytes) == manifest['case_sha256'], 'Original case/reference file changed')
    require(lfhash(manifest_bytes) == frozen['manifest_sha256'], 'Original manifest freeze mismatch')
    case_by_id = {c['id']: c for c in cases}
    require(len(case_by_id) == len(cases), 'Duplicate source case ID')
    jev_jobs = [j for j in plan['jobs'] if j['backend'] == 'jev']
    jobs = {j['id']: j for j in jev_jobs}
    require(len(jobs) == len(jev_jobs), 'Duplicate Jev job ID')
    events = [(line_no, load_json(line)) for line_no, line in enumerate(
        (study/'results/jev.jsonl').read_text(encoding='utf-8').splitlines(), 1) if line.strip()]
    headers = [event for _, event in events if event['event'] == 'header']
    require(len(headers) == 1, 'Expected one raw header')
    require(headers[0]['plan_sha256'] == lfhash(plan_bytes), 'Raw/header plan hash mismatch')
    require(len(headers[0]['job_ids']) == len(jobs) and set(headers[0]['job_ids']) == set(jobs),
            'Header jobs disagree with original plan or contain duplicates')
    finished, rows = {}, []
    for line_no, event in events:
        if event['event'] != 'call_finish':
            continue
        job_id = event['job_id']
        require(job_id in jobs and job_id not in finished, 'Unknown or duplicate finished job: '+job_id)
        finished[job_id] = event
        job = jobs[job_id]
        if job['phase'] != 'main':
            continue
        case = case_by_id[job['item_id']]
        require(job['request']['state'] == case['state'], 'Request/case state mismatch: '+job_id)
        require(job['tree_id'] == case['family_id'], 'Family mismatch: '+job_id)
        options = job['options']
        require(len(options) == 3 and set(options) == {'yes', 'no', 'maybe'}, 'Unexpected options')
        require(case['reference'] in options, 'Unknown stored reference label')
        criteria = job['request']['questions']['decision']['criteria']
        require(all(criteria[k] == f'The truth value is exactly {options[i]}.' for i, k in enumerate('ABC')),
                'Option map and submitted criteria disagree: '+job_id)
        result = event['result']
        answer = result.get('detail', {}).get('raw_response', {}).get('answers', {}).get('decision', {})
        confidence, confidence_status = confidence_value(answer.get('confidence', MISSING))
        choice = answer.get('choice')
        action = options['ABC'.index(choice)] if result['status'] == 'ok' and choice in ('A', 'B', 'C') else None
        require(action == result.get('action'), 'Raw choice/saved action mismatch: '+job_id)
        rows.append({'job_id': job_id, 'item_id': case['id'], 'family_id': case['family_id'],
                     'mapping': job['mapping'], 'reference': case['reference'], 'action': action,
                     'correct': action is not None and action == case['reference'],
                     'confidence': confidence, 'confidence_status': confidence_status,
                     'raw_confidence_value': str(answer['confidence']) if 'confidence' in answer else None,
                     'raw_choice': choice, 'result_status': result['status'], 'raw_line': line_no})
    require(set(finished) == set(jobs), 'Missing finished jobs; no silent completion selection')
    expected = {(c['id'], mapping) for c in cases for mapping in (0, 1)}
    require(len(rows) == len(expected) and {(r['item_id'], r['mapping']) for r in rows} == expected,
            'Main-grid cases/mappings are incomplete or duplicated')
    return rows, {'events': dict(sorted(Counter(e['event'] for _, e in events).items())),
                  'completed_jev_jobs': len(finished), 'excluded_smoke_jobs': len(finished)-len(rows),
                  'main_decisions': len(rows), 'unique_cases': len(cases),
                  'parent_families': len({r['family_id'] for r in rows}),
                  'mappings_are_repeated_measurements': True, 'all_native_actions_match_saved_actions': True,
                  'plan_matches_raw_header': True, 'original_case_and_plan_freezes_verified_with_lf_hashes': True,
                  'confidence_statuses': dict(Counter(r['confidence_status'] for r in rows))}


def build_report(repo, reference_zip=None, *, prior_external_reference=None):
    require((reference_zip is None) != (prior_external_reference is None), 'Supply archive or prior provenance, exactly one')
    rows, integrity = load_rows(repo)
    groups = {'pooled': rows, **{f'mapping_{m}': [r for r in rows if r['mapping'] == m] for m in (0, 1)}}
    aggregates = {}
    for name, selected in groups.items():
        aggregates[name] = {'decisions': bucket(selected), 'thresholds': {
            t: {mode: threshold_counts(selected, Decimal(t), mode) for mode in MODES} for t in THRESHOLDS}}
    records = []
    for row in rows:
        records.append({**row, 'confidence': str(row['confidence']) if row['confidence'] is not None else None,
                        'threshold_decisions': {t: {mode: accepted(row['confidence'], Decimal(t), mode)
                            for mode in MODES} for t in THRESHOLDS}})
    deltas = {}
    for t in THRESHOLDS:
        changed = [r for r in rows if accepted(r['confidence'], Decimal(t), MODES[0]) != accepted(r['confidence'], Decimal(t), MODES[1])]
        deltas[t] = {**bucket(changed), 'job_ids': [r['job_id'] for r in changed]}
    source_names = ['research/rule-direction/results/jev.jsonl', 'research/rule-direction/request_plan.json',
                    'research/rule-direction/cases.json', 'research/rule-direction/freeze.json',
                    'research/rule-direction/manifest.json',
                    'research/rule-direction/specification.py', 'research/rule-direction/analyze.py']
    local_sources = ['confidence_recheck.py', 'test_confidence_recheck.py']
    return {'analysis': 'rule_direction_decimal_confidence_recheck_v1',
            'evidence_status': 'Post-hoc arithmetic reanalysis of existing exploratory results; not calibration or independent confirmation.',
            'model_calls': 0, 'reference_labels_modified': False, 'raw_runs_modified': False,
            'method': {'json_numeric_parser': 'json.loads(parse_float=Decimal)',
                'confidence_path': 'call_finish.result.detail.raw_response.answers.decision.confidence',
                'score': 'native returned confidence, not maximum option probability',
                'correct_comparison': "confidence >= Decimal(threshold_string)",
                'legacy_comparison_for_diagnosis_only': 'Fraction(float(confidence)) >= Fraction(Decimal(threshold_string))',
                'epsilon': None, 'missing_or_invalid_confidence': 'Rejected at every threshold; retained in total counts.',
                'exact_boundary_definition': 'Original decimal confidence equals threshold, regardless of comparison mode.',
                'correctness': 'Raw selected choice decoded using original request options and compared to unchanged cases.json reference.',
                'unit': 'Decision under one option mapping; 108 cases and 12 parent families, not 216 independent cases.',
                'threshold_selection': 'Post-hoc audit thresholds 0.9, 0.95, 0.99; no fitted/calibrated acceptance rule.',
                'source_coverage': 'Main Jev grid only; six smoke calls excluded via original plan phase.'},
            'provenance': {'inputs': [file_evidence(repo/n, n) for n in source_names],
                           'implementation': [file_evidence(HERE/n, 'research/series-closeout/'+n) for n in local_sources],
                           'external_reference_zip': reference_evidence(reference_zip) if reference_zip is not None else prior_external_reference,
                           'verification_policy': 'Without --reference-zip, recompute local science and implementation hashes while retaining external metadata as prior provenance only; with the ZIP, also recheck its bytes and recorded members.'},
            'integrity': integrity, 'aggregates': aggregates, 'comparison_disagreements': deltas,
            'binary_float_boundary_diagnostic': {t: {'exact_threshold_fraction': str(Fraction(Decimal(t))),
                'fraction_after_binary_float': str(Fraction(float(Decimal(t)))),
                'legacy_accepts_exact_boundary': accepted(Decimal(t), Decimal(t), MODES[1])} for t in THRESHOLDS},
            'records': records,
            'limits': ['No new model inference or human label review.', 'Synthetic unit-test fixtures are not research observations.',
                       'Threshold counts do not establish calibrated confidence, deployment safety, or a universal zero-error region.',
                       'Original source labels are preserved, not independently revalidated by this arithmetic check.']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['build', 'verify'])
    parser.add_argument('--reference-zip', type=Path)
    parser.add_argument('--output', type=Path, default=HERE/'confidence_report.json')
    args = parser.parse_args()
    output = args.output.resolve()
    require(output.is_relative_to(HERE), 'Outputs must remain under research/series-closeout')
    if args.command == 'build':
        require(args.reference_zip is not None, 'build requires --reference-zip; no invented external-source provenance')
        report = build_report(REPO, args.reference_zip)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        external_check = {'external_reference_reopened': True,
                          'external_reference_verification': 'Archive inspected and hashes recorded during build.'}
    else:
        saved = json.loads(output.read_text(encoding='utf-8'))
        prior, external_check = verification_reference(saved, args.reference_zip)
        report = build_report(REPO, prior_external_reference=prior)
        require(saved == report, 'Saved report differs from fresh raw-source reconstruction')
    print(json.dumps({'command': args.command, 'status': 'passed', 'main_decisions': report['integrity']['main_decisions'],
                      'decimal_0.99': report['aggregates']['pooled']['thresholds']['0.99']['decimal_exact'],
                      'report_sha256': hashlib.sha256(output.read_bytes()).hexdigest(), **external_check}))


if __name__ == '__main__':
    main()
