"""Read-only checks of the finite screen and canonical software reproduction."""
from __future__ import annotations

from collections import Counter
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_external_sources(sources, source_dir=None):
    """A manifest is prior provenance; only an explicit directory is rechecked."""
    files = sources["files"]
    report = {
        "manifest_files": len(files),
        "manifest_bytes": sum(source["bytes"] for source in files),
        "source_cache_rechecked": False,
        "files_verified": 0,
        "bytes_verified": 0,
        "note": "External source cache was not reopened; manifest provenance only.",
    }
    if source_dir is None:
        return report
    source_dir = Path(source_dir)
    if not source_dir.is_dir():
        raise FileNotFoundError(f"Explicit source directory is missing: {source_dir}")
    for source in files:
        path = source_dir / source["path"]
        if not path.is_file():
            raise FileNotFoundError(f"Missing external source: {source['path']}")
        if path.stat().st_size != source["bytes"]:
            raise ValueError(f"External source size mismatch: {source['path']}")
        if digest(path) != source["sha256"]:
            raise ValueError(f"External source SHA-256 mismatch: {source['path']}")
        report["files_verified"] += 1
        report["bytes_verified"] += source["bytes"]
    report["source_cache_rechecked"] = True
    report["note"] = "Every external source in the manifest was reopened and checked."
    return report


def main(source_dir=None):
    selection = read(ROOT / "selection.json")
    assert selection["protocol_sha256"] == digest(ROOT / "PROTOCOL.md")
    decisions = read(ROOT / "decisions.json")
    assert [row["id"] for row in decisions["pairs"]] == selection["selected_pair_ids"]
    counts = Counter(row["disposition"] for row in decisions["pairs"])
    assert all(counts[key] == value for key, value in decisions["counts"].items())
    sources = read(ROOT / "sources.json")
    source_verification = verify_external_sources(sources, source_dir)
    assert sources["selected_pairs"] == selection["selected_pair_ids"]

    atomicity = ROOT / "atomicity-repro"
    shipped_source_counts = {}
    for base in (atomicity, ROOT.parent / "integration"):
        shipped_sources = read(base / "sources.json")
        for source in shipped_sources:
            path = base / source["file"]
            assert path.stat().st_size == source["bytes"], source["file"]
            assert digest(path) == source["sha256"], source["file"]
        shipped_source_counts[base.name] = len(shipped_sources)
    frozen_counts = {}
    fix = atomicity / "proposed-fix"
    for base in (atomicity, fix, ROOT.parent / "integration", ROOT.parent):
        frozen = read(base / "freeze.json")["sha256"]
        for name, expected in frozen.items():
            assert digest(base / name) == expected, name
        frozen_counts[base.name] = len(frozen)

    initial = read(atomicity / "upstream/initial_state.json")
    original_attempts = 0
    original_errors = 0
    for attempt in ("attempt-001", "attempt-002"):
        summary = read(atomicity / "results" / attempt / "summary.json")
        original_attempts += summary["tool_attempts"]
        original_errors += summary["expected_tool_errors"]
        assert summary["model_calls"] == 0
        assert all(event["host"] in {"127.0.0.1", "::1", "localhost"}
                   for event in summary["network_audit_events"])
    expected = {
        "no_action": (0, 0, False, True),
        "privacy_only": (2, 0, False, False),
        "invalid_visibility_with_bio": (2, 1, True, True),
        "invalid_visibility_without_bio": (2, 1, False, True),
    }
    for name, (calls, errors, changed, passed) in expected.items():
        case = read(atomicity / "results/attempt-002" / (name + ".json"))
        assert case["state_before"] == initial, name
        assert len(case["controller_calls"]) == calls
        assert sum(not event["success"] for event in case["controller_calls"]) == errors
        assert case["public_bio_changed"] is changed
        assert case["isolated_native_commit_check"]["pass"] is passed
        if changed:
            assert case["state_after"]["profile"]["public_bio"] == initial["profile"]["saved_bio_draft"]
    assert (original_attempts, original_errors) == (12, 4)
    fixed_events = []
    for attempt in ("attempt-001", "attempt-002", "portable-staged-001"):
        fixed_events.extend(json.loads(line)["event"] for line in
                            (fix / "results" / attempt / "attempts.jsonl").read_text(encoding="utf-8").splitlines())
    assert len(fixed_events) == 20
    assert sum(not event["success"] for event in fixed_events) == 5
    fixed_summary = read(fix / "results/attempt-002/summary.json")
    assert fixed_summary["all_case_checks_pass"] is True
    assert fixed_summary["both_invalid_cases_complete_state_unchanged"] is True
    assert fixed_summary["model_calls"] == 0
    portable_frozen = read(fix / "portable-freeze.json")
    for name, expected in portable_frozen["sha256"].items():
        assert digest(fix / name) == expected, name
    portable = read(fix / "portability-checks/staged-001/verification.json")
    assert portable["bytecode_before"] == [] and portable["bytecode_after"] == []
    assert portable["execution_return_code"] == 0
    for item in portable["collected_results"]:
        assert digest(REPO / item["collected_path"]) == item["sha256"]
    print(json.dumps({
        "status": "pass",
        "selected_pairs": len(decisions["pairs"]),
        "decisions": decisions["counts"],
        "external_source_verification": source_verification,
        "shipped_source_files_verified": shipped_source_counts,
        "frozen_hash_counts": frozen_counts,
        "canonical_states_equal_utf8_source": 4,
        "original_environment_attempts_all_runs": original_attempts,
        "original_environment_expected_errors_all_runs": original_errors,
        "derivative_environment_attempts_all_runs": len(fixed_events),
        "derivative_expected_tool_errors_all_runs": 5,
        "derivative_preserved_harness_assertion_failures": 1,
        "canonical_derivative_cases_passed": fixed_summary["scripted_resets"],
        "all_software_reproduction_tool_attempts": original_attempts + len(fixed_events),
        "portable_staged_replay_tool_attempts": portable["new_tool_attempts"],
        "portable_staged_inputs_unchanged": portable["copied_input_files_unchanged"],
        "portable_staged_bytecode_absent_before_and_after": True,
        "model_calls_added": 0,
        "note": "Checks saved sources, selected counts and recorded runs; executes no environment or model."
    }, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-dir", type=Path,
        help="Optional AgentAbstain dataset cache root; requires all manifest files to match.",
    )
    main(parser.parse_args().source_dir)
