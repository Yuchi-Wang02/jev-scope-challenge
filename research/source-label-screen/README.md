# Parallel exploration with public source labels

2026-09-30. The [prospective protocol](PROTOCOL.md) and explicit
[exploration amendment](EXPLORATION_AMENDMENT.md) now specify the separate run.
No model predictions exist at preparation time. Exact inputs and source pins are
published by `screen.py prepare` before execution; all source-derived artifacts
carry the [attribution and CC BY-SA 3.0 notice](ATTRIBUTION.md).

Current execution status: all 48 distinct Jev requests have returned, after two
explicitly frozen readout repairs; the original strict run remains incomplete.
The fixed local Qwen grid is still running at this status update. No cross-model
source-agreement result is claimed yet. The [API audit](results/jev_audit.json)
reproduces every raw response under its phase's original readout and separately
extracts the final native choice. Total usage: 30,196 input /2,160 output tokens,
zero repeated job IDs, one nonunit probability sum and one choice/maximum mismatch.
See the [first repair](READOUT_REPAIR.md) and [final policy](FINAL_READOUT.md).
The observed anomalies do not by themselves establish wrong source-rule decisions.

Frozen materials: [exact plan](plan.json), [source references](references.json),
[original selected rows](selection.json), [code/data freeze](freeze.json).
There are 48 Jev requests and 96 local generations; actual local input encoding
totals 28,256 tokens. Source labels are Yes 10, No 8 and ASK 6. These are planned
inputs and source references, not completed model results or human judgments.

The reviewed [training-pair pilot](../external-validation/TASK_CARD.md) remains
closed to inference pending its two reviews and adjudication. That commitment
does not require abandoning all exploratory model feedback. A separate diagnostic
could use the public **development** split's original labels and explicitly
report source-label agreement, without claiming those labels were independently
verified by this project. It would not turn either cohort into independent
confirmation after prompts or methods are adjusted.

## Read-only feasibility evidence

`source_inventory.py` reuses the pinned official ShARC archive and existing
one-history-answer pair definition. It parses train/dev only, never the public
test. Source pin: `72dca3f4f3ba73b1d796b40e952a80d53cd2011ef90b2168b8bcaa818f5edd1e`.

Observed: 69 dev trees / 2,270 rows; zero tree-ID overlap with all 628 train trees;
zero exact rule-snippet overlap after case folding and whitespace normalization.
One conflicting-visible-action group is excluded by the existing deduplication
rule. Near duplicates and semantic overlap have not been ruled out. This is
neither a hidden test nor proof of no pretraining exposure.

|Source-action pair|Eligible pairs|Distinct dev trees containing a pair|
|---|---:|---:|
|ASK / ASK|4|2|
|ASK / No|49|14|
|ASK / Yes|42|13|
|No / No|6|2|
|No / Yes|168|62|
|Yes / Yes|14|6|

These are overlapping candidate-pair inventories, not independent sample counts.
Only a later selection of one pair per distinct tree could define the sample.
Actions other than literal Yes/No/Irrelevant are provisionally mapped to ASK;
source disagreement must not automatically be reported as a model mistake.

## Design basis and fixed scope

The frozen screen uses 12 distinct parent trees / 24 unchanged source inputs:
four No/Yes pairs, four ASK/decisive pairs, and four invariant pairs. Selection
must use a declared deterministic hash order, settle distinct-tree allocation,
and freeze all requests before any prediction. This adds an invariant group
missing from the reviewed training queue without changing that queue.

The candidate grid would reuse the common four-action instructions, two option
orders, Jev and Qwen direct/thinking interfaces: 48 API attempts and 96 local
generations, no retries. At the existing caps, the local output ceiling would be
110,592 tokens. Exact tokenization, wall/input limits and all execution/source
hashes still need a separate protocol. No budget is consumed merely by describing
this candidate, and this page does not itself authorize a runnable freeze.

The question would be narrow: do these interfaces follow the source's changed
and invariant action labels, and what do direct/thinking modes cost? All shallow
controls and failures would be reported. It is a diagnostic comparison, not new
counterfactual methodology or a dedicated-model necessity claim. The existing
[nearest-work findings](../external-validation/NEAREST_WORK_UPDATE.md) apply.

The published prospective amendment distinguishes this unreviewed dev diagnostic
from the review-first training study and preserves that earlier gate. No training
review item may be scored in this branch. Retain
source attribution and CC BY-SA 3.0 obligations if adapted inputs are published;
the attribution inside the [existing review ZIP](../external-validation/public-review/README.md)
identifies the original dataset and authors. No third-party rows are published
by this feasibility page.

```bash
# Public archive download and structural counts only; no model or credential.
python research/source-label-screen/source_inventory.py
# After a clean committed freeze, with existing pinned local model files:
python research/source-label-screen/screen.py verify --model-dir /path/to/pinned/qwen35
python research/source-label-screen/screen.py jev --model-dir /path/to/pinned/qwen35
python research/source-label-screen/screen.py qwen --model-dir /path/to/pinned/qwen35
python research/source-label-screen/screen.py analyze --model-dir /path/to/pinned/qwen35
# Reproduce completed API evidence offline, without keys, weights or calls:
python research/source-label-screen/jev_audit.py --verify
```
