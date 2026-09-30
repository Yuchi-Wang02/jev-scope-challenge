# Right Payment, Wrong Order? — Jev results

**Status: incomplete. Independent human annotations: 0.**

This is a static diagnostic derived from a public simulated tau retail database.
It is not a tau-bench agent score, real-customer evaluation, or confirmed generalization result.

|Condition|Correct views /48|Complete four-view parents /12|Wrong VALID /24 invalid|Needless deferrals /48|
|---|---:|---:|---:|---:|
|full_0|0|0|0|0|
|full_1|0|0|0|0|
|full_mean|0|0|0|0|
|related_0|0|0|0|0|
|related_1|0|0|0|0|
|related_mean|0|0|0|0|
|Finite-language parser + rules|48|12|0|0|
|Always VALID|24|3|24|0|
|Always INVALID|24|3|0|0|
|Always NOT_ESTABLISHED|0|0|0|48|

`0` is the prespecified primary option mapping; `1` is its reverse. `mean`
averages semantic probabilities over those two mappings. Each condition has
24 explicit-ID and 24 item-reference views. Detailed counts are in summary.json.

The related-evidence condition was selected using construction metadata. It
remains pending independent review and is not a deployable repair method.
All 48 main references are determined (24 VALID, 24 INVALID). There are zero
main missing-evidence cases; unknown-state reliability cannot be estimated.

## Actual execution

- Smoke: 0/0; main terminal records: 0/192.
- HTTP attempts: 0; retries: 0; unknown-usage attempts: 0.
- Provider-reported input tokens: 0; conservative planned input units used: 0.
- Usage-estimated cost: $0.00000000, at $0.042/M input tokens. This is not an invoice.
- Median successful request latency: None seconds; includes network/service latency.
- Full-input option-order disagreements: 0/48.

All raw responses, probabilities, timing, failures and accounting events are retained.
The 192 calls are repeated measurements of 12 source-user groups, not 192 independent examples.

## Stage decision

**INCOMPLETE**. Follow-up model calls: 0.

Inspect every error and provisional label before choosing at most one follow-up.
No follow-up is approved by this report alone; its exact inputs must first be frozen
under the existing user authorization and shared stage budget.

## Reproduce and audit

Run `python research/payment-ownership/study.py verify-freeze` and
`python research/payment-ownership/report.py --verify` from the repository root.
These checks are offline and never call a model. Open [the replay](../../docs/payment_ownership.html).
See [the protocol](PROTOCOL.md), [data and source notes](README.md),
[review instructions](review/README.md), and [nearest-work assessment](RELATED_WORK.md).
