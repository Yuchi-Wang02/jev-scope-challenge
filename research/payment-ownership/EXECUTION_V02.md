# v0.2 execution amendment — after smoke, before all main requests

Date: 2026-09-30. Original data, protocol, request list and implementation freeze
remain unchanged at `0569f8d`. See [the v0.1 stop audit](SMOKE_AUDIT.md).

**Outcome-aware amendment:** the agent inspected six smoke outputs, including the
ambiguous-target error, before writing this amendment. Zero main-grid outputs had
been observed. This is exploratory execution, not an unchanged preregistration.

Replace only the all-six-semantically-correct launch prerequisite with: all six
predeclared smoke jobs must have successful HTTP/schema/model/usage validation.
Wrong semantic answers are scored and retained. The observed 5/6 smoke score does
not become 6/6. There are no new smoke inputs, reruns, prompt changes or exclusions.

The exact same 192 primary request bodies, scheduling, source data, labels,
candidate mappings, analysis and main-grid continuation rule remain frozen.
The budget is shared with the original six attempts: <=405 total attempts,
<=15 retries and <=2,000,000 planned input units, not a restarted budget.
`run_api_v02.py` is a versioned copy of the original runner with the revised
prerequisite, execution identity recording and an additional amendment hash check.
It preserves append-only ledgers, response validation and interruption safeguards.

`execution_v02.json` freezes this amendment and the new runner, records hashes of
the stopped six-response snapshot, and verifies the prior data/code freeze before
any new call. The amendment and stopped outputs must be committed publicly before
running the main grid. No additional per-batch approval is needed under the user's
explicit authorization for bounded Jev research; this is not authorization for an
unbounded search or for bypassing a real data/API integrity failure.

The primary comparison still cannot confirm missing-evidence or ambiguity handling:
all 48 main references are determined. The independent ambiguous smoke failure must
remain visible even if every main request succeeds. Human review remains pending.
