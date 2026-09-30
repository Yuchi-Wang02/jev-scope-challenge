# One answer changes. Does the decision follow?

Completed 2026-09-30: a frozen public-source diagnostic with Jev 1.13.0 and
Qwen3.5-4B on 12 ShARC development trees /24 unchanged inputs, each in two
option orders. **Zero project human reviews. Source-label agreement is not
independently verified correctness.**

[Full results](RESULTS.md) · [Interpretation and next decision](INTERPRETATION.md) ·
[Interactive replay](../../docs/source_label_screen.html) ·
[All-pair source audit](SOURCE_REVIEW.md) · [Source and license](ATTRIBUTION.md)

|Condition|Source agreement, two orders|Fully matching pairs, two orders|
|---|---|---|
|Jev native choice|18/24; 18/24|8/12; 8/12|
|Qwen3.5-4B direct|11/24; 12/24|3/12; 3/12|
|Qwen3.5-4B thinking, 2,048-token cap|5/24; 6/24|0/12; 0/12|
|Copy last history answer, no model|14/24|4/12|

The thinking arm has 37/48 cap-truncated outputs, all retained in denominators.
The other four shallow controls and the all-response displayed-argmax view are
also in the full report. No order or readout is selected for a better headline.

The original strict API experiment stopped on a nonunit probability sum and,
after one repair, a native-choice/displayed-maximum mismatch. Two explicit,
prospective readout repairs completed only previously unstarted requests.
All 48 original API jobs returned with no repeats. The final native view is an
adaptive engineering repair; both stopped original ledgers remain intact.
Read the [first repair](READOUT_REPAIR.md), [final policy](FINAL_READOUT.md) and
[raw-response audit](results/jev_audit.json).

## Evidence and reproducibility

- [Prospective protocol](PROTOCOL.md) and [exploration amendment](EXPLORATION_AMENDMENT.md).
- [Exact requests](plan.json), [separate source references](references.json),
  [unaltered selected rows](selection.json) and [code/data freeze](freeze.json).
- [Structured results](results/comparison.json), [original strict analysis](results/original_strict_analysis.json),
  [local raw journal](results/qwen.jsonl) and [token audit](results/token_audit.json).
- The frozen archive SHA-256 is `72dca3f4f3ba73b1d796b40e952a80d53cd2011ef90b2168b8bcaa818f5edd1e`.
  One pair per tree; four invariant, four ASK/decisive and four No/Yes pairs.
  Source actions are Yes 10, No 8, ASK 6. There is no Irrelevant-reference stratum.
- All 24 rows were rechecked against the official source. The title-only
  child-seat snippet is upstream content, not our input truncation. No label was
  changed or row excluded following the source audit or model outputs.

```bash
# No API keys, weights or model calls:
python research/source-label-screen/jev_audit.py --verify
python research/source-label-screen/report.py verify
python research/source-label-screen/replay.py --verify
# Additional pinned-tokenizer re-decoding; no model weights loaded:
python research/source-label-screen/report.py verify --model-dir /path/to/pinned/qwen35
```

Ordinary offline verification checks saved extraction, hashes and arithmetic.
The optional local check independently re-decodes all 96 saved token sequences.
The generated replay's source-derived content also carries CC BY-SA 3.0;
independently authored page and analysis code remain under the repository MIT license.
No ShARC implementation was forked or copied.

## Scope and stopping point

The selection excludes development trees sharing a training tree ID or exact
case-folded, whitespace-normalized rule snippet. Semantic near-duplicates and
pretraining contamination are not ruled out. This is selected public development
material, not a hidden test, new benchmark or confirmation study.

This grid is closed. No prompt search, cap extension or repeat of failed outputs
is part of it. The separate [training review queue](../external-validation/TASK_CARD.md)
remains unscored pending its own reviews and adjudication; the payment-study
reviewers did not review this new slice. See the interpretation note for the next
engineering question and the much higher bar for a paper contribution.
