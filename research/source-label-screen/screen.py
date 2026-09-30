"""Separate, frozen source-label screen; never open the reviewed training queue."""
import argparse
import json
import subprocess
import sys
from collections import Counter, defaultdict
from contextlib import ExitStack, contextmanager
from pathlib import Path

from source_inventory import ROOT, ARCHIVE_SHA256, load_source, eligible_rows, normalized
from inspect_sharc_pairs import action, dedupe_visible, iter_one_answer_pairs
from comparison_plan import (ORDERS, QWEN_REVISION, visible_state, task_instruction,
    qwen_prompt, jev_request, tokenizer_renderer, canonical, readable, sha)
from shortcut_controls import CONTROL_NAMES
from paired_metrics import validate_pairs
from execution_journal import execute, exclusive_lock, read_events
from analyze_comparison import analyze, local_checker
from run_comparison import SOURCE_FILES as SHARED_SOURCES

HERE = Path(__file__).resolve().parent
STUDY = 'sharc-dev-source-label-screen-v1'
GROUPS = ('invariant', 'clarification_change', 'decisive_change')
LIMITS = {'http_attempts': 48, 'http_retries': 0, 'local_generations': 96,
    'jev_planning_bytes_plus_allowance': 250000, 'jev_actual_input_tokens': 100000,
    'local_input_tokens': 500000, 'local_generated_tokens': 110592,
    'local_generation_wall_seconds': 3600, 'local_context_tokens': 32768}
SOURCES = (*SHARED_SOURCES, 'research/source-label-screen/screen.py',
    'research/source-label-screen/source_inventory.py',
    'research/source-label-screen/PROTOCOL.md',
    'research/source-label-screen/EXPLORATION_AMENDMENT.md',
    'research/source-label-screen/ATTRIBUTION.md')


def rank(*parts):
    return sha(canonical([STUDY, *parts]).encode())


def choose(train, dev, per_group=4):
    eligible = eligible_rows(train, dev)
    _, _, kept = dedupe_visible(eligible)
    grouped = {g: defaultdict(list) for g in GROUPS}
    for left, right in iter_one_answer_pairs(kept):
        a, b = action(left), action(right)
        group = ('invariant' if a == b else
                 'clarification_change' if 'ASK' in (a, b) else 'decisive_change')
        if a != b and 'ASK' not in (a, b) and {a, b} != {'Yes', 'No'}:
            raise ValueError('Unexpected source-action contrast')
        rows = sorted((left, right), key=lambda r: str(r['utterance_id']))
        tree = str(left['tree_id'])
        ids = [str(r['utterance_id']) for r in rows]
        grouped[group][tree].append({'tree_id': tree, 'source_ids': ids,
            'group': group, 'source_actions': [action(r) for r in rows],
            'pair_id': rank('pair', tree, ids)[:24], 'rows': rows})
    selected, used_trees, used_snippets = [], set(), set()
    for group in GROUPS:
        taken = 0
        for tree in sorted(grouped[group], key=lambda t: rank('tree', t)):
            candidate = min(grouped[group][tree], key=lambda c: rank('within-tree', group, c['source_ids']))
            snippet = normalized(candidate['rows'][0]['snippet'])
            if tree in used_trees or snippet in used_snippets:
                continue
            selected.append(candidate)
            used_trees.add(tree); used_snippets.add(snippet); taken += 1
            if taken == per_group:
                break
        if taken != per_group:
            raise ValueError('Insufficient distinct trees; do not shrink or change selection')
    return selected


def assemble(selected, render):
    jobs, references = [], []
    for pair in selected:
        ids = [rank('item', pair['tree_id'], str(r['utterance_id']))[:24] for r in pair['rows']]
        references.append({'pair_id': pair['pair_id'], 'tree_id': pair['tree_id'],
            'item_ids': ids, 'reference_actions': [action(r) for r in pair['rows']]})
        for ident, row in zip(ids, pair['rows']):
            state = visible_state(row)
            for order_index, order in enumerate(ORDERS):
                jobs.append({'id': f'{ident}_jev_order{order_index}', 'item_id': ident,
                    'backend': 'jev', 'condition': f'jev_order{order_index}', 'options': list(order),
                    'request': jev_request(state, task_instruction(order), order)})
                for thinking in (False, True):
                    mode = 'thinking' if thinking else 'direct'
                    cap = 2048 if thinking else 256
                    prompt = qwen_prompt(state, order)
                    rendered, tokens = render(prompt, thinking, cap)
                    if (not isinstance(rendered, str) or not isinstance(tokens, list) or not tokens or
                            any(type(t) != int or t < 0 for t in tokens)):
                        raise ValueError('Invalid rendering')
                    if len(tokens) + cap > LIMITS['local_context_tokens']:
                        raise ValueError('Context limit exceeded; no truncation')
                    jobs.append({'id': f'{ident}_qwen_{mode}_order{order_index}', 'item_id': ident,
                        'backend': 'qwen', 'condition': f'qwen_{mode}_order{order_index}',
                        'options': list(order), 'thinking': thinking, 'seed': 17,
                        'max_new_tokens': cap, 'prompt': prompt, 'rendered_input': rendered,
                        'input_ids': tokens})
    validate_pairs(references)
    jobs.sort(key=lambda j: rank('job-order', j['id']))
    references.sort(key=lambda r: r['pair_id'])
    jev, local = ([j for j in jobs if j['backend'] == b] for b in ('jev', 'qwen'))
    counts = {'http_attempts': len(jev), 'local_generations': len(local),
        'jev_planning_bytes_plus_allowance': sum(len(canonical(j['request']).encode()) + 256 for j in jev),
        'local_input_tokens': sum(len(j['input_ids']) for j in local),
        'local_generated_tokens': sum(j['max_new_tokens'] for j in local)}
    if any(value > LIMITS[name] for name, value in counts.items()):
        raise ValueError('Planned budget exceeded')
    return {'study': STUDY, 'status': 'frozen_inputs_before_execution',
        'reference_basis': 'public source labels; no project human verification or adjudication',
        'human_truth_automatically_verified': False, 'model_calls_executed_at_freeze': 0,
        'reference_pairs': len(references), 'items': 2 * len(references),
        'planned_non_model_controls': list(CONTROL_NAMES), 'qwen_revision': QWEN_REVISION,
        'limits': LIMITS, 'counts': counts, 'jobs': jobs}, references


def sources():
    return {name: sha((ROOT / name).read_bytes().replace(b'\r\n', b'\n')) for name in SOURCES}


def preserve(path, payload):
    if path.exists():
        if path.read_bytes().replace(b'\r\n', b'\n') != payload:
            raise ValueError('Existing frozen evidence differs; preserve it')
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(payload)


def prepare(model_dir):
    train, dev = load_source()
    selected = choose(train, dev)
    render, files = tokenizer_renderer(model_dir)
    plan, refs = assemble(selected, render)
    if len(selected) != 12 or plan['items'] != 24 or plan['counts']['http_attempts'] != 48:
        raise ValueError('Fixed grid changed')
    plan['tokenizer_config_files'] = files
    selection = {'study': STUDY, 'source_archive_sha256': ARCHIVE_SHA256,
        'source_split': 'dev', 'labels': 'original source labels, not project-adjudicated',
        'modifications': 'Original selected rows preserved; model state uses four visible fields only.',
        'selected': selected}
    artifacts = {'plan.json': readable(plan), 'references.json': readable(refs),
                 'selection.json': readable(selection)}
    freeze = {'study': STUDY, 'status': 'frozen_for_source_label_exploration',
        'artifact_sha256_lf': {name: sha(data) for name, data in artifacts.items()},
        'source_hashes_lf': sources(), 'human_reviews': 0,
        'counts': plan['counts'], 'limits': LIMITS,
        'source_action_counts': dict(Counter(a for p in selected for a in p['source_actions'])),
        'interpretation': 'Descriptive source agreement; not human-confirmed correctness.'}
    # Check all conflicts before writing; partial freezes are not silently repaired.
    artifacts['freeze.json'] = readable(freeze)
    existing = [HERE / name for name in artifacts if (HERE / name).exists()]
    if existing and (len(existing) != len(artifacts) or any(
            (HERE / n).read_bytes().replace(b'\r\n', b'\n') != data for n, data in artifacts.items())):
        raise ValueError('Existing or partial freeze differs')
    for name, payload in artifacts.items():
        preserve(HERE / name, payload)
    return freeze


def check_freeze():
    if not (HERE / 'freeze.json').exists():
        raise ValueError('Source-label execution freeze missing')
    if subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT).strip():
        raise ValueError('A clean committed checkout is required')
    freeze = json.loads((HERE / 'freeze.json').read_bytes())
    if (freeze['study'] != STUDY or freeze['status'] != 'frozen_for_source_label_exploration' or
            freeze['source_hashes_lf'] != sources()):
        raise ValueError('Source-label freeze/source mismatch')
    for name in ('freeze.json', *freeze['artifact_sha256_lf']):
        path = HERE / name
        payload = path.read_bytes().replace(b'\r\n', b'\n')
        if name != 'freeze.json' and sha(payload) != freeze['artifact_sha256_lf'][name]:
            raise ValueError('Frozen artifact changed')
        committed = subprocess.check_output(['git', 'show', 'HEAD:' + path.relative_to(ROOT).as_posix()], cwd=ROOT)
        if committed.replace(b'\r\n', b'\n') != payload:
            raise ValueError('Freeze is not committed')
    plan = json.loads((HERE / 'plan.json').read_bytes())
    refs = json.loads((HERE / 'references.json').read_bytes())
    return freeze, plan, refs


def verify_source_and_tokens(model_dir, plan, refs):
    train, dev = load_source()
    selected = choose(train, dev)
    saved = json.loads((HERE / 'selection.json').read_bytes())
    if saved['selected'] != selected or saved['source_archive_sha256'] != ARCHIVE_SHA256:
        raise ValueError('Frozen selection does not reproduce')
    render, files = tokenizer_renderer(model_dir)
    rebuilt, rebuilt_refs = assemble(selected, render)
    rebuilt['tokenizer_config_files'] = files
    if plan != rebuilt or refs != rebuilt_refs:
        raise ValueError('Frozen input/reference grid does not reproduce')


def directory(freeze):
    return ROOT / '.local' / STUDY / ('execution-' + freeze['artifact_sha256_lf']['plan.json'])


def analysis(freeze, plan, refs, model_dir):
    root = directory(freeze)
    journals, hashes = {}, {}
    with ExitStack() as stack:
        for backend in ('jev', 'qwen'):
            stack.enter_context(exclusive_lock(root / (backend + '.lock')))
            path = root / (backend + '.jsonl')
            journals[backend] = read_events(path)
            hashes[backend] = sha(path.read_bytes()) if path.exists() else None
    need_tokenizer = any(e['event'] == 'call_finish' and e['result']['status'] != 'execution_error'
                         for e in journals['qwen'])
    report = analyze(plan, refs, journals, freeze['artifact_sha256_lf']['plan.json'],
                     qwen_checker=local_checker(model_dir) if need_tokenizer else None)
    report.update(study=STUDY, reference_basis=plan['reference_basis'],
        metric_key_interpretation='Shared scorer correctness/accuracy keys mean source-label agreement only.',
        journal_sha256=hashes, new_model_calls_during_analysis=0)
    path = root / ('analysis-' + sha(readable(hashes))[:16] + '.json')
    preserve(path, readable(report))
    return report, path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('prepare', 'verify', 'jev', 'qwen', 'analyze'))
    parser.add_argument('--model-dir', type=Path, required=True)
    args = parser.parse_args()
    stage = args.command
    try:
        if args.command == 'prepare':
            freeze = prepare(args.model_dir)
            print(json.dumps({'status': 'prepared_not_executed', 'counts': freeze['counts']}, indent=2))
            return
        stage = 'freeze'
        freeze, plan, refs = check_freeze()
        if args.command == 'analyze':
            report, path = analysis(freeze, plan, refs, args.model_dir)
            print(json.dumps({'status': report['status'], 'output': str(path)}, indent=2))
            return
        stage = 'source_and_tokens'
        verify_source_and_tokens(args.model_dir, plan, refs)
        if args.command == 'verify':
            print(json.dumps({'status': 'source_and_token_grid_verified', 'new_model_calls': 0}))
            return
        from comparison_backends import jev_backend, qwen_backend
        @contextmanager
        def factory():
            factory_context = (jev_backend() if args.command == 'jev' else qwen_backend(
                args.model_dir, [j for j in plan['jobs'] if j['backend'] == 'qwen']))
            with factory_context as (call, metadata):
                commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
                yield call, {**metadata, 'execution_commit': commit, 'study': STUDY}
        stage = 'execution'
        result = execute(directory(freeze), plan, freeze['artifact_sha256_lf']['plan.json'], args.command, factory)
        print(json.dumps({'status': result['status'], 'backend': args.command,
            'attempts': len(result['state']['started']), 'finished': len(result['state']['results']),
            'input_tokens': result['state']['input_tokens'], 'output_tokens': result['state']['output_tokens'],
            'usage_incomplete': result['state']['unknown_usage'], 'overruns': result['overruns']}, indent=2))
    except (Exception, KeyboardInterrupt) as error:
        print(json.dumps({'status': 'stopped', 'stage': stage, 'error_type': type(error).__name__}))
        raise SystemExit(1)


if __name__ == '__main__':
    main()
