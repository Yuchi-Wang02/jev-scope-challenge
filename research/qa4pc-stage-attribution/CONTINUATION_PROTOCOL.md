# Outcome-aware Qwen continuation: semantic smoke results are observations

2026-09-30. This amendment is written after the original second smoke failure
and after all Jev results were inspected, but before any Qwen main output exists.
It does not replace the [original protocol](PROTOCOL.md), [stopped journal](results/qwen.jsonl)
or [original report](RESULTS.md). This is not an untouched confirmatory comparison.

## Rationale and exact change

The original gate conflated valid, accountable model output with correct target
reasoning. Qwen's no-OR-no response was well formed and selected a unique legal
letter, but wrong. Retain that failure and change only the continuation's gate:
semantic smoke accuracy is recorded, not a reason to stop an otherwise valid
measurement. Do not change prompts, tokenizer, model, precision, graph help,
source cases, letter mappings, candidate logits or main scoring.

The original backend is reused without editing it. For the four remaining smoke
jobs, the wrapper changes only the internal phase marker passed to the backend,
so its historical semantic gate is not applied. The model input/token sequence
is identical to the original frozen job. The new journal keeps the original job
ID and records expected/observed smoke actions under the amended gate policy.
Model/usage/schema errors, nonfinite logits, physical-forward count errors,
unknown usage and unresolved calls still stop. Exact ties remain invalid
decisions; they are not repaired using labels or new precision.

## Jobs and accounting

Verify the original journal has exactly the first two planned Qwen jobs, one
correct semantic smoke and the preserved second-smoke failure, with no active
session or unmatched call. The successor contains exactly the remaining original
260 Qwen jobs, in their original order: four smoke and 256 main. Every successor
job hash must equal its original hash. No Jev requests, no replay of the two
completed Qwen jobs, no new cases or warmups, no generation and no automatic retry.

Separate limits: 260 physical prefills, 77,150 input tokens, zero generated
tokens, 32,768 tokens per context and 600 callback-session seconds. Aggregate
original plus successor: 262 prefills and 77,528 planned input tokens. Report both
model loads and verification times; do not hide restart overhead. A stopped
successor cannot be restarted under another directory to bypass its journal.

Publish the exact successor manifest, original hashes, code pins and protocol
before running. Use a distinct named successor journal, never append new sessions
to the originally halted journal or reclassify its failure as successful.

## Analysis and stopping

Replay original and successor journals separately against their own plan hashes.
Their job sets must be disjoint and their union must equal the original Qwen job
set when complete. Keep original smoke failure status; combine only the records
for reporting coverage, main metrics and total costs. Original Jev results are
shared, not rerun or charged twice. Preserve any invalid main decisions in all
24-scenario denominators. Trees remain the 12 units, mappings are repeated measures.

Retain the same D/G/F/L source-agreement metrics and limitations. This amendment
does not authorize prompt searches or another same-cohort rescue. Stop after
this single successor grid, report all observations, and reassess next research
steps from the completed comparison and remaining semantic/cost limitations.
