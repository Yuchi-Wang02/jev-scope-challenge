# Current novelty and reuse boundaries

This is a series-wide synthesis of the repository's existing source registers
and completed diagnostics, with a bounded primary-source check. It is not an
exhaustive literature review or a claim of priority. It extends the scope of
the historical [matched-base matrix](research/next-study/novelty_matrix.md)
without changing that document or any frozen study. Pair it with the
[current claim ledger](RESEARCH_CLAIMS.md) and [attribution inventory](THIRD_PARTY_NOTICES.md).

**Current contribution: inspectable experimental artifacts, diagnostic contrasts,
and documented failures of particular compositions. A novel general method or
paper-level contribution has not been established.**

The public-source screen also requires a stricter measurement distinction:
matching a ShARC label is not proof that a decision follows from its visible
rule. The [all-pair evidence audit](research/source-label-screen/SOURCE_REVIEW.md)
retains concrete source concerns without changing the frozen references.
The [additional nearest-work check](research/external-validation/NEAREST_WORK_UPDATE.md)
adds direct precedents for ShARC shortcut controls and condition-question
expression trees; neither becomes a new contribution by using Jev.
The [QA4PC source audit](research/qa4pc-audit/README.md) now implements standard
three-valued composition checks on released annotations. Its 429/429 consistency
result is a software/data check, not a model score or a novel executor. A proposed
stage comparison must control human graph assistance in both corresponding arms.
The [completed Jev portion](research/qa4pc-stage-attribution/RESULTS.md) does so:
facts+code has no consistent advantage over graph-direct despite more calls.
Qwen's original gate stopped before main evaluation; a separately frozen amendment
then completed only its unexecuted jobs. Facts+code also fails to improve Qwen
over graph-direct, and answer mapping changes many decisions. This is a bounded
negative intervention/interface-sensitivity result, not a novel decomposition method.

The subsequent [fresh-cluster six-way interface control](research/qa4pc-answer-interface/RESULTS.md)
completes finite letters, same-prompt generated letters and generated semantic
labels. Cleaner outputs and more stable semantic labels do not improve mean
source agreement here. The letter bridge attributes its observed difference to
tie handling. [Primary method sections](research/qa4pc-answer-interface/RELATED_WORK.md)
already establish option/token sensitivity and voting/calibration precedents;
this diagnostic adds an auditable bounded comparison, not a new decoder.

## Components, precedents and what this repository adds

|Component or observation|Existing work or ordinary component|Current contribution and boundary|
|---|---|---|
|Cancellation scope and quoted/current instructions|Laya's pinned [Feishu diagnostic](https://github.com/NandhaKishorM/laya/blob/9d955671415fc19f069b9cc998928075c1f255ec/research/benchmarks/feishu_zh/README.md) is a close task neighbor. [CheckList](https://aclanthology.org/2020.acl-main.442/) and [Contrast Sets](https://aclanthology.org/2020.findings-emnlp.117/) precede this project's behavioral and controlled-change tests.|Our constructed cases and saved Jev/Qwen comparison are inspectable artifacts. Scope testing, matched perturbations and complete-pair scoring are not claimed as new evaluation theory.|
|Base/native versus adapted/native versus pointer|Kev's [native/adapted probe](https://github.com/jaredpalmer/kev/blob/0c142becde423a0c68ec857f7831dac0315588a1/scripts/base_mmlu_probe.py) and [historical model implementation](https://github.com/jaredpalmer/kev/blob/29d71c78368657b3a522729a01c748ea15272abc/kev/model.py) are direct precedents and reused implementation.|Pinned loaders, budgets, local parity audits and new diagnostic records. No pointer-architecture invention or clean isolation of head capacity. N1/K1 contain upstream-trained adaptation.|
|State/question layout and answer-order controls|Input serialization and candidate perturbations already belong to model/interface evaluation; the upstream Kev encoder defines these boundaries.|The [layout ablation](research/layout-boundary/) documents a ranking change and byte-identical native controls in this historical stack. It is an engineering diagnostic, not a generally optimal layout or new architecture.|
|Null subtraction, order averaging and confidence thresholds|[Calibrate Before Use](https://proceedings.mlr.press/v139/zhao21c.html) estimates answer bias with content-free input; [Surface Form Competition](https://aclanthology.org/2021.emnlp-main.564/) supplies a likelihood-ratio precedent. Averaging and thresholding are standard controls.|Our meaningful no-evidence null and typed-score subtraction are an ablation, not those papers' exact setting or a new calibration algorithm. [Evidence-gap results](research/evidence-gap/) show why higher total accuracy can coexist with more false commitments.|
|Missing-field guards and finite-world policy execution|Known-grammar parsing, explicit policy rules and enumeration are ordinary program components. [Binder](https://arxiv.org/abs/2210.02875) is an existing language-model/symbolic-program composition framework.|[Guards](research/evidence-guards/) and [facts plus execution](research/fact-execution/RESULTS.md) isolate consequences of adding declared policy knowledge. This is a different implementation, not a Binder reproduction or a new neural-symbolic paradigm.|
|Evidence spans, support/refute/insufficient states, and linked fields|[FEVER](https://aclanthology.org/N18-1074/) links verification labels to sentence evidence; [DocRED](https://aclanthology.org/P19-1074/) studies document-level entities and relations.|The [line and joint pilots](research/fact-execution/JOINT_ROUTE_SCOPE_AUDIT.md) audit a narrow prompted interface on controlled records. Evidence selection, attribution and joint binding are not first introduced here. Both executed pilot screens failed.|
|Visible-ID gating of saved routes|Extracting an explicit ID from a supported sentence and testing equality is ordinary deterministic validation. Composition with an extractor does not make equality a new learned method.|The [post-hoc replay](research/fact-execution/VISIBLE_ID_GATE_AUDIT.md) records 38 corrections, two regressions and a perfect prefix shortcut. These are useful failure cases, not independent validation or proof that gating always helps.|
|Same-prefix target switching|The controlled-change idea has the behavioral/contrastive precedents above; the gate and executor are existing components in this repo.|[24 new scenes](research/request-ownership/RESULTS.md) remove the old prefix cue while reusing sentence/policy templates. Joint 2/24 becomes gated 23/24 complete pairs; direct filtering stays 2/24 and grammar code reaches 24/24. The result identifies a bounded attribution failure; it does not establish a new general algorithm.|
|Field error remaining after correct request selection|Entity/field relationships are part of established information extraction; explicit scope validation cannot certify every semantic dimension.|The latest saved trace separates a correct ID decision from an incorrect field assignment. It is an observable pipeline failure, not evidence of the model's internal causal mechanism.|
|Multi-fact lines, language rewrites and external rule tasks|Richer relation extraction and language/program composition already exist in the cited work. Wider task coverage is not novel merely because it is new to this repo.|The [multi-fact analysis](research/fact-execution/MULTIFACT_LINE_STRESS.md) checks representational reachability; [rewrite](research/fact-execution/review/) and [external-data](research/external-validation/) artifacts are preparation. Transfer has not been tested or established.|

## Reuse is separate from scientific novelty

- The repository is not a GitHub fork of Kev or Laya. It does vendor unchanged,
  pinned Kev source under Apache-2.0 and executes pinned pretrained Qwen and
  upstream-trained Kev artifacts. The [reuse inventory](THIRD_PARTY_NOTICES.md)
  records exact revisions, licenses and checksums.
- Laya is a related-work and design reference. No Laya implementation,
  checkpoint, dataset or saved result records are incorporated in these
  experiments, and no Laya model evaluation ran here.
- Citation of a source is not replication of its results. Binder, FEVER,
  DocRED, CheckList, Contrast Sets and the calibration papers are precedents;
  this repository does not report new evaluations on their benchmarks.
- A new implementation or a combination of standard components can be useful.
  That usefulness does not establish that the method is new, necessary,
  computationally superior or robust outside the declared grammar.

## What the present evidence does and does not distinguish

The current results distinguish several observable pipeline errors: wrong
actions despite sufficient evidence, unjustified commitment when evidence is
missing, foreign records accepted as evidence, and target records assigned to
the wrong field. Raw traces, pure-code and always-defer controls, failed screens,
and disclosed regressions make those distinctions inspectable.

They do not yet distinguish a broadly necessary model capability from a weakness
of one prompt/readout/representation. Pure code already solves the declared
grammar, human submissions do not settle the payment scope objection, and multiple later analyses
reuse 12 familiar development parents. The target-switch study's 24 scenes and
candidate-coverage study's 12 new source users add instances, not evidence of
unseen language structure. No claim of independent confirmation, model
necessity, broad small-model substitution or language transfer follows.

This matrix records unresolved contribution boundaries. It does not select or
authorize a new experiment. The older [source register](research/next-study/related_work.md),
[missing-evidence register](research/evidence-gap/related_work.md) and
[extraction scope audit](research/fact-execution/JOINT_ROUTE_SCOPE_AUDIT.md)
retain their narrower context and additional sources.

## 2026-09-30 addition: payment ownership

The [new live-Jev diagnostic](research/payment-ownership/RESULTS_V02.md) adapts
Sierra's pinned tau retail rules and simulated records. It reuses target-switch,
contrast and oracle-style diagnostic ideas; it introduces no new binding algorithm.
Jev and the finite parser match the original main references. One ambiguous smoke case fails;
the resulting launch amendment is disclosed. Current contribution: a reproducible
bounded result with source provenance and retained failure, not a general benchmark
or model replacement finding. The [bounded nearest-work review](research/payment-ownership/RELATED_WORK.md)
includes entity binding, Legible Failures and When History Lies. Two reviewers have
since submitted judgments on the same 96 items, conditionally agreeing with original
references while raising a scope objection for 24 product-reference inputs. See the
[disposition](research/payment-ownership/REVIEW_DISPOSITION.md). Reviewer-endorsed adjudication,
ordinary-model comparison and independent confirmation remain incomplete.

The [completed candidate-coverage diagnostic](research/candidate-completeness/RESULTS.md)
tests an explicitly supplied coverage condition on 12 disjoint source users.
Jev's unnecessary explicit-ID deferrals contrast with Qwen's predominantly
accepting native readout. The known-grammar baseline solves all 72 inputs.
Closed/open candidate-set reasoning and abstention are not new; see the
[bounded context-sufficiency review](research/candidate-completeness/RELATED_WORK.md).
Current contribution is an inspectable controlled failure and negative controls,
not a new abstention algorithm or causal model explanation. New independent labels,
capable ordinary-model comparison and transfer beyond one template family remain
gates before stronger claims. The [fixed-budget reasoning control](research/candidate-completeness/REASONING_RESULTS.md)
is now complete: it improves Qwen's aggregate correctness while leaving every
unknown-reference case committed in both mappings. This is a baseline check,
not a new reasoning method. The [post-result literature check](research/candidate-completeness/RELATED_WORK_POSTRUN.md)
also identifies direct precedents in prompt-induced abstention and evidence boundaries.

The [ordinary-model readiness audit](research/baseline-readiness/README.md) further
qualifies the fixed-budget result: Qwen's pinned model card recommends sampling
for thinking and warns against greedy decoding. Our greedy run followed its own
protocol but is not the recommended-settings capability reference. Model-family
claims need that missing comparison, separately reviewed material, and explicit
precision/template/budget controls. The audit acquired no model or inference data.

Later [runtime smoke](research/baseline-readiness/QWEN35_SMOKE_RESULTS.md) and
[output-budget calibration](research/generation-calibration/README.md) use actual
local Qwen3.5 generations, but only on generic development fixtures. The strict
parser, generated-token presence penalty and completion-based cap selection are
ordinary engineering preparation. They do not supply the missing natural-language
comparison or constitute an algorithmic contribution.

## 2026-09-30 addition: external rule-action comparison

The [focused nearest-work update](research/external-validation/NEAREST_WORK_UPDATE.md)
adds EXtrA-ShaRC and LDPC, with primary sources and inspection limits. We cannot
claim novelty for changed-condition testing or rule decomposition with logic.
A frozen end-to-end pipeline is a testable constraint, not a novelty certificate.
The [task card](research/external-validation/TASK_CARD.md) remains a candidate
replacement-boundary comparison; human review, task predictions, confirmation
and any useful new method remain incomplete. Published adapter checks establish
technical readiness only. New citations are not forks or reproduced baselines.

## Decision sufficiency: a specification example, not a method claim

The [executable contract lab](research/decision-sufficiency/README.md) distinguishes
a predicate answer that is invariant across candidate orders from identifying one
order. [Certain-answer and query-completeness literature](research/decision-sufficiency/RELATED_WORK.md)
directly precedes this distinction's possible-world implementation. The program
already solves the declared finite schema; 730 finite software checks are not a
benchmark score or evidence of language-model failure. No new model experiment,
independent annotation, theorem or operational demand has been established.
Keep this branch as documentation unless a real predicate-before-identity need
and separately reviewed natural-language test justify further work.

## Single-prefill finite-choice control: a measured baseline

The [completed Qwen3.5 control](research/finite-choice-readout/RESULTS.md) uses
standard single-token candidate logits, softmax normalization and option mapping.
It adds no algorithmic novelty. Source agreement is 13/24 and 10/24, without
consistent gain over direct JSON; one exact tie is invalid. The negative result
and explicit probability-mass/runtime accounting strengthen the baseline record,
not a dedicated-model replacement claim. Inputs are reused, source truth remains
unadjudicated, and prompt/verbalizer/readout changes are confounded. No upstream
implementation was forked; ShARC-derived input plans retain CC BY-SA attribution.

## Implementation and data reuse audit

The [source inspection](research/implementation-audit/README.md) finds that a
named heuristic's setup uses annotation-derived question inventories; comparing
it as a text-only baseline would conceal assistance. EXtrA already supplies
counterfactual profiles, but the pinned release has two identical-visible-input
pairs with conflicting actions under our input contract and policy overlap with
our inspected screen. These are dataset/contract diagnostics, not a new method.
QA4PC's supplied graphs offer a possible assisted-stage comparison; using them
requires attribution, validated scope and symmetric access, not novelty language.
