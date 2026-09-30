# Evidence and replication notes

This document's original evidence description below concerns the cancellation
study. For the whole series, see [RESEARCH_INDEX.md](RESEARCH_INDEX.md) and
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Kev diagnostics use an exact
historical checkpoint; current upstream releases are not interchangeable.

## Offline verification of the complete series

Clone with full history: the latest study verifies source at the execution
commit. Use Python 3.10 and `pip install -r requirements.txt`. The following
checks use committed artifacts only, without credentials, weights or inference:

```bash
python research/candidate-completeness/analyze.py --verify
python research/candidate-completeness/publish.py --verify
python research/candidate-completeness/review_tools.py --verify
python research/candidate-completeness/reasoning_analyze.py --verify
python research/candidate-completeness/reasoning_report.py --verify
python research/candidate-completeness/plot_results.py --verify
python research/decision-sufficiency/build.py --verify
python research/baseline-readiness/preflight.py verify
python research/baseline-readiness/qwen35_report.py --verify
python -m unittest discover -s tests -v
python verify_evidence.py
python analyze.py --verify
python research/next-study/verify_study.py
python research/layout-boundary/verify_layout.py
python research/evidence-gap/verify_gap.py
python research/evidence-gap/review_tools.py verify
python research/evidence-guards/verify_guards.py
python research/fact-execution/data_tools.py verify
python research/fact-execution/fact_analyze.py --verify
python research/fact-execution/publish_facts.py --verify
python research/fact-execution/review_starter.py --verify
python research/fact-execution/line_evidence.py
python research/fact-execution/line_plan_tools.py verify
python research/fact-execution/line_run.py verify-freeze
python research/fact-execution/line_analyze.py --verify
python research/fact-execution/line_oracle_decomposition.py --verify
python research/fact-execution/publish_line.py --verify
python research/fact-execution/joint_route_plan.py verify
python research/fact-execution/joint_token_control.py verify
python research/fact-execution/joint_execution.py verify-freeze
python research/fact-execution/joint_analyze.py --verify
python research/fact-execution/publish_joint.py --verify
python research/fact-execution/scope_gate_audit.py verify
python research/request-ownership/prepare.py verify
python research/request-ownership/execution.py verify-freeze
python research/request-ownership/analyze.py --verify
python research/request-ownership/plot_results.py verify
python docs/build_four_line_challenge.py verify
python docs/build_risk_tradeoff.py verify
python docs/build_request_switch.py verify
python verify_publication.py
```

The full [CI workflow](.github/workflows/check.yml) also verifies generated
publication bundles and other preparation artifacts. Offline consistency is
different from reproducing model inference in a new environment or auditing
labels independently. Our original outputs and failed attempt remain available.
The request-ownership checks verify the original execution freeze and the
completed 500-row scientific run. Its scorer requires complete raw evidence,
exact execution-commit sources and runtime/weight/tensor audits. In-memory
software fixtures test the scorer without writing model records or calling a model.
The figure verifier recomputes chart rows from validated raw evidence and checks
SVG metadata and published asset hashes without loading Matplotlib. Rendering
used Matplotlib 3.10.0, recorded in its manifest; cross-version pixel identity is
not claimed. `plot_results.py build` regenerates only the figure artifacts.
The request-switch explorer is also checked against all 24 pairs, 48 visible
texts and 500 planned prompts. Its program references are recomputed from the
visible grammar, and the builder never reads scientific model predictions.
The four-line challenge verifier rebuilds the standalone page from the pinned
S01 input texts and all 32 saved S01 model decisions across backends, mappings
and rounds. It also recomputes the four grammar-specific code decisions and
checks the full-probe code summary; it does not call either model.

The cost explorer verifier recomputes the three saved N1 development paths,
derives always-defer and the existing grammar parser from visible inputs, then
grades their predictions against program-derived labels. It uses exact rational
arithmetic to find optimal ranges under two hypothetical loss definitions. It
makes no model calls; the controls' CPU time and actual human handling costs
were not benchmarked. Its 72 views are the same public development inputs.

## Original cancellation evidence

This release contains real direct Jev API calls and real local Qwen3-4B forward
passes. The result explorer replays them; it does not simulate inference.

- 48 unique inputs, 12 four-way cases, both candidate mappings, two rounds.
- 192 formal terminal records per model; 3 separate smoke records per model.
- All formal records succeeded. Raw choices/logits were also tallied independently
  from the reporting function: Jev 96/96 and 12/12; Qwen 83/96 and 8/12, in both
  rounds. No repeat disagreement. All 4 Qwen failed complete cases are object-scope cases.
- The S01 four-line example was selected in the design before live calls.
- The original data text and labels match the earlier design draft; only label
  provenance/status fields were finalized. There was no test-set difficulty change.
- Tests cover the complete quartet invariants, grammar-reference decisions,
  exclusion of gold/IDs from model inputs, cache mapping/round identity,
  invalid probability rejection, and scoring of stable-wrong and missing decisions.
- `python analyze.py --verify` validates the frozen files, all exact requests,
  expected unique record grid, and full recomputation of the stored summary.

The final local pre-execution freeze was commit `2c08d9b` / tag
`prereg-v0.1-final`. Its preceding preflight commit is retained. A pre-model
amendment made text hashes invariant to Windows/Linux line endings; task text,
labels, prompts, mappings, baselines and endpoints did not change. The original
manifest and explanation are in `provenance/`. No model call preceded this amendment.

One startup attempt encountered a missing output directory before any model
prediction or API request. The output directory was created and smoke then ran.
It caused no data/prompt change or billed inference request.

**This was a local freeze, not an externally timestamped preregistration.** GitHub
publication followed the runs. The included local pre-execution Git bundle lets
readers inspect those commits; local Git timestamps alone are not independent
proof of preregistration. AI-assisted drafting/review does not constitute an
independent human label audit.

## New live replication

The committed files are the evidence from the original run. Use the newer
`replicate.py --output .local/my-replication` entry point shown in the README.
It keeps results separate and session metadata immutable across resume. The
original `run.py` remains frozen and is not the recommended replication entry point.
Jev credentials go only in the `TYPESAFE_API_KEY` environment variable.

After-run strict validation: `python verify_evidence.py`. This adds raw evidence
chain checks and manifest self-fingerprint validation without changing the original
analyzer or experimental result. Its report is in `provenance/postrun-verification.json`.

Python 3.10.18, torch 2.8.0+cu128, transformers 4.55.4 and accelerate 1.10.1 were
the executed environment. Offline analysis used numpy 2.1.2 and matplotlib 3.10.9.
The hosted/local runtime metadata are in `results/*runtime.json`. Other platforms
or fresh dependency installations were not independently reproduced.

## Interpretation

The primary denominator is 12 constructed cases. Every case has eight decisions
(four messages, two mappings); neither those repeated decisions nor a second
round adds independent cases. The bootstrap is within-probe reweighting
sensitivity only. Jev's perfect probe score does not prove perfect real-world
reliability, and the Qwen result concerns this frozen model and readout.

The known-grammar parser solves this grammar without a model. It has full
knowledge of the explicit construction grammar and must be labeled accordingly.
That result matters: this release does not show that any model is necessary for
these artificial inputs. Natural-language extensions require separate tests.

API cost is estimated from returned input-token usage and the documented fee,
not verified against an account invoice. Local GPU time is not converted into
an artificial zero-dollar deployment price. No hosted/local architecture speed
claim follows from the latency table.

## Payment-ownership study (2026-09-30)

Run `python research/payment-ownership/verify_run.py` for offline raw-response,
source-freeze, explicit execution-amendment, aggregate and publication checks.
It requires full Git history for preparation commits `0569f8d` and `08fdda6`.
`python research/payment-ownership/study.py verify-source` additionally re-fetches
pinned public source files into memory; it performs no inference. The original
v0.1 runner retains the failed semantic gate. The v0.2 runner and amendment remain
separately frozen, with shared append-only accounting. Published completed outputs
are not a blank replication destination. Two submissions of 96 items each are received,
with a candidate-scope objection; no reviewer-endorsed adjudication or reference
update is claimed. Run `python research/payment-ownership/audit_review.py --verify` to check
the unaltered submission hash, IDs, evidence paths, saved scores and the neutral
second-reviewer package. The checks do not establish semantic validity or independence.
See the [audit](research/payment-ownership/REVIEW_AUDIT.md). The separate
[candidate-completeness plan](research/candidate-completeness/PLAN.md) retains its
historical preparation status; its subsequent [completed results](research/candidate-completeness/RESULTS.md)
use different inputs and are not validated by these two payment reviews.

Run `python research/payment-ownership/review_pair.py --verify` for the two-review
comparison and exact date-normalization check. The [reporting disposition](research/payment-ownership/REVIEW_DISPOSITION.md)
retains the conditional labels and intake metadata limitations.
