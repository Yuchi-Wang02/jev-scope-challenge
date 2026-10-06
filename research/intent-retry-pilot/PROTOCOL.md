# Draft pilot: conversational operation identity

Status: **measurement pilot; 72 exploratory inputs prepared, independent review pending**. The earlier nine simulator seeds remain separate. Preparation and freeze/run status are recorded in `plans/preparation.json`, any subsequent `freeze.json`, and append-only result logs. No method intervention is defined by this protocol.

## Question and contract

Given visible dialogue, an existing operation handle, its tool arguments, and the visible execution receipt/status, predict:

- `RESUME_EXISTING`: satisfy the original operation once, recovering its outcome with the same key.
- `START_ADDITIONAL`: satisfy the original operation once and a separately authorized identical operation once, using distinct keys. Pilot wording must explicitly authorize two total effects; otherwise this action is not justified.
- `CLARIFY`: do not initiate an additional effect while the user's intended count/operation is unresolved. In this pilot, clarification also defers resuming a pending original; report that cost explicitly.

The deterministic runtime enforces the chosen operation IDs. It handles transport retries, stores receipts, checks same-key argument consistency and rejects mismatched payloads. The model is not asked to infer a hidden transport outcome or generate random keys. Tool arguments and known operation handles remain visible. Gold new-operation IDs and intended counts are evaluator-only.

## Planned material

Twelve parent dialogues: three simulated effect domains (a purchase, a message, and a job submission), four execution histories per domain:

1. acknowledged success;
2. timeout with an unknown outcome;
3. delayed follow-up after acknowledged success;
4. known failure before any effect.

For each parent, author three intent branches (resume, additional, clarify), each with two phrasings: **72 visible inputs**. Independent human checks are pending; an AI consistency review is not a replacement. Clarify has two distinct strata: explicit deferral (success/failed histories) and unresolved reference to a visible two-option question (timeout/delayed histories). They are not interchangeable evidence of natural ambiguity. This stratum/history association is a limitation of the pilot and prevents attribution of a clarification difference to history alone. Only the last user turn varies within a parent. The same common question is visible to every branch of an unresolved-reference parent. Delayed follow-ups and rapid legitimate repeats prevent elapsed time from serving as a sufficient identifier. Clear, plausible repetition motives are included, but the cases remain authored synthetic material, not observed user behavior.

Two fixed label orders produce **144 scored decisions per model**: (RESUME_EXISTING, START_ADDITIONAL, CLARIFY) and (CLARIFY, RESUME_EXISTING, START_ADDITIONAL). Every label changes position; these are only two of six possible permutations, not a full invariance test. Timeout inputs are replayed against both hidden worlds (committed before response loss / never committed); these use the same prediction and require no extra model calls. Hidden worlds are indistinguishable before recovery, so they must not receive different intent labels or leak state through IDs.

The twelve parent dialogues are the analysis clusters, **not twelve demonstrably independent samples**: domains/history templates are reused. Report per-parent results, template dependence, and descriptive uncertainty. No significance or benchmark-ranking claim from this pilot. Paraphrases, label orders and hidden-state replays are repeated measurements.

## Baselines

| System | Role |
|---|---|
| Correct operation identity supplied externally + deterministic runtime | Assisted upper bound for execution; not a fair semantic competitor. |
| Always reuse a key for the same payload; always allocate a fresh key per turn | Diagnostic endpoint controls, not headline opponents. Both should expose obvious tradeoffs. |
| Frozen keyword/rule linker with abstention | Cheap semantic control with transparent rules. Author knowledge of the pilot must be disclosed; report coverage. This is not a validated strong non-model system. |
| Explicit user choice: continue earlier operation / do one more / clarify | Interaction-based engineering alternative. Report extra user turns and unresolved sessions, not zero-cost perfection. |
| Capable ordinary instruction model + the same runtime | Required primary reference; name exact accessible model/version before freezing. A small model alone is not this reference. |
| Jev + the same semantic inputs and runtime | Main continuity with the existing project. Use the same output contract, visible evidence and tool availability. |
| Local ordinary small model, if already available | Optional efficiency reference. A historical Kev-LoRA run does not substitute for a current capable-model baseline. |

For two primary models, 288 science decisions; an optional third adds 144. Each model gets at most three separate smoke requests, and at most nine transient-failure retries across the pilot. Thus the corresponding HTTP-attempt ceilings are 303 (two hosted models) or 450 (three hosted models); local forward passes must be counted separately rather than called HTTP requests. One response per item/order, no best-of selection, adaptive prompt search or model-based post-hoc relabeling. Token and money ceilings depend on the named endpoints and must be recorded in the frozen manifest before execution. Existing Jev authorization is not authorization to purchase arbitrary new services.

Execution amendment before inference: permit the Jev exploratory arm to be frozen/run first, using existing authorization, while the capable ordinary endpoint remains unresolved. It has 144 scored + 3 smoke + at most 9 retries = **156 HTTP attempts**, at most two attempts for any job, and a shared **1,000,000 input-unit** ceiling. Units reserve UTF-8 request bytes rather than claiming a measured tokenizer count; actual returned tokens are retained separately and checked against the working ceiling. At the checked input price of $0.042/Mtok this corresponds to a $0.042 nominal input-token ceiling estimate, not a bill guarantee. Pricing source: https://docs.typesafe.ai/models (checked 2026-10-05). This staggered execution authorizes no comparative conclusion or adaptive case selection. Later model arms must use the same frozen inputs and be documented before running.

## Scoring

Report all three layers, not just classification accuracy:

1. **Intent**: confusion matrix; both-branches-correct per parent for resume vs additional; three-branch correctness; paraphrase and label-order disagreement; clarification on clear versus unresolved cases.
2. **Effects**: extra effects beyond authorized count, missing original work, missing additional work, clarification with pending original work, write attempts, newly created effects, and correct final state after recovery. A false-merge decision is specifically RESUME on an additional-operation reference; missing additional work caused by CLARIFY is separately counted. On clarify references, distinguish a wrong scope decision, a write attempt, and an effect created while the policy required deferral; do not call all three a duplicate or unauthorized new operation. Gold intended obligations define errors; system-generated IDs cannot make duplicates legitimate by definition.
3. **Cost**: model requests/tokens/latency, status checks, write attempts, user clarifications and completion. Report safety versus completion/interaction cost jointly. Never call a system that refuses everything best overall.

Scope-and-effect success requires correct intent and correct simulated effects. This is an explicit scope-router probe, not an unconstrained agent or a full task-completion evaluation: user-facing receipt delivery is not implemented. A wrong intent that accidentally produces the right count in one hidden world remains an intent failure. Infrastructure failures are retained, separately counted, and are not silently retried into extra scientific samples.

Malformed/no-answer/model-version mismatch/retry-exhausted jobs remain in the fixed denominator as unsuccessful, with a separate infrastructure category. A not-yet-attempted job is pending, not a model failure; report completion count and withhold complete-run accuracy until all planned jobs reach terminal outcomes. Probabilities are saved as returned and mapped through the frozen ABC order; no post-hoc renormalization or replacing native choice with argmax.

## Checks before model execution

- Same input bytes for paired hidden timeout worlds; no evaluator labels/counts or hidden commit flags in model payloads.
- Same-key retries cannot duplicate; changed payload with an existing key is rejected; a genuinely new operation can use identical payload safely.
- Full-visible-record baseline retained, with existing handles and receipts. No artificial loss of IDs to create difficulty.
- Only the declared utterance changes within an intent contrast; paraphrases preserve the intended authorization and scope.
- Reviewer checks for unresolved cases and naturalness; pending labels remain provisional. Reviewers do not see model predictions for first-pass labels. Exploratory inference may run while review is pending, but cannot certify label validity.
- Freeze cases, prompts, label maps, model versions, decoding, limits and hashes before scored calls. Keep all outputs, errors and abandoned hypotheses.

## Decisions after one fixed pilot

- If errors disappear under a reasonable full-context prompt or simple rule linker, retain a small boundary note; do not immediately add adversarial complexity.
- If errors occur only on disputed language or one option order, repair/report that issue rather than asserting a robust operation-identity defect.
- If capable models show repeatable false merges/splits across clear paired inputs, use the failure analysis to propose a genuinely distinct treatment in a separate protocol. Explicit linking is already this pilot's task and cannot be counted as its own intervention.
- If a future treatment helps only on author-written templates, stop the generalization claim. Obtain fresh human-authored or suitably licensed interaction material before expansion.
- Even perfect pilot performance is useful: it closes this narrow candidate without implying perfect real-world reliability.

For the first checkpoint, a practical **follow-up trigger** is at least two parent dialogues with a clear, reviewer-supported error persisting across both phrasings and both label orders in the capable baseline. This is a work-allocation heuristic, not a significance threshold. Below it, publish only the observed boundary or improve ecological validity if independent evidence warrants doing so; do not hunt indefinitely for a failure.

## Possible later contribution

Only after a genuine pilot signal: a separate, blinded, fresh material set with multiple active operations, corrections and natural follow-ups; a fixed intervention; comparisons to appropriate upstream systems; parent/source-grouped splits; uncertainty and full cost accounting. Inspect Irrevon's actual fixtures and Cordon's task-boundary construction before claiming a missing evaluation: both are close precedents, and the two-sided error metrics are not new. Dataset size should follow the pilot variance and intended claim, not an arbitrary large example count. GitHub can host a small reproducible research note first. A paper needs the missing external validity, novelty comparison and held-out result; a Hugging Face upload is distribution, not validation.
