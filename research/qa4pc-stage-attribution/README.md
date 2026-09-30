# Facts, rules, or both? — cohort preparation

**Cohort selected before model execution, 2026-09-30. Zero model calls.**
This is the next step after the [QA4PC structural audit](../qa4pc-audit/README.md)
and [stage-attribution design](../qa4pc-audit/NEXT_EXPERIMENT_DESIGN.md).
Exact prompts, token budgets, smoke cases and the runner freeze remain unfinished.
The published IDs are a selection manifest, not an executed experiment.

## Fixed selection

From 60 QA4PC development trees and 437 scenarios, exclude whole trees for:

|Reason|Trees|Scenarios on those trees|
|---|---:|---:|
|Missing formula variable|1|8|
|Previously inspected EXtrA material|4|35|
|Pending ShARC training review queue|3|29|
|Earlier 12-tree source-label screen|0|0|
|Union|8|72|

There are **52 eligible trees /365 scenarios**. All have at least two scenarios.
Hash-rank tree IDs using the fixed study name, select the first 12, then hash-rank
scenario IDs within each tree and select two. No label stratification, difficulty
filtering or model-output selection is used. All eligible policies have distinct
exact policy strings; broader semantic duplicates have not been adjudicated.

The resulting **12 trees /24 scenarios /56 condition questions** have released
labels 9 yes, 8 no, 7 maybe. These counts were observed after applying the selection
rule. The two scenarios within a tree are not controlled counterfactual pairs:
they may differ in multiple facts. The statistical cluster is the policy tree.

[cohort.json](cohort.json) records selected source IDs, input hashes, aggregate
labels, exclusions, source revision and dependency hashes. It contains no source
text or full label vector. Excluded pending-queue IDs are not exported as a
queue-to-source mapping. Source texts remain subject to their upstream terms;
the audit has not located an explicit QA4PC dataset license.

## Pending-review isolation

Reconstruct the already frozen ShARC training selection with its existing code
and exact source archive hash, verify its manifest, and compare IDs in memory.
It shares three trees but zero exact utterance IDs with QA4PC development data.
Excluding whole trees removes this overlap from the selected cohort. The original
queue still has zero completed human reviews and zero model predictions. This
preparation does not amend its review requirement, label it, or score it.

ID disjointness from the enumerated project materials is not a claim that models
have never seen QA4PC/ShARC, that these policies are semantically independent, or
that released references have received new independent validation.

## Concrete next execution scope

For each of two fixed option mappings and each of Jev /existing Qwen3.5-4B:

- 24 plain direct decisions (D).
- 24 decisions with supplied condition questions and graph (G).
- 56 condition predictions composed by the fixed executor (F).
- 24 supplied-fact model execution decisions (L), explicitly label-assisted.

This is **128 scored decisions per model/mapping, 512 total**: 256 Jev decisions
and 256 local decisions. Smoke and retry allowances are not included in that
number and must be separately frozen before launch. Code applied to released
facts is a software control, not another model decision. D/G/F/L contracts and
interpretation limits are explained in the linked design.

Next work is to implement and validate the compiler/runner, check input lengths,
freeze the precise plan and then execute under existing user authorization.
This manifest alone does not authorize arbitrary retries or prompt searches.

## Reproduce the preparation

```powershell
python research/qa4pc-audit/audit.py fetch --source-dir .local/qa4pc-audit
python research/qa4pc-stage-attribution/cohort.py verify --source-dir .local/qa4pc-audit
python -m unittest discover -s tests -p test_qa4pc_cohort.py -v
```

The cohort command downloads the previously pinned ShARC archive to reconstruct
the pending queue; it does not read completed human opinions or model outputs.
`build` writes a new manifest; `verify` recomputes without overwriting and rejects
drift. The original synthetic tests check order/label invariance, whole-tree
exclusion, union accounting and insufficient/duplicate-data failures. CI runs
those tests, not a network source audit.
