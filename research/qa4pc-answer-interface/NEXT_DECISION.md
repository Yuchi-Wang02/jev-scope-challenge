# Close the interface grid; inspect the remaining decision errors

Follow-up status: steps 1 and 2 below now have an [exhaustive source audit](SOURCE_AUDIT.md)
and [local source-only review tooling](REVIEW_PACKAGE.md). Human assessment remains
pending; tooling completion does not complete that requirement. Eight final-label
review flags and a unanimous-model counterexample make semantic validation the
next priority before any repair based on these observed errors. The original
cohort remains closed and its scores unchanged. Stronger-comparator readiness
and future independent study design remain open work.

The [focused local resource refresh](../baseline-readiness/CURRENT_RESOURCES.md)
now completes the cache-inspection part of step 3: the inspected caches contain
the measured 4B models, smaller models and historical adapters, with no 8B-or-larger
general instruction comparator found. This is not a whole-machine scan or a
capability test. Selecting a stronger comparator or a declared capability-oriented
configuration on new reviewed material remains unfinished.

## Milestone audit

Goal: determine whether an unfairly narrow output interface explains the earlier
model comparison before investing in more fact-pipeline interventions.

Completed: all 648 prospective jobs on 12 disjoint policy clusters, identical-
prompt generated-letter bridge, exhaustive six mappings, costs, invalids and an
independent source/raw-output replay. No execution amendment was needed.

Reality versus expectation: normal generation is perfectly format-compliant,
but generation of semantic labels does not increase mean source agreement.
Finite-versus-generated letter differences arise only at exact ties. Semantic
generation improves permutation consistency while slightly lowering agreement.
This rejects a simple "just generate semantic labels" repair for this setting;
it does not reject all generation methods or ordinary models.

The broader research remains incomplete. We started with evidence ownership and
reliable software decisions; continued generic option-permutation studies would
drift toward rediscovering known evaluation artifacts. These controls help us
interpret model comparisons but are not, alone, a research contribution.

## Next bounded work

1. Audit the remaining errors against the original policy, scenario, question
   and supplied graph. Separate visible-evidence problems, reference semantics,
   missing information and genuine rule application. Preserve original labels
   and all scores; an AI-assisted source audit is not independent human review.
   Inspect systematic passes too, not only a few attractive failures.
2. Make the human-review gap actionable with a compact blinded review unit and
   a clear question. The existing training queue remains unscored; do not quietly
   convert it into another exploratory model set while review is pending.
3. Check locally available stronger ordinary-model options and comparable
   bounded inference settings before new downloads or a larger grid. A second
   stronger comparator is necessary before a specialization argument; do not
   choose it by repeatedly optimizing this now-closed cohort.
4. Choose the next study only after the error audit: new independently reviewed
   decision material if the semantic signal is sound, or a task/reference repair
   if source-evidence discrepancies dominate. Do not manufacture an intervention
   solely because there is unused API quota.

No new experiment is frozen by these next steps. Current cohort is closed to
new inference. Remaining eligible trees are not yet a confirmed holdout; they
must be screened for overlap and frozen for a concrete hypothesis before use.

## Public presentation

Lead with the falsifiable result: **"Generated outputs were valid and sometimes more stable. They did not close
the decision gap."** Keep
all six mappings next to this claim; highlight the tie-only difference between
finite and generated letters. Link raw outputs and cost accounting.

The repository now offers a connected negative-results sequence, not a proof
that Jev is useless and not a claim that a new model is necessary. The long-term
paper path still requires valid new task material, strong fair comparisons,
a useful intervention or well-supported boundary, and external human judgment.
