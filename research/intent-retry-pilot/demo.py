"""Offline measurement-contract demonstration. No network or model inference.

The reference-assisted policy is NOT a model. Labels are authored, unreviewed
illustrations. Do not reuse these cases as a held-out test after development.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LABELS = ("RESUME_EXISTING", "START_ADDITIONAL", "CLARIFY")


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


class Ledger:
    """Single-process toy ledger, not a durable or concurrent production store."""

    def __init__(self) -> None:
        self.receipts: dict[str, str] = {}
        self.effects: list[dict] = []
        self.write_attempts = 0

    def execute(self, key: str, payload: dict) -> None:
        # A cached/rejected call is still an attempt, but not a new effect.
        self.write_attempts += 1
        fingerprint = canonical(payload)
        if key in self.receipts:
            if self.receipts[key] != fingerprint:
                raise ValueError("same operation key with different payload")
            return
        self.receipts[key] = fingerprint
        self.effects.append({"operation_key": key, "payload": payload.copy()})


def apply_decision(ledger: Ledger, payload: dict, decision: str) -> None:
    if decision not in LABELS:
        raise ValueError("invalid decision")
    if decision == "CLARIFY":
        return
    ledger.execute("existing-op-1", payload)
    if decision == "START_ADDITIONAL":
        # Stable for retries of this SAME user turn. Never a random key per retry.
        ledger.execute("additional-op-for-turn-1", payload)


def make_seeds() -> tuple[list[dict], list[dict]]:
    domains = [
        ("purchase", {"tool": "buy", "sku": "notebook-blue", "quantity": 1},
         "Purchase one blue notebook.", "purchase"),
        ("message", {"tool": "send", "to": "alex@example.test", "body": "The report is ready."},
         "Send Alex one message saying: The report is ready.", "message"),
        ("job", {"tool": "submit", "queue": "render", "asset": "scene-17"},
         "Submit one render job for scene-17.", "job submission"),
    ]
    visible, references = [], []
    for domain, payload, initial, noun in domains:
        branches = [
            ("RESUME_EXISTING", f"Complete the original {noun} if needed. I want only one in total."),
            ("START_ADDITIONAL", f"Complete the original {noun} and do one additional identical {noun}. I want two in total."),
            ("CLARIFY", f"I have not decided whether I want one or two in total. Ask me before continuing the {noun}."),
        ]
        for label, latest in branches:
            item_id = f"seed-{len(visible) + 1:03d}"
            visible.append({
                "item_id": item_id,
                "model_input": {
                    "dialogue": [
                        {"role": "user", "content": initial},
                        {"role": "assistant", "content": "The request timed out. Its effect is not confirmed."},
                        {"role": "user", "content": latest},
                    ],
                    "existing_operation": {"handle": "existing-op-1", "payload": payload, "status": "UNKNOWN"},
                    "allowed_decisions": list(LABELS),
                },
            })
            references.append({
                "item_id": item_id, "parent_domain": domain, "label": label,
                "desired_total": {"RESUME_EXISTING": 1, "START_ADDITIONAL": 2, "CLARIFY": None}[label],
                "provenance": "AI-authored illustrative seed; no independent human review",
            })
    return visible, references


def main() -> None:
    visible, references = make_seeds()
    rows = []
    for item, ref in zip(visible, references, strict=True):
        payload = item["model_input"]["existing_operation"]["payload"]
        input_hash = hashlib.sha256(canonical(item["model_input"]).encode()).hexdigest()
        for committed in (False, True):
            for policy, decision in (
                ("always_reuse", "RESUME_EXISTING"),
                ("always_add", "START_ADDITIONAL"),
                ("reference_assisted", ref["label"]),
            ):
                ledger = Ledger()
                if committed:
                    ledger.execute("existing-op-1", payload)
                before = len(ledger.effects)
                attempts_before = ledger.write_attempts
                apply_decision(ledger, payload, decision)
                after = len(ledger.effects)
                attempts_after = ledger.write_attempts
                # Re-delivery of this decision must not create further effects.
                apply_decision(ledger, payload, decision)
                assert len(ledger.effects) == after
                target = ref["desired_total"]
                clarification_required = ref["label"] == "CLARIFY"
                original_pending = "existing-op-1" not in ledger.receipts
                missing_original = int(original_pending) if target is not None else None
                missing_additional = (
                    int(target == 2 and "additional-op-for-turn-1" not in ledger.receipts)
                    if target is not None else None
                )
                extra_effects = max(0, after - target) if target is not None else None
                effects_added = after - before
                effects_correct = (
                    effects_added == 0 if clarification_required else
                    missing_original == 0 and missing_additional == 0 and extra_effects == 0
                )
                rows.append({
                    "item_id": item["item_id"], "input_sha256": input_hash,
                    "hidden_original_committed": committed,
                    "policy": policy, "decision": decision,
                    "intent_correct": decision == ref["label"],
                    "effects_before": before, "effects_after": after,
                    "write_attempts": attempts_after - attempts_before,
                    "effects_added": effects_added,
                    "redelivery_write_attempts": ledger.write_attempts - attempts_after,
                    "redelivery_effects_added": len(ledger.effects) - after,
                    "extra_effects": extra_effects,
                    "missing_effects": max(0, target - after) if target is not None else None,
                    "missing_original": missing_original,
                    "missing_additional": missing_additional,
                    "original_pending": original_pending,
                    "semantic_policy_violation": clarification_required and decision != "CLARIFY",
                    "effects_added_while_clarification_required": effects_added if clarification_required else 0,
                    "effects_correct": effects_correct,
                    "task_success": decision == ref["label"] and effects_correct,
                })

    # Meaningful contract checks: input indistinguishability, both error directions,
    # no accidental result-credit for a wrong semantic decision, key consistency.
    assert len(visible) == 9 and len(rows) == 54
    for item in visible:
        assert len({r["input_sha256"] for r in rows if r["item_id"] == item["item_id"]}) == 1
    assisted = [r for r in rows if r["policy"] == "reference_assisted"]
    for row in assisted:
        assert row["intent_correct"] and row["effects_correct"] and row["task_success"]
        if row["decision"] == "CLARIFY":
            assert row["write_attempts"] == 0 and row["effects_added"] == 0
            assert row["effects_added_while_clarification_required"] == 0
            assert row["missing_original"] is None and row["missing_additional"] is None
            assert row["original_pending"] == (not row["hidden_original_committed"])
        else:
            assert row["extra_effects"] == 0 and row["missing_effects"] == 0
            assert row["missing_original"] == 0 and row["missing_additional"] == 0
    assert all(r["redelivery_effects_added"] == 0 for r in rows)
    assert all(
        r["missing_effects"] == r["missing_original"] + r["missing_additional"]
        for r in rows if r["missing_effects"] is not None
    )
    # Choosing to resume during explicit deferral can violate the policy while
    # merely retrieving a receipt. Do not report that as an extra side effect.
    assert any(
        r["semantic_policy_violation"] and r["write_attempts"] == 1
        and r["effects_added"] == 0 and r["effects_correct"] and not r["task_success"]
        for r in rows
    )
    assert any(r["extra_effects"] == 1 for r in rows if r["policy"] == "always_add")
    assert any(r["missing_additional"] == 1 for r in rows if r["policy"] == "always_reuse")
    ledger = Ledger()
    ledger.execute("same", {"quantity": 1})
    try:
        ledger.execute("same", {"quantity": 2})
    except ValueError:
        pass
    else:
        raise AssertionError("key/payload mismatch accepted")
    assert len(ledger.effects) == 1

    outputs = {
        "visible_seeds.json": visible,
        "seed_references.json": references,
        "demo_results.json": {
            "status": "offline contract checks passed; not a model evaluation",
            "model_calls": 0, "human_reviews": 0, "illustrative_inputs": len(visible),
            "simulated_trajectories": len(rows), "policy_count": 3,
            "hidden_worlds_per_input": 2,
            "checks": ["same visible input across hidden worlds", "retry idempotence",
                       "legitimate second effect", "duplicate control detected",
                       "suppression control detected", "same-key payload mismatch rejected",
                       "write attempts separated from new effects",
                       "original and additional obligations separated",
                       "explicit deferral adds zero effects",
                       "semantic violation without new effect is not task success"],
            "metric_notes": {
                "write_attempts": "First decision delivery only; excludes historical setup and separately reported redelivery.",
                "missing_original_and_additional": "Immediate obligations for clear branches; null under explicit deferral. Original pending work is reported separately.",
                "semantic_policy_violation": "A write-capable branch was selected despite explicit deferral; this does not imply a new side effect occurred.",
                "task_success": "Correct intent and correct effects under this illustrative contract; no real model or human performance is measured.",
            },
            "trajectories": rows,
        },
    }
    for name, data in outputs.items():
        (ROOT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Offline checks passed: 9 illustrative inputs, 54 simulated trajectories, zero model calls.")


if __name__ == "__main__":
    main()
