# Prospective paired scoring contract

Status: implemented on synthetic software fixtures only. Zero ShARC predictions
or adopted human references. This is a scorer for a future protocol, not a run
freeze, model evaluation or novel metric.

## Why aggregate accuracy is insufficient

Consider two pairs, each with references `(Yes, No)`. All outputs below are
invented for a software test; they are not model observations.

|Condition|Pair 1 predictions|Pair 2 predictions|Item correctness|Both items correct in a pair|
|---|---|---|---|---|
|Synthetic A|Yes, No|No, Yes|2/4|1/2|
|Synthetic B|Yes, Yes|Yes, Yes|2/4|0/2|

The item scores agree while pair success differs. Likewise, a wrong-to-wrong
change can follow an input change without understanding it. An unchanged
prediction can be appropriate on a pair whose correct action should stay fixed.
Report all of these outcomes rather than equating sensitivity with correctness.
See the [prior-work update](NEAREST_WORK_UPDATE.md) for the methodological context.

## Input and accounting rules

[`score_condition`](paired_metrics.py) accepts explicit pair and prediction
lists for exactly one named model/prompt/order/seed condition. Each pair has a
unique `pair_id`, unique `tree_id`, two ordered `item_ids` and two clear semantic
`reference_actions`. Allowed references are `Yes`, `No`, `Irrelevant`, `ASK`.
`UNCLEAR` has to be resolved or declared ineligible through the existing human
review process; the scorer does not choose a resolution.

One prediction row must exist per expected item. `action: null` records a failed
output and remains in the denominator. Missing rows, duplicates, foreign IDs,
unsupported actions, reused trees and unresolved references raise an error.
The future runner must separately retain transport, parsing and termination
reasons; a null action is not sufficient provenance by itself. The adapter,
review-finalization and cohort checks still belong upstream of this function.

The one-pair-per-tree assumption matches the frozen pilot selection. A future
design with multiple pairs per tree needs a different grouping contract; it
must not rename trees to bypass this check. Each mapping/seed is scored
separately on the same verified cohort. Repeats are never extra independent
samples. A caller must verify equal cohorts when comparing conditions.

## Returned evidence

- Item accuracy and pair-both-correct with explicit numerators/denominators.
- All four correctness states: both, first only, second only, neither. The
  within-pair order is declared input order, not an inferred temporal direction.
- Separate reference-changing and reference-invariant counts. Within each:
  changed predictions, unchanged predictions, incomplete pairs and pair success.
- Full four-reference by five-output confusion table, including invalid output.
- `Yes`/`No` when the reference is `ASK`, and `ASK` when the reference is
  `Yes`/`No`, each divided by its eligible reference count. Wrong `Irrelevant`
  decisions remain visible in the confusion table, not mislabeled as Yes/No.
- Pair-level records preserving references and predictions for audit.

An absent stratum has an undefined rate (`null`), not zero performance. Two
failed outputs do not count as unchanged predictions. `ASK` is a real task
action, not permission to omit that item from scoring. Cost and latency need
separate all-call records; this scoring function does not fabricate them.

No confidence interval, significance claim or population extrapolation is
produced. The current frozen queue has no deliberately invariant controls or
source-Irrelevant examples. Software support for these categories does not
establish their empirical coverage.

## Validation

Six test methods cover the equal-accuracy counterexample, changed-but-wrong
outputs, invariant references, failed-output denominators, absent strata,
duplicate/missing/foreign rows, unresolved references and ordering invariance.
They do not certify semantic labels, reviewer independence or model quality.

```bash
python -m unittest discover -s tests -p test_rule_paired_metrics.py -v
```
