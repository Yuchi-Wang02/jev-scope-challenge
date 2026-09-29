"""Safe v0.1 replication entry point; preserves the historical frozen runner.

Fresh outputs are required outside results/. Successful cache entries skip
backend creation. Runtime metadata are per-session, never overwritten by resume.
"""
from __future__ import annotations
import argparse
import json
import random
import time
import uuid
from collections import Counter
from pathlib import Path
from core import MAPPINGS, SEED, append_jsonl, canonical, digest, job_key, read_jsonl, request_for, semantic_probs
import run as legacy
from verify_evidence import verify_fingerprint, verify_row


def ledger_state(rows):
    starts = [(r["job_key"], r["attempt"]) for r in rows if r["event"] == "attempt_started"]
    finishes = [(r["job_key"], r["attempt"]) for r in rows if r["event"] == "attempt_finished"]
    if len(starts) != len(set(starts)) or len(finishes) != len(set(finishes)) or not set(finishes) <= set(starts):
        raise RuntimeError("Ledger has duplicate or unmatched completed attempts")
    if set(starts) - set(finishes):
        raise RuntimeError("Unfinished HTTP attempt has unknown cost; reconcile the ledger before resume")
    if any(not r.get("cost_known", False) for r in rows if r["event"] == "attempt_finished"):
        raise RuntimeError("HTTP attempt has unknown cost; reconcile before resume")
    return Counter(k for k, _ in starts), len(starts), sum(r.get("known_cost_usd", 0) for r in rows)


class Jev(legacy.Jev):
    def __init__(self, budget, attempt_limit, output):
        super().__init__(budget, attempt_limit)
        self.ledger_path = output / "jev_attempts.jsonl"

    def ask(self, body, key):
        per_job, attempted, cost = ledger_state(read_jsonl(self.ledger_path))
        already = per_job[key]
        if any(r["event"] == "attempt_finished" and r["job_key"] == key and r.get("http_status") == 200 for r in read_jsonl(self.ledger_path)):
            raise RuntimeError("Successful HTTP attempt without cached terminal record; reconcile before another call")
        if already >= 2:
            raise RuntimeError("Persistent per-job HTTP attempt cap reached")
        started, attempts = time.perf_counter(), 0
        terminal = {"ok": False, "error": "not_started"}
        for number in range(already + 1, 3):
            if attempted >= self.attempt_limit or cost >= self.budget:
                raise RuntimeError("API attempt/cost stop threshold reached")
            attempted += 1
            attempts += 1
            append_jsonl(self.ledger_path, {"event": "attempt_started", "job_key": key, "attempt": number, "ts_utc": legacy.utc()})
            status, data = None, None
            try:
                response = self.http.post("https://api.typesafe.ai/v1/systemone", json=body,
                    headers={"Authorization": "Bearer " + self.key, "Content-Type": "application/json"})
                status = response.status_code
                if status == 200:
                    data = self.safe_response(response.json())
            except Exception as exc:
                terminal = {"ok": False, "error": type(exc).__name__}
            tokens = (data or {}).get("usage", {}).get("input_tokens") if isinstance(data, dict) else None
            known = isinstance(tokens, int) and not isinstance(tokens, bool) and tokens >= 0
            known_cost = tokens * legacy.PRICE_PER_TOKEN if known else 0
            cost += known_cost
            append_jsonl(self.ledger_path, {"event": "attempt_finished", "job_key": key, "attempt": number,
                "http_status": status, "input_tokens": tokens if known else None, "cost_known": known,
                "known_cost_usd": known_cost, "ts_utc": legacy.utc()})
            if status == 200:
                try:
                    answer = data["answers"]["decision"]
                    probs, letter = answer["probabilities"], answer["choice"]
                    semantic_probs(probs, "cancel_first")
                    if data["model"] != "jev-1.13.0" or answer["type"] != "choice" or probs[letter] < max(probs.values()) - 1e-6:
                        raise ValueError("Invalid served model or choice")
                    terminal = {"ok": True, "letter": letter, "letter_probabilities": probs,
                        "served_model": data["model"], "raw_response": data, "input_tokens": tokens if known else None}
                except (KeyError, TypeError, ValueError, AssertionError) as exc:
                    terminal = {"ok": False, "error": "response_validation:" + type(exc).__name__, "raw_response": data}
                break
            terminal = {"ok": False, "error": "http_" + str(status) if status else terminal["error"]}
            # Failed requests with absent usage have an unknown charge; stop rather
            # than treating that cost as zero or silently retrying across restarts.
            if not known or status not in (408, 429, 500, 502, 503, 504, 529):
                break
            if number < 2:
                time.sleep(1)
        terminal.update(latency_s=time.perf_counter() - started, http_attempts=attempts)
        return terminal


def execute(args, backend_factory=None):
    manifest = legacy.verify_manifest()
    verify_fingerprint(manifest)
    output = Path(args.output).resolve()
    published = (legacy.ROOT / "results").resolve()
    if output == published or published in output.parents:
        raise ValueError("Use a fresh output directory outside published results/")
    cases = read_jsonl(legacy.ROOT / ("data/cases.jsonl" if args.phase == "formal" else "data/smoke.jsonl"))
    jobs = []
    for rep in ([0, 1] if args.phase == "formal" else [0]):
        batch = [(c, m, rep) for c in cases for m in (MAPPINGS if args.phase == "formal" else ["cancel_first"])]
        random.Random(SEED + rep).shuffle(batch)
        jobs.extend(batch)
    if args.limit:
        jobs = jobs[:args.limit]
    record_path = output / f"{args.backend}_{args.phase}.jsonl"
    previous = read_jsonl(record_path)
    old = {r["job_key"]: r for r in previous}
    if len(old) != len(previous):
        raise ValueError("Duplicate terminal jobs")
    allowed = {job_key(manifest["config_hash"], c["id"], m, rep): (c, m, rep) for c, m, rep in jobs}
    for row in previous:
        if row["config_hash"] != manifest["config_hash"] or not row["ok"] or row["job_key"] not in allowed:
            raise ValueError("Foreign or failed cached record; do not silently rerun/select attempts")
        case, mapping, rep = allowed[row["job_key"]]
        verify_row(row, case, manifest, args.backend, args.phase)
        if row["request"] != request_for(case, mapping) or row["request_sha256"] != digest(canonical(row["request"]).encode()):
            raise ValueError("Cached request mismatch")
    pending = [(c, m, rep) for c, m, rep in jobs if job_key(manifest["config_hash"], c["id"], m, rep) not in old]
    status = {"jobs": len(jobs), "cached": len(previous), "pending": len(pending), "backend": args.backend,
              "smoke_sha256": legacy.sha_file(legacy.ROOT / "data/smoke.jsonl"), "config_hash": manifest["config_hash"]}
    if args.dry_run or not pending:
        print(json.dumps(status))
        return status
    output.mkdir(parents=True, exist_ok=True)
    lock = output / ".replication.lock"
    with lock.open("x", encoding="utf-8") as stream:
        stream.write(legacy.utc())
    try:
        session = output / "sessions" / (legacy.utc().replace(":", "-") + "-" + uuid.uuid4().hex[:8])
        session.mkdir(parents=True)
        settings = {**status, "phase": args.phase, "budget_stop_usd": args.budget, "http_attempt_limit": args.attempt_limit,
                    "runner_sha256": legacy.sha_file(Path(__file__)), "started_at_utc": legacy.utc()}
        settings["session_config_hash"] = digest(canonical(settings).encode())
        (session / "manifest.json").write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
        factory = backend_factory or (lambda: Jev(args.budget, args.attempt_limit, output) if args.backend == "jev" else legacy.Qwen(None))
        backend = factory()
        (session / "runtime.json").write_text(json.dumps(backend.runtime, indent=2) + "\n", encoding="utf-8")
        for case, mapping, rep in pending:
            key = job_key(manifest["config_hash"], case["id"], mapping, rep)
            body = request_for(case, mapping)
            row = {"backend": args.backend, "phase": args.phase, "case_id": case["id"], "parent_id": case["parent_id"],
                   "variant": case["variant"], "family": case["family"], "mapping": mapping, "replicate": rep,
                   "config_hash": manifest["config_hash"], "job_key": key, "request": body,
                   "request_sha256": digest(canonical(body).encode()), "ts_utc": legacy.utc(), "session": session.name}
            row.update(backend.ask(body, key))
            if row["ok"]:
                row["prediction"] = MAPPINGS[mapping][row["letter"]]
                row["probabilities"] = semantic_probs(row["letter_probabilities"], mapping)
            append_jsonl(record_path, row)
            if not row["ok"]:
                raise RuntimeError("Stopped on instrument/service failure: " + row.get("error", "unknown"))
        if args.backend == "qwen":
            backend.runtime["peak_allocated_mib"] = backend.torch.cuda.max_memory_allocated() / 1024**2
        backend.runtime["completed_at_utc"] = legacy.utc()
        (session / "runtime.json").write_text(json.dumps(backend.runtime, indent=2) + "\n", encoding="utf-8")
        return status
    finally:
        lock.unlink(missing_ok=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", choices=["jev", "qwen"], required=True)
    parser.add_argument("--phase", choices=["smoke", "formal"], default="formal")
    parser.add_argument("--output", required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--budget", type=float, default=1.0)
    parser.add_argument("--attempt-limit", type=int, default=400)
    parser.add_argument("--dry-run", action="store_true")
    options = parser.parse_args()
    if not 0 < options.budget <= 1 or not 0 < options.attempt_limit <= 400 or (options.limit is not None and options.limit <= 0):
        parser.error("budget must be in (0,1], attempt limit in [1,400], and limit positive")
    execute(options)
