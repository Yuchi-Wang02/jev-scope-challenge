# Same facts. Different answer interface.

Prospective design, 2026-09-30. This document freezes the research choices before
new outputs; it is not by itself an executable-run authorization artifact.
The runner and exact prompt/token manifests must be verified and committed
before any model call. Existing user authorization covers the bounded study.

## Question and population

How sensitive is the Jev/Qwen comparison to finite letter readout versus normal
generation? Select 12 new QA4PC development policy trees and two scenarios per
tree by deterministic hash ranking. Exclude incomplete graphs, every previously
inspected EXtrA tree, the previous source screen and stage-attribution trees,
and the pending training-review queue. Retain source text locally and publish
IDs/hashes, code and derived outputs under the existing redistribution boundary.

These are new model-output-free project clusters, not newly collected policies.
The entire source development structure was already audited. Upstream labels
have been inspected for consistency; independent project semantic reviews are
absent. The estimand is source-label agreement on the selected 24 scenarios.

## Fixed grid

Use only direct D: policy, question and scenario. No supplied fact labels,
graphs, retrieved evidence, teacher judgments, or new decomposition. Reuse the
previous explicit yes/no/maybe and three-valued-rule instruction verbatim.
Pin the same Jev version and Qwen checkpoint/runtime/precision as the preceding
stage. There is no model download or training.

All six permutations of `(yes,no,maybe)` are fixed in itertools.permutations
order. At each mapping, run all four routes:

|Route|Output/readout|Main decisions|Synthetic smoke decisions|
|---|---|---:|---:|
|Jev native letters|Native A/B/C criteria, mapped to semantic labels|144|18|
|Qwen finite letters|One prefill, constrained A/B/C maximum; exact ties invalid|144|18|
|Qwen generated letters|Same prompt and input IDs as finite letters, normal unconstrained greedy generation|144|18|
|Qwen generated semantics|Same task/state, request one literal semantic label; list allowed labels in corresponding order|144|18|

Total: 162 HTTP attempts and 486 local decisions, including 72 smoke decisions.
Local decisions comprise 162 prefills and 324 generations; generated tokens and
physical forwards must be charged separately. No automatic retries. Greedy
generation, thinking disabled, maximum 32 new tokens, one beam, no sampling,
no custom logit penalties or constrained decoding. This controlled configuration
is not claimed to be the vendor-recommended or best possible generation setup.

The letter-generation bridge holds the prompt constant while changing readout.
Generated semantics changes the output vocabulary and format instruction; it is
a bundled interface intervention, not an isolated token-bias causal estimate.
Fixed A/B/C rows plus reassigned meanings also change semantic display position.
Jev's internal serialization and decoding are opaque; request order does not
prove its internal prompt has the same order. No equal-compute claim follows.

## Gates, invalids and integrity

Three synthetic direct-rule smoke cases cover yes/no/maybe at all mappings for
each route. Their semantic errors are observations, not pass requirements; this
rule is declared before outputs. A valid API envelope with a wrong answer does
not stop the run. Transport failure, incompatible served version, absent usage,
invalid job/input hash, nonfinite local logits, unknown interrupted calls, or
runtime/configuration mismatch stop execution and preserve evidence.

An ordinary generated answer is valid only if it terminates with the pinned EOS
and its whitespace-trimmed body is exactly the requested case-sensitive letter
or semantic label. No JSON, punctuation, explanations, label mining, coercion,
or repair. Unsupported special tokens, empty output and token-limit/deadline
truncation are invalid observations. Save full output IDs and decoded body.
Finite exact ties remain invalid; unconstrained generation follows its defined
greedy behavior. Report first-token ties separately instead of making the two
routes artificially agree. Invalid model outputs retain their denominator.

The journal must durably record each start, result and backend session. No
restarting in a fresh directory to bypass a recorded halt. Freeze full local
inputs and references, public per-job hashes, tokenizer/configuration/code
hashes and ordering before execution. No reading of main results while deciding
whether to add a route. Inference order is smoke first, then fixed item, mapping
and route order; latency is descriptive, not a randomized speed experiment.

Proposed hard caps to verify during compilation: 162 HTTP attempts, 486 local
decisions, 2,000,000 serialized-request bytes plus 4,096 per Jev call as a
planning proxy; 500,000 actual Jev input tokens; 500,000 planned local input
tokens; 10,368 generated tokens (324 x32); 1,800 local callback-session seconds;
32,768 tokens per local prompt including its output allowance. Report any final
call overrun. Verification/load time is separate and also reported.

## Readout of the experiment

Primary: each route's six per-mapping source-agreement counts (denominator24),
mean across the six mappings, and invalid counts. Secondary: all-six-valid
semantic consistency, all-six-correct items, strict two-scenario tree success,
class confusion, paired fixes/regressions, candidate mass and exact ties.
Invalid-either and valid-both changes are separate. Policy tree is the cluster;
the six mappings do not multiply independent sample size. No p-values or
population-level reliability claim on twelve clusters.

For an executable six-call aggregation baseline, require a strict majority of
at least four valid mapped votes out of six; otherwise abstain. Apply the same
rule to all four routes. Invalid votes never count as `maybe`. The denominator
stays24. All six calls/tokens/time are charged; do not compare aggregated quality
to a single call as if budgets matched. This is established ensemble logic.
Do not tune probability weights, choose a best mapping, or fit calibration here.

Stop after the fixed grid. If interfaces do not change the comparison, publish
that boundary. If semantic generation changes it, the conclusion is interface
dependence in this checkpoint/cohort; reserve new trees for later confirmation.
Do not attribute a change to training specialization or infer that one model is
generally necessary. If invalids dominate, first report contract feasibility.
No same-cohort precision, prompt, token-budget, or decoding search follows.
