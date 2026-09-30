# Explicit request IDs: a post-hoc gate, two exposed errors

**A visible-ID program gate changes saved joint-route decisions from 34/72 to 70/72.**
This is a post-hoc composition of ordinary parsing and already recorded model outputs.
It adds zero model forwards and does not change the failed frozen joint pilot.
The same 72 public development views in 12 parent groups remain program-labeled,
with zero independent human annotations. There is no new Jev result.

## What was computed

The [gate](scope_gate.py) reads only the visible request header and one visible
record line. Five anchored sentence shapes locate the request-ID slot. Exact
identity keeps the saved route; an explicit foreign ID replaces it with
`OTHER_REQUEST`. Unsupported text is `UNKNOWN` and retains the saved route
in this replay. It is never silently certified as foreign or absent.
The gate returns no field or polarity. The existing aggregator and executor
then run unchanged. Construction records and gold labels enter only afterward
for scoring. This is grammar-specific validation, not a new extraction algorithm.

|Pipeline|Correct /72|False commitments /24|Determined correct /48|Needless deferrals /48|Complete parents /12|
|---|---:|---:|---:|---:|---:|
|Frozen joint result|34|11|21|27|1|
|Post-hoc visible-ID replay|70|1|47|1|11|

The existing full known-grammar parser remains **72/72**, and always-defer
remains **24/72**, both with zero model calls. Those controls are reported in
[the completed study](JOINT_RESULTS.md). The gate does not beat the full parser.
A new filtered-direct model comparison has not run; 70/72 must not be marketed
as proof that fact decomposition beats equally filtered direct inference.

## Two wrongs can conceal each other

**38 wrong decisions become correct, but two correct decisions become wrong.**
The other 32 stay correct. Both remaining failures are these regressions:

|View|Reference|Original joint|Gated replay|
|---|---|---|---|
|`route_lookup-4-flip`|ALLOW|ALLOW|INSUFFICIENT|
|`route_lookup-4-conflict`|INSUFFICIENT|INSUFFICIENT|DENY|

Both affected cases contain a wrong-field route on a target record. Removing
foreign-request evidence exposes the effect of that remaining extraction error.
In both regressions the original fact vector also matched the program reference:
the foreign route happened to supply the value missed on the target line.
Even a correct action and fact vector can conceal incorrect supporting records.
This is a saved-output computation, not an inference about model internals.

The gate keeps 162 target lines and drops 66 foreign lines, with 228/228 scope
matches and no UNKNOWN in this grammar. Replayed field statuses are correct for
166/168 fields; 70/72 entire vectors match.
0/18 truly missing fields become asserted values.

## A perfect naming shortcut limits the original experiment

The original generator assigns `request-…` to every target and `other-…` to
every distractor. Merely accepting the first prefix agrees with all 228
reference scopes. Existing results cannot distinguish actual ID comparison
from that shortcut. Before applying view variants, the generator adds a
foreign record on a key field with opposite polarity. Record ordering and
formatting variation are also limited.

The following checks rename only visible request IDs in the 72 texts.
They test code, with no transferred model predictions or new model scores.
Each row has 228 correlated lines; all three rows reuse the same 12 parents.

|Software-only renaming|Exact-ID gate correct /228|Prefix shortcut correct /228|Substring shortcut correct /228|
|---|---:|---:|---:|
|prefix_collision|228|162|162|
|same_namespace|228|162|228|
|swapped_prefix|228|0|228|

Same-namespace uses `request-NEUTRAL` and `request-DISTANT`; swapped-prefix
makes `other-NEUTRAL` the requested target; prefix-collision uses
`request-ABC` versus `request-ABCD`. Exact equality survives these injective
renamings by construction. That is a software property, not language transfer.

The [16 contract cases](data/scope_gate/contract_cases.jsonl) also include
mixed owners, two target facts, quotation, negation, implicit reference,
unfamiliar IDs and numbered lines. Unsupported shapes return UNKNOWN.
The gate does not establish that a record is true, current or authoritative,
and it does not solve [the one-line/two-fact limit](MULTIFACT_LINE_STRESS.md).

## Historical cost and the unexecuted deployment projection

This replay depends on **228 recorded joint forwards / 95,889 input tokens**.
**Zero additional forwards** were executed. Each historical joint query sees
only one record plus the same target/policy/definitions, so rejecting a record
before querying would leave every retained serialized prompt unchanged.
The corresponding saved subset has **162 queries / 68,636 input tokens**. That is a
deployment projection, not a newly timed run. Parser CPU cost and end-to-end
latency were not measured. Different prompts or filtered full-context direct
decisions cannot reuse these scores and require new authorized inference.

The old screen stays failed. Applying its thresholds to a method selected
after viewing the data would not make that method prospectively validated.

## Evidence and next falsifiable step

[Summary](data/scope_gate/summary.json), [all 72 decisions](data/scope_gate/decisions.jsonl),
[all 228 line gates](data/scope_gate/lines.jsonl), [168 field checks](data/scope_gate/fields.jsonl),
[216 unscored renamings](data/scope_gate/name_checks.jsonl), and
[replay implementation](scope_gate_audit.py) preserve the complete derivation.

```bash
python research/fact-execution/scope_gate_audit.py verify
```

The next preparation is a [target-switch challenge](../request-ownership/PROTOCOL.md):
hold a two-request record block fixed and change only the target header.
Both IDs use the same namespace. Compare full joint, gated joint, direct
and equally filtered direct decisions; count pairs with both answers correct.
The public original corpus is diagnostic material, not fresh confirmation.
Program-generated scenes with familiar wording remain synthetic preparation;
independent language review and later confirmation are still outstanding.

Entity binding and robustness to name variation have direct prior art:
[Feng and Steinhardt, ICLR 2024](https://arxiv.org/abs/2310.17191) and
[Meng et al., Findings ACL 2024](https://aclanthology.org/2024.findings-acl.969/).
Those papers motivate controls; no code, data or results from them are copied.
See the earlier [bounded extraction audit](JOINT_ROUTE_SCOPE_AUDIT.md) and
[Kev/Laya/Qwen attribution](../../THIRD_PARTY_NOTICES.md).
