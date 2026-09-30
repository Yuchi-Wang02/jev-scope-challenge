"""Build a private, inference-closed comparison draft after verified adjudication.

No API client, credential loading or model weight loading is provided here.
"""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

from action_interface import ACTIONS
from shortcut_controls import CONTROL_NAMES
from prepare_sharc_review import (
    ROOT, STUDY, item_id, pair_id, prepare_with_selection, readable, verify_manifest,
)
from review_reconcile import (
    blank_adjudication_csv, load_review, private_directory, reconciliation,
)
from review_finalize import load_adjudication, reviewed_manifest, validate_adjudication_rows

sys.path.insert(0, str(ROOT / 'research/action-backends'))
from adapters import jev_request, qwen_final

HERE = Path(__file__).resolve().parent
PLAN_ID = 'sharc-direct-comparison-draft-v1'
QWEN_REVISION = '851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a'
ORDERS = (ACTIONS, tuple(reversed(ACTIONS)))
INSTRUCTIONS = (
    'Select the next action for the user question using only the visible snippet, '
    'scenario and conversation history. Treat the snippet as the historical rule '
    'to interpret; do not apply outside facts or current policy. Follow its stated '
    'logical conditions. Do not assume an unanswered condition is false. '
    'Yes: the visible facts establish a positive answer under the rule. '
    'No: the visible facts establish a negative answer under the rule. '
    'Irrelevant: the question is not addressed by this rule. '
    'ASK: further information from the user is needed to decide. '
    'Select the action only; do not generate a follow-up question.'
)
LIMITS = {
    'http_attempts': 96, 'http_retries': 0, 'local_generations': 192,
    'jev_planning_bytes_plus_allowance': 1000000, 'jev_actual_input_tokens': 500000,
    'local_input_tokens': 1000000, 'local_generated_tokens': 221184,
    'local_generation_wall_seconds': 7200, 'local_context_tokens': 32768,
}


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def visible_state(item):
    fields = ('snippet', 'question', 'scenario', 'history')
    if any(not isinstance(item.get(k), str) for k in fields[:3]):
        raise ValueError('Visible text fields must be strings')
    history = item.get('history')
    if not isinstance(history, list):
        raise ValueError('History must be a list')
    safe = []
    for turn in history:
        keys = ('follow_up_question', 'follow_up_answer')
        if not isinstance(turn, dict) or any(not isinstance(turn.get(k), str) for k in keys):
            raise ValueError('Malformed visible history')
        safe.append({k: turn[k] for k in keys})
    return {**{k: item[k] for k in fields[:3]}, 'history': safe}


def verified_review_inputs(review_a, review_b, adjudication, review_dir):
    """Recompute existing review artifacts rather than trust a status flag."""
    paths = [Path(p).resolve() for p in (review_a, review_b, adjudication)]
    if len(set(paths)) != 3 or any(not p.is_file() for p in paths):
        raise ValueError('Three distinct existing review/adjudication files required')
    directory = private_directory(Path(review_dir))
    # Fail before source access if required recorded stages are absent.
    saved = {name: (directory / name).read_bytes() for name in (
        'adjudication_queue.json', 'adjudication_blank.csv', 'reviewed_selection.json')}
    a, hash_a = load_review(paths[0])
    b, hash_b = load_review(paths[1])
    manifest, pack_bytes, _, selected = prepare_with_selection()
    verify_manifest(manifest)
    pack = json.loads(pack_bytes)
    queue = reconciliation(pack, selected, a, b)
    queue.update(selection_sha256=manifest['selection_sha256'],
                 review_a_sha256=hash_a, review_b_sha256=hash_b)
    if (saved['adjudication_queue.json'] != readable(queue) or
            saved['adjudication_blank.csv'] != blank_adjudication_csv(queue)):
        raise ValueError('Saved reconciliation differs from submitted reviews')
    header, rows, hash_adj = load_adjudication(paths[2])
    judgments = validate_adjudication_rows(header, rows, queue)
    final = reviewed_manifest(selected, judgments, manifest['selection_sha256'],
                              (hash_a, hash_b), hash_adj)
    if saved['reviewed_selection.json'] != readable(final):
        raise ValueError('Saved final cohort differs from revalidated adjudication')
    if final['final_pairs'] != 24 or final['final_individual_items'] != 48:
        raise ValueError('Frozen primary cohort size changed')
    provenance = {'review_a_sha256': hash_a, 'review_b_sha256': hash_b,
                  'adjudication_sha256': hash_adj,
                  'reviewed_selection_sha256': sha(readable(final)),
                  'review_pack_sha256': sha(pack_bytes),
                  'source_selection_sha256': manifest['selection_sha256']}
    return pack, selected, final, provenance


def material(pack, selected, final, render):
    """Pure draft compiler; injected renderer is synthetic in software tests."""
    items = {item['item_id']: item for item in pack['items']}
    candidates = {pair_id(c): c for c in selected}
    if len(items) != len(pack['items']) or len(candidates) != len(selected):
        raise ValueError('Repeated source identity')
    references, jobs, used_items, used_trees, used_pairs = [], [], set(), set(), set()
    for entry in final['selected']:
        ident = entry['pair_id']
        if ident not in candidates or ident in used_pairs:
            raise ValueError('Foreign or repeated finalized pair')
        candidate = candidates[ident]
        ids = [item_id(row) for row in candidate['rows']]
        refs = entry['adjudicated_actions']
        if (entry['item_ids'] != ids or len(ids) != 2 or len(set(ids)) != 2 or
                not isinstance(refs, list) or len(refs) != 2 or
                any(not isinstance(a, str) or a not in ACTIONS for a in refs)):
            raise ValueError('Finalized member/reference mismatch')
        tree = candidate['tree_id']
        if tree in used_trees or any(i in used_items or i not in items for i in ids):
            raise ValueError('Repeated tree/item or missing visible material')
        used_pairs.add(ident); used_trees.add(tree); used_items.update(ids)
        references.append({'pair_id': ident, 'tree_id': tree, 'item_ids': ids,
                           'reference_actions': refs})
        for item in ids:
            state = visible_state(items[item])
            for order_index, order in enumerate(ORDERS):
                instruction = INSTRUCTIONS + ' Allowed actions in display order: ' + ', '.join(order) + '.'
                jobs.append({'id': f'{item}_jev_order{order_index}', 'item_id': item,
                             'backend': 'jev', 'condition': f'jev_order{order_index}',
                             'options': list(order), 'request': jev_request(state, instruction, order)})
                for thinking in (False, True):
                    mode = 'thinking' if thinking else 'direct'
                    prompt = instruction + '\nstate: ' + canonical(state) + (
                        '\nReturn only a JSON object with exactly one key "action" whose value '
                        'is one of the allowed actions. Put the object in your final answer.')
                    cap = 2048 if thinking else 256
                    rendered, input_ids = render(prompt, thinking, cap)
                    if (not isinstance(rendered, str) or not isinstance(input_ids, list) or
                            not input_ids or any(type(t) != int or t < 0 for t in input_ids)):
                        raise ValueError('Renderer must supply nonempty token IDs and text')
                    if len(input_ids) + cap > LIMITS['local_context_tokens']:
                        raise ValueError('Context budget exceeded; no truncation permitted')
                    jobs.append({'id': f'{item}_qwen_{mode}_order{order_index}',
                                 'item_id': item, 'backend': 'qwen',
                                 'condition': f'qwen_{mode}_order{order_index}',
                                 'options': list(order), 'thinking': thinking, 'seed': 17,
                                 'max_new_tokens': cap, 'prompt': prompt,
                                 'rendered_input': rendered, 'input_ids': input_ids})
    if not references:
        raise ValueError('Empty finalized cohort')
    jobs.sort(key=lambda job: sha((PLAN_ID + ':' + job['id']).encode()))
    references.sort(key=lambda row: row['pair_id'])
    jev = [j for j in jobs if j['backend'] == 'jev']
    qwen = [j for j in jobs if j['backend'] == 'qwen']
    counts = {'jev_calls': len(jev), 'local_generations': len(qwen),
              'local_input_tokens': sum(len(j['input_ids']) for j in qwen),
              'local_generated_token_cap': sum(j['max_new_tokens'] for j in qwen),
              'jev_planning_bytes_plus_allowance': sum(len(canonical(j['request']).encode()) + 256 for j in jev)}
    for count, limit in (('jev_calls', 'http_attempts'), ('local_generations', 'local_generations'),
                         ('local_input_tokens', 'local_input_tokens'),
                         ('local_generated_token_cap', 'local_generated_tokens'),
                         ('jev_planning_bytes_plus_allowance', 'jev_planning_bytes_plus_allowance')):
        if counts[count] > LIMITS[limit]:
            raise ValueError('Draft exceeds budget: ' + count)
    plan = {'study': PLAN_ID, 'status': 'draft_only_inference_closed',
            'human_truth_automatically_verified': False, 'model_calls_executed': 0,
            'reference_pairs': len(references), 'items': len(used_items),
            'planned_non_model_controls': list(CONTROL_NAMES),
            'qwen_revision': QWEN_REVISION, 'limits': dict(LIMITS),
            'counts': counts, 'jobs': jobs}
    return plan, references


def tokenizer_renderer(model_dir):
    """Load only pinned tokenizer/config files, never weights or remote code."""
    for key in ('HF_HUB_OFFLINE', 'TRANSFORMERS_OFFLINE', 'HF_HUB_DISABLE_TELEMETRY'):
        os.environ[key] = '1'
    import transformers
    if transformers.__version__ != '5.3.0':
        raise ValueError('Use the pinned Transformers 5.3.0 environment')
    manifest = json.loads((ROOT / 'research/baseline-readiness/qwen35-smoke-repaired/run.json').read_text())
    files = [f for f in manifest['model_files'] if not f['name'].endswith('.safetensors')]
    for record in files:
        payload = (Path(model_dir) / record['name']).read_bytes()
        if len(payload) != record['bytes'] or sha(payload) != record['sha256']:
            raise ValueError('Pinned tokenizer/configuration mismatch')
    tokenizer = transformers.AutoTokenizer.from_pretrained(model_dir, local_files_only=True,
                                                            trust_remote_code=False)
    def render(prompt, thinking, cap):
        text = tokenizer.apply_chat_template([{'role': 'user', 'content': prompt}],
                    tokenize=False, add_generation_prompt=True, enable_thinking=thinking)
        ids = tokenizer(text, add_special_tokens=False)['input_ids']
        qwen_final(tokenizer, [], thinking=thinking, rendered_prompt=text, max_new_tokens=cap)
        return text, ids
    return render, files


def preserve(directory, plan, references):
    directory = private_directory(Path(directory))
    outputs = {'comparison_plan.json': readable(plan), 'scoring_references.json': readable(references)}
    if any((directory / name).exists() for name in outputs):
        if not all((directory / name).is_file() and (directory / name).read_bytes() == data
                   for name, data in outputs.items()):
            raise ValueError('Existing or partial output differs; preserve it')
        return 'verified_existing'
    directory.mkdir(parents=True, exist_ok=True)
    for name, data in outputs.items():
        with (directory / name).open('xb') as target:
            target.write(data)
    return 'created'


def compile_reviewed(review_a, review_b, adjudication, review_dir, tokenizer_dir):
    pack, selected, final, provenance = verified_review_inputs(
        review_a, review_b, adjudication, review_dir)
    render, files = tokenizer_renderer(tokenizer_dir)
    plan, references = material(pack, selected, final, render)
    plan['provenance'] = {**provenance, 'tokenizer_config_files': files,
                          'compiler_sha256': sha(Path(__file__).read_bytes()),
                          'shortcut_controls_sha256': sha((HERE / 'shortcut_controls.py').read_bytes()),
                          'draft_protocol_sha256': sha((HERE / 'COMPARISON_DRAFT.md').read_bytes())}
    plan['scoring_references_sha256'] = sha(readable(references))
    return plan, references


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--review-a', required=True, type=Path)
    p.add_argument('--review-b', required=True, type=Path)
    p.add_argument('--adjudication', required=True, type=Path)
    p.add_argument('--review-dir', type=Path, default=ROOT / '.local' / STUDY)
    p.add_argument('--tokenizer-dir', required=True, type=Path)
    p.add_argument('--output-dir', type=Path, default=ROOT / '.local' / PLAN_ID)
    args = p.parse_args()
    private_directory(args.output_dir)
    plan, references = compile_reviewed(args.review_a, args.review_b,
        args.adjudication, args.review_dir, args.tokenizer_dir)
    status = preserve(args.output_dir, plan, references)
    print(json.dumps({'status': status, 'counts': plan['counts'],
                      'model_inference_open': False, 'model_calls_executed': 0}))


if __name__ == '__main__':
    main()
