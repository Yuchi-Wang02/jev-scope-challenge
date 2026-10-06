"""Free provider input-token counting only; never calls message generation."""
from __future__ import annotations

import datetime
import hashlib
import json
import os
from pathlib import Path
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parent
ENDPOINT = "https://api.anthropic.com/v1/messages/count_tokens"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def main():
    plan_path = ROOT / "requests.json"
    output = ROOT / "token_counts.json"
    journal = ROOT / "token_count_attempts.jsonl"
    if output.exists() or journal.exists():
        raise SystemExit("Preserve prior token-count preparation; do not overwrite or retry silently.")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    jobs = plan["jobs"]
    assert len(jobs) == 222
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise SystemExit("ANTHROPIC_API_KEY is required for token counting; no key value logged.")
    opener = urllib.request.build_opener(NoRedirect)
    rows = []
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    for index, job in enumerate(jobs, 1):
        payload = {name: job["payload"][name] for name in ("model", "messages", "thinking", "output_config")}
        raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        record = {"job_id": job["job_id"], "phase": "free_input_token_count",
                  "count_request_sha256": hashlib.sha256(raw).hexdigest(),
                  "model_generations": 0}
        started_request = time.perf_counter()
        request = urllib.request.Request(ENDPOINT, data=raw, method="POST", headers={
            "x-api-key": key, "anthropic-version": "2023-06-01",
            "Content-Type": "application/json", "Accept": "application/json"})
        try:
            with opener.open(request, timeout=30) as response:
                result = json.load(response)
                value = result.get("input_tokens")
                if type(value) is not int or value <= 0:
                    raise ValueError("Invalid token-count response schema")
                record.update(http_status=response.status, input_tokens=value,
                              request_id=response.headers.get("request-id"), raw_response=result)
        except Exception as exc:
            record.update(error_type=type(exc).__name__, http_status=getattr(exc, "code", None))
            record["seconds"] = time.perf_counter() - started_request
            with journal.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(record) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
            raise SystemExit("Token-count preparation stopped; preserved status only, no generation or retry.") from None
        record["seconds"] = time.perf_counter() - started_request
        with journal.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        rows.append(record)
        if index == 1 or index % 25 == 0 or index == len(jobs):
            print(json.dumps({"counted": index, "planned": len(jobs), "model_generations": 0}), flush=True)
    total = sum(row["input_tokens"] for row in rows)
    result = {"model": "claude-sonnet-5-5", "endpoint": ENDPOINT,
              "started_at_utc": started, "model_generations": 0,
              "requests_sha256_lf": hashlib.sha256(plan_path.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
              "counts": rows, "estimated_input_tokens": total,
              "reserved_input_tokens": total + 2048 * len(rows),
              "note": "Free token-count estimates, not actual generation usage; generation max_tokens is not a count endpoint field."}
    assert result["reserved_input_tokens"] <= 600000
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
