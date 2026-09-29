# Evidence and replication notes

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

The committed files are the evidence from the original run. In a separate copy,
archive the entire included `results/` directory, then create an empty `results/`
directory before smoke/formal commands. Keep the frozen data and code unchanged.
The included successful records otherwise cause resume to skip API/model calls.
Jev credentials go only in the `TYPESAFE_API_KEY` environment variable.

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
