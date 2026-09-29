# Can a guard tell missing evidence from missing fields?

Exploratory, post-hoc development follow-up to `evidence-gap`. Original scores
were already reviewed before this design. This is not a fresh confirmation,
calibrated policy, new inference run or new algorithm. Publish this specification
and implementation before deriving the new tables; do not call it preregistration.

## Inputs and scope

Reuse only the 648 real **development main** records at prior source commit
`434703989b08d003a44a95b0528765d2b94e11d3`. N0/N1/K1 retain exact inputs and
weights. Do not score or fit on reserved calibration/test, compose new model
outputs, train, download models or call paid endpoints. No independent annotations
exist. The 108 previous null records are not inputs to these new methods.
All original study source/data/output files remain unchanged.

`development_cases.jsonl` is a 72-item extraction of the existing development
cases for metric definitions. Only its `state` and `instruction` strings enter
the parser/gates. IDs, family, gold and structured construction facts are used
for auditing/metrics, never as inputs to guard decisions. All 12 parent groups
retain six views and three option orders. New method predictions are derived,
not new model calls or independent samples.

## Fixed ablation ladder

- Raw argmax: unchanged historical three-way prediction.
- Maximum candidate probability cutoffs: 0.5, 0.7, 0.9, 0.95, 0.99.
- Top-two candidate probability margin cutoffs: 0.2, 0.5, 0.8, 0.95.
- Schema presence gate: suppress a model action if any target-schema field is
  missing or contradictory. This deliberately naive baseline ignores logical
  redundancy and the irrelevance of an unselected route's permission.
- Policy determinacy gate: reject target-schema conflict; joint approval is
  determined by an explicit rejection or both approvals; reversal needs base
  and exception; route needs selected-site permission or agreement across all
  possible routes. Otherwise suppress a model action. This gate knows policy
  semantics and is already part of a policy engine. It does **not** correct a
  wrong ALLOW/DENY action when the evidence is determined, and does not force a
  raw INSUFFICIENT to become an action.
- Always INSUFFICIENT control: zero model calls.
- Separate known-grammar parser + full finite-policy solver reference: zero
  model calls. It uses the same strong grammar/policy prior as the guards and
  must be reported alongside them; it is not a general NLP baseline.

All score cutoffs are listed above; **no label-based threshold/temperature fit,
no best-threshold selection, no calibrated risk guarantee**. Report every grid
point. Conditional softmax on three candidates is not correctness confidence.
Low score maps to the task's INSUFFICIENT label, which claims underdetermination;
that is different from a generic external reject action. False INSUFFICIENT on
determined evidence is explicitly scored as an error.

The exact grammar parser is shared over 72 texts across paths/orders. Conflicts
and absent fields concern target-schema records only. It rejects unrecognized
grammar or the reserved composed policy. It does not infer facts from other
requests. The policy gate uses visible parsed facts, not an oracle mask from
construction metadata. However, hand-coded schema/logic is external knowledge
unavailable to the raw model. Apply it equally to all three paths and describe
the comparison as pipelines with different helpers, not model-only superiority.

## Metrics and checks

For every path/method: total correctness /216, complete parents /12, paired
deletion correctness /36, every family and view, corrections/regressions,
unsupported commitments /72 uncertain decisions, false INSUFFICIENT /144
determined decisions, wrong ALLOW/DENY /144 determined decisions, action count
and error among those actions. Action coverage = non-INSUFFICIENT /216; action
risk = wrong actions / action count, undefined when zero. These are descriptive
task metrics, not a certified selective-classification guarantee. Parent groups
are the sampling units; no significance or held-out generalization inference.

Cross-check the determinate flag against finite-world determinacy over all 96
partial/conflicting states of the three development policies. This checks code
logic, not independent natural-language annotation. Include failure tests for
redundant missing approval, unselected permission, missing route with equal
permissions, cross-request distraction, target conflict, unsupported policy,
tampered source records, foreign/duplicate grid and input metadata leakage.

Freeze source, development extraction and prior raw evidence hashes. Save all
8,424 derived predictions (13 methods x 648 records), 216 code-reference rows,
per-input gate certificates and all threshold points. Keep verification read-
only, including source hash/counter checks. Scientific forwards added = 0;
reserved model records = 0; paid calls/training/downloads = 0. Any gate failure
is preserved; do not overwrite partial output or select successful retries.

CPU preparation timing/counts are local measurements, not endpoint latency
comparisons. Each model-dependent nominal decision still requires its original
single forward plus any parsing/gate work; reuse does not make model cost zero.

## Attribution and limits

Confidence-based rejection and risk/coverage reporting are established work;
see [Geifman and El-Yaniv, 2017](https://papers.nips.cc/paper_files/paper/2017/hash/4a8423d5e91fda00bb7e46540e2b0cf1-Abstract.html).
We do not implement their risk-guaranteed threshold selection. Exact finite
policy checks and short-circuit logic are standard software. No architecture,
calibration or policy-engine novelty claim. Human review and a separately
versioned calibration/test protocol remain required. Kev results are not Jev.
