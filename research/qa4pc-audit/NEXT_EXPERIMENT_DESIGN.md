# Next diagnostic: facts, rules, or both?

**Design only, 2026-09-30. No selected model cohort, frozen query plan or model
output yet.** This document records the decision after the [source audit](README.md).
An executable manifest, exact input contracts and runner checks must precede
inference. Existing API authorization remains in force; these are implementation
gates, not another approval request.

**Follow-up:** [cohort preparation](../qa4pc-stage-attribution/README.md) subsequently
fixed 12 trees /24 scenarios /56 condition questions. The full query/compiler
freeze and all model execution remain pending; the original design status above
describes this document's creation.

## Falsifiable question

On a bounded QA4PC development cohort with complete supplied graphs, does replacing
model composition with a fixed executor improve agreement with released labels
when both routes receive the same condition-question inventory and graph?

The essential comparison is graph-assisted direct decision versus model facts
plus execution. Comparing only plain direct decision with decomposition would
confound the execution change with access to human-authored structure.

|Arm|Model receives|Produces|Purpose|
|---|---|---|---|
|D: plain direct|Policy, question, scenario|yes/no/maybe|Unaided input-contract reference.|
|G: graph-assisted direct|Same text, supplied condition questions and expression|yes/no/maybe|Controls access to the human decomposition.|
|F: facts then code|Same text and supplied structure, with one condition question selected per call|One fact label per question; code composes all labels|Tests the fact-prediction route, including its extra calls.|
|L: supplied facts, model execution|Supplied expression and released fact labels|yes/no/maybe|Isolates symbolic execution under explicit label-derived assistance.|
|C: supplied facts, code execution|Same formula and released fact labels|Deterministic final label|Software/reference consistency control, already audited.|

L and C are assisted diagnostics, not competitors for end-to-end accuracy. No
automatic policy-to-graph extraction is implemented. Human graph construction
cost is unavailable and must be reported as an unmeasured deployment cost.

## Selection and freeze requirements

1. Use development data only. Exclude the incomplete graph from model stage
   comparisons, retaining its eight IDs as reported exclusions. Do not fix it
   using final answers. Account for the four EXtrA-overlap trees before sampling.
2. Check tree/utterance IDs against the pending training review queue without
   scoring it or exposing its labels to prompts. Do not call any QA4PC cohort
   independent of earlier project material until this check is complete.
3. Start with at most 12 trees and 24 scenarios. Choose deterministic hash ordering
   before model results, document label-based stratification if used, and keep
   all selected cases regardless of failures. Do not construct a new contrast
   by pairing unrelated scenarios and claiming only one factor changed.
4. Pin Jev, the existing Qwen3.5 checkpoint, templates, option mappings and every
   request. Use two fixed label-to-letter mappings; no prompt or precision sweep.
5. Count all condition questions before fixing budget. For S selected scenarios
   and F total condition questions, two models and two mappings require
   `4 * (3*S + F)` scored decisions for D/G/F/L, plus a separately frozen smoke
   allowance and bounded retries. This is a counting formula, not an executed grid.
6. Compile every input and estimate/check tokens before launching. Preserve raw
   inputs locally if redistribution terms remain unresolved; publish hashes,
   retrieval pins, original templates and derived outputs. Do not upload the
   source dataset to Hugging Face under the repository's license.

## Measurement and stopping

- Report per-arm source agreement, per-question agreement, unknown-to-determined
  errors, invalid outputs, option-order changes and full-tree outcomes. Use trees
  as clustered units; the two mappings and repeated questions are not new samples.
- Invalid F facts propagate to an invalid composition; never replace invalid
  outputs with `maybe`, majority votes or source labels.
- For F failures, distinguish wrong fact labels that change the final answer
  from those masked by the formula. For G/L, report only the supported stage
  diagnosis: L success alone cannot establish correct natural-language reasoning.
- Report physical calls, input/output tokens, raw latency measurements, retries,
  model loading and code-execution costs separately. F has more calls; no
  budget-matched superiority claim follows without a later fixed-budget control.
- If D already saturates, publish the boundary and stop this candidate. If F
  helps G only by increasing inference cost, measure that tradeoff before
  interpreting it as a useful intervention. If F fails mainly on facts, do not
  keep adding composition machinery. No same-cohort prompt rescue search.

## Presentation and contribution boundary

Working public question: **"Does a decision model need help reading the facts,
or executing the rule?"** The hook is an inspectable attribution experiment,
with model failures and passes both publishable. It is not a claim that Jev is
unnecessary. Decomposition and execution have direct prior art in
[Saeidi et al.](https://aclanthology.org/2021.emnlp-main.678/); the prospective
contribution is a controlled comparison and reusable measurement artifacts.

This pilot remains exploratory, with released labels rather than new independent
human adjudication. A paper would still require a distinct confirmatory cohort,
semantic label review, fair stronger-model/budget controls, and evidence that the
identified boundary persists beyond this source and supplied-graph setting.
