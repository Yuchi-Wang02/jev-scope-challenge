"""Descriptive exploratory reporting. Never calls a model or edits raw responses."""
from __future__ import annotations
from collections import Counter, defaultdict
import json
import re
from pathlib import Path

from demo import Ledger, apply_decision
from run_jev import read_rows, accounting, verify

ROOT = Path(__file__).resolve().parent
LABELS = ["RESUME_EXISTING", "START_ADDITIONAL", "CLARIFY"]


def rule_linker(state):
    """Author-aware transparent control, not independently tuned/validated.

    Uses visible text only. An abstention means asking the user, not correctness.
    Rules and their limitations are frozen before model outputs are obtained.
    """
    text = state["dialogue"][-1]["content"].lower()
    if re.search(r"\b(pause|hold|wait|hold off)\b|until i|before i|before taking", text):
        return "CLARIFY"
    no_extra = re.search(r"\b(only|single)\b|don't|do not|no (new|additional)|not (asking|requesting)|without", text)
    additional = re.search(r"\b(second|two|another|additional|again|repeat|repetition)\b|in addition|as well|both", text)
    if no_extra:
        return "RESUME_EXISTING"
    if additional:
        return "START_ADDITIONAL"
    if re.search(r"original|receipt|confirmation|hasn't changed", text):
        return "RESUME_EXISTING"
    return "CLARIFY"


def effect_record(state, ref, decision, committed):
    ledger = Ledger()
    payload = state["existing_operation"]["payload"]
    if committed:
        ledger.execute("existing-op-1", payload)
    before, attempts_before = len(ledger.effects), ledger.write_attempts
    if decision in LABELS:
        apply_decision(ledger, payload, decision)
    after = len(ledger.effects)
    missing_original = int("existing-op-1" not in ledger.receipts)
    need_additional = ref["label"] == "START_ADDITIONAL"
    missing_additional = int(need_additional and "additional-op-for-turn-1" not in ledger.receipts)
    is_clarify = ref["label"] == "CLARIFY"
    extra = max(0, after - ref["intended_total"]) if not is_clarify else None
    effects_ok = (after == before) if is_clarify else (not missing_original and not missing_additional and extra == 0)
    return {"hidden_original_committed": committed, "write_attempts": ledger.write_attempts - attempts_before,
            "effects_added": after-before, "extra_effects": extra,
            "missing_original": missing_original if not is_clarify else None,
            "missing_additional": missing_additional if not is_clarify else None,
            "original_pending": bool(missing_original),
            "effects_added_during_required_deferral": after-before if is_clarify else 0,
            "false_merge_decision": need_additional and decision == "RESUME_EXISTING",
            "unnecessary_clarification": not is_clarify and decision == "CLARIFY",
            "scope_and_effect_success": decision == ref["label"] and effects_ok}


def summarize(predictions, refs, states):
    by_parent, by_stratum, by_item = defaultdict(list), defaultdict(list), defaultdict(list)
    confusion = Counter()
    traces = []
    for row in predictions:
        ref = refs[row["item_id"]]
        pred = row["prediction"]
        correct = pred == ref["label"]
        confusion[f"{ref['label']} -> {pred or 'NO_VALID_OUTPUT'}"] += 1
        by_parent[ref["parent_id"]].append(correct)
        by_stratum[ref["stratum"]].append(correct)
        by_item[row["item_id"]].append(pred)
        for committed in ref["hidden_committed_worlds"]:
            traces.append({"item_id": row["item_id"], "option_order_index": row["order"],
                           "prediction": pred, "reference": ref["label"], "stratum": ref["stratum"],
                           **effect_record(states[row["item_id"]], ref, pred, committed)})
    return {"decisions": len(predictions), "reference_matches": sum(map(sum, by_parent.values())),
            "strata": {s: {"reference_matches": sum(v), "decisions": len(v)} for s,v in by_stratum.items()},
            "parent_all_12_decisions_correct": {p: len(v)==12 and all(v) for p,v in by_parent.items()},
            "two_order_disagreements": sum(len(v)==2 and v[0]!=v[1] for v in by_item.values()),
            "confusion": dict(confusion),
            "effect_replay_count": len(traces),
            "effect_note": "Hidden worlds and option orders are repeated simulations, not independent observations.",
            "effect_totals": {k: sum(t[k] or 0 for t in traces) for k in (
                "write_attempts", "effects_added", "extra_effects", "missing_original", "missing_additional",
                "effects_added_during_required_deferral", "false_merge_decision", "unnecessary_clarification", "scope_and_effect_success")},
            "replay_traces": traces}


def main():
    jobs, freeze, freeze_hash = verify(ROOT)
    visible = json.loads((ROOT/'data/visible.json').read_text(encoding='utf-8'))
    refs = {r['item_id']:r for r in json.loads((ROOT/'data/references.json').read_text(encoding='utf-8'))}
    states = {v['item_id']:v['model_input'] for v in visible}
    primary = [j for j in jobs if j['phase']=='primary']
    policies = {"always_reuse": lambda s: LABELS[0], "always_add": lambda s: LABELS[1],
                "always_clarify": lambda s: LABELS[2], "author_aware_rule": rule_linker}
    summaries = {}
    for name, policy in policies.items():
        preds = [{"item_id":j['item_id'], "order":j['job_id'].split('-o')[-1],
                  "prediction":policy(states[j['item_id']])} for j in primary]
        summaries[name] = summarize(preds, refs, states)
    outputs = read_rows(ROOT/'results/jev_responses.jsonl')
    by_job = {r['job_id']:r for r in outputs}
    stats = accounting(read_rows(ROOT/'results/jev_attempts.jsonl'), jobs, freeze_hash)
    reached = [j for j in primary if j['job_id'] in by_job]
    preds = [{"item_id":j['item_id'], "order":j['job_id'].split('-o')[-1],
              "prediction":by_job[j['job_id']].get('prediction') if by_job[j['job_id']]['ok'] else None} for j in reached]
    if reached:
        summaries['jev'] = summarize(preds, refs, states)
    report = {"status":"exploratory; references not human-validated", "freeze_sha256":freeze_hash,
              "primary_terminal":len(reached), "primary_planned":len(primary), "pending":len(primary)-len(reached),
              "complete_run":len(reached)==len(primary), "human_review_count":0,
              "ordinary_capable_baseline":"not run; no model-comparison conclusion",
              "rule_provenance":"Author knew material; simple diagnostic control, no independent tuning claim",
              "clarification_warning":"12 unresolved-reference items may admit a recency interpretation; no binding-defect claim from those outputs",
              "accounting":{k:stats[k] for k in ('attempts','retries','planned_input_units','known_input_tokens','known_output_tokens','unknown_usage_attempts','unfinished')},
              "known_input_price_estimate_usd":stats['known_input_tokens']*0.042/1e6,
              "summaries":summaries}
    (ROOT/'results').mkdir(exist_ok=True)
    (ROOT/'results/analysis.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='summaries'},ensure_ascii=False))
    for name, summary in summaries.items():
        print(json.dumps({"system":name, **{k:v for k,v in summary.items() if k not in ('replay_traces','effect_note','parent_all_12_decisions_correct')}},ensure_ascii=False))


if __name__ == '__main__':
    main()
