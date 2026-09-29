"""Strict offline evidence-chain checks added after the original v0.1 run.

The frozen runner and analyzer remain unchanged. This verifier checks the saved
raw evidence independently; it does not make model calls or rewrite results.
"""
from __future__ import annotations
import argparse
import json
import math
from collections import Counter
from pathlib import Path
from core import MAPPINGS, PRICE_PER_TOKEN, QWEN_REVISION, canonical, digest, job_key, read_jsonl, request_for, semantic_probs, user_prompt
from run import ROOT, sha_file, verify_manifest


def require(condition, message):
    if not condition:
        raise ValueError(message)


def close(a, b):
    return isinstance(a, (int, float)) and isinstance(b, (int, float)) and math.isfinite(a) and math.isfinite(b) and math.isclose(a, b, rel_tol=2e-5, abs_tol=1e-7)


def verify_fingerprint(manifest):
    payload = {k: v for k, v in manifest.items() if k not in {"config_hash", "frozen_at_utc"}}
    require(digest(canonical(payload).encode()) == manifest["config_hash"], "Manifest self-fingerprint mismatch")


def verify_row(row, case, manifest, backend, phase):
    mapping, rep = row["mapping"], row["replicate"]
    require(mapping in MAPPINGS and rep in (0, 1), "Unknown mapping/round")
    require(row["backend"] == backend and row["phase"] == phase, "Backend/phase mismatch")
    require(row["config_hash"] == manifest["config_hash"], "Config mismatch")
    for field in ("parent_id", "variant", "family"):
        require(row[field] == case[field], f"Case {field} mismatch")
    body = request_for(case, mapping)
    require(row["request"] == body, "Exact request mismatch")
    require(row["request_sha256"] == digest(canonical(body).encode()), "Request hash mismatch")
    require(row["job_key"] == job_key(manifest["config_hash"], case["id"], mapping, rep), "Job key mismatch")
    require(row["ok"] is True, "Published run includes a failed terminal row")
    probs = row["letter_probabilities"]
    expected_semantic = semantic_probs(probs, mapping)
    require(set(row["probabilities"]) == set(expected_semantic), "Semantic keys mismatch")
    require(all(close(row["probabilities"][k], v) for k, v in expected_semantic.items()), "Semantic probabilities mismatch")
    letter = row["letter"]
    require(letter in probs and probs[letter] >= max(probs.values()) - 1e-7, "Choice is not candidate argmax")
    require(row["prediction"] == MAPPINGS[mapping][letter], "Semantic choice mismatch")
    if backend == "jev":
        raw = row["raw_response"]
        answer = raw["answers"]["decision"]
        require(raw["model"] == row["served_model"] == manifest["jev_model"], "Served model mismatch")
        require(answer["type"] == "choice" and answer["choice"] == letter, "Raw choice mismatch")
        require(set(answer["probabilities"]) == set(probs) and all(close(answer["probabilities"][k], v) for k, v in probs.items()), "Raw probability mismatch")
        require(raw["usage"]["input_tokens"] == row["input_tokens"], "Raw usage mismatch")
    else:
        require(row["served_model"] == "Qwen/Qwen3-4B@" + QWEN_REVISION, "Qwen model mismatch")
        expected_prompt = "<|im_start|>user\n" + user_prompt(body) + "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
        require(row["prompt"] == expected_prompt, "Serialized Qwen prompt mismatch")
        require(row["prompt_sha256"] == digest(row["prompt"].encode()), "Prompt hash mismatch")
        logits = row["candidate_logits"]
        require(set(logits) == {"A", "B"} and all(math.isfinite(v) for v in logits.values()), "Invalid logits")
        maximum = max(logits.values())
        weights = {k: math.exp(v - maximum) for k, v in logits.items()}
        total = sum(weights.values())
        require(all(close(probs[k], weights[k] / total) for k in weights), "Logit-to-probability mismatch")
        raw = row["raw_token_probabilities"]
        require(set(raw) == {"A", "B", " A", " B"} and all(math.isfinite(v) and 0 <= v <= 1 for v in raw.values()), "Invalid vocabulary probabilities")
        mass = raw["A"] + raw["B"]
        require(mass > 0 and close(mass, row["candidate_mass"]), "Candidate mass mismatch")
        require(all(close(raw[k] / mass, probs[k]) for k in probs), "Vocabulary-to-conditional mismatch")
        require(row["low_mass"] == (mass < .01), "Low-mass flag mismatch")


def audit(root=ROOT):
    require(root == ROOT, "Original evidence must use the repository root")
    manifest = verify_manifest()
    verify_fingerprint(manifest)
    jev_rows, files, count = [], {}, 0
    for phase in ("formal", "smoke"):
        cases = read_jsonl(root / ("data/cases.jsonl" if phase == "formal" else "data/smoke.jsonl"))
        by_id = {c["id"]: c for c in cases}
        expected = {(c["id"], m, rep) for c in cases for m in (MAPPINGS if phase == "formal" else ["cancel_first"]) for rep in ([0, 1] if phase == "formal" else [0])}
        for backend in ("jev", "qwen"):
            path = root / f"results/{backend}_{phase}.jsonl"
            rows = read_jsonl(path)
            actual = [(r["case_id"], r["mapping"], r["replicate"]) for r in rows]
            require(set(actual) == expected and len(actual) == len(expected), f"Incomplete/duplicate grid: {path.name}")
            for row in rows:
                try:
                    verify_row(row, by_id[row["case_id"]], manifest, backend, phase)
                except (KeyError, ValueError, AssertionError, TypeError) as exc:
                    raise ValueError(f"{path.name}/{row.get('case_id')}/{row.get('mapping')}/{row.get('replicate')}: {exc}") from exc
            if backend == "jev":
                jev_rows.extend(rows)
            count += len(rows)
            files[path.relative_to(root).as_posix()] = sha_file(path)
    ledger_path = root / "results/jev_attempts.jsonl"
    ledger = read_jsonl(ledger_path)
    starts = [(r["job_key"], r["attempt"]) for r in ledger if r["event"] == "attempt_started"]
    finishes = {(r["job_key"], r["attempt"]): r for r in ledger if r["event"] == "attempt_finished"}
    require(len(starts) == len(set(starts)) == len(finishes) and set(starts) == set(finishes), "Unmatched/duplicate ledger attempts")
    require(len(ledger) == len(starts) * 2, "Unexpected ledger event")
    per_job = Counter(k for k, _ in starts)
    require(set(per_job) == {r["job_key"] for r in jev_rows}, "Ledger/record job set mismatch")
    for row in jev_rows:
        key = row["job_key"]
        require(per_job[key] == row["http_attempts"] == 1, "Original one-attempt provenance changed")
        finish = finishes[key, 1]
        require(finish["http_status"] == 200 and finish["cost_known"] is True, "Unknown/failed original HTTP attempt")
        require(finish["input_tokens"] == row["input_tokens"], "Ledger usage mismatch")
        require(math.isclose(finish["known_cost_usd"], finish["input_tokens"] * PRICE_PER_TOKEN, rel_tol=1e-9, abs_tol=1e-12), "Ledger cost mismatch")
    files[ledger_path.relative_to(root).as_posix()] = sha_file(ledger_path)
    return {"status": "passed", "verifier_version": "1.0", "formal_records": 384, "smoke_records": count - 384,
            "matched_http_attempts": len(starts), "manifest_self_fingerprint": True,
            "raw_evidence_chain": True, "files_sha256_lf": files,
            "limitations": ["Offline consistency check, not authentication of a hosted service", "No independent human label review", "No model calls"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = audit()
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
