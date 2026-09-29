# Research map and evidence status

This repository contains one original Jev/Qwen comparison and five subsequent
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

Next development work is a cited-fact extraction contract and language-transfer
protocol. Independent review remains a separate gate; a valid CSV or a green CI
run cannot certify reviewer independence or semantic truth.
