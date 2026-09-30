# Explicit readout repair after the original Jev stop

2026-09-30. Written after 23 Jev requests and before any suffix repair request.
The independently running fixed Qwen grid continues under the original freeze.
No source-agreement score was used to choose this repair or its remaining jobs.

## Original observation and preserved failure

Original execution commit: `e90f051459370ad99be8ddfaf29e65c013d2eda1`.
The original Jev ledger closed after 23 requests, 23 returned results and 14,346
reported input tokens. Request 23 returned HTTP 200, model `jev-1.13.0`, choice A,
confidence 0.91, and probabilities D=0.01, C=0.05, A=0.93, B=0.0. Their sum is
0.99. The original validator required sum-to-one within 0.0001 and therefore
recorded a protocol error and stopped. That result and all earlier results remain
unchanged in the byte-preserved [original stopped ledger](results/jev_original_stopped.jsonl).
Ledger SHA-256: `e4fd6de17a6156bf54322f7a1cdcc110095ae4588ca1b0464c974922d22e6a27`.

The [official API reference](https://docs.typesafe.ai/api), checked 2026-09-30,
describes probabilities summing to one and choice as the highest-probability
option. The observed values do not meet our original sum check. Their two-decimal
form is compatible with rounding, but the cause is not established. We did not
contact the provider and do not claim a server implementation diagnosis.
[Confidence](https://docs.typesafe.ai/confidence) is a distribution-derived
statistic, not a requirement to equal the selected option's probability; the
0.91 versus 0.93 difference is not this failure.

The original strict run remains **incomplete**: 22 accepted decisions, one
protocol failure, 25 unstarted requests. It cannot receive a full-grid Jev score.
This is not evidence that Jev made a wrong policy decision on that item.

## Prospective decision readout

The research endpoint is the native chosen action. Separate that extraction from
probability-distribution quality in a newly named readout:

- Keep HTTP success, exact served version, answer/option keys, declared type,
  finite probabilities within [0,1] with positive total, chosen-option argmax,
  bounded confidence and nonnegative integer usage requirements.
- Read the native `choice` as the action even if the raw probability sum differs
  from one. Preserve original probabilities, sum and the old-check pass/fail flag.
- Never normalize the values, widen a rounding tolerance, infer missing precision,
  or claim calibration from the accepted action. This is decision-only acceptance,
  including a flagged sum such as 0.4; it is not certification of the distribution.
- Other interface/transport/invariant failures still halt, with no automatic retry.

Re-extract all 23 preserved responses under the new rule as a separately labeled
derived view. Verify the 22 previously accepted actions do not change. Retain the
original protocol-error status alongside the newly recoverable native choice.
Do not overwrite the original analysis or silently turn its failure into success.

## Exact remaining work and accounting

Continue only the 25 **never-started** requests from the original frozen order.
No successful or failed request is sent again. The combined HTTP-attempt cap
stays 48; the suffix input-token limit is 100,000 minus the original 14,346 usage.
No input, criterion, option order, source reference, selected case or model version
changes. No additional model comparisons, cap/seed changes or prompt searches.

Before running, commit `repair_plan.json` and `repair_freeze.json` with parent
ledger/plan hashes, suffix job identities and repair source hashes. The runner
revalidates the parent against its original execution commit, checks the terminal
prefix, and uses a distinct append-only suffix journal. Resumption cannot revisit
a prefix request or erase an uncertain suffix call.

The report must show both views: original strict incomplete grid, and repaired
decision-only grid if all remaining requests return. Combined cost includes every
original and suffix attempt. Report probability anomalies separately from native
action/source agreement. A repaired readout is an adaptive engineering correction,
not independent confirmation or an improvement in the model's reasoning.

This repair is within the user's existing API authorization and the original
total call limit. Its substantive change is explicit acceptance of native choices
with separately flagged probability quality. All source-label and review limits
of the original experiment remain in force.
