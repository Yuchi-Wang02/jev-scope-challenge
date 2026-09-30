# Comparison execution core: implemented, not yet used on the task

2026-09-30. The [runner](run_comparison.py), [journal](execution_journal.py) and
[backend factories](comparison_backends.py) now implement the prospective
execution path. Tests use synthetic callbacks and records, not model outputs.
**No real ShARC reviews, execution freeze or task run have been created.**

## Execution gate

The CLI first requires committed `EXECUTION_FREEZE.json` and
`EXECUTION_PROTOCOL.md` in this directory, plus a clean checkout. Those files
do not exist yet. There is no force/skip flag. This is the research gate already
adopted by the project, not a new request for user spending permission.

The future freeze must contain `status: frozen_for_execution`, the compiler's
study ID, exact plan/reference hashes, normalized-LF hashes for the complete
`SOURCE_FILES` inventory in the runner, and the execution protocol's normalized
hash. The CLI rechecks saved reviewer forms, reconciliation, adjudication,
reserves and real tokenizer output through the existing compiler, then compares
the result byte-for-byte with the plan/reference files. A status flag alone
does not open inference. Hashes do not independently certify human truth.

Only after these checks can the backend factory load a credential or weights.
Outputs have one deterministic private directory per plan hash. Each backend
has its own journal and operating-system lock. There is no arbitrary CLI output
path that could accidentally start a second copy of the same run elsewhere.
Deliberate code changes or manual file deletion are outside this protection.

## Durable call history and safe resumption

The runner appends JSONL records and flushes/fsyncs each record:

1. A header binds the backend, ordered job IDs and exact plan hash.
2. A session start records backend/runtime setup metadata.
3. A call start is saved **before** the callback can send a request or generate.
4. A call finish preserves the returned record, action, usage and elapsed time.
5. A session end records generation-session wall time, including loop overhead.

A complete recorded run resumes as a no-op. A closed partial session resumes
only jobs with no prior start. Previously accumulated usage and session time
carry forward; restarting does not replenish the budget.

An unmatched call start is ambiguous: the server or GPU may have performed work.
It is never automatically repeated. An unclosed session also stops because its
wall time is unaccounted for. Partial journal tails, repeated/out-of-order calls,
foreign plan hashes and invalid result records stop for investigation. Existing
files are not truncated, repaired or reset. A process crash releases the OS lock;
the remaining lock file does not itself imply an active process. Recovery from
an ambiguous interruption requires a documented disposition, not an automatic
retry or a fresh output directory.

## Budget and failure semantics

Every call start consumes an attempt. The HTTP transport has zero retries and
does not follow redirects. The runner checks total attempts and known input
usage before each call. For local generation it also reserves the next input
and full output cap against remaining work limits. Total session time carries
across clean resumes; backend loading and verification are recorded separately
on successful setup and excluded from the generation-session deadline.

The local backend checks the remaining deadline at generation token boundaries.
These checks are not real-time scheduling guarantees. Any recorded input or time
overrun is reported explicitly; `complete` means every planned result exists,
not that every budget was respected. Jev usage is known only after a response,
so a single response can cross its stage input limit. No further request follows.
Missing usage is reported as unknown and halts the stage; it is never converted
to a proved zero cost.

No reference label is passed to the execution loop or backend factory. A wrong
semantic answer cannot trigger selective stopping. An ordinary Qwen malformed
final answer or truncation records a null action and counts as a failed output,
while the grid continues if budget remains. A Jev response-schema/version error,
backend adapter invariant failure or execution/transport error stops the run.
Every returned token sequence survives local adapter rejection. Invalid API JSON
is preserved as redacted text; duplicate keys and nonfinite values are rejected.
Headers and exception messages are never journaled. Exceptions record their
type only, since transport messages can contain request credentials.

If the process fails before a callback returns, a partial token stream or server
usage may be unavailable. The journal records uncertainty rather than inventing
an output. A backend setup exception occurs before session/call start; the CLI
reports the failing stage and exception type, but failed-setup duration is not
yet part of the durable journal. Do not count a header-only journal as inference.

## Local and API backend scope

Jev uses the existing four-action request/response adapter and checks the served
version and probability/usage fields. Qwen rechecks every pinned model file,
runtime versions, prompt rendering, input IDs, BF16 placement, sampling settings,
generated-token presence penalty and actual processor order. It saves generated
token IDs, completion/final extraction, configuration, timing and stage peak
memory. No warm-up forward, model download or remote code is added.

The earlier [technical smoke](../action-backends/README.md) supplies live evidence
for the underlying interfaces. It does not prove this new orchestrator has run
successfully. This stage has **zero new HTTP attempts and zero model forwards**.

## Checks performed and remaining work

Fourteen targeted software tests cover completed and partial resumption,
interruption after start, corrupt/partial records, concurrent locks, unknown
usage, input/time/output limits, schema failure, malformed JSON, and the committed
freeze/recompiled-plan gate. Synthetic null-action results demonstrate that
ordinary bad outputs do not selectively stop the grid.

The full task remains closed until independent review, human adjudication,
exact-cohort tokenization and a separately published execution freeze. The
cross-condition [result analyzer](ANALYSIS_CONTRACT.md) now verifies a common
cohort, extracts predictions from journals, scores all five controls, and preserves
incomplete grids and resource limits alongside scores. Final freeze/publication
checks and a live task run remain outstanding. Do not present callback tests or
offline historical-record replay as task evaluation.

```bash
python -m unittest discover -s tests -p test_rule_execution_journal.py -v
python -m unittest discover -s tests -p test_rule_comparison_runner.py -v
```
