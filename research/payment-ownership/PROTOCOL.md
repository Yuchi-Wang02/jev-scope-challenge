# Right Payment, Wrong Order? — v0.1 exploratory protocol

Prepared 2026-09-30 before this study's live requests. This document preserves
pre-inference intent; RESULTS.md and the append-only ledger establish later outcomes.
The user authorized bounded live Jev exploration, including a conditional follow-up.

## Question, data and scope

Does mixing another order's records change Jev's judgment of the target order's
refund destination? This is a static component diagnostic derived from tau retail,
not a tau-bench agent run, production interaction, or new binding algorithm.
Upstream revision: `5bfa7e37b36656b37dc6d022156be6563c1007f3`.

Twelve disjoint source users supply two source orders each. Six parents switch
between valid and invalid as the target changes; three remain valid and three
remain invalid. Each has explicit-ID and unique-item/card-descriptor request
versions, giving 48 inputs, 24 VALID and 24 INVALID. No main input has an intended
NOT_ESTABLISHED label. Abstention/unknown handling therefore has only software and
smoke coverage, not a scored missing-evidence benchmark. Report its denominator
as zero/not applicable, never as demonstrated reliability.

Pair selection uses a fixed SHA256 ranking and no model outputs. Original payment
histories have exactly one payment, limiting policy ambiguity from mixed payments.
Users do not overlap between strata. Item names uniquely identify the target among
the two displayed orders; card brand/last-four descriptors are unique in the user's
profile. The requests are deterministic AI-authored constructions, not human-written
customer text or independent natural-language samples. The item-reference form is
still a template. Review may expose semantic problems despite program agreement.

Keep source `order_id`, `user_id`, `items`, `payment_history` and user
`payment_methods` structures. Omit address, name, email, fulfillment and order status
uniformly. Authentication, delivery, return items and confirmation are explicitly
outside this decision. A VALID result does not authorize a refund or full return.
The state contains the same explicit component policy in every input.

## Conditions and readout

Use versioned `jev-1.13.0` and Choice with A/B/C mapped to VALID_DESTINATION,
INVALID_DESTINATION and NOT_ESTABLISHED. Evaluate the declared order and its reverse.
These are two selected permutations, not all six; no permutation-invariance claim.
The primary condition is full records, mapping zero. Report all four conditions;
also report the secondary mean-probability decision over the two mappings.
Ties in the secondary aggregate follow the semantic label order listed above.

The `related` condition deletes only the non-target order. It preserves the policy,
user profile, customer request and the target order without modification. This uses
construction target metadata to choose evidence, hence is an oracle-style diagnostic,
not deployable filtering. Until two humans verify both input versions, call it
**program-selected related evidence, pending independent review**. It cannot prove
an internal binding mechanism: shorter context, selection burden and representation
change together. It is not a matched-token efficiency comparison.

Six separate toy smoke cases cover original payment, foreign payment, existing gift
card, missing payment history, ambiguous target and unknown destination (two per
semantic label). They are not part of the 12 parent denominator. All must return
valid responses and their reference labels before the main 192 requests run.

## Accounting and integrity

Freeze exact inputs, request list, code and this protocol before live calls. All
scientific and smoke jobs contain one question per HTTP request. No silent alias,
fallback model, prompt tuning or provider retry layer. The runner supports one
transient retry per job, at most 15 retries overall. It stops on permanent failures,
invalid responses, unexpected model identity or unreconciled interrupted attempts.
Every started attempt is persisted and counted before network transmission.

Primary: 6 smoke + 48 inputs x 2 evidence views x 2 mappings = 198 requests.
At most one separately frozen follow-up can add 192. Total HTTP attempts <=405,
including <=15 retries. Planned input units <=2,000,000, using serialized UTF-8
request byte length +256 per attempt as a conservative proxy, not exact tokenization.
Actual provider input usage is separately logged, including each reported retry.
Unknown billing is explicitly unknown. Current published price is $0.042/M input
tokens; output tokens free, verified at https://docs.typesafe.ai/models on 2026-09-30.
Usage-based cost is not an invoice. Never expose credentials in source or logs.

## References, controls and human review

Program references compare the resolved destination to the target order's original
payment, with the existing-gift-card exception. A separate finite-language parser
resolves IDs or the two declared phrase patterns from visible state; it may abstain
outside that coverage. It must not consume construction target IDs or reference
labels. Its success is a genuine program baseline, not evidence that models are
necessary. Include always-VALID, always-INVALID and always-NOT_ESTABLISHED controls.

Two reviewers independently label all 96 full/related review items, without model
outputs, program labels or pair IDs. The repository is public, so blinding is
procedural, not cryptographic. Preserve original forms and disagreements; authorship
and reviewer identity must be declared. Templates are immutable; submissions go in
separate files. No completed independent human labels exist at freeze.

## Analysis and continuation decision

Report correctness per view, per style, per mapping and per complete four-view
parent. Report target-pair correctness per style, wrong VALID acceptance among
INVALID references, needless deferral among determined cases, and all transitions
between full/related. Source user/parent is the independent unit (n=12). No population
significance, robust calibration, unseen-language transfer or universal model claim.

Prespecified operational stop: if full-input mapping-zero solves all 48 and both
mappings have >=47/48 correct, stop without harder examples or prompt search.
Otherwise inspect all errors, not just dramatic examples. If at least two distinct
parents have full-wrong/related-correct cases, a single ownership-focused diagnostic
may be prepared. If both views fail, investigate task/field understanding. If errors
are mapping-specific, investigate that interface sensitivity. Freeze the one chosen
follow-up and its <=192-request plan before any additional inference. These are
development continuation rules, not statistical tests or confirmation thresholds.

Label/program errors require a versioned correction retaining every original raw
record. No outcome-dependent silent exclusions. Successful later human review does
not turn adaptively used development data into untouched confirmation.

Jev is the only live model in this first grid. Historical Kev-LoRA continuity and a
strong ordinary instruction-model comparator remain outstanding; no replacement or
model-ranking claim is supported by Jev-only results.
