"""Frozen task, candidate mappings, checks, and restricted-grammar references."""
from __future__ import annotations
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

INSTRUCTIONS = (
    "Classify the customer's currently effective request for the named target service. "
    "CANCEL means the current actual instruction is to cancel or terminate that target. "
    "KEEP means the current actual instruction is to retain or continue that target. "
    "Instructions about other services, quoted examples explicitly marked as examples, "
    "and requests explicitly marked as superseded do not control this decision. "
    "Explicit current/final markers take precedence over the display order. "
    "Use only the supplied message. Choose one of the two options."
)
DESCRIPTIONS = {
    "CANCEL": "The customer's current actual instruction is to cancel or terminate the target service.",
    "KEEP": "The customer's current actual instruction is to retain or continue the target service.",
}
MAPPINGS = {"cancel_first": {"A": "CANCEL", "B": "KEEP"},
            "keep_first": {"A": "KEEP", "B": "CANCEL"}}
QWEN_REVISION = "1cfa9a7208912126459214e8b04321603b3df60c"
PRICE_PER_TOKEN = 0.042 / 1_000_000
SEED = 20260929

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def canonical(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

def append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
        f.flush()

def validate_cases(rows: list[dict]) -> dict:
    groups = defaultdict(list)
    assert len(rows) == 48, "Expected 48 distinct inputs"
    assert len({r["id"] for r in rows}) == 48
    assert len({r["customer_message"] for r in rows}) == 48
    for row in rows:
        groups[row["parent_id"]].append(row)
        assert row["human_reviewed"] is False, "Do not invent human review"
    assert len(groups) == 12
    for parent, group in groups.items():
        assert {r["variant"] for r in group} == set("ABCD"), parent
        assert len({r["target"] for r in group}) == 1, parent
        assert Counter(r["gold"] for r in group) == {"CANCEL": 2, "KEEP": 2}, parent
        bags = [Counter(re.findall(r"[a-z]+", r["customer_message"].lower())) for r in group]
        assert all(b == bags[0] for b in bags), parent
        by_variant = {r["variant"]: r for r in group}
        assert by_variant["A"]["gold"] == by_variant["C"]["gold"] == "KEEP"
        assert by_variant["B"]["gold"] == by_variant["D"]["gold"] == "CANCEL"
    return {"inputs": 48, "parents": 12, "labels": {"CANCEL": 24, "KEEP": 24},
            "same_word_multisets": True, "human_reviewed": False}

def request_for(case: dict, mapping: str) -> dict:
    """No IDs, gold labels, variants, or family names reach the model."""
    meanings = MAPPINGS[mapping]
    return {"model": "jev-1.13.0",
            "state": {"target": case["target"], "customer_message": case["customer_message"]},
            "questions": {"decision": {"type": "choice", "instructions": INSTRUCTIONS,
                "criteria": {letter: DESCRIPTIONS[meaning] for letter, meaning in meanings.items()}}}}

def user_prompt(request: dict) -> str:
    q = request["questions"]["decision"]
    options = "\n".join(f"{letter}: {description}" for letter, description in q["criteria"].items())
    return ("STATE:\n" + json.dumps(request["state"], ensure_ascii=False, indent=2)
            + "\n\nQUESTION:\n" + q["instructions"] + "\n\nOPTIONS:\n" + options
            + "\n\nAnswer with the letter only.")

def semantic_probs(probs: dict, mapping: str) -> dict:
    assert set(probs) == {"A", "B"}
    assert all(isinstance(x, (float, int)) and math.isfinite(x) and 0 <= x <= 1 for x in probs.values())
    assert abs(sum(probs.values()) - 1) <= 1e-4
    return {MAPPINGS[mapping][k]: float(v) for k, v in probs.items()}

def normalized_object(text: str) -> str:
    return re.sub(r"^the\s+", "", text.strip().lower().strip('" .'))

def grammar_reference(state: dict) -> str | None:
    """Restricted to the declared grammar; does not accept case IDs or gold."""
    message, target = state["customer_message"], normalized_object(state["target"])
    current = re.search(
        r"(?:My actual request|What I am asking you to do|My own instruction is|Actual request|"
        r"Current request|Follow this new instruction|Final request|I now say)\s*:\s*([^\.]+)",
        message, re.I)
    clauses = [current.group(1)] if current else message.split(".")
    results = []
    for clause in clauses:
        clause = clause.strip().strip('"').lower()
        action, obj = None, None
        direct = re.fullmatch(r"(cancel|end|terminate|keep|retain|continue)\s*:?\s+(.+)", clause)
        wanted = re.fullmatch(r"i want (.+) (canceled|continued)", clause)
        if direct:
            action, obj = direct.groups()
            obj = obj.split(", not ")[0]
            obj = re.sub(r"\s+active$", "", obj)
        elif wanted:
            obj, action = wanted.groups()
        if obj is not None and normalized_object(obj) == target:
            results.append("CANCEL" if action in {"cancel", "end", "terminate", "canceled"} else "KEEP")
    unique = set(results)
    return next(iter(unique)) if len(unique) == 1 else None

def keyword_reference(state: dict) -> str:
    return "CANCEL" if re.search(r"\b(?:cancel|canceled|cancelled|end|terminate)\b",
                               state["customer_message"].lower()) else "KEEP"

def job_key(config_hash: str, case_id: str, mapping: str, replicate: int) -> str:
    return digest(canonical([config_hash, case_id, mapping, replicate]).encode())

def score_records(cases: list[dict], records: list[dict], replicate: int = 0) -> dict:
    selected = [r for r in records if r["replicate"] == replicate]
    index = {(r["case_id"], r["mapping"]): r for r in selected}
    assert len(index) == len(selected), "Duplicate terminal record"
    correct = {(c["id"], m): bool(index.get((c["id"], m), {}).get("ok")) and
               index[(c["id"], m)].get("prediction") == c["gold"] for c in cases for m in MAPPINGS}
    groups = defaultdict(list)
    for c in cases:
        groups[c["parent_id"]].append(c)
    parent_pass = {p: all(correct[(c["id"], m)] for c in group for m in MAPPINGS)
                   for p, group in groups.items()}
    mapping_pass = {m: sum(all(correct[(c["id"], m)] for c in group)
                          for group in groups.values()) for m in MAPPINGS}
    unsafe = sum(index.get((c["id"], m), {}).get("prediction") == "CANCEL"
                 for c in cases if c["gold"] == "KEEP" for m in MAPPINGS)
    missed = sum(index.get((c["id"], m), {}).get("prediction") == "KEEP"
                 for c in cases if c["gold"] == "CANCEL" for m in MAPPINGS)
    mapping_disagreements = sum(
        index.get((c["id"], "cancel_first"), {}).get("prediction") !=
        index.get((c["id"], "keep_first"), {}).get("prediction")
        for c in cases if all(index.get((c["id"], m), {}).get("ok") for m in MAPPINGS))
    semantic_errors_both = sum(all(index.get((c["id"], m), {}).get("ok") and
                                  not correct[(c["id"], m)] for m in MAPPINGS) for c in cases)
    relations = {"flip": [("A", "B"), ("C", "D")], "hold": [("A", "C"), ("B", "D")]}
    pair_counts = {}
    for kind, edges in relations.items():
        count = 0
        for group in groups.values():
            v = {c["variant"]: c for c in group}
            for a, b in edges:
                for m in MAPPINGS:
                    count += bool(correct[(v[a]["id"], m)] and correct[(v[b]["id"], m)])
        pair_counts[kind] = {"correct_pairs": count, "total_pairs": len(groups) * 4}
    valid = [r for r in selected if r.get("ok")]
    brier, nll = [], []
    golds = {c["id"]: c["gold"] for c in cases}
    for r in valid:
        if r.get("probabilities"):
            pc = r["probabilities"]["CANCEL"]
            y = int(golds[r["case_id"]] == "CANCEL")
            brier.append((pc - y) ** 2)
            nll.append(-math.log(max(r["probabilities"][golds[r["case_id"]]], 1e-30)))
    return {"expected": len(cases)*2, "terminal_records": len(selected), "valid": len(valid),
            "missing": len(cases)*2-len(selected), "failed": len(selected)-len(valid),
            "correct": sum(correct.values()), "robust_pass": sum(parent_pass.values()),
            "parents": len(groups), "parent_pass": parent_pass, "mapping_pass": mapping_pass,
            "wrong_cancel": unsafe, "missed_cancel": missed,
            "mapping_disagreements": mapping_disagreements,
            "semantic_errors_both_mappings": semantic_errors_both, "pairs": pair_counts,
            "brier": sum(brier)/len(brier) if brier else None,
            "nll": sum(nll)/len(nll) if nll else None}

