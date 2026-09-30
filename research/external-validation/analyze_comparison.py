"""Offline, freeze-bound comparison analysis; never run models or repair records."""
import argparse
import json
import sys
from collections import Counter, defaultdict
from contextlib import ExitStack
from pathlib import Path

from comparison_plan import (ROOT, PLAN_ID, ORDERS, checked_tokenizer, jev_request,
    task_instruction, qwen_prompt, private_directory, readable, sha)
from comparison_backends import adapt_jev
from adapters import qwen_final
from execution_journal import exclusive_lock, read_events, replay, stop_reason, outcome
from paired_metrics import score_condition, validate_pairs
from shortcut_controls import predict_controls
from run_comparison import check_freeze

CONDITIONS = tuple(f'{model}_order{order}' for model in ('jev', 'qwen_direct', 'qwen_thinking')
                   for order in (0, 1))


def cohort(plan, references):
    _, trees, ids = validate_pairs(references)
    jobs = plan['jobs']
    if len({j['id'] for j in jobs}) != len(jobs):
        raise ValueError('Repeated job ID')
    groups = defaultdict(list)
    states = {}
    for job in jobs:
        name = job['condition']
        groups[name].append(job)
        if name not in CONDITIONS:
            raise ValueError('Unknown condition')
        expected_backend = 'jev' if name.startswith('jev_') else 'qwen'
        if job['backend'] != expected_backend or job['options'] != list(ORDERS[int(name[-1])]):
            raise ValueError('Backend/order differs from named condition')
        if job['backend'] == 'jev':
            state = job['request']['state']
            if job['request'] != jev_request(state, task_instruction(job['options']), job['options']):
                raise ValueError('Jev request does not match the common task contract')
            if job['item_id'] in states and states[job['item_id']] != state:
                raise ValueError('Visible state changed across option orders')
            states[job['item_id']] = state
    if set(groups) != set(CONDITIONS) or set(states) != ids:
        raise ValueError('Missing model conditions or visible states')
    for name, rows in groups.items():
        if len(rows) != len(ids) or {r['item_id'] for r in rows} != ids:
            raise ValueError('Conditions do not use exactly the same reference cohort')
        for job in rows:
            if job['backend'] == 'qwen':
                if (job['prompt'] != qwen_prompt(states[job['item_id']], job['options']) or
                        job['thinking'] is not ('_thinking_' in name)):
                    raise ValueError('Qwen input/mode differs from the common task contract')
    return groups, states, len(trees)


def local_checker(model_dir):
    """Verify token/configuration evidence with the pinned tokenizer, no weights."""
    tokenizer, _ = checked_tokenizer(model_dir)
    sys.path.insert(0, str(ROOT / 'research/generation-calibration'))
    from qwen_configuration import loaded_configurations
    configs = {row['thinking']: row for row in loaded_configurations(model_dir)}
    def check(job, result):
        rendered = tokenizer.apply_chat_template([{'role': 'user', 'content': job['prompt']}],
                tokenize=False, add_generation_prompt=True, enable_thinking=job['thinking'])
        if (rendered != job['rendered_input'] or
                tokenizer(rendered, add_special_tokens=False)['input_ids'] != job['input_ids']):
            raise ValueError('Local prompt or input token drift')
        detail = result['detail']
        config = dict(configs[job['thinking']]['effective_generation_config'])
        config['max_new_tokens'] = job['max_new_tokens']
        if (detail['effective_generation_config'] != config or detail['presence_penalty'] != 1.5 or
                detail['processor_order'] != configs[job['thinking']]['processor_order']):
            raise ValueError('Local generation settings differ from the declared configuration')
        try:
            adapted = qwen_final(tokenizer, detail['output_ids'], thinking=job['thinking'],
                                 rendered_prompt=rendered, max_new_tokens=job['max_new_tokens'])
        except (ValueError, TypeError, KeyError) as error:
            if result['status'] != 'protocol_error' or detail.get('adapter_error') != type(error).__name__:
                raise ValueError('Unrecorded local adapter failure')
            return {'action': None, 'strict_json': False, 'completion': 'adapter_error'}
        if result['status'] != 'ok' or detail.get('adapted') != adapted:
            raise ValueError('Saved final-channel extraction differs from generated tokens')
        return {'action': adapted['parsed']['action'], 'strict_json': adapted['parsed']['strict_json'],
                'completion': adapted['completion']}
    return check


def audit_result(job, result, qwen_checker):
    if result['status'] == 'execution_error':
        if (result['action'] is not None or result['input_tokens'] is not None or
                result['output_tokens'] is not None or
                set(result['detail']) != {'exception_type'}):
            raise ValueError('Execution-error record differs from the runner contract')
        return {'action': None, 'strict_json': False, 'completion': 'execution_error'}
    if job['backend'] == 'jev':
        detail = result['detail']
        expected = adapt_jev(detail['raw_response'], detail['http_status'], job['options'], result['latency_seconds'])
        if result != expected:
            raise ValueError('Saved Jev action/usage differs from raw response')
        return {'action': expected['action'], 'strict_json': None,
                'completion': expected['status']}
    if qwen_checker is None:
        raise ValueError('Returned local tokens require an independent tokenizer audit')
    detail = result['detail']
    if (result['input_tokens'] != len(job['input_ids']) or
            result['output_tokens'] != len(detail['output_ids'])):
        raise ValueError('Local usage differs from saved token counts')
    audited = qwen_checker(job, result)
    if result['action'] != audited['action']:
        raise ValueError('Saved local action differs from audited token output')
    return audited


def analyze(plan, references, journals, plan_hash, *, qwen_checker=None):
    groups, states, tree_count = cohort(plan, references)
    records, resources = {}, {}
    for backend in ('jev', 'qwen'):
        jobs = [j for j in plan['jobs'] if j['backend'] == backend]
        state = replay(journals.get(backend, []), plan_hash=plan_hash, backend=backend, jobs=jobs)
        reason = stop_reason(state, backend, jobs, plan['limits'], state['session_seconds'])
        report = outcome(reason or 'closed_partial_session', state, backend, plan['limits'])
        if not state['started'] and state['active_session'] is None:
            report['status'] = 'not_started'
        resources[backend] = {
            'status': report['status'], 'planned_calls': len(jobs),
            'attempts_started': len(state['started']), 'results_recorded': len(state['results']),
            'unresolved_attempts': len(state['started']) - len(state['results']),
            'result_status_counts': dict(Counter(r['status'] for r in state['results'].values())),
            'known_input_tokens': state['input_tokens'], 'known_output_tokens': state['output_tokens'],
            'usage_incomplete': state['unknown_usage'] or state['active_job'] is not None,
            'known_closed_session_seconds': state['session_seconds'],
            'session_time_incomplete': state['active_session'] is not None,
            'recorded_call_latency_seconds': sum(r['latency_seconds'] for r in state['results'].values()),
            'overruns': report['overruns'],
            'session_setup_metadata': [e['backend_metadata'] for e in journals.get(backend, [])
                                       if e['event'] == 'session_start'],
        }
        for job in jobs:
            ident = job['id']
            if ident in state['results']:
                result = state['results'][ident]
                records[ident] = {'state': 'finished', **audit_result(job, result, qwen_checker)}
            else:
                records[ident] = {'state': 'started_without_result' if ident in state['started'] else 'not_started'}
    scores, predictions = {}, {}
    for name in CONDITIONS:
        rows = groups[name]
        statuses = Counter(records[j['id']]['state'] for j in rows)
        complete = statuses['finished'] == len(rows)
        pred = [{'item_id': j['item_id'], 'action': records[j['id']]['action']}
                for j in rows if records[j['id']]['state'] == 'finished']
        predictions[name] = {r['item_id']: r['action'] for r in pred}
        scores[name] = {'grid_complete': complete, 'planned_items': len(rows),
                       'finished': statuses['finished'], 'not_started': statuses['not_started'],
                       'started_without_result': statuses['started_without_result'],
                       'metric': score_condition(references, pred, condition=name) if complete else None,
                       'completion_counts': dict(Counter(records[j['id']]['completion'] for j in rows
                                                        if records[j['id']]['state'] == 'finished')),
                       'strict_bare_json_count': sum(records[j['id']].get('strict_json') is True for j in rows)
                                                if name.startswith('qwen_') else None}
    order_effects = {}
    for model in ('jev', 'qwen_direct', 'qwen_thinking'):
        a, b = (model + '_order' + str(i) for i in (0, 1))
        if not scores[a]['grid_complete'] or not scores[b]['grid_complete']:
            order_effects[model] = {'available': False, 'reason': 'incomplete_grid'}
            continue
        comparable = [i for i in states if predictions[a][i] is not None and predictions[b][i] is not None]
        order_effects[model] = {'available': True, 'total_items': len(states),
            'valid_in_both': len(comparable), 'invalid_in_either': len(states) - len(comparable),
            'changed_valid_action': sum(predictions[a][i] != predictions[b][i] for i in comparable)}
    controls = predict_controls([{'item_id': i, 'state': s} for i, s in sorted(states.items())])
    complete_grid = all(s['grid_complete'] for s in scores.values())
    accounted = all(not r['usage_incomplete'] and not r['session_time_incomplete'] and
                    not any(r['overruns'].values()) for r in resources.values())
    return {'status': 'complete_grid' if complete_grid else 'incomplete_grid',
            'plan_sha256': plan_hash, 'tree_units': tree_count,
            'complete_grid_within_recorded_budgets': complete_grid and accounted,
            'complete_grid_without_execution_or_protocol_errors': complete_grid and all(
                all(status == 'ok' for status in r['result_status_counts']) for r in resources.values()),
            'independent_human_truth_automatically_verified': False,
            'conditions': scores, 'order_effects': order_effects, 'resources': resources,
            'controls': {name: score_condition(references, rows, condition=name) for name, rows in controls.items()}}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plan-dir', type=Path, default=ROOT / '.local' / PLAN_ID)
    p.add_argument('--model-dir', type=Path)
    args = p.parse_args()
    freeze = check_freeze()
    directory = private_directory(args.plan_dir)
    plan_bytes = (directory / 'comparison_plan.json').read_bytes()
    refs_bytes = (directory / 'scoring_references.json').read_bytes()
    if sha(plan_bytes) != freeze['plan_sha256'] or sha(refs_bytes) != freeze['references_sha256']:
        raise ValueError('Analysis inputs differ from the committed freeze')
    root = private_directory(ROOT / '.local' / ('execution-' + freeze['plan_sha256']))
    journals, hashes = {}, {}
    with ExitStack() as stack:
        for backend in ('jev', 'qwen'):
            stack.enter_context(exclusive_lock(root / (backend + '.lock')))
            path = root / (backend + '.jsonl')
            journals[backend] = read_events(path)
            hashes[backend] = sha(path.read_bytes()) if path.exists() else None
    qwen_returned = any(e['event'] == 'call_finish' and e['result']['status'] != 'execution_error'
                        for e in journals['qwen'])
    if qwen_returned and args.model_dir is None:
        raise ValueError('Local returned outputs require --model-dir for tokenizer auditing')
    checker = local_checker(args.model_dir) if qwen_returned else None
    report = analyze(json.loads(plan_bytes), json.loads(refs_bytes), journals,
                     freeze['plan_sha256'], qwen_checker=checker)
    report['journal_sha256'] = hashes
    report['model_forwards_during_analysis'] = 0
    report['http_attempts_during_analysis'] = 0
    target = root / ('analysis-' + sha(readable(hashes))[:16] + '.json')
    payload = readable(report)
    if target.exists():
        if target.read_bytes() != payload:
            raise ValueError('Existing analysis for this snapshot differs; preserve it')
    else:
        with target.open('xb') as output:
            output.write(payload)
    print(json.dumps({'status': report['status'], 'tree_units': report['tree_units'],
                      'complete_grid_within_recorded_budgets': report['complete_grid_within_recorded_budgets'],
                      'output': str(target)}, indent=2))


if __name__ == '__main__':
    main()
