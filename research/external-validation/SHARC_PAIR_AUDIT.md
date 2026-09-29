# Flip one answer, check whether the action flips

The [ShARC source audit](README.md) identified short external rule texts and
conversation histories as a candidate for a later decision study. This
**train-only structural audit** asks whether the source actually contains
controlled contrasts. It is not a Jev/Kev/Qwen run, independent confirmation,
new human annotation or a new benchmark.

The [inspector](inspect_sharc_pairs.py) reads the pinned official archive in
memory and compares two utterances only when `tree_id`, exact visible rule
snippet, question and scenario all match. Their history has the same length
and the same follow-up questions in the same order; **exactly one prior answer
changes between No and Yes**. This explicitly checks visible content rather
than assuming that a shared `tree_id` guarantees identical questions. The
source's `tree_id` groups can contain multiple question variants.
In the pinned train split, all 628 tree groups have more than one visible
question, so `tree_id` alone is insufficient for this pair definition.

Before pairing, identical visible inputs are collapsed to one row when their
four-way action agrees. One visible-input group has contradictory action
labels across three rows; the group is excluded and counted, not silently
resolved. `ASK` is a provisional normalization of answer text other than
literal `Yes`, `No` or `Irrelevant`. Question-text quality is not evaluated.

|Pinned train inventory|Count|
|---|---:|
|Source utterances|21,890|
|Unique visible inputs|21,850|
|Repeated visible-input groups|34|
|Action-conflicting group / rows excluded|1 / 3|
|One-answer-flip pairs after deduplication|3,334|
|Pairs with different provisional action|3,037|
|Pairs with the same provisional action|297|
|Distinct `tree_id` groups containing an action flip|599|

The [machine-readable summary](sharc_pair_summary.json) also gives the
`ASK/No`, `ASK/Yes`, and `No/Yes` transition counts. A future small challenge
could sample entire `tree_id` groups or freeze an ID-only subset **before**
model inference and ask independent reviewers to inspect the paired semantics.
The 3,037 changing pairs are correlated examples from a public training set,
not 3,037 independent demonstrations of model failure. Public training text
may also have appeared in model pretraining, so this slice is useful for
development and mechanism checks, not a clean final generalization claim.
No source rows, free-form answers, pair IDs or third-party text are copied
into this repository.

Recompute the inventory from the official archive (network required, no model
weights or API key):

```bash
python research/external-validation/inspect_sharc_pairs.py verify
```
