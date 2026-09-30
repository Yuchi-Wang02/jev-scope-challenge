# Research map and evidence status

Start with the [series claims and limits](RESEARCH_CLAIMS.md) and
[current novelty assessment](NOVELTY_MATRIX.md). An earlier completed grid is the
[single-prefill Qwen control](research/finite-choice-readout/RESULTS.md), on the same public-source inputs.
A later [implementation/data audit](research/implementation-audit/README.md) adds no model calls and identifies two invisible-change label conflicts in the pinned EXtrA release.
The subsequent [QA4PC graph audit](research/qa4pc-audit/README.md) verifies 429 complete development compositions and retains eight cases with a missing formula variable.
Its [amended stage-attribution run](research/qa4pc-stage-attribution/CONTINUATION_RESULTS.md) now completes both models while preserving Qwen's original smoke stop.
The latest [answer-interface grid](research/qa4pc-answer-interface/RESULTS.md)
completed all 648 jobs on 12 new policy clusters, with six mappings and three
Qwen output routes. Generated semantic labels do not close the mean agreement gap.
Its subsequent [all-case semantic audit](research/qa4pc-answer-interface/SOURCE_AUDIT.md)
retains eight provisional final-label concerns and a unanimous-model counterexample.
No scores change; local retrospective review tooling is prepared, with zero reviews.
The tables below separate actual model runs, analyses of existing evidence,
and preparation that has no model result.

The original comparison used Jev and Qwen. Intermediate runs use a **historical
pinned Kev checkpoint based on Qwen3-4B-Base**. The payment-ownership study returns
to live Jev; it does not measure current Kev.
N0 is unchanged Base/native; N1 adds upstream Kev LoRA while retaining the native
LM head; K1 uses the adapted backbone and Kev pointer path. Laya was inspected
as related work and was not executed. See [credits and reuse](THIRD_PARTY_NOTICES.md).

## Completed model runs

|Study|Actual evidence and result|Scope and remaining limits|
|---|---|---|
|[Six-way answer interfaces](research/qa4pc-answer-interface/RESULTS.md)|162 Jev requests,162 Qwen prefills,324 Qwen generations. Across six repeated mappings: native 101/144, finite 85/144, generated letters 89/144, generated semantics 87/144. Five finite ties; zero generated invalids. All 162 paired letter first-logit vectors agree exactly.|12 new trees /24 scenarios, zero human labels. Semantic consistency improves but mean agreement does not. Finite/generated-letter differences are tie handling. Four-vote aggregation costs six calls. No stronger-model, matched-budget or specialization conclusion.|
|[QA4PC amended stage attribution](research/qa4pc-stage-attribution/CONTINUATION_RESULTS.md)|262 Jev requests and 262 Qwen prefills. Jev G 20/24 both mappings, F 19/24 and 20/24. Qwen G 14/24 and 16/24, F 12/24 and 14/24; direct D 13/24 and 19/24. Ten Qwen main ties.|12 trees /24 scenarios, zero new human labels. Outcome-aware semantic-gate amendment preserves original stop. F uses 2.33x G calls without consistent gain. Mapping/readout sensitivity, label assistance and absence of stronger/generated-label controls limit model claims.|
|[Single-prefill Qwen control](research/finite-choice-readout/RESULTS.md)|8 smoke +48 main physical forwards; 14,448 input and zero generated tokens; 10.672 session seconds. Source agreement 13/24 and 10/24, pairs 3/12 and 2/12; one exact tie invalid.|Same inspected 24 ShARC inputs, zero new human reviews. Prompt/verbalizer/readout change together. No consistent gain over JSON or copy-last; different sessions prevent controlled speedup claims. Closed without prompt search.|
|[Public-source contrast](research/source-label-screen/RESULTS.md)|12 ShARC dev trees /24 inputs; 48 distinct Jev requests and 96 Qwen3.5 generations. Jev native source agreement 18/24 in both mappings; Qwen direct 11/24 and 12/24; thinking 5/24 and 6/24 with 37/48 truncated. Last-answer copy 14/24. Local generation: 92,559 tokens, 2,983.875 seconds.|Zero project human reviews; title-only and other source-evidence concerns. Two prospective API readout repairs preserve strict failures. Source agreement is not verified correctness or independent confirmation. All raw data and both API readouts retained.|
|[Candidate coverage](research/candidate-completeness/RESULTS.md)|12 disjoint source users /72 inputs; 150 Jev requests and 150 Qwen3-4B native prefills including six smoke each. Jev 63/72 and 67/72; Qwen 34/72 and 30/72. Strict parents 3/12 and 0/12; grammar code 72/72.|Synthetic coverage premises, one wording family, zero new independent reviews. Jev errors are unnecessary explicit-ID deferrals. Native Qwen is not a reasoning-ceiling comparator. Both freezes published before main outputs. No adaptive follow-up on these grids.|
|[Fixed-budget Qwen control](research/candidate-completeness/REASONING_RESULTS.md)|Same 72 inputs, six smoke +144 main decisions; 69,771 generated tokens and 19,129 batched physical forwards. Scores 58/72 and 59/72; all 12 unknown-reference cases per mapping still receive a determined answer; strict parents 0/12.|Outcome-aware extra-compute comparison, not new independent data. 69/144 main traces truncated. An earlier six-case sampled smoke attempt is preserved separately; an explicit greedy repair preceded all v2 outputs. No third configuration searched.|
|[Payment ownership](research/payment-ownership/RESULTS_V02.md)|12 source users /48 constructed views; 192 main + six smoke live Jev requests. Both full and related conditions, both mappings: 48/48; parser 48/48. Smoke 5/6. 245,241 input tokens, zero retries; no follow-up.|Public simulated tau source, AI-authored requests. Two submissions cover the same 96 items, with conditional label agreement and a candidate-scope objection for 24 product-reference inputs; explicit-ID inputs remain 24/24 per condition. No adjudicated reference update. [Review disposition](research/payment-ownership/REVIEW_DISPOSITION.md). A documented launch-gate amendment followed the smoke error and preceded all main calls. No main unknown-reference cases or ordinary-model comparison.|
|[Cancellation scope](results/REPORT.md)|12 four-view cases / 48 texts; 384 formal records across Jev and Qwen, plus six smoke records. Primary complete cases: Jev 12/12, Qwen 8/12; grammar code 12/12.|Local pre-execution freeze; public release followed execution. Repeated mappings and rounds are not independent examples.|
|[Matched base](research/next-study/)|24 parents / 96 texts; 864 completed scientific forwards. N0/N1/K1 exploratory test: 85/111/98 correct out of 144 repeated decisions.|A 576-record stopped attempt is archived and excluded. The inspected test is now development/regression material.|
|[Input boundary](research/layout-boundary/)|Same matched-base corpus; 2,016 new scientific forwards and 2,592 logical rows including shared native records. Rankings change with layout/split.|No new independent dataset. Another 864 parity forwards and six warmups are reported separately.|
|[Evidence gap](research/evidence-gap/)|48 candidate parents / 288 texts; only 12 development parents / 72 texts scored, with 648 main + 108 null scientific forwards.|216 calibration/test texts remain unscored. Another 252 parity forwards and six warmups are separate. Program-derived labels.|
|[Fact extraction + execution](research/fact-execution/RESULTS.md)|Same 72 development texts; 1,656 scientific forwards. Primary N1 direct 31/72 versus facts + code 44/72; 14/18 missing fields became asserted values.|Another 552 parity forwards and six warmups are separate. Rewrites and reserved inputs remain unscored.|
|[Line evidence pilot](research/fact-execution/LINE_EVIDENCE_RESULTS.md)|Same 72 texts; 548 scientific forwards / 133,977 input tokens. Correct 29/72; false commitments 6/24; determined correct 11/48.|Failed its prewritten screen. No budget-matched direct control; no rewrite, reserved or Jev scores.|
|[Joint routing pilot](research/fact-execution/JOINT_RESULTS.md)|Same 72 texts; 514 scientific forwards / 191,738 input tokens, plus two warmups. Joint 34/72 versus both matched direct controls 31/72; 60/66 foreign lines became target evidence.|Failed both screens: false commitments 11/24, determined correct 21/48. Controls match either calls or input tokens, not both.|
|[Target switching](research/request-ownership/RESULTS.md)|24 newly constructed scenes / 48 views; 500 scientific forwards / 188,797 input tokens, plus two warmups. Joint 2/24 complete pairs becomes 23/24 with an ID gate; false commitments 7/12 to 0/12. Direct filtering remains 2/24; grammar code 24/24.|Passes its frozen directional diagnostic. Same-prefix IDs remove the earlier prefix shortcut, but sentence/policy grammar was already inspected. Zero independent human annotations.|

These are constructed diagnostics except the selected public-source screen.
Forward counts, repeated views and
derived rows must not be added together as independent benchmark examples.
Complete-case/parent/pair definitions also differ between studies. The earlier target-switch
gate corrects 30 view decisions with no regression in that run; its one remaining
field-assignment error and all direct-filter regressions are preserved in the report.

For individual records, use the [original result explorer](docs/explorer.html),
[line-evidence explorer](research/fact-execution/docs/line_explorer.html), and
[joint saved-query viewer](docs/joint_route.html). These replay evidence without
model calls. The [target-switch input explorer](docs/request_switch.html) shows
frozen texts, planned prompts and program references only; it contains no model
predictions and is not a blinded human-review instrument.

## Runtime preparation with actual generation

The [public-dev screen](research/source-label-screen/README.md) is now complete
and listed in the model-run table above. It is unreviewed source agreement,
not independent confirmation. The training-review queue below remains unscored.

The [Qwen3.5-4B technical smoke](research/baseline-readiness/QWEN35_SMOKE_RESULTS.md)
completed one BF16 GPU load and six generic generation calls (550 generated tokens,
one truncated thinking output). It preserves a zero-forward dependency failure
and pre-output amendments. This is not another research dataset or a demonstrated
stronger comparator; no closed study was rerun.

The following [generation calibration](research/generation-calibration/README.md)
adds 48 development-only calls over 12 new elementary fixtures and two seeds.
All calls end naturally; direct has 24/24 strict outputs with 22 content matches,
thinking has 11/24 strict outputs. The other 13 thinking finals are single
Markdown JSON blocks containing reference-matching objects, identified in a
separate post-run inspection. No thinking cap qualifies under the frozen strict
format gate. This is interface evidence, not 13 proven reasoning errors.

The separate [four-action backend integration](research/action-backends/README.md)
then completed 8 Jev calls and 8 local generations on four explicit label-copy
records, all returning the specified label. It validates mappings, token-grounded
final extraction and accounting, including one predeclared JSON-fence case.
It does not add ShARC predictions, independent labels or a capability ranking.

## Analyses of saved outputs and software checks

The [QA4PC structural audit](research/qa4pc-audit/README.md) covers 437 development
scenarios and 1,600 question rows. Of these, 429 have complete graphs and reproduce
their source labels; eight remain unexecutable with the complete-input contract.
This is source consistency, not model accuracy or independent semantic validation.
Its [next comparison design](research/qa4pc-audit/NEXT_EXPERIMENT_DESIGN.md) is not run.
The [selected next cohort](research/qa4pc-stage-attribution/README.md) has 12 trees,
24 scenarios and 56 condition questions after whole-tree overlap exclusions;
its 524-job grid was frozen before execution. The later Jev completion and Qwen
smoke stop are listed in the model-run table; the original freeze stays unchanged.

The computational analyses below add no model forwards or independent human annotations. A large number of
derived predictions is not a larger evaluated dataset.

|Analysis|What it adds|Interpretation boundary|
|---|---|---|
|[All-case QA4PC semantic audit](research/qa4pc-answer-interface/SOURCE_AUDIT.md)|24 scenarios /12 trees: four decisive-evidence flags, four rule-scope flags, ten intermediate concerns. Prepared two local source-only review slots.|AI-assisted, outcome-aware, not adjudication. Zero reference updates, new calls or completed human reviews. Model consensus does not establish label error.|
|[Ordinary-model readiness audit](research/baseline-readiness/README.md)|Pinned metadata for four checkpoints, installed-runtime registry and GPU inspection; identifies the greedy-control departure from Qwen's recommended thinking decoding.|Zero weights downloaded and zero inference. Weight bytes are not runtime memory; architecture registration is not a successful load. Closed-grid scores are unchanged.|
|[Decision-sufficiency specification lab](research/decision-sufficiency/README.md)|20 artificial examples, five invalid-input controls; a finite database enumerator checks 730 valid and rejects 180 inconsistent contracts. Distinguishes predicate-only answers from unique-target requirements.|Zero model calls or human annotations. Applies existing certain-answer semantics; software test counts are not empirical results. Does not relabel earlier experiments or authorize refunds.|
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
|[Candidate coverage review](research/candidate-completeness/review/README.md)|72 review-only inputs, offline interface and blank reviewer template. Jev/native model runs are now complete (table above), but these new labels have no independent human review.|Obtain separate review exports and document adjudication; do not claim later review makes these inspected inputs fresh confirmation.|
|[Evidence-gap label review](research/evidence-gap/review/)|Blank review material; 216 reserved calibration/test texts remain unscored.|Independent policy/label review and adjudication.|
|[Language-pair review](research/fact-execution/review/)|144 provisional AI-generated rewrite pairs, including a 12-pair procedural starter; no completed independent annotations or rewrite scores.|Verify preservation of facts, not only equal final decisions.|
|[Cited-fact model comparison](research/fact-execution/CITED_FACT_PLAN.md)|A design with a strict grammar-code citation control and software checks.|A separately frozen model comparison; code tests are not model evidence.|
|[ShARC external-data inventory](research/external-validation/), [task card](research/external-validation/TASK_CARD.md) and [licensed review package](research/external-validation/public-review/)|Train/dev source audit; frozen 30 pairs / 60 blinded items. The attributed CC BY-SA 3.0 package now distributes visible inputs with zero completed reviews or model scores.|Two independent reviews, adjudication, declared reserve workflow and a separate model protocol.|
|[Head-only versus joint training](research/next-study/PLAN.zh-CN.md)|Historical second-phase design; no training run or new checkpoint.|Fresh data, matched tuning/compute budgets, seeds and a new approved execution protocol.|

The [payment review disposition](research/payment-ownership/REVIEW_DISPOSITION.md)
records two submissions covering the same 96 full/related items and a scope objection
affecting 48 of those items. The 48 underlying inputs were already model-scored as
exploratory development material. Both original forms and process self-reports are
preserved; no reviewer-endorsed adjudication or updated references are claimed.

There is no held-out confirmation of
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
