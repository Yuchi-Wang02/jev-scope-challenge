"""Preserve strict and repaired views; locally re-decode tokens before publication."""
import argparse
import json
from collections import Counter
from dataclasses import asdict
from pathlib import Path

import screen
from screen import ROOT, HERE, readable, sha, preserve
from jev_audit import audit as audit_jev
from execution_journal import exclusive_lock, read_events
from analyze_comparison import analyze, local_checker, condition_resources
from paired_metrics import score_condition
from action_interface import parse_final

RESULTS = HERE / 'results'


def load(name):
    return json.loads((HERE / name).read_bytes())


def frozen_inputs():
    freeze = load('freeze.json')
    for name, digest in freeze['artifact_sha256_lf'].items():
        if sha((HERE / name).read_bytes().replace(b'\r\n', b'\n')) != digest:
            raise ValueError('Frozen data changed')
    for name, digest in freeze['source_hashes_lf'].items():
        if sha((ROOT / name).read_bytes().replace(b'\r\n', b'\n')) != digest:
            raise ValueError('Frozen analysis dependency changed')
    return freeze, load('plan.json'), load('references.json')


def stored_extraction_check(job, result):
    """CI check of saved extraction ONLY; token-audit hashes are checked separately."""
    detail = result['detail']
    if result['status'] == 'protocol_error':
        if not detail.get('adapter_error'):
            raise ValueError('Missing recorded adapter error')
        return {'action': None, 'strict_json': False, 'completion': 'adapter_error'}
    adapted = detail['adapted']
    completion = 'unknown' if adapted['boundary_error'] else adapted['completion']
    parsed = asdict(parse_final(adapted['final_text'] or '', completion=completion))
    if parsed != adapted['parsed']:
        raise ValueError('Saved parsed action differs from saved final text')
    return {'action': parsed['action'], 'strict_json': parsed['strict_json'],
            'completion': adapted['completion']}


def order_effects(predictions, names):
    a, b = (predictions[name] for name in names)
    if set(a) != set(b):
        return {'available': False, 'reason': 'incomplete_grid'}
    valid = [i for i in a if a[i] is not None and b[i] is not None]
    return {'available': True, 'total_items': len(a), 'valid_in_both': len(valid),
            'invalid_in_either': len(a) - len(valid),
            'changed_valid_action': sum(a[i] != b[i] for i in valid)}


def combine(strict, plan, refs, api):
    conditions = {k: v for k, v in strict['conditions'].items() if k.startswith('qwen_')}
    predictions = {}
    records = {r['job_id']: r for r in api['records']}
    api_jobs = [j for j in plan['jobs'] if j['backend'] == 'jev']
    if set(records) != {j['id'] for j in api_jobs}:
        raise ValueError('Final API cohort is incomplete or foreign')
    for mode in ('native', 'unique_argmax'):
        for order in (0, 1):
            name = f'jev_{mode}_order{order}'
            jobs = [j for j in api_jobs if j['condition'] == f'jev_order{order}']
            rows = [{'item_id': j['item_id'], 'action': records[j['id']]['native_action']
                     if mode == 'native' else records[j['id']]['quality']['unique_argmax_action']} for j in jobs]
            costs = {j['id']: {'state': 'finished', 'result_status': 'ok',
                **{k: records[j['id']][k] for k in ('input_tokens', 'output_tokens', 'latency_seconds')}} for j in jobs}
            predictions[name] = {r['item_id']: r['action'] for r in rows}
            conditions[name] = {'grid_complete': True, 'planned_items': len(jobs),
                'finished': len(jobs), 'not_started': 0, 'started_without_result': 0,
                'metric': score_condition(refs, rows, condition=name),
                'resources': condition_resources(jobs, costs),
                'readout_scope': 'Same API requests and costs; unique-argmax is a secondary view, not extra calls.',
                'metadata_anomalies': sum(not records[j['id']]['quality']['all_original_metadata_checks_pass'] for j in jobs)}
    effects = {k: v for k, v in strict['order_effects'].items() if k.startswith('qwen_')}
    for mode in ('native', 'unique_argmax'):
        effects['jev_' + mode] = order_effects(predictions, [f'jev_{mode}_order{i}' for i in (0, 1)])
    return {'status': 'complete_repaired_decision_grid' if all(c['grid_complete'] for c in conditions.values())
                     else 'incomplete_repaired_decision_grid',
        'study': screen.STUDY, 'reference_basis': plan['reference_basis'],
        'metric_key_interpretation': 'Accuracy/correctness fields mean source-label agreement, not established truth.',
        'tree_units': len(refs), 'independent_human_reviews': 0,
        'original_strict_status': strict['status'],
        'original_strict_jev_conditions': {k: v for k, v in strict['conditions'].items() if k.startswith('jev_')},
        'conditions': conditions, 'order_effects': effects, 'controls': strict['controls'],
        'resources': {'jev_all_phases': {k: v for k, v in api.items() if k != 'records'},
                      'qwen': strict['resources']['qwen']},
        'new_model_calls_during_analysis': 0, 'readout_repairs': 2,
        'scope': 'Selected public development pilot with adaptively repaired API readout; no confirmation or population claim.'}


def ratio(metric):
    return f"{metric['numerator']}/{metric['denominator']}"


def markdown(report):
    lines = ['# Public-source contrast results', '',
        'This is source-label agreement on 12 selected public dev trees /24 inputs.',
        '**Zero project human reviews.** The original strict API experiment stopped;',
        'the final native-choice view follows two disclosed engineering repairs.',
        'Source disagreement is not automatically a proved model error.', '',
        '## Per-condition source agreement', '',
        '|Condition|Finished / planned|Item agreement|Both pair members agree|Invalid output|',
        '|---|---:|---:|---:|---:|']
    names = [f'{m}_order{o}' for m in ('jev_native', 'qwen_direct', 'qwen_thinking', 'jev_unique_argmax') for o in (0, 1)]
    for name in names:
        c = report['conditions'][name]; m = c['metric']
        values = [ratio(m[k]) for k in ('item_accuracy', 'pair_both_correct', 'invalid_output')] if m else ['unavailable'] * 3
        lines.append(f"|{name}|{c['finished']}/{c['planned_items']}|" + '|'.join(values) + '|')
    lines += ['', 'Each order has 24 items /12 parent pairs; do not pool them as independent samples.',
        'The unique-argmax rows re-read the same API responses and incur no new calls.',
        'Invalid/truncated outputs remain in denominators. No score for incomplete conditions.', '',
        '## Non-model controls', '', '|Control|Item agreement|Both pair members agree|', '|---|---:|---:|']
    for name, m in report['controls'].items():
        lines.append(f"|{name}|{ratio(m['item_accuracy'])}|{ratio(m['pair_both_correct'])}|")
    lines += ['', 'These constants/copying controls are shallow checks, not complete natural-language rule interpreters.', '',
        '## Resource and termination accounting', '',
        '|Condition|Input tokens|Output tokens|Callback seconds|Median seconds|p95 seconds|',
        '|---|---:|---:|---:|---:|---:|']
    for name in names[:6]:
        r = report['conditions'][name]['resources']
        med = r['recorded_latency_median_seconds']; p95 = r['recorded_latency_p95_nearest_rank_seconds']
        lines.append(f"|{name}|{r['known_input_tokens']}|{r['known_output_tokens']}|{r['recorded_call_latency_seconds']:.3f}|"
                     f"{med:.3f}|{p95:.3f}|" if med is not None and p95 is not None else
                     f"|{name}|{r['known_input_tokens']}|{r['known_output_tokens']}|{r['recorded_call_latency_seconds']:.3f}|unavailable|unavailable|")
    qwen = report['resources']['qwen']; api = report['resources']['jev_all_phases']
    lines += ['', f"All API phases together: {api['total_http_attempts']} distinct requests, {api['input_tokens']} input /"
        f"{api['output_tokens']} output tokens. Input list-price estimate: ${api['estimated_input_list_price_usd']} "
        f"at ${api['list_price_usd_per_million_input_tokens']}/million, checked {api['price_checked_date']}. "
        '[Official model pricing](https://docs.typesafe.ai/models). This is not an invoice.', '',
        f"Local closed-session time: {qwen['known_closed_session_seconds']:.3f} seconds. "
        f"Usage incomplete: {qwen['usage_incomplete']}; session time incomplete: {qwen['session_time_incomplete']}. "
        f"Overruns: `{json.dumps(qwen['overruns'], sort_keys=True)}`.", '',
        '|Local condition|Termination counts|Strict bare JSON / planned|', '|---|---|---:|']
    for name in names[2:6]:
        c = report['conditions'][name]
        lines.append(f"|{name}|`{json.dumps(c['completion_counts'], sort_keys=True)}`|{c['strict_bare_json_count']}/{c['planned_items']}|")
    lines += ['', 'All generated thinking tokens count. Shared verification/loading and peak memory are in the',
        'raw session metadata; they are not arbitrarily allocated across conditions. Callback latency',
        'is not whole-program elapsed time. Remote API and local GPU serving differ; no architectural',
        'speed claim or assumption of free local computation follows from this table.', '',
        '## Preserved API failures and alternative readouts', '',
        'The original strict run completed 23 requests (22 accepted, one probability-sum failure).',
        'The first repair completed seven new requests (six accepted, one native-choice/argmax mismatch).',
        'The final policy completed the last 18 requests. No request was repeated.',
        'Both stopped ledgers remain incomplete under their original rules.', '',
        f"Final metadata anomaly counts: `{json.dumps(api['metadata_anomaly_counts'], sort_keys=True)}`.", '',
        'See [first repair](READOUT_REPAIR.md), [final policy](FINAL_READOUT.md), and [all-phase audit](results/jev_audit.json).',
        'No probabilities were normalized and no native choice was replaced by the source label.', '',
        '## Reproduction and limits', '',
        '[Structured comparison](results/comparison.json) retains confusion matrices, changed/invariant',
        'strata, order effects and every pair. [Original strict analysis](results/original_strict_analysis.json)',
        'retains its missing grid. [Local raw journal](results/qwen.jsonl) and [token audit](results/token_audit.json)',
        'support inspection. Inputs and [source attribution](ATTRIBUTION.md) are preserved.', '',
        'Local capture re-runs the pinned tokenizer over every returned sequence. Ordinary offline',
        'verification checks journal hashes, saved final-text parsing and score arithmetic; it does',
        'not independently decode token IDs without the local tokenizer. To repeat that additional',
        'check, supply the pinned local model directory (no weights are loaded for analysis).', '',
        '```bash', 'python research/source-label-screen/report.py verify',
        'python research/source-label-screen/report.py verify --model-dir /path/to/pinned/qwen35', '```', '',
        'This single-seed, selected source-labeled development screen has no project human adjudication,',
        'source-Irrelevant stratum, semantic near-duplicate guarantee or pretraining-contamination control.',
        'The 256/2,048 caps are fixed resource constraints, not established reasoning ceilings. The API',
        'readout was adaptively repaired. No significance, population, new-method or dedicated-model',
        'necessity claim is warranted. The separate training review queue remains unscored.', '']
    return '\n'.join(lines).encode()


def calculate(checker):
    freeze, plan, refs = frozen_inputs()
    journals = {'jev': read_events(RESULTS / 'jev_original_stopped.jsonl'),
                'qwen': read_events(RESULTS / 'qwen.jsonl')}
    strict = analyze(plan, refs, journals, freeze['artifact_sha256_lf']['plan.json'], qwen_checker=checker)
    strict.update(study=screen.STUDY, reference_basis=plan['reference_basis'],
        metric_key_interpretation='Accuracy/correctness fields mean source-label agreement only.',
        journal_sha256={backend: sha((RESULTS / name).read_bytes()) for backend, name in
                       (('jev', 'jev_original_stopped.jsonl'), ('qwen', 'qwen.jsonl'))},
        model_forwards_during_analysis=0, http_attempts_during_analysis=0)
    api = audit_jev()
    if api != load('results/jev_audit.json'):
        raise ValueError('API audit changed')
    report = combine(strict, plan, refs, api)
    report['evidence_sha256'] = {name: sha((HERE / name).read_bytes()) for name in (
        'results/jev_audit.json', 'results/qwen.jsonl', 'freeze.json', 'final_readout_freeze.json')}
    return strict, report, journals


def token_receipt(freeze, strict, journal, payload):
    return {'status': 'pinned_tokenizer_redecode_completed',
        'plan_sha256': freeze['artifact_sha256_lf']['plan.json'],
        'qwen_journal_sha256': sha(payload), 'strict_analysis_sha256': sha(readable(strict)),
        'sequences_checked': sum(e['event'] == 'call_finish' and e['result']['status'] != 'execution_error'
                                 for e in journal),
        'tokenizer_config_files': load('plan.json')['tokenizer_config_files'],
        'model_weights_loaded_during_analysis': False, 'new_model_forwards': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('capture', 'verify'))
    parser.add_argument('--model-dir', type=Path)
    args = parser.parse_args()
    if args.command == 'capture':
        if args.model_dir is None:
            raise ValueError('Capture requires the pinned tokenizer directory')
        freeze, _, _ = screen.check_freeze()
        root = screen.directory(freeze)
        with exclusive_lock(root / 'qwen.lock'):
            payload = (root / 'qwen.jsonl').read_bytes()
            read_events(root / 'qwen.jsonl')
        preserve(RESULTS / 'qwen.jsonl', payload)
        strict, report, journals = calculate(local_checker(args.model_dir))
        receipt = token_receipt(freeze, strict, journals['qwen'], payload)
        for path, data in ((RESULTS / 'original_strict_analysis.json', readable(strict)),
                (RESULTS / 'comparison.json', readable(report)),
                (RESULTS / 'token_audit.json', readable(receipt)),
                (HERE / 'RESULTS.md', markdown(report))):
            preserve(path, data)
    else:
        receipt = load('results/token_audit.json')
        freeze, _, _ = frozen_inputs()
        if (receipt['plan_sha256'] != freeze['artifact_sha256_lf']['plan.json'] or
                receipt['qwen_journal_sha256'] != sha((RESULTS / 'qwen.jsonl').read_bytes())):
            raise ValueError('Token-audited snapshot changed')
        checker = local_checker(args.model_dir) if args.model_dir else stored_extraction_check
        strict, report, journals = calculate(checker)
        if (receipt != token_receipt(freeze, strict, journals['qwen'], (RESULTS / 'qwen.jsonl').read_bytes()) or
                load('results/original_strict_analysis.json') != strict or load('results/comparison.json') != report or
                (HERE / 'RESULTS.md').read_bytes().replace(b'\r\n', b'\n') != markdown(report)):
            raise ValueError('Published report does not reproduce')
    print(json.dumps({'status': report['status'], 'tokenizer_checked_this_command': args.model_dir is not None,
                      'new_model_calls': 0}, indent=2))


if __name__ == '__main__':
    main()
