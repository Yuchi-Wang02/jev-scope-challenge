# Milestone audits and next decisions

This log separates completed work from research validity. Each milestone records
the objective, actual evidence, plan-versus-reality gap, next action and public
presentation. It does not claim a paper is ready.

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
