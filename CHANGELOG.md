# Release notes

## 2026-09-30 — sourced payment-ownership Jev exploration

Published the initial 198-request preparation before calls at `0569f8d`. The
original launch prerequisite stopped on the fifth smoke case: an ambiguous target
received VALID with probability 0.97. All six predeclared smoke cases were completed
without reissuing earlier calls, scoring 5/6. The explicit v0.2 execution amendment
and preserved smoke evidence were published at `08fdda6` before any main-grid call.
It changes the prerequisite from perfect semantic accuracy to valid API responses;
main inputs, labels, mappings, scoring and budgets remain unchanged.

Completed 192 main requests on 12 distinct tau-source users /48 constructed views.
All full/related and primary/reversed-mapping cells score 48/48, as does the finite
parser. The main stop rule triggers; zero follow-up calls. Total actual work:
198 HTTP attempts, 245,241 input tokens, zero retries, usage-estimated $0.010300122.
The ambiguity error, outcome-aware amendment and zero independent human annotations
remain visible in the [report](research/payment-ownership/RESULTS_V02.md) and
[replay](docs/payment_ownership_v02.html). Added MIT upstream attribution, a 96-item
review pack, source checks, budget/response tests and offline CI. No weights,
training, new Kev/Laya run, HF upload or general reliability claim.


## 2026-09-29 — series documentation audit and current evidence map

Reorganized the README around the original cancellation study and the latest
completed ownership diagnostic. The research index now separates completed
inference, saved-output/software analyses and prepared but unrun work. Corrected
the fact-execution overview's stale target-switch status and added series-wide
[claims](RESEARCH_CLAIMS.md) and [novelty/reuse](NOVELTY_MATRIX.md) ledgers.
Earlier matched-base ledgers remain study-specific historical records.

This is a documentation update. Scientific sources, inputs, frozen protocols,
raw outputs, derived results, licenses and upstream files are unchanged. No
new inference, training, annotation or experiment design is included. The
current ledgers describe evidence and limits; they do not select a future
paper claim or certify novelty. Older entries below describe their release-time
state and must be read with the later completed-run entry.

## 2026-09-29 — completed target-switch diagnostic

Published the separately approved 500-scientific-forward run plus two warmups
at commit `56a9882e644da003ce602999e37dae5841768ad8`, executed from the frozen
source at `ff8de16f0241b720d14f659b58a7ceaacd2f7100`. Scientific work used
188,797 input tokens on 24 constructed scenes /48 target views with
same-prefix request IDs. Joint routing plus the visible-ID gate completed
23/24 pairs versus 2/24 ungated, reducing false commitments from 7/12 to 0/12.
Direct filtering remained at 2/24 pairs, with four corrections and three
regressions; known-grammar code completed all 24 pairs.

The prewritten directional rule passed. All raw/derived records, fixed methods,
the remaining field error, actual costs and a source-backed figure are in the
[completed report](research/request-ownership/RESULTS.md). New scene instances
reuse inspected policy and sentence grammar; independent human annotations
remain zero. The gated method reuses saved joint outputs and adds no model
forward. No new Jev call, training, download, rewrite or reserved score occurred.
The original preparation and execution protocols preserve their earlier status.

## 2026-09-29 — visible-ID replay and target-switch preparation

Added an explicitly post-hoc visible-text request-ID gate over the saved joint
routes. Correct decisions change from 34/72 to 70/72, with 38 corrections and
two regressions; the original failed screen stays failed. Full known-grammar
code remains 72/72. Published all derived decisions, line gates, field checks,
216 unscored name transformations and 16 software-only contract cases.

The audit exposes a perfect target/distractor prefix shortcut in the original
grammar. New target-switch preparation uses 24 constructed scenes / 48 views
with two same-namespace request IDs and an identical record block within each
pair. Prompts and program references are preparation only, with zero model
outputs or independent human annotations; an execution freeze is still pending.
No historical scientific source or output, paid API, model download, training,
rewrite score or reserved score was changed or added.

## 2026-09-29 — completed joint-route N1 development pilot

Executed the separately approved frozen 514-forward joint/direct union plus two
warmups on cached historical Kev-LoRA N1. Joint reached 34/72 correct, with
11/24 false commitments and 21/48 correct determined decisions, failing both
screen conditions. The call- and input-token-matched direct methods each reached
31/72. All 72 single-direct inputs, logits, candidate probabilities and actions
exactly reproduced the earlier N1 run. The observed scope failure is 60/66
other-request lines assigned target fields, versus 160/162 exact target routes.

Published every raw/derived record, the post-run result report, a static research
figure and an offline/online saved-query viewer. Added raw-result and publication
checks to CI. Frozen scientific source and protocols are unchanged. No training,
new model download, paid API, Jev, packed-line, rewrite or reserved inference ran;
independent human annotations remain zero. UTC execution began on September 30;
the local America/New_York date was September 29.

## 2026-09-29 — cost explorer baseline correction

Added always-defer and the existing visible-text known-grammar parser to the
post-hoc cost explorer. The previous version showed only three saved model
paths and emphasized their pairwise crossover. The line reader never minimizes
loss when only needless deferrals cost one unit; charging all deferrals gives
it a narrow four-path winning range, where the grammar-specific code is cheaper.
Both conventions now have exact rational intervals and boundary ties, with
outcomes and unmatched model budgets visible. No model prediction, frozen
protocol, model call or human annotation was added or changed.

## 2026-09-29 — series attribution audit and review preparation

Added prominent Kev/Laya/Qwen/TypeSafe credit, an exact-revision reuse inventory,
a schema-validated CITATION.cff, a six-study index, complete offline verification
instructions and the newest derivative-data card. GitHub metadata confirms this
is not a fork; the unchanged vendored Kev source and its Apache license remain
explicitly attributed. Laya is a research reference, not an executed backend.

Added a pack-fingerprinted, read-only rewrite-review CSV checker and a design-only
cited-fact extraction follow-up. Blank sheets do not count as annotations; valid
CSV syntax does not certify independence or open inference. No historical
scientific result, model input, frozen implementation or upstream code changed.
See [the publication audit](docs/PUBLICATION_AUDIT_2026-09-29.md).

## Complete v0.1 evidence publication and post-run tooling

The 2026-09-29 real results, inputs, frozen runner, analyzer, manifest and protocol
are preserved byte-for-byte modulo Git line endings. This release publishes the
previously missing data, results, figures, explorer, tests and pre-execution bundle.

Added after the experiment:

- `verify_evidence.py` independently checks manifest fingerprint, exact requests,
  raw response/logit-to-probability-to-choice consistency, prompt hashes, grids,
  and the complete original HTTP ledger. `provenance/postrun-verification.json`
  records this later audit, not an earlier preregistration.
- `replicate.py` is the recommended new-run entry point. It protects published
  results, skips backend construction on a full cache hit, uses immutable session
  directories, caps HTTP attempts per job across restarts, and stops for unknown
  request costs. Local model-directory overrides are deliberately not supported;
  it resolves the pinned Hub revision instead.
- Offline GitHub Actions and adversarial regression checks require no credentials
  or weights. Tests inject faults, not model outputs for scientific scoring.

`run.py` remains the historical source used for the original result. Its known
resume/runtime blind spots are described above; use `replicate.py` for new work.
New runtime/runner conditions are explicit and must not be attributed to v0.1.
