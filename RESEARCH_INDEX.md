# Research map and evidence status

Start with the [series claims and limits](RESEARCH_CLAIMS.md) and
[current novelty assessment](NOVELTY_MATRIX.md). The latest completed model run
is the [target-switch diagnostic](research/request-ownership/RESULTS.md).
The tables below separate actual model runs, analyses of existing evidence,
and preparation that has no model result.

The original comparison used Jev and Qwen. Later runs use a **historical pinned
Kev checkpoint based on Qwen3-4B-Base**, not current Kev or new Jev measurements.
N0 is unchanged Base/native; N1 adds upstream Kev LoRA while retaining the native
LM head; K1 uses the adapted backbone and Kev pointer path. Laya was inspected
as related work and was not executed. See [credits and reuse](THIRD_PARTY_NOTICES.md).

## Completed model runs

|Study|Actual evidence and result|Scope and remaining limits|
|---|---|---|
|[Cancellation scope](results/REPORT.md)|12 four-view cases / 48 texts; 384 formal records across Jev and Qwen, plus six smoke records. Primary complete cases: Jev 12/12, Qwen 8/12; grammar code 12/12.|Local pre-execution freeze; public release followed execution. Repeated mappings and rounds are not independent examples.|
|[Matched base](research/next-study/)|24 parents / 96 texts; 864 completed scientific forwards. N0/N1/K1 exploratory test: 85/111/98 correct out of 144 repeated decisions.|A 576-record stopped attempt is archived and excluded. The inspected test is now development/regression material.|
|[Input boundary](research/layout-boundary/)|Same matched-base corpus; 2,016 new scientific forwards and 2,592 logical rows including shared native records. Rankings change with layout/split.|No new independent dataset. Another 864 parity forwards and six warmups are reported separately.|
|[Evidence gap](research/evidence-gap/)|48 candidate parents / 288 texts; only 12 development parents / 72 texts scored, with 648 main + 108 null scientific forwards.|216 calibration/test texts remain unscored. Another 252 parity forwards and six warmups are separate. Program-derived labels.|
|[Fact extraction + execution](research/fact-execution/RESULTS.md)|Same 72 development texts; 1,656 scientific forwards. Primary N1 direct 31/72 versus facts + code 44/72; 14/18 missing fields became asserted values.|Another 552 parity forwards and six warmups are separate. Rewrites and reserved inputs remain unscored.|
|[Line evidence pilot](research/fact-execution/LINE_EVIDENCE_RESULTS.md)|Same 72 texts; 548 scientific forwards / 133,977 input tokens. Correct 29/72; false commitments 6/24; determined correct 11/48.|Failed its prewritten screen. No budget-matched direct control; no rewrite, reserved or Jev scores.|
|[Joint routing pilot](research/fact-execution/JOINT_RESULTS.md)|Same 72 texts; 514 scientific forwards / 191,738 input tokens, plus two warmups. Joint 34/72 versus both matched direct controls 31/72; 60/66 foreign lines became target evidence.|Failed both screens: false commitments 11/24, determined correct 21/48. Controls match either calls or input tokens, not both.|
|[Target switching](research/request-ownership/RESULTS.md)|24 newly constructed scenes / 48 views; 500 scientific forwards / 188,797 input tokens, plus two warmups. Joint 2/24 complete pairs becomes 23/24 with an ID gate; false commitments 7/12 to 0/12. Direct filtering remains 2/24; grammar code 24/24.|Passes its frozen directional diagnostic. Same-prefix IDs remove the earlier prefix shortcut, but sentence/policy grammar was already inspected. Zero independent human annotations.|

All of these are constructed diagnostics. Forward counts, repeated views and
derived rows must not be added together as independent benchmark examples.
Complete-case/parent/pair definitions also differ between studies. The latest
gate corrects 30 view decisions with no regression in that run; its one remaining
field-assignment error and all direct-filter regressions are preserved in the report.

For individual records, use the [original result explorer](docs/explorer.html),
[line-evidence explorer](research/fact-execution/docs/line_explorer.html), and
[joint saved-query viewer](docs/joint_route.html). These replay evidence without
model calls. The [target-switch input explorer](docs/request_switch.html) shows
frozen texts, planned prompts and program references only; it contains no model
predictions and is not a blinded human-review instrument.

## Analyses of saved outputs and software checks

These add no model forwards or independent human annotations. A large number of
derived predictions is not a larger evaluated dataset.

|Analysis|What it adds|Interpretation boundary|
|---|---|---|
|[Evidence guards](research/evidence-guards/)|13 methods over saved evidence-gap scores; 8,424 derived predictions and a grammar-code reference.|Post-hoc development analysis.|
|[Parent-paired audit](research/fact-execution/PARENT_PAIRED_AUDIT.md)|Recomputes line-pilot changes across 12 parents: determined correctness falls in 10; false commitments fall in eight.|Clustered descriptive analysis, not population inference.|
|[Cost sensitivity](docs/risk_tradeoff.html)|Compares three saved N1 paths, always-defer and grammar code under two explicit loss conventions.|Hypothetical costs; model call/token budgets differ. Added zero-call comparators change the earlier three-path interpretation.|
|[Oracle decomposition](research/fact-execution/LINE_ORACLE_DECOMPOSITION.md)|16 counterfactual corrections diagnose extraction and binding failures.|Uses unavailable construction labels; counterfactual scores are not model results.|
|[Visible-ID gate replay](research/fact-execution/VISIBLE_ID_GATE_AUDIT.md)|Saved joint outcomes change from 34/72 to 70/72, with 38 corrections and two regressions; code remains 72/72. Also exposes the original ID-prefix shortcut.|Post-hoc; cannot turn the failed original screen into a pass. Its 216 name transformations were not model-scored.|
|[Route interface audit](research/fact-execution/JOINT_ROUTE_SCOPE_AUDIT.md) and [multi-fact stress](research/fact-execution/MULTIFACT_LINE_STRESS.md)|Shows that one exclusive route cannot express two target facts on one line; stress checks 56 paired development texts / 112 packed versions.|Software reachability, not model performance or new independent examples.|

The [joint token control](research/fact-execution/JOINT_TOKEN_CONTROL.md) uses
95,849 input tokens versus joint's 95,889, but 286 versus 228 calls. Its shared
physical execution is included in the joint run above. Saved-output analyses,
shared records and zero-call controls should not be counted as additional runs.

## Prepared or designed, with no model result

|Work|Current state|Required before interpreting it as confirmation|
|---|---|---|
|[Evidence-gap label review](research/evidence-gap/review/)|Blank review material; 216 reserved calibration/test texts remain unscored.|Independent policy/label review and adjudication.|
|[Language-pair review](research/fact-execution/review/)|144 provisional AI-generated rewrite pairs, including a 12-pair procedural starter; no completed independent annotations or rewrite scores.|Verify preservation of facts, not only equal final decisions.|
|[Cited-fact model comparison](research/fact-execution/CITED_FACT_PLAN.md)|A design with a strict grammar-code citation control and software checks.|A separately frozen model comparison; code tests are not model evidence.|
|[ShARC external-data inventory](research/external-validation/) and [review protocol](research/external-validation/SHARC_REVIEW_PROTOCOL.md)|Train/dev source audit and train-only selection of 30 pairs / 60 blinded items. Public source summaries only; no public dataset copy, completed human review or model scores.|Two-reviewer review, adjudication and the declared selection workflow.|
|[Head-only versus joint training](research/next-study/PLAN.zh-CN.md)|Historical second-phase design; no training run or new checkpoint.|Fresh data, matched tuning/compute budgets, seeds and a new approved execution protocol.|

Independent human annotations remain zero. There is no held-out confirmation of
the evolving method, language-transfer result, new learned checkpoint, Hugging
Face dataset/model release, or submitted paper from this project. Earlier
calibration does not calibrate later raw probabilities. Public development inputs
cannot become untouched confirmation by renaming their split.

The series-level [claims](RESEARCH_CLAIMS.md) and [novelty matrix](NOVELTY_MATRIX.md)
describe the current evidence. The earlier
[matched-base claims](research/next-study/claims.md) and
[matched-base novelty matrix](research/next-study/novelty_matrix.md) retain their
study-specific scope; they are not a current assessment of the whole series.
Frozen protocols and preparation manifests preserve their creation-time status;
completed runtime and result reports establish what subsequently ran.

## Reproduce or challenge a result

Use Python 3.10, root requirements and full Git history for the
[offline checks](REPRODUCIBILITY.md); source audits inspect historical commits.
No weights or credentials are needed. Replay establishes artifact consistency,
not independent inference replication, reviewer independence or semantic truth.

Only the original cancellation study has an isolated-output live replication
CLI. Later scientific runners protect their published output and reject
overwriting it. Fresh inference needs a separately versioned replication with
explicit output and provenance handling, not a rerun into existing directories.

Use [CONTRIBUTING.md](CONTRIBUTING.md) and the structured issue forms for a label
objection, minimal counterexample or reproduction. Identify the study and commit,
explain the assumptions, retain exact prompts/costs, and credit upstream work.
Human exports require provenance and adjudication; a valid CSV or green CI does
not automatically authorize inference or establish independent labels.
