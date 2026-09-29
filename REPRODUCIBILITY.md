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
python verify_publication.py
```

The full [CI workflow](.github/workflows/check.yml) also verifies generated
publication bundles and other preparation artifacts. Offline consistency is
different from reproducing model inference in a new environment or auditing
labels independently. Our original outputs and failed attempt remain available.

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
