# Milestone audits and next decisions

This log separates completed work from research validity. Each milestone records
the objective, actual evidence, plan-versus-reality gap, next action and public
presentation. It does not claim a paper is ready.

## 2026-09-30: QA4PC source graphs and stage-attribution feasibility

Follow-up: [cohort preparation](research/qa4pc-stage-attribution/README.md)
reconstructed the frozen pending training queue and found three overlapping
trees /zero exact utterance IDs. Excluding them, the incomplete graph and four
EXtrA trees leaves 52 eligible trees /365 scenarios. A label-independent hash
selection fixes 12 trees /24 scenarios /56 condition questions. This implies
512 main decisions across two models, two mappings and D/G/F/L, still unrun.
The compiler and runner subsequently froze 524 jobs: 512 main and 12 smoke,
77,528 local input tokens and 1,416,558 Jev planning units. Five new execution
tests and the 293-test full suite passed before execution. Next is the committed
Jev/Qwen run; no performance result is claimed by this preparation entry.

- Objective: establish whether supplied graphs and condition labels support
  separating fact interpretation from logical execution.
- Reality: 437 dev scenarios /60 trees /1,600 condition rows join exactly. One
  graph lacks Q1, affecting eight scenarios; the remaining 429 compositions
  reproduce source final labels. No source edits or new inference.
- Verification: original safe-parser implementation, exhaustive binary truth
  tables, malformed-input tests, pinned byte checks and a second source download
  reproduce the derived report. All 193 shared dev/test graphs were inspected;
  test scenario and label files were not fetched.
- Gap: source consistency is not independent semantic truth. Four EXtrA-overlap
  trees cover 35 scenarios. Explicit reuse terms and comparison with the pending
  training review queue remain to be resolved before any independence claim.
- Decision: retain the eight unavailable scenarios; do not infer a repair.
  Publish [the audit](research/qa4pc-audit/README.md), not upstream dataset text.
- Next: implement the [bounded stage comparison](research/qa4pc-audit/NEXT_EXPERIMENT_DESIGN.md),
  with graph-assisted direct control, model facts plus code, and separately marked
  supplied-fact execution. No model cohort or query plan is frozen yet.
- Presentation: a transparent reading-versus-execution diagnostic, crediting
  QA4PC's existing decomposition framework. No novel-method or replacement claim.

## 2026-09-30: inspect reusable implementations and the EXtrA release

- Objective: locate prior implementations and a useful next causal contrast,
  rather than construct another uncredited decomposition pipeline.
- Reality: audited all 100 EXtrA original/counterfactual pairs, spanning 40 trees.
  Two pairs have identical four-field visible inputs but different source actions;
  three entire pairs are unchanged. Seven trees overlap our prior screen.
- Verification: byte-pinned sources, ID-based joins, full-field comparison,
  per-pair hashes and executable replay. No new model calls or human labels.
- Gap: the Verma smart heuristic uses annotation-derived question inventories;
  it is not a drop-in same-information baseline. LDPC implementation availability
  remains unestablished by the bounded search. QA4PC data metadata was located,
  but contents and reuse terms are not yet validated.
- Decision: do not score EXtrA as fresh independent confirmation or repair its
  labels ourselves. Publish [the audit](research/implementation-audit/README.md)
  without redistributing upstream files or claiming an implementation reproduction.
- Next: inspect QA4PC's supplied graphs and fact labels for controlled stage
  attribution. Explicitly account for that human assistance in every model arm.

## 2026-09-30: close the one-prefill ordinary-model control

- Objective: measure an existing finite-choice readout against the prior direct
  JSON interface on exactly the same source inputs, with explicit compute bounds.
- Reality: 56/56 physical prefills, smoke 8/8, 14,448 input tokens, zero generated
  tokens and 10.672 session seconds. Source agreement 13/24 and 10/24, pairs 3/12
  and 2/12; one exact stored-logit tie counted invalid. No retries or overruns.
- Gap: the observed lower callback times accompany prompt/verbalizer changes and
  a different session. Neither consistent semantic gain nor a new method emerged.
  Human labels and independent confirmation remain missing for this source slice.
- Audit: immutable pre-execution freeze, logit/decision and cost replay, all
  per-item transitions retained. This does not validate source truth.
- Decision: close without prompt/precision search. Publish the measured tradeoff
  and all cases in the shared replay. Preserve this as a baseline, not a success
  story about replacing Jev. [Full stage audit](research/finite-choice-readout/INTERPRETATION.md).
- Next: audit whether the next task adds a distinct decision need and causal
  contrast. Keep the separate pending human-review queue unscored.

## 2026-09-30: close the public-source screen and audit its measurement target

- Objective: complete the frozen 12-tree Jev / Qwen3.5 comparison with paired
  source agreement, failed-output denominators, costs and an inspectable replay.
- Reality: 48 distinct API jobs and 96 local generations returned. Native Jev
  scores 18/24 in each order; direct Qwen 11/24 and 12/24; last-answer copy 14/24.
  Thinking truncates 37/48 times and scores 5/24 and 6/24 under the fixed cap.
- Verification: all 96 local token sequences re-decoded with the pinned tokenizer;
  offline extraction/scoring replay agrees. All 24 selected source rows match the
  official archive. The existing 270-test suite passes.
- Gap: strict API execution needed two disclosed readout repairs. A source audit
  completed before reading scores found a title-only rule and other sufficiency
  concerns. Labels remain unchanged; no new human adjudication or confirmation.
- Decision: close this grid without cap extension or prompt search. Preserve the
  evidence in [results](research/source-label-screen/RESULTS.md) and the
  [replay](docs/source_label_screen.html). The original training queue stays unscored.
- Next: inspect a bounded finite-choice local readout as an outcome-aware interface
  diagnostic, with an explicit new freeze before inference. Semantic adjudication
  and new confirmation material remain separate paper requirements. See the
  [full interpretation](research/source-label-screen/INTERPRETATION.md).

## 2026-09-30: preserve two API stops and finish the original 48 requests

- Objective: obtain native decisions while keeping probability-field quality and
  protocol failures separately auditable.
- Reality: the original strict run stopped after 23 requests at a probability
  sum of 0.99. A separately frozen repair stopped after seven new requests at
  native choice C=0.38 versus displayed maximum B=0.39. Both ledgers remain intact.
- Repair: [final native-choice policy](research/source-label-screen/FINAL_READOUT.md)
  accepts only valid native action/core fields for the primary view and reports
  metadata issues plus unique displayed argmax separately. It sends only the
  remaining 18 requests; no response is re-requested or probability normalized.
- Evidence: [offline API audit](research/source-label-screen/results/jev_audit.json)
  accounts for all 48 distinct original jobs, 30,196 input /2,160 output tokens,
  and exactly those two metadata anomalies. API latency sum is 7.361 seconds,
  excluding setup and pauses. Source agreement is not scored in this audit.
- Gap: the initially frozen strict experiment did not complete. The final view
  is an adaptive interface repair, not improved model reasoning or confirmation.
  Qwen's original fixed grid is still running; no cross-model ranking is justified.
- Next: finish or budget-stop that live grid, verify raw token outputs, publish
  both strict and repaired views with cost and failed-output denominators, and
  then make the next research decision. No further readout repair in this screen.

## 2026-09-30: freeze the bounded public-dev source-label screen

- Objective: obtain real natural-language feedback while the distinct training
  review proceeds, without upgrading source labels to human-confirmed truth.
- Completed: [prospective amendment and protocol](research/source-label-screen/PROTOCOL.md),
  deterministic 12-tree selection, 24 original inputs, exact 48-request /96-generation
  plan, separate references, code/data hashes, attribution and resource limits.
- Audit: five software tests cover whole-tree overlap exclusion, conflicting
  visible labels, duplicate-rule units, deterministic selection, reference leakage,
  context rejection and missing freeze. Actual tokenization gives 28,256 local
  input tokens. Source distribution is Yes 10 /No 8 /ASK 6, not a prevalence estimate.
- Gap: no live call has occurred at this freeze milestone. Source truth and
  semantic near-duplicate independence are unverified. No source-Irrelevant group.
- Next: verify the committed freeze, run each backend once, preserve failures,
  re-audit raw records and publish descriptive agreement/costs before choosing
  whether this candidate warrants any intervention. No prompt or seed search.
- Presentation: original train review remains closed. This separate dev screen
  is explicitly exploratory and cannot supply independent confirmation after tuning.

## 2026-09-30: check a parallel source-label diagnostic without opening the review queue

- Objective: avoid making project-added human review a prerequisite for every
  exploratory observation, while keeping the frozen training queue untouched.
- Evidence: [dev-source inventory](research/source-label-screen/README.md) found
  69 dev trees, zero train tree-ID or normalized-exact-snippet overlap, changed
  and invariant action pairs, and one conflicting visible-action group excluded.
  These are source-label counts; semantic overlap and label truth remain unverified.
- Decision: a separate 12-tree /24-input source-label screen is feasible enough
  to specify. No cases are selected, no protocol is frozen and no predictions
  exist. A prospective amendment and deterministic selection are required next.
- Gap and presentation: this would yield source-agreement observations sooner,
  not human-confirmed errors or a new method. Do not change the pending train
  review gate, quietly use its cases, or call subsequent adaptive work confirmation.

## 2026-09-30: audit raw records before comparing conditions

- Objective: make a future comparison inspectable across common inputs, output
  failures, repeated option orders and actual resource accounting.
- Completed: [offline analyzer](research/external-validation/ANALYSIS_CONTRACT.md),
  failure-inclusive condition metrics, shallow controls, order-sensitivity counts,
  resource uncertainty and distinct grid/error/budget flags.
- Audit: eight synthetic tests and re-extraction of 16 pinned historical technical
  records. Initial real-record audit failed on null/false output flags. Inspection
  identified the exact Transformers load-path difference; the new check reproduces
  that path rather than weakening equality. Five in-memory mutations are rejected.
  No historical scores or source records changed; no new inference occurred.
- Gap: historical readout consistency and software tests are not a live task run.
  Two ShARC reviews, adjudication, exact input tokenization and the execution freeze
  are still absent. This stage supplies no new evidence for model replacement.
- Next: bring the reviewed cohort through the existing pipeline when available.
  Avoid accumulating cosmetic preparation or re-running closed grids to manufacture
  activity. A separate live technical check needs its own explicit bounded purpose.
- Presentation: show what can now be audited and the configuration repair, keeping
  technical readiness distinct from research findings or publication readiness.
- Follow-through: stage self-review identified that backend totals alone pooled
  direct/thinking costs. Added per-condition tokens, failure/unknown counts and
  callback-latency summaries, with shared setup unallocated. A ninth synthetic
  test reconciles condition totals to backend totals and preserves unknown usage.

## 2026-09-30: implement durable, bounded task execution without running the task

- Objective: retain every attempted call and prevent interruptions or retries
  from silently changing cost, sample size or the frozen grid.
- Completed: [execution core and live-backend code](research/external-validation/RUNNER_DESIGN.md),
  an exact committed-freeze/review-chain gate, OS locks, append-only start/finish
  events, cumulative budgets and conservative handling of uncertain interruptions.
- Audit: 14 targeted software tests cover safe partial resumption, no duplicate
  completed calls, unknown usage, limits, malformed responses and missing freeze.
  Execution receives no reference labels and cannot stop merely on a wrong answer.
- Gap: this orchestrator has not made a live call. No execution freeze or reviewed
  ShARC cohort exists. Failed-setup duration is not yet a durable journal field;
  returned outputs and uncertain started calls have explicit preservation rules.
- Next: build cross-condition result extraction with incomplete-grid reporting,
  then finalize the exact reviewed plan/freeze when human materials are available.
- Presentation: software reliability checks remain distinct from model evidence.
  Zero new HTTP attempts, model forwards or human annotations in this stage.

## 2026-09-30: add transparent shortcut controls

- Objective: test whether the selected history-answer contrasts might reward
  trivial copying, before interpreting a future model score as rule understanding.
- Completed: four constant-action controls and last-history-answer copying,
  restricted to visible state and integrated with the prospective paired scorer
  in synthetic tests. The plan declares all five; none are chosen after results.
- Audit: a deliberately opposite-rule fixture makes the unchanged copy answer
  fail. This exposes the shortcut's limitation rather than treating it as truth.
  References and review metadata are rejected at the control input boundary.
- Gap: no real control scores or model predictions exist. These shallow controls
  cannot establish that general deterministic rule interpretation is inferior.
- Next: retain them in the reviewed pilot and report all outcomes; implement
  task-run accounting without previewing pending task predictions.
- Presentation: show controls alongside model results, with their exact behavior
  and scope. A model advantage over a shortcut is not an algorithmic contribution.

## 2026-09-30: compile a reviewed comparison without opening inference

- Objective: turn the next comparison's input/fairness requirements into an
  inspectable plan, while preserving independent review and historical evidence.
- Completed: [draft contract](research/external-validation/COMPARISON_DRAFT.md)
  and compiler for 96 Jev requests /192 local generations after review. The
  compiler recomputes the review/adjudication chain, separates references from
  requests, declares work limits and refuses conflicting output files.
- Audit: synthetic tests exercise the complete 24-pair grid, prove that changing
  reference actions alone leaves requests unchanged, reject source-label leakage
  and altered final cohorts, and stop missing-review paths before source access.
  A separate real-tokenizer check verified nine non-weight files and both template
  branches on one disclosed synthetic prompt; no weight load or forward occurred.
- Gap: no real ShARC review chain or task plan exists yet. The tokenizer-loading
  path passed the small check, but actual cohort tokenization and the task runner
  remain before a separately published execution
  freeze. No model calls ran.
- Next: implement the remaining accounting requirements using software
  fixtures while human review proceeds; do not use pending task outputs for tuning.
- Presentation: label all counts as planned and keep synthetic tests distinct
  from model results. A compileable design does not establish research validity.

## 2026-09-30: check the counterfactual precedent and implement paired scoring

- Objective: determine whether the planned contrast differs from the nearest
  method and prevent aggregate scores from concealing paired failures.
- Completed: inspected relevant EXtrA author-thesis pages, including method
  and result-table images. Confirmed substantial one-condition overlap; recorded
  source hash and inspection limits in the [update](research/external-validation/NEAREST_WORK_UPDATE.md).
  Implemented a [prospective scorer](research/external-validation/PAIRED_METRICS.md).
- Audit: synthetic counterexamples show equal item accuracy with different
  pair success. The scorer retains failed outputs, refuses missing/duplicate
  records and does not pool repeated conditions or label absent strata as zero.
- Gap: these checks establish calculations, not human labels, a useful model
  comparison or novelty. No task predictions or additional API calls occurred.
- Next: complete review/adjudication and the task-run contract; integrate scorer
  with authenticated finalized references and recorded backend outputs then.
- Presentation: keep software tests visibly distinct from model results. The
  public question remains open, with prior work stated before any contribution.

## 2026-09-30: narrow the external-task contribution after closer prior work

- Objective: decide whether the next comparison could distinguish anything
  beyond established conversational rule reading and standard decomposition.
- Completed: a [primary-source update](research/external-validation/NEAREST_WORK_UPDATE.md)
  adds two closer precedents, records inspection limits and upstream provenance,
  and defines training/help/cost obligations for any adapted baseline.
- Audit: no counterfactual-testing or general decomposition novelty claim is
  supported. A fully frozen pipeline is a constraint to compare, not evidence
  of novelty. No upstream implementation was forked, imported or executed.
- Gap: no useful model boundary has been demonstrated on the new task. Two
  independent ShARC reviews, adjudication and a task-specific run freeze remain
  outstanding. The EXtrA full-paper and reproduction audit are not complete.
- Next: retain the frozen queue, complete the source/method comparison without
  reading queued predictions, then run the reviewed direct comparison before
  investing in a decomposition intervention.
- Presentation: use a question-led research card with explicit prior work and
  no claim that this is a newly invented benchmark or method.

## 2026-09-30: exercise both four-action backends once

- Objective: replace adapter assumptions with bounded live transport, mapping,
  final-channel and termination evidence before a later task comparison.
- Completed: frozen 8 Jev requests and 8 local Qwen3.5 generations; every output
  copied its explicitly supplied label. Jev used 3,236 input tokens, estimated
  $0.000135912; Qwen used 764 input and 2,195 generated tokens in 70.113 seconds
  generation-stage wall time. Zero retries/downloads/task-dataset items.
- Audit: all raw records, events, settings and tokens are retained. Offline
  tokenizer checks recompute local boundaries; semantic probability remapping and
  freeze/source/work checks pass. One thinking JSON fence is accepted under the
  already declared contract. No earlier score is recomputed.
- Gap: tiny supplied-label checks do not establish rule interpretation, a useful
  task budget, or fairness on the next workload. ShARC still has zero completed
  human reviews; the original two payment reviews do not cover these items.
- Decision: close this smoke at its predeclared limit. Do not start another generic
  calibration grid. Next task evidence requires independent labels, adjudication
  and a frozen comparison. Full-paper novelty assessment remains independent work.
- Presentation: [technical integration report](research/action-backends/README.md),
  outside research accuracy tables.

## 2026-09-30: separate future action parsing from model correctness

- Objective: prevent a future comparison from treating one harmless JSON fence
  as a reasoning error, without permissive answer extraction or historical rescoring.
- Completed: four-action parser accepts exact bare or singly fenced JSON; tracks
  strict compliance separately; rejects conflicting/multiple answers, duplicate
  or extra fields, invalid labels and unverified termination. Six synthetic test
  methods exercise these boundaries. No inference, downloads or API calls.
- Gap: no backend-specific final-channel extraction/completion integration, task
  budget, reviewed labels or end-to-end task predictions. Parser tests prove
  implementation behavior, not model capability or a fair completed comparison.
- Decision: retain all old parsers and scores. Integrate this contract only in a
  separately frozen task protocol after the required review process.
- Presentation: [contract and limits](research/external-validation/ACTION_INTERFACE.md).

## 2026-09-30: make the external-rule review queue distributable

- Objective: move from private preparation to an attributable, usable external
  natural-language review handoff and a precise next-comparison question.
- Completed: corrected the license inventory from the official ShARC data page;
  created a CC BY-SA 3.0 package containing the identical 60 frozen visible items,
  blank CSV, offline interface, cover note and source credit. Added an offline
  verifier, leakage/drift checks, and a task card with primary-source prior-work
  screening. Original selection, protocols and private files remain unchanged.
- Gap: zero ShARC human reviews and zero task predictions. This source-balanced
  train selection has no deliberately invariant pairs or Irrelevant reference
  examples. It cannot support a representative four-class or confirmation claim.
- Decision: use this queue only as the declared development pilot. Preserve the
  human-review gate; implement a separate fair output contract before the later
  model freeze. Do not rerun closed grids or confuse interface failures with
  reasoning failures. Full-paper novelty review and new-material confirmation
  remain separate work, not completed by the abstract-level screen.
- Presentation: [task card](research/external-validation/TASK_CARD.md),
  [review handoff](research/external-validation/public-review/README.md), and
  [distribution amendment](research/external-validation/PUBLICATION_AMENDMENT.md).
  The public question is "One fact changes. Should the decision change?";
  no claimed model failure or new algorithm accompanies it.

## 2026-09-30: calibrate output completion and audit format failures

- Objective: exercise a strict final-answer interface and choose a finite output
  budget using completion, independently of content correctness.
- Completed: 12 new elementary fixtures x two seeds x direct/thinking, 48 calls;
  8,128 input and 11,463 generated tokens; 368.783 seconds generation-stage wall
  time. Zero API cost, new downloads, retries or token-cap stops. Frozen sampling
  uses a tested standard presence penalty. All raw inputs and outputs are retained.
- Gap: direct meets the strict format gate at 256 tokens but has two content
  mismatches. Thinking ends naturally on all calls but 13 use Markdown JSON
  fences, so no cap qualifies under the frozen parser. Post-run inspection finds
  all 13 inner objects reference-matching; it does not rewrite the primary gate.
- Decision: stop this calibration at its planned calls. A future ordinary-model
  comparison needs a declared final-output contract that does not confuse
  harmless wrappers with reasoning mistakes. More thinking tokens would not
  resolve this particular format mismatch. New reviewed task material and a
  realistic need beyond deterministic code remain the scientific bottlenecks.
- Presentation: [complete calibration](research/generation-calibration/README.md),
  separately labeled from research scores. No new performance leaderboard or
  claim that a dedicated model is necessary.

## 2026-09-30: establish an executable Qwen3.5 comparator resource

- Objective: move beyond model metadata and verify local loading/generation.
- Completed: pinned BF16 checkpoint, isolated runtime, six technical calls,
  550 generated tokens, one truncated thought. Raw records and two pre-output
  compatibility amendments preserve the failure/recovery sequence. Unique model
  and wheel payloads total 8.715 GiB; zero paid API calls.
- Gap: no task-specific capability comparison or new reviewed labels. Short
  generic prompts do not establish long-context performance or a capable ceiling.
- Decision: keep all previous research grids closed. Define separate development
  calibration and new reviewed comparison material, with adequate thinking budget,
  declared sampling settings, a final-answer parser and code baseline.
- Presentation: [technical smoke report](research/baseline-readiness/QWEN35_SMOKE_RESULTS.md).
  Runtime evidence belongs outside the research score table.

## 2026-09-30: close review intake and qualify the payment pilot

- Objective: preserve two initial human submissions and settle how to report
  the ambiguity they expose without rewriting the past.
- Completed: two 96-item exports, byte-preserved originals, one-date normalization,
  row-level comparison, process self-reports, reporting disposition and updated
  replay. Commit `59fc36d`; its offline CI and Pages deployment succeeded.
- Gap: 100% decision-label agreement is conditional. Candidate scope remains
  unresolved for 24 underlying product-reference inputs. Self-reports do not
  establish reviewer independence; one export has an unexplained timestamp issue.
- Decision: close the original model pilot at its prior stop, retain the full
  historical score, and separate explicit-ID results from conditional references.
  No revised gold set or extra calls on that pilot.
- Presentation: [reporting disposition](research/payment-ownership/REVIEW_DISPOSITION.md)
  and full replay, including failures and limitations. No celebratory benchmark claim.

## 2026-09-30: candidate coverage preparation

- Objective: make candidate completeness explicit and distinguish missing
  relevant candidates from harmless omissions.
- Completed: 12 disjoint users, 72 constructed inputs, opposite-outcome hidden
  witnesses, 150 predeclared Jev requests and meaningful semantic/budget tests.
  Known-grammar code scores 72/72; two shallow alternatives score 60/72, and an
  always-refuse-on-omission rule scores 36/72. These are software results only.
- Gap: new independent human review is not complete. Supplied coverage premises
  and one template family are artificial. An exact template parser solves them.
- Authorization change: the later user request expressly authorizes bounded
  API and local-model exploration. [PROTOCOL.md](research/candidate-completeness/PROTOCOL.md)
  records exploratory execution before new human review; the earlier design's
  review-first requirement is not silently presented as fulfilled.
- Next: publish the freeze, run all six smoke cases and fixed main Jev grid,
  audit outcomes against the original screen, and prepare a separately frozen
  ordinary Qwen comparison using already-cached weights.
- Presentation: exact case replay, all baselines, raw records and a bounded
  conclusion. Novelty screen cites prior sufficiency/abstention work; no new
  algorithm, broad model ranking or paper-level confirmation is claimed.

## 2026-09-30: completed coverage grids and changed interpretation

- Objective: distinguish relevant candidate incompleteness from harmless omissions,
  with an ordinary instruction-model comparator and complete cost accounting.
- Completed: data freeze `680fb6f`, local-readout freeze `c327d59`; 150 Jev calls,
  zero retries, 226,329 input tokens, estimated $0.009505818; 150 Qwen native
  prefills, 181,360 prompt tokens. All planned inputs retained; no extra inference.
- Evidence: Jev 63/72 and 67/72 by mapping, strict complete parents 3/12; Qwen
  34/72 and 30/72, strict parents 0/12; grammar code 72/72. Jev correctly defers
  on ambiguous product references but over-defers on explicit IDs. Qwen mostly
  accepts under both option orders, not merely the first letter.
- Plan/reality gap: the observed Jev issue is unnecessary deferral, not the initially
  suspected foreign-order payment substitution. The native Qwen comparison cannot
  establish its reasoning ceiling. New labels remain program-derived; the earlier
  two reviews concern other inputs. One template family remains easy for code.
- Decision: stop both fixed grids without adaptive prompt search. Next prepare one
  fixed-budget Qwen reasoning control to test whether native readout understates
  this checkpoint's capability. Disclose it as outcome-aware and keep these data
  exploratory. New-material confirmation waits for semantic review and design.
- Presentation: [complete report](research/candidate-completeness/RESULTS.md),
  replay of every input/response, all baseline scores and neutral review package.
  Hook: "One visible match: when is caution wrong?" No general Jev defeat or
  dedicated-model replacement claim. Publication/CI checks establish consistency,
  not scientific validity. No Hugging Face release yet.

## 2026-09-30: stop a generation-default mismatch before main execution

- Objective: execute one frozen fixed-budget reasoning control after native results.
- Reality: Transformers 4.55.4 overwrote default-valued `do_sample=False` with the
  checkpoint's True. Six smoke outputs at freeze `db2837c` therefore used sampling,
  not the intended greedy configuration. No main job ran. Preserve 2,249 generated
  tokens, 932 physical forwards and 11,104 processed padded token positions.
- Audit: reproduced configuration merging on CPU without loading weights. The
  model shards also match official pinned Hub LFS SHA256 values. The raw smoke
  responses are retained under `reasoning_*`, not relabeled as valid greedy data.
- Repair: [v2 amendment](research/candidate-completeness/REASONING_GREEDY_V2.md)
  disables model-default merging and passes greedy mode explicitly, then validates
  the effective mode before inference. No prompt/data/label/schedule change. Publish
  the new freeze before any v2 output; total stage decisions capped at 156.
- Publication repair: Linux CI exposed platform-dependent ZIP container metadata.
  Verify each exact uncompressed review member and reject extra/missing/changed
  members; preserve the original published archive. This changes no review content.

## 2026-09-30: budgeted reasoning improves decisions but not unknown recognition

- Objective: check whether the poor ordinary native readout understates this
  checkpoint's performance under one fixed extra-compute policy.
- Completed: repaired greedy freeze `4527534`, 150 decisions, 69,771 generated
  tokens, 19,129 physical forwards and 563,924 padded token positions. Measured
  batch work 831.71 seconds; no new API spending or downloads. Original sampled
  smoke cost remains separate and included in the total control record.
- Result: Qwen improves from 34/72 and 30/72 to 58/72 and 59/72; corrections/regressions
  are 25/1 and 29/0. However, all 12 unknown-reference cases per mapping still
  receive a determined answer. Strict complete parents remain 0/12. Jev remains
  3/12 under the same strict criterion; known-grammar code is 12/12.
- Gap: 69/144 main traces hit the cap. Twelve unknown repeated decisions end
  naturally and twelve are truncated; neither subgroup abstains correctly. This
  does not prove a larger cap cannot help. New labels lack independent review,
  and the product-name wording has a plausible alternative reading to adjudicate.
- Decision: close all arms on these inputs. Do not add a third prompt/cap to
  chase a desired result. Next use the [research gates](research/candidate-completeness/NEXT_RESEARCH_GATES.md):
  neutral review, then a new-material language/coverage contrast and stronger
  ordinary comparator, or stop/redirect if the effect is just a wording artifact.
- Presentation: [reasoning report](research/candidate-completeness/REASONING_RESULTS.md),
  seven-row scientific figure and replay toggle. Headline remains a question about
  justified caution; show both over-deferral and unsupported commitment, code
  success, extra cost and failed execution. No model replacement or novelty claim.

## 2026-09-30: make the identity/predicate distinction executable

- Objective: progress on the next task definition while candidate-coverage human
  review is pending, without reopening the closed model grids.
- Delivered: [specification lab](research/decision-sufficiency/README.md), 20
  authored cases, five invalid-contract cases, a standard-library CLI, projected
  witnesses and an interactive page. A separately implemented database enumerator
  agrees on 730 valid finite contracts and rejects 180 inconsistent ones.
- Learned: different unknown identities can share a known policy predicate. A
  no-target possibility, unresolved destination and inconsistent contract need
  distinct handling. None of these component answers authorizes an operation.
- Novelty audit: certain answers and query-scoped completeness are direct prior
  work. This is a specification/control artifact, not a new inference algorithm.
- Plan versus reality: the program solves this finite schema; no unmet user need
  for predicate-before-identity has been established, and language comprehension
  has been removed from the input. No new empirical research claim is supported.
- Decision: retain the useful public example, do not turn it into another model
  leaderboard. Require a concrete interface need and independent semantic review
  before allocating new model experiments. Existing 72-input review and stronger
  ordinary comparators remain the primary research gates. Zero new model calls.

## 2026-09-30: distinguish a conforming run from a capable comparator

- Objective: make the stronger ordinary-model comparison concrete while human
  semantic review remains pending.
- Evidence: [metadata/runtime audit](research/baseline-readiness/README.md) pins
  four checkpoints and their weights' listed sizes without downloading them.
  The installed Transformers 4.55.4 registry supports qwen3 but not qwen3_5.
  Qwen3-8B BF16 weights consume about 15.26 GiB before runtime overhead; FP8 and
  Qwen3.5-4B have smaller stored artifacts but untested runtime compatibility.
- Material correction: our existing Qwen3-4B card explicitly warns against
  greedy decoding for thinking. The repaired 512-token run conforms to its
  protocol, but cannot stand in for vendor-recommended reasoning capability.
  Added the qualification to current reports and navigation; no score changed.
- Execution limits: only public metadata fetched and an installed-registry/GPU
  probe run. Retained/recovered metadata after an absent generation_config.json;
  disclosed an FP8 size-declaration discrepancy and the failed initial check.
  Zero new weights, model forwards or paid API calls; old environments unchanged.
- Plan versus reality: a suitable stronger comparator is still not ready. The
  next protocol must distinguish a capability reference from budget-constrained
  configurations and preserve parsing failures, truncation and seed variation.
  Asked whether another model resource already exists; do not assume credentials.
- Decision: do not repeat the closed grid with a different setting. Use new
  reviewed material and a supported, explicitly budgeted comparator when ready.

## Long-term direction and gates

The project asks when models plus programs can provide reliable typed decisions,
and whether dedicated decision training is needed. A useful public sequence is
an inspectable phenomenon, a separately reviewed new-material test, fair controls
and inference costs, then a mechanism/intervention or a bounded negative result.
Each small repository study should offer one concrete claim, runnable evidence,
an understandable replay and an explicit reason to continue or stop.

The accumulated studies have not yet met the gate for a general replacement or
novel-method paper. Pure-code success, artificial templates, readout sensitivity
and limited independent review remain central challenges. Do not replace those
gaps with additional stars, result pages or repeated forwards. Hugging Face
packaging follows data/license/review readiness, not the number of experiments.
