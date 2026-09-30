# Close this cohort; investigate the interface before adding more reasoning

## Milestone audit

Objective: distinguish natural-language fact judgment from supplied-graph
execution, with a dedicated decision model and a frozen ordinary small model.
Reality: main coverage is complete after an explicit outcome-aware gate amendment.
The original smoke failure and its two forwards remain visible and charged.
Jev is comparatively stable across the two mappings. Qwen changes many decisions
and has ten exact maximum ties. Facts+code fails to consistently beat graph-direct
for either model. Supplied-fact execution helps, but is answer-assisted.

The original goal of a comparison has now been met for this configuration, not
for ordinary small models generally. Label semantics, stronger comparators,
interface parity, full order coverage and cost-matched inference remain gaps.
Source agreement is not validated business-decision reliability. This is not a
paper-ready demonstration that a specialized decision model is necessary.

## Stop rule now

Close this 24-scenario cohort to further prompt, precision, verbalizer or mapping
search. Keep it as a regression/replay example. Do not choose the better Qwen
mapping or rerun ties until its score improves. A structural gate amendment is
documented history, not a reason for unlimited rescue experiments.

## Most useful next research question

**How much of the observed model gap is sensitive to the answer interface?**

Before another fact pipeline, prepare a separate, unseen-with-respect-to-model-
outputs source cohort and a bounded comparison of finite letter readout with a
normal generated semantic-label baseline. Use the same checkpoint and matching
task content, and enumerate all six label permutations in advance where that
interface permits. Include Jev's corresponding option permutations rather than
giving external stability help to only one side. Count any aggregation's six
calls, tokens and time; order averaging is established methodology, not novelty.

No exact new cohort, query plan or baseline implementation is frozen by this
document. First check existing ordinary-model generation infrastructure and
prior work on answer-order and verbalizer sensitivity; avoid selecting a new
configuration by performance on the just-closed cohort. No new large-model
download or cloud deployment is implied.

Decision gates for that next study:

- If semantic-label generation substantially changes the gap, report an
  interface-dependent comparison and test on a separate held-out set before
  claiming a general reliability intervention.
- If the gap persists across fair interfaces and budgets, add a stronger ordinary
  model and independent semantic review before attributing it to specialization.
- If source disagreements dominate, resolve task/reference semantics rather than
  optimizing agreement through more prompt search.

## Presentation and long-term path

A bounded primary-source metadata/abstract check on 2026-09-30 confirms that this
direction has direct precedents: [Pezeshkpour and Hruschka, NAACL Findings 2024](https://aclanthology.org/2024.findings-naacl.130/)
study answer-option order sensitivity; [Unveiling Selection Biases, ACL Findings
2024](https://aclanthology.org/2024.findings-acl.333/) studies order and token
sensitivity; [Zhao et al., ICML 2021](https://proceedings.mlr.press/v139/zhao21c.html)
introduce contextual calibration for prompt-dependent bias. This short check is
not a full-paper or implementation audit and does not establish the cause of our
observed Qwen behavior. A future calibration/control design must credit and
inspect these existing methods before making any contribution claim.

Public hook: **"Same facts. Different answer key."** Pair it with the full model,
mapping, invalid-output and cost tables. It should invite reproduction of a
bounded result, not advertise a new discovery of option-order sensitivity.
Keep the earlier hook—extra fact calls did not reliably help—as a second finding.

The research path remains: observable phenomenon -> fair interface/budget
controls -> independently reviewed new material -> intervention/generalization.
At present, the repository offers real, inspectable diagnostics and explicit
failures; scientific novelty and deployment reliability remain unestablished.
