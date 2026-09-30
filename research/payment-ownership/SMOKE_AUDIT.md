# Preserved v0.1 semantic stop

On 2026-09-30, the original public pre-inference freeze `0569f8d` ran five smoke
requests and stopped on the fifth, as its all-correct prerequisite required.
The sixth predeclared smoke request was then completed without reissuing any of
the first five. Main requests executed under v0.1: **zero**.

The API returned valid schemas, the pinned model, and usage for all six requests.
Five matched provisional references. The ambiguous case did not:

> Please refund on my Mug order to payment method card_a. Is that destination eligible?

Both displayed orders contain a Mug. `#SMOKE_A` originally used `card_a`, while
`#SMOKE_B` used `card_b`. No unique target is stated. The declared Choice rubric
assigns ambiguous targets to NOT_ESTABLISHED. Jev returned VALID_DESTINATION with
distribution VALID=0.97, INVALID=0.00, NOT_ESTABLISHED=0.03 (confidence field 0.95).
These numbers are returned values, not a calibrated correctness probability.

Under the construction semantics, choosing A makes the destination valid and
choosing B makes it invalid; neither order is uniquely identified by the request.
This remains one AI-constructed, independently unreviewed example. It cannot
establish the prevalence of ambiguity failures, and no response explanation or
internal binding mechanism was observed. Reviewers may challenge the intended
interpretation; preserve such challenges rather than silently changing the label.

All six smoke requests together used 4,661 provider-reported input tokens, zero
retries, and estimated $0.000195762 at the published input rate. Raw outputs are
in `results/responses.jsonl`; append-only accounting is in `results/attempts.jsonl`.

The all-correct prerequisite conflated a functioning experiment with perfect model
behavior. It prevents investigating the phenomenon when an independent boundary
case already fails. The stopped v0.1 outcome is retained. Any later main grid needs
the explicit [execution amendment](EXECUTION_V02.md); it must not be described as
passing the original prerequisite or as independent confirmation.
