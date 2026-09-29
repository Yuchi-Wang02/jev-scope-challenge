# Frozen-scope N1 pilot: one line, one owner, with two direct budget controls

**Status before inference: execution source and encoded plans are frozen;
no model result exists.** This is a post-hoc development follow-up to the
[failed line-wise pilot](LINE_EVIDENCE_RESULTS.md) and the
[program-oracle decomposition](LINE_ORACLE_DECOMPOSITION.md). Both the data and
prior outputs were public during design. A pass cannot become an independent
confirmation or a Jev comparison.

## Scientific scope and exact methods

Only the 72 original synthetic development texts in 12 parent groups may be
scored. No provisional rewrite, reserved calibration/test input, composed
policy, new checkpoint, training, paid API, cloud job or Jev call is allowed.
The model path is the historical pinned Kev-LoRA N1 over Qwen3-4B-Base in
native causal-logit mode, with the same exact cached adapter-tensor and
weight-digest checks as the previous line pilot. The program supplies policy
and target-field definitions from visible strings to both joint routing and
direct controls. No structured construction record, reference label, case
family, variant, split tag or gold decision enters a model prompt.

The [joint-route candidate](JOINT_ROUTE_PROTOCOL.md) makes one mutually
exclusive A–F or A–H choice per visible evidence line. It uses only its fixed
primary option order. Its 228 choices are aggregated into TRUE, FALSE, MISSING
or CONFLICT per target field, then passed to the unchanged deterministic policy
executor. MISSING means no line was selected for that field, **not** certified
absence. Program offsets are locations of selected lines, not proof of their
meaning. No strict known-grammar audit or program reference can repair a
runtime prediction.

The [direct control plans](JOINT_TOKEN_CONTROL.md) share one 286-query union:

|Derived direct method|Saved forwards used|Planned input tokens|What matches joint routing|
|---|---:|---:|---|
|Single first order|72|Recomputed from saved rows|Historical one-call anchor|
|Call-matched|228|76,855|Calls, but 19,034 fewer input tokens|
|Input-token-matched|286|95,849|Within 40 input tokens, but 58 more calls|

The 228 call-matched queries are a subset of the 286 input-token-matched
queries; they are **not** executed twice. For each input and each derived
direct method, convert its candidate logits to a conditional A/B/C softmax,
map the three positions back to ALLOW/DENY/INSUFFICIENT, average those three
semantic probabilities over its included option orders with equal weight,
and select the maximum. An exact tie uses ALLOW, then DENY, then INSUFFICIENT.
This is a fixed order-sensitivity control, not independent samples or
calibrated correctness probability. Report both comparisons rather than a
single unsupported claim of equal total compute.

The scientific union contains **514 forwards**: 228 joint and 286 direct,
with **191,738 planned input tokens** and two unscored warmups. The runner
interleaves all queries with one frozen random seed, records exact prompts,
input/candidate token IDs, selected logits and conditional probabilities,
candidate mass, latency, checkpoint/load audit and runtime. A complete run is
required: no arm or option order may be picked after seeing partial scores.

## Evaluation and screening decision

[`joint_analyze.py`](joint_analyze.py) will recompute all decisions from the raw
forward records. For each method report correct decisions /72, false
commitments /24 uncertain, correct /48 determined, false INSUFFICIENT, wrong
supported actions, complete parent groups /12, six variants, calls, input
tokens and summed forward latency. For joint routing also report correct
field statuses /168, exact fact vectors /72 and all 228 program-derived line
audits: wrong request, wrong field, wrong polarity, missed relevant line, safe
nonselection and exact route. These construction labels are post-run audit
references only, with zero independent human annotation.

The joint candidate passes the previously fixed **development screening**
threshold only if false commitments are at most 7/24 **and** correct decisions
on determined inputs are at least 34/48. A failure stops this exact method
from advancing unchanged. A pass only justifies independently reviewed
language variation and stronger matched-resource comparisons; it does not
establish novelty, statistical significance, generalization or superiority
over a specialized decision model. Parent groups, not 514 calls or 72 correlated
views, are the sampling units.

## Freeze, approval and release boundary

The [execution builder](joint_execution.py) pins the 514 encoded prompts and
answer-token boundaries, source hashes, model revisions, seed, scope and
budgets in a separate manifest. The runner refuses a dirty checkout, an
existing output directory and any changed or foreign query. It writes only to
`joint_results/v0.1`. After a complete authorized run, the analyzer checks
every raw score against the committed plan and the source files at the
execution commit; it refuses overwriting derived results. GitHub CI verifies
the **pre-inference freeze** without tokenizer/model weights or inference.
Only after real outputs exist may CI add the raw-result recomputation step.

Building and verifying the freeze are not authorization to execute. The
earlier user approval covered only one completed 548-forward line pilot; this
514-forward joint/direct run requires its own review of the frozen plan and
local-resource cost before use. The first publication of this file, encoded
plan and runner contains no N1 scores or new model calls.

```bash
python research/fact-execution/joint_execution.py verify-freeze
```
