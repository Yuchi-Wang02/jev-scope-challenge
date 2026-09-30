# Research map and evidence status

This repository contains one original Jev/Qwen comparison and seven subsequent
diagnostics. Later studies use a **historical pinned Kev-4B checkpoint based on
Qwen3-4B-Base**. Kev and Jev are distinct systems. Laya was inspected as related
work; it was not executed here. Read [credits and reuse](THIRD_PARTY_NOTICES.md)
before interpreting the project as a new architecture or upstream implementation.

## Completed work

|Study|Question and evidence|Boundary|
|---|---|---|
|[Cancellation scope](README.md)|12 four-view cases / 48 texts. 384 formal records across Jev and Qwen, plus six smoke records. Jev 12/12 vs Qwen 8/12 complete cases in the primary round.|Original local pre-execution freeze; public release followed execution. Artificial grammar, no independent human label audit.|
|[Matched base](research/next-study/)|24 parents / 96 texts. 864 completed scientific forwards. N0/N1/K1 test counts 85/111/98 out of 144 repeated decisions.|An earlier 576-record stopped attempt is archived and excluded from the completed-run headline. The inspected exploratory test is now a development/regression resource.|
|[Input boundary](research/layout-boundary/)|Same matched-base corpus; 2,016 new scientific forwards, 2,592 logical rows including shared native records. Historical anchors match; rankings depend on layout/split.|No new independent dataset. Includes 864 separate parity forwards and six warmups.|
|[Evidence gap](research/evidence-gap/)|48 candidate parents / 288 texts; only 12 development parents / 72 texts scored. 648 main + 108 null scientific forwards.|216 calibration/test texts unscored. Program-derived labels; 252 parity forwards and six warmups are separate.|
|[Evidence guards](research/evidence-guards/)|Reuses evidence-gap scores. 13 methods produce 8,424 derived predictions, with a known-grammar pure-code reference.|Post-hoc analysis with zero new model forwards; derived rows are not new samples.|
|[Fact extraction + execution](research/fact-execution/)|Reuses the 72 original development texts for a new task: 1,656 scientific forwards. Kev-LoRA/native primary direct 31/72 vs facts + code 44/72; 14/18 missing fields became asserted values.|552 parity forwards and six warmups are separate. 144 provisional rewrite pairs remain unreviewed and unscored.|
|[Line evidence pilot](research/fact-execution/LINE_EVIDENCE_RESULTS.md)|Same 72 original development texts; 548 new N1/native forwards. False commitments 6/24, but correct determined decisions only 11/48; 29/72 overall.|Prewritten screening rule failed. 548 calls / 133,977 input tokens, no budget-matched direct control; no rewrite, reserved or Jev scores.|
|[Joint routing pilot](research/fact-execution/JOINT_RESULTS.md)|Same 72 original texts; 514 new N1/native forwards. Joint 34/72 versus 31/72 for both matched direct controls; 60/66 other-request lines were assigned target fields.|Both screen conditions failed: 11/24 false commitments, 21/48 determined correct. Two warmups are separate. Controls match either calls or input tokens; no independent review, rewrite, reserved or Jev scores.|

Download and open the [offline line-evidence explorer](research/fact-execution/docs/line_explorer.html)
to inspect all 72 inputs and 548 saved judgments behind the failed pilot.
The [paired parent audit](research/fact-execution/PARENT_PAIRED_AUDIT.md)
shows determined correctness fell in 10 of 12 parent groups while false
commitments fell in eight; it recomputes saved decisions without new calls or
an inferential claim.
The [interactive cost sensitivity page](docs/risk_tradeoff.html) compares three
saved paths with newly derived always-defer and existing visible-text grammar
controls, making no new model calls. It shows exact optimal cost ranges under
two hypothetical deferral-cost conventions and displays unmatched call and
input-token budgets separately. Adding the omitted zero-call comparators changes
the earlier three-model interpretation. Its slider is an explainer, not a score.
The [16-way post-hoc oracle decomposition](research/fact-execution/LINE_ORACLE_DECOMPOSITION.md)
uses unavailable construction labels to diagnose binding errors; it adds no
model measurement.
The [joint-routing candidate](research/fact-execution/JOINT_ROUTE_PROTOCOL.md)
has now run with a call-matched direct control and an
[ID-only token-matched direct control](research/fact-execution/JOINT_TOKEN_CONTROL.md).
The latter uses 95,849 versus joint's 95,889 input tokens, but 286 rather than
228 calls. Both direct controls reached 31/72 with identical per-view predictions.
The [joint N1 execution freeze](research/fact-execution/JOINT_EXECUTION_PROTOCOL.md)
pins the 514 unique forwards and 191,738 input tokens that were executed across
the candidate and shared direct union. CI now verifies the raw results as well
as the unchanged pre-inference source. The [saved-query viewer](docs/joint_route.html)
shows every route and direct judgment; its filters make no model calls.
The [visible-ID gate replay](research/fact-execution/VISIBLE_ID_GATE_AUDIT.md)
uses only displayed request IDs to veto foreign records in saved joint outputs.
It changes 34/72 to 70/72, with 38 corrections and two regressions, while the
full grammar parser remains 72/72. This is post-hoc code-plus-saved-model
composition, with zero new forwards and no retrospective screen pass.
The original ID namespace perfectly encodes ownership; 216 unscored name
transformations and 16 software contract cases expose that boundary.
The [target-switch preparation](research/request-ownership/PROTOCOL.md) uses
24 newly constructed scenes / 48 paired views, with the same record block
queried for two same-namespace IDs. It reuses existing policy/sentence templates;
new scenes are not new independent policies or reviewed natural language.
The [completed target-switch diagnostic](research/request-ownership/RESULTS.md)
contains 500 new scientific forwards /188,797 input tokens and two unscored
warmups. Joint routing changes from 2/24 complete pairs and 7/12 false
commitments to 23/24 and 0/12 with the explicit-ID gate. Direct filtering stays
at 2/24 pairs, and known-grammar code is 24/24. The frozen directional rule
passes; this remains a constructed development diagnostic with no independent
human annotations. The [execution protocol](research/request-ownership/EXECUTION_PROTOCOL.md)
and scientific freeze retain their pre-inference contents.
The [input explorer](https://yuchi-wang02.github.io/jev-scope-challenge/request_switch.html)
displays all paired texts and their program references, without reading model
outputs. Its visible-ID overlay is a software rule; the page is not a blinded
human-review tool or a new evaluation result.
The [scope audit](research/fact-execution/JOINT_ROUTE_SCOPE_AUDIT.md) compares
related extraction work and demonstrates that one exclusive label cannot carry
two facts from the same line. That software test is not a model measurement.
The [paired multi-fact line stress](research/fact-execution/MULTIFACT_LINE_STRESS.md)
tests that interface limit on 56 existing development texts; all 112 packed
versions are unscored transformations and carry zero independent annotations.
The [external rule-data audit](research/external-validation/) identifies ShARC
as a candidate for a later four-way action task and publishes source structure
only; no ShARC model result, human mapping audit or dataset copy exists here.
Its [one-answer-flip inventory](research/external-validation/SHARC_PAIR_AUDIT.md)
counts exact train-only contrasts, excludes one contradictory visible-input
group and likewise contains no model evaluation.
The [ShARC review protocol](research/external-validation/SHARC_REVIEW_PROTOCOL.md)
freezes 30 train-only pairs as 60 blinded items and defines a two-reviewer,
adjudication and reserve-selection workflow. Its annotations and model scores
remain zero.

Different tables have different denominators. Do not compare a six-view
complete-parent score with an eighteen-order complete-parent score, add repeated
views to claim independent sample size, or describe accumulated forward counts
as new benchmark examples. N0 is unchanged Base/native; N1 is the same Base plus
upstream Kev LoRA/native; K1 uses the same adapted backbone and Kev pointer path.

## What is not complete

Independent human annotations remain zero. There is no held-out confirmation of
the evolving research method, language-transfer result, head-only training run,
new learned checkpoint, Hugging Face dataset/model release, or submitted paper
from this project. Calibration in the earlier pilot does not make later raw
conditional probabilities calibrated. Old public tests and exposed development
inputs cannot become fresh confirmation by renaming their split.

The original [label-review pack](research/evidence-gap/review/) and the
[language-pair review pack](research/fact-execution/review/) serve different
purposes: policy/label interpretation versus preservation of facts across a
rewrite. Equal final decisions alone do not establish equal facts.

## Reproduce and contribute

Use Python 3.10 and the root requirements for offline checks; see
[REPRODUCIBILITY.md](REPRODUCIBILITY.md). They require no model credentials or
weights. Keep full Git history (`git clone` without `--depth`), because the
fact-execution audit checks source blobs at its pre-inference commit. Offline
replay proves artifact consistency, not independent scientific replication.

Fresh inference has different requirements. The original cancellation study
has an isolated-output replication CLI; later scientific runners preserve their
published output and reject overwriting it. Do not imply that an unmodified
checkout can simply rerun all GPU studies into the existing results directories.
Use a separately versioned replication with explicit output/provenance handling.

Useful contributions include independently justified label objections, bounded
language rewrites, reproductions with exact prompts/costs, and fixes that preserve
historical evidence. Record the study and commit, explain any changed assumptions,
and include upstream attribution. Human exports require provenance and
adjudication before they can support a confirmation claim or open a new run.
Use the [contribution guide](CONTRIBUTING.md) and the repository's structured
GitHub issue forms to make objections and reproductions reviewable.

The first [bounded line-by-line pilot](research/fact-execution/LINE_EVIDENCE_RESULTS.md)
failed its screening rule, so that method is not advancing unchanged. A
[strict pure-code citation control](research/fact-execution/CITED_FACT_PLAN.md)
and [12-pair procedural review starter](research/fact-execution/review/README.md)
are prepared; those controls are not human labels. Independent review
remains a separate gate; a valid CSV or a green CI
run cannot certify reviewer independence or semantic truth.
