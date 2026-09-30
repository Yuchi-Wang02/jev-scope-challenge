# One fact changes. Should the decision change?

Status, 2026-09-30: external-data development candidate; review material ready;
**0 completed human reviews, 0 model calls, no demonstrated new method**.
Working display title, not a claim of observed model failure.

## The falsifiable question

On short natural-language rules and a conversation history, can a typed decision
model and a capable ordinary instruction model each select the correct next
action when exactly one history answer changes? Count a pair as correct only
when both actions match independently reviewed references. A model changing its
answer is not sufficient: it must change to the right answer, and should keep
its answer when the reviewed meaning warrants no change.

This is a bridge from the payment study's candidate-scope ambiguity to a broader
rule-action setting. Inputs contain natural language that a model must interpret;
they do not contain our completed logical graph or resolved facts. ShARC is
existing prior work, built from real-world rule text and crowd-generated questions
and scenarios; it is not a newly collected production workflow. See the
[original paper](https://aclanthology.org/D18-1233/).

## What the current selection can and cannot establish

The [frozen queue](SHARC_REVIEW_PROTOCOL.md) has 30 candidate pairs from 30 trees,
24 primary and six ordered reserves, supplied as 60 shuffled items. Source labels
were used to select three action-changing strata. No source-`Irrelevant` examples
or deliberately invariant pairs were sampled. Four labels in an interface do
not make this a representative four-class benchmark. Human review may retain
same-action pairs when clear human judgments disagree with source labels;
it must not discard them to preserve an attractive contrast.

The final primary pilot has at most 24 tree units. Reserve items, prompt orders,
models and seeds do not increase that independent count. With this small selected
training slice, use raw paired outcomes and tree-level descriptive summaries;
avoid population prevalence, capability-ceiling or generalization claims.
Public training data may have appeared in pretraining. No claim of hidden testing.

A later confirmation design needs separately selected and reviewed data,
preplanned changed-action **and unchanged-action** controls, and a documented
approach to contamination. That is a new design, not an after-the-fact expansion
of this frozen queue.

## Candidate comparison contract — design, not an executable freeze

|Element|Requirement before a new task run|
|---|---|
|Visible inputs|Identical snippet, question, scenario and history. No source answer, evidence, IDs, resolved graph or human rationale in any end-to-end arm.|
|Action|`Yes`, `No`, `Irrelevant`, `ASK`. `UNCLEAR` is a review disposition, not an automatically correct model abstention. No question-generation quality claim.|
|Jev|Pin actual version, save label mapping and all probabilities/usage/errors. Check the four-way adapter separately.|
|Ordinary model|Use the established pinned Qwen3.5-4B runtime. Predeclare direct and thinking generation settings and total budgets; count every call and truncation. No reuse of the closed calibration fixtures for tuning.|
|Final-output handling|For a future protocol, accept either one exact JSON object or that same object inside one complete `json` fence, with only surrounding whitespace. Reject extra prose, multiple candidates, extra keys, invalid actions and incomplete outputs. Report raw strict-format compliance separately. This proposal was motivated by the completed calibration and does not rescore it.|
|Readout fairness|Map each arm's final action to the same four semantic labels. Do not interpret Jev probabilities and sampled-generation frequencies as identical uncertainty measures. Option orders and any extra calls must be declared and charged.|
|Code baseline|A reusable deterministic method may receive the same visible text. Manually parsed logic/facts are an assisted upper-bound condition and must be labeled and costed, not called an end-to-end code baseline. No per-test answer lookup.|
|Prior methods|Rule decomposition/entailment are established. Any intervention needs a stated difference and comparable help for both model families.|
|Metrics|Per-action confusion counts, pair-both-correct, wrong decisive answers where the reference is ASK, unnecessary ASK where decisive, order sensitivity, parse failures, latency and all tokens/calls. Keep repeats clustered by tree.|
|Stopping|Run the frozen grid once. Preserve passed cases and failures. Do not increase difficulty until Jev fails, or tune the ordinary model only until an appealing contrast appears.|

Thinking budget readiness is not yet established for this task. The completed
[generic calibration](../generation-calibration/README.md) found all outputs ended
naturally, but 13 thinking outputs failed its strict parser because of JSON fences.
That observation motivates the proposed wrapper contract; it does not prove a
task-specific budget or model capability. Hardware capacity alone is not a fair
comparison protocol.

The proposed [final-action interface](ACTION_INTERFACE.md) is implemented and
tested on synthetic parser fixtures. A separate [backend integration smoke](../action-backends/README.md)
now adds eight live Jev calls and eight local label-copy generations with checked
final-channel/termination extraction. It supplies neither ShARC predictions nor
a task-specific budget. The independent-review gate remains unchanged.

The [prospective paired scorer](PAIRED_METRICS.md) now checks per-condition
denominators, pair correctness, changed/invariant strata and invalid outputs
on synthetic software fixtures. It has not scored the queued task inputs.

The [direct-comparison draft](COMPARISON_DRAFT.md) specifies a 96-request Jev /
192-generation Qwen candidate grid. Its compiler revalidates saved reviews and
adjudication before preparing private requests and separate scoring references.
It cannot run inference. Five declared non-model controls (four constants and
last-history-answer copying) are implemented as shallow checks, not general
rule interpreters. The [execution core](RUNNER_DESIGN.md) now has durable-call,
budget and resumption tests. The [cross-condition analyzer](ANALYSIS_CONTRACT.md)
now passes synthetic journal checks and an offline audit of 16 historical
technical-smoke records. Real reviewed inputs and an exact execution freeze
remain outstanding; no live task run has occurred.

## Nearest-work screen and reuse ledger

Primary abstracts and bibliographic records checked 2026-09-30. The first four
rows are an initial screen. The [focused update](NEAREST_WORK_UPDATE.md) adds
two closer precedents with explicit inspection depth and baseline obligations.
Neither review is an exhaustive novelty search or reproduction.

|Source|Already established|Consequence for this project|Reuse this stage|
|---|---|---|---|
|[ShARC, Saeidi et al. 2018](https://aclanthology.org/D18-1233/)|Conversational interpretation of rules with clarification and rule-based/learned baselines.|Neither rule-action decisions nor asking for missing information is a new task.|60 existing training inputs repackaged with credit and CC BY-SA 3.0; no upstream implementation copied.|
|[Explicit Memory Tracker, Gao et al. 2020](https://aclanthology.org/2020.acl-main.88/)|Tracks whether rule conditions are satisfied and generates clarification questions.|A condition-status memory is not by itself a novel mechanism.|Abstract inspected; linked author implementation not run or forked.|
|[Discern, Gao et al. 2020](https://aclanthology.org/2020.emnlp-main.191/)|Discourse segmentation with per-unit entailment supports decisions and follow-up questions.|Rule splitting plus entailment cannot be claimed as first proposed here.|Abstract inspected; linked author implementation not run or forked.|
|[Explicit Alignment and Many-to-many Entailment, Luo et al. 2023](https://arxiv.org/abs/2310.13409)|Explicit document/user alignment and many-to-many entailment for conversational reading.|Any binding/alignment intervention must be distinguished from this line of work.|Abstract inspected; no code or weights imported.|
|[EXtrA-ShaRC, Ramos and Lipani 2024](https://um.org/umap2024/proceedings/)|Counterfactual-profile evaluation.|Changed-condition testing is not itself new.|Official abstract and pinned author README inspected; no fork or imported implementation.|
|[LDPC, Erwin et al. 2025](https://arxiv.org/html/2501.11335v1)|Few-shot decomposition with logic execution.|Do not claim a new decomposition paradigm or describe the full prior pipeline as training-free.|Targeted full-text sections inspected; no implementation run.|

The possible contribution is a **controlled, costed replacement-boundary study**
on reviewed decision contrasts, if the comparison reveals a useful, reproducible
boundary. It is not yet demonstrated, and this table does not establish novelty.
A ceiling result is also useful: publish it and stop this candidate rather than
manufacture a new failure. A model gap alone would not establish its cause or
justify a new algorithm.

## Sequence and stage gates

1. Deliver the [licensed blinded package](public-review/README.md). Two people
   independently complete all 60 items and disclose prior exposure/assistance.
2. Reconcile only after both are saved. Human adjudication and frozen reserves
   determine eligible primary pairs. Preserve ambiguity and source disagreement.
3. Freeze the exact prompts, adapters, wrapper parser, model settings, budgets,
   paired metrics, code baseline and stop rule. Validate interfaces without
   inspecting task predictions beforehand.
4. Execute one comparison on the reviewed development pilot under existing user
   authorization. Publish the entire grid, including no-gap/no-improvement results.
5. Decide whether new-material confirmation is justified. Only then pursue a
   separate confirmatory dataset or intervention claim.

The repository can presently demonstrate traceability and usable preparation.
It cannot yet demonstrate reliable rule-action performance or a publication-ready
finding. The public hook should invite checking the question, not announce the answer.
