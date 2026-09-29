"""Execute the frozen probe. API keys are read only from the environment."""
from __future__ import annotations
import argparse
import datetime as dt
import importlib.metadata
import json
import os
import platform
import random
import re
import time
from pathlib import Path
from core import (MAPPINGS, PRICE_PER_TOKEN, QWEN_REVISION, SEED, append_jsonl, canonical,
                  digest, job_key, read_jsonl, request_for, semantic_probs, user_prompt, validate_cases)

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "manifest.json"

def utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()

def sha_file(path: Path) -> str:
    return digest(path.read_bytes())

def versions() -> dict:
    out = {"python": platform.python_version(), "os": platform.platform()}
    for name in ("httpx", "numpy", "torch", "transformers", "accelerate", "matplotlib"):
        try:
            out[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            out[name] = None
    return out

def freeze() -> None:
    cases = read_jsonl(ROOT / "data/cases.jsonl")
    validation = validate_cases(cases)
    payload = {"experiment": "jev-scope-challenge-v0.1", "seed": SEED,
        "data_sha256": sha_file(ROOT / "data/cases.jsonl"),
        "core_sha256": sha_file(ROOT / "core.py"), "runner_sha256": sha_file(ROOT / "run.py"),
        "analysis_sha256": sha_file(ROOT / "analyze.py"),
        "protocol_sha256": sha_file(ROOT / "PROTOCOL.md"),
        "qwen_model": "Qwen/Qwen3-4B", "qwen_revision": QWEN_REVISION,
        "jev_model": "jev-1.13.0", "thinking": False, "dtype": "bfloat16",
        "qwen_readout": "bare A/B single-token logits; conditional softmax",
        "candidate_mappings": MAPPINGS, "replicates": [0,1], "primary_replicate": 0,
        "validation": validation, "human_reviewed": False,
        "label_provenance": "Rule-constructed; AI reviewed; no independent human label audit",
        "api_price_usd_per_million_input_tokens": 0.042,
        "price_source": "https://docs.typesafe.ai/models", "budget_stop_usd": 1,
        "http_attempt_limit": 400, "max_attempts_per_job": 2}
    payload["config_hash"] = digest(canonical(payload).encode())
    payload["frozen_at_utc"] = utc()
    if MANIFEST.exists():
        old = json.loads(MANIFEST.read_text(encoding="utf-8"))
        if old["config_hash"] != payload["config_hash"]:
            raise RuntimeError("Existing freeze differs. Do not silently replace a preregistration.")
        print("Freeze unchanged: " + old["config_hash"])
        return
    MANIFEST.write_text(json.dumps(payload, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))

def verify_manifest() -> dict:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for file, key in [("data/cases.jsonl", "data_sha256"), ("core.py", "core_sha256"),
                      ("run.py", "runner_sha256"), ("analyze.py", "analysis_sha256"),
                      ("PROTOCOL.md", "protocol_sha256")]:
        if sha_file(ROOT/file) != manifest[key]:
            raise RuntimeError("Frozen file changed: " + file)
    validate_cases(read_jsonl(ROOT/"data/cases.jsonl"))
    return manifest

class Jev:
    def __init__(self, budget: float, attempt_limit: int):
        import httpx
        self.key = os.environ.get("TYPESAFE_API_KEY", "")
        if not self.key:
            raise RuntimeError("Set TYPESAFE_API_KEY in your environment")
        self.http = httpx.Client(timeout=45)
        self.ledger_path = ROOT/"results/jev_attempts.jsonl"
        self.budget = min(budget, 1.0)
        self.attempt_limit = min(attempt_limit, 400)
        self.runtime = versions()

    def safe_response(self, data):
        if isinstance(data, dict):
            return {k:self.safe_response(v) for k,v in data.items()
                    if k.lower() not in {"authorization", "headers", "api_key", "apikey"}}
        if isinstance(data, list):
            return [self.safe_response(v) for v in data]
        if isinstance(data, str):
            data = data.replace(self.key, "[REDACTED]")
            return re.sub(r"apikey_[A-Za-z0-9_]+", "[REDACTED]", data)
        return data

    def ask(self, body: dict, key: str) -> dict:
        attempt_logs = read_jsonl(self.ledger_path)
        attempted = sum(r["event"] == "attempt_started" for r in attempt_logs)
        cost = sum(r.get("known_cost_usd", 0) for r in attempt_logs)
        started = time.perf_counter()
        attempts = 0
        terminal = {"ok": False, "error": "not_started"}
        for i in range(2):
            if attempted >= self.attempt_limit or cost >= self.budget:
                raise RuntimeError("API attempt/cost stop threshold reached")
            attempted += 1
            attempts += 1
            append_jsonl(self.ledger_path, {"event":"attempt_started", "job_key":key,
                         "attempt":i+1, "ts_utc":utc()})
            status, data = None, None
            try:
                response = self.http.post("https://api.typesafe.ai/v1/systemone", json=body,
                    headers={"Authorization":"Bearer " + self.key, "Content-Type":"application/json"})
                status = response.status_code
                if status == 200:
                    data = self.safe_response(response.json())
            except Exception as exc:
                # Only exception type is persisted, never a request/credential dump.
                terminal = {"ok":False, "error":type(exc).__name__}
            usage = (data or {}).get("usage", {}) if isinstance(data,dict) else {}
            tokens = usage.get("input_tokens")
            known = isinstance(tokens,int) and tokens >= 0
            known_cost = tokens*PRICE_PER_TOKEN if known else 0
            cost += known_cost
            append_jsonl(self.ledger_path, {"event":"attempt_finished", "job_key":key,
                "attempt":i+1, "http_status":status, "input_tokens":tokens if known else None,
                "cost_known":known, "known_cost_usd":known_cost, "ts_utc":utc()})
            if status == 200:
                try:
                    assert data["model"] == "jev-1.13.0", "served_model_mismatch"
                    a = data["answers"]["decision"]
                    assert a["type"] == "choice"
                    probs = a["probabilities"]
                    semantic_probs(probs, "cancel_first")
                    letter = a["choice"]
                    assert letter in probs
                    assert probs[letter] >= max(probs.values())-1e-6
                    terminal = {"ok":True, "letter":letter, "letter_probabilities":probs,
                        "served_model":data["model"], "raw_response":data,
                        "input_tokens":tokens if known else None}
                except (KeyError,TypeError,AssertionError) as exc:
                    terminal = {"ok":False, "error":"response_validation:"+type(exc).__name__,
                                "raw_response":data}
                break
            if status is not None:
                terminal = {"ok":False, "error":"http_"+str(status), "http_status":status}
            if status in (401,403) or (status and status not in (408,429,500,502,503,504,529)):
                break
            if i == 0:
                time.sleep(1)
        terminal.update({"latency_s":time.perf_counter()-started, "http_attempts":attempts})
        return terminal

class Qwen:
    def __init__(self, model_path: str | None):
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM
        self.torch = torch
        torch.manual_seed(SEED)
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        self.runtime = versions()
        start = time.perf_counter()
        if model_path:
            source = model_path
            kwargs = {"local_files_only":True}
        else:
            source = "Qwen/Qwen3-4B"
            kwargs = {"revision":QWEN_REVISION}
        self.tok = AutoTokenizer.from_pretrained(source, **kwargs)
        self.model = AutoModelForCausalLM.from_pretrained(source, torch_dtype=torch.bfloat16,
                                                         device_map="cuda", **kwargs).eval()
        torch.cuda.synchronize()
        self.runtime.update({"gpu":torch.cuda.get_device_name(0), "cuda":torch.version.cuda,
            "model_load_s":time.perf_counter()-start, "tf32":False,
            "chat_template_sha256":digest(self.tok.chat_template.encode()),
            "tokenizer_config_sha256":digest(json.dumps(self.tok.init_kwargs,sort_keys=True,default=str).encode()),
            "candidate_ids":{x:self.tok.encode(x, add_special_tokens=False) for x in ["A","B"," A"," B"]}})
        # A directory override must actually be the pinned snapshot, not another model.
        if model_path and Path(model_path).name != QWEN_REVISION:
            raise RuntimeError("Local path must name the pinned Qwen snapshot")
        for x in ["A","B"," A"," B"]:
            assert len(self.runtime["candidate_ids"][x]) == 1

    def ask(self, body: dict, key: str) -> dict:
        torch = self.torch
        start = time.perf_counter()
        prompt = self.tok.apply_chat_template([{"role":"user", "content":user_prompt(body)}],
            tokenize=False, add_generation_prompt=True, enable_thinking=False)
        ids = self.tok.encode(prompt, add_special_tokens=False)
        for x in ["A","B"]:
            continuation = self.tok.encode(prompt+x, add_special_tokens=False)
            assert continuation[:-1] == ids and continuation[-1] == self.runtime["candidate_ids"][x][0], "candidate boundary mismatch"
        enc = self.tok(prompt, return_tensors="pt", add_special_tokens=False).to("cuda")
        torch.cuda.synchronize()
        with torch.inference_mode():
            logits = self.model(**enc).logits[0,-1,:].float()
            candidate_ids = [self.runtime["candidate_ids"][x][0] for x in ["A","B"]]
            chosen_logits = logits[candidate_ids]
            conditional = torch.softmax(chosen_logits, dim=-1)
            full = torch.softmax(logits, dim=-1)
            probs = {x:float(conditional[i].item()) for i,x in enumerate(["A","B"])}
            raw = {x:float(full[self.runtime["candidate_ids"][x][0]].item()) for x in ["A","B"," A"," B"]}
            mass = raw["A"] + raw["B"]
            assert mass > 0 and bool(torch.isfinite(chosen_logits).all()), "invalid candidate mass"
            letter = max(probs, key=probs.get)
            values = {x:float(chosen_logits[i].item()) for i,x in enumerate(["A","B"])}
        torch.cuda.synchronize()
        return {"ok":True, "letter":letter, "letter_probabilities":probs,
                "served_model":"Qwen/Qwen3-4B@"+QWEN_REVISION,
                "input_tokens":len(ids), "latency_s":time.perf_counter()-start,
                "candidate_mass":mass, "raw_token_probabilities":raw,
                "candidate_logits":values, "prompt_sha256":digest(prompt.encode()),
                "prompt":prompt, "low_mass":mass < 0.01}

def run(args) -> None:
    manifest = verify_manifest()
    cases = read_jsonl(ROOT/("data/cases.jsonl" if args.phase == "formal" else "data/smoke.jsonl"))
    jobs=[]
    for replicate in ([0,1] if args.phase == "formal" else [0]):
        round_jobs=[(case,mapping,replicate) for case in cases
                    for mapping in (MAPPINGS if args.phase == "formal" else ["cancel_first"])]
        random.Random(SEED+replicate).shuffle(round_jobs)
        jobs.extend(round_jobs)
    if args.limit:
        jobs=jobs[:args.limit]
    if args.dry_run:
        print(json.dumps({"backend":args.backend,"phase":args.phase,"jobs":len(jobs),
            "max_http_attempts":len(jobs)*2 if args.backend == "jev" else 0,
            "config_hash":manifest["config_hash"],"sample_request":request_for(jobs[0][0],jobs[0][1])},indent=2))
        return
    out_path=ROOT/"results"/(args.backend+"_"+args.phase+".jsonl")
    previous=read_jsonl(out_path)
    old={r["job_key"]:r for r in previous}
    for row in previous:
        assert row["config_hash"] == manifest["config_hash"]
        assert row["ok"], "Failed terminal job exists; do not silently rerun/select successful attempts"
    backend = Jev(args.budget, args.attempt_limit) if args.backend == "jev" else Qwen(args.model_path)
    runtime_path = ROOT/"results"/(args.backend+"_"+args.phase+"_runtime.json")
    runtime_path.write_text(json.dumps({"config_hash":manifest["config_hash"], "started_at_utc":utc(),
        **backend.runtime}, indent=2)+"\n",encoding="utf-8")
    failures=0
    completed=0
    for n,(case,mapping,replicate) in enumerate(jobs,1):
        key=job_key(manifest["config_hash"],case["id"],mapping,replicate)
        if key in old:
            completed+=1
            continue
        body=request_for(case,mapping)
        row={"backend":args.backend,"phase":args.phase,"case_id":case["id"],
             "parent_id":case["parent_id"],"variant":case["variant"],"family":case["family"],
             "mapping":mapping,"replicate":replicate,"config_hash":manifest["config_hash"],
             "job_key":key,"request":body,"request_sha256":digest(canonical(body).encode()),"ts_utc":utc()}
        try:
            result=backend.ask(body,key)
        except Exception as exc:
            result={"ok":False,"error":type(exc).__name__}
        row.update(result)
        if row["ok"]:
            row["prediction"]=MAPPINGS[mapping][row["letter"]]
            row["probabilities"]=semantic_probs(row["letter_probabilities"],mapping)
        append_jsonl(out_path,row)
        completed+=1
        failures+=not row["ok"]
        if n % 12 == 0 or not row["ok"] or n == len(jobs):
            print(f"{args.backend}/{args.phase}: {completed}/{len(jobs)} terminal, failures={failures}",flush=True)
        if not row["ok"] and (args.phase == "smoke" or failures/len(jobs) > 0.05 or
                                 row.get("error","").startswith(("response_validation", "http_401","http_403"))):
            raise RuntimeError("Paused on instrument/service failure: "+row.get("error","unknown"))
    if args.backend == "qwen":
        backend.runtime["peak_allocated_mib"] = backend.torch.cuda.max_memory_allocated()/1024**2
    runtime_path.write_text(json.dumps({"config_hash":manifest["config_hash"],
        "completed_at_utc":utc(), **backend.runtime},indent=2)+"\n",encoding="utf-8")
    print(f"Completed {args.backend}/{args.phase}; {completed} terminal records",flush=True)

if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest="command",required=True)
    sub.add_parser("freeze")
    r=sub.add_parser("run")
    r.add_argument("--backend",choices=["jev","qwen"],required=True)
    r.add_argument("--phase",choices=["smoke","formal"],default="formal")
    r.add_argument("--model-path")
    r.add_argument("--budget",type=float,default=1)
    r.add_argument("--attempt-limit",type=int,default=400)
    r.add_argument("--limit",type=int)
    r.add_argument("--dry-run",action="store_true")
    args=p.parse_args()
    freeze() if args.command == "freeze" else run(args)

