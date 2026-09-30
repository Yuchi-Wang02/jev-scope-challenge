# Final native-choice readout after a second interface stop

2026-09-30. Frozen before the final 18 never-started requests. This is the last
readout repair allowed in this screen. No source-reference agreement score was
used to choose the readout. All original model inputs and references remain fixed.

The first decision-only repair retained an argmax consistency requirement.
It stopped after seven new requests: overall request 30 returned choice C with
probabilities C=0.38, B=0.39, A=0.01, D=0.22, confidence 0.19, HTTP 200 and the
pinned served version. Unlike the first stop, the sum is one; the returned choice
is not the displayed maximum. The [API reference](https://docs.typesafe.ai/api)
describes choice as the highest-probability option. Cause is unestablished.
No provider contact or server-side explanation is claimed.

Preserve the [original strict stop](results/jev_original_stopped.jsonl) and
[first repair stop](results/jev_first_repair_stopped.jsonl). First-repair ledger
SHA-256: `2ca5f2c900e2df8e433b17a6ad8955902e9683bb382629081db1df650696aec3`.
Their original statuses stay incomplete. The first repair's retained coupling
between native choice and probability quality was insufficient to finish this
decision comparison; that engineering limitation is part of the record.

## Final policy, fixed independently of source agreement

Primary output is exactly the service's native `choice`, mapped through the
frozen option order. Accept it only after HTTP success, exact served model,
expected answer key/type, declared choice membership and valid integer usage.
This primary readout mirrors evaluating Qwen's declared final action; it does
not certify the entire Jev response as API-contract conforming.

Probability/uncertainty fields are a separate diagnostic channel. Record key
shape, finite [0,1] values, positive total, raw sum, original sum-check result,
whether native choice is a displayed maximum, ties and confidence validity.
Missing or invalid metadata remains visible but does not replace a well-formed
native action. Do not normalize, round, infer missing probabilities, recalibrate
confidence or override native choice with the source label or displayed maximum.

Report an additional **displayed unique-argmax** view on every returned response,
not only on disagreement cases. A tie, invalid/absent probabilities or nonpositive
sum has no unique-argmax action and stays a failed output in that view's denominator.
Both native and unique-argmax views use the same sources and incurred cost; they
are alternative readings of the same requests, not additional independent trials.
Always report both. Native choice remains primary regardless of which view agrees
more often with source labels. All metadata anomalies remain separate outcomes.

## Finite continuation

Re-extract the already preserved 30 responses offline, verifying that accepted
native actions do not change. Original rejected statuses remain available. Send
only the final 18 unstarted requests. No retries or repeated requests: the total
cap remains 48 attempts and 100,000 input tokens. Prior reported usage is 18,819;
the remaining stage limit is 81,181 input tokens. Qwen's existing fixed execution
is unchanged. No source or case replacement, generation changes or added help.

The new freeze pins both prior journals, the exact final suffix and final-readout
code before continuation. If a core action/schema/usage or transport failure
occurs, preserve it and end the Jev branch incomplete without another repair.
The final combined view is explicitly an adaptively repaired interface diagnostic,
not the originally frozen strict experiment and not independent confirmation.

The report must distinguish: original strict stop; first-repair stop; final native
coverage; all metadata issues; alternative unique-argmax agreement; and complete
cost across all attempts. No full-condition score when final coverage is missing.
These observations alone do not establish model reasoning failure or a new method.
