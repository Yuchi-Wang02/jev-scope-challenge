# Same records, different request: ownership-switch preparation

**Status: design and tokenizer-only preparation. Model forwards and independent
human annotations are both zero. This is not an execution-ready freeze.** No
runner or execution approval is included. The existing completed studies remain
unchanged; this directory contains new constructed scene instances.

The [joint-routing pilot](../fact-execution/JOINT_RESULTS.md) confused other
requests with target facts. Its original generator also used `request-` for
targets and `other-` for distractors. This preparation removes that naming
shortcut and makes ownership change while the evidence stays identical.

## Falsifiable question and paired construction

Can a visible request-ID equality gate improve decision correctness on **both
members of a target-switch pair**, while preserving relevant evidence and not
increasing false commitments? The gate is a program component, not a learned
model improvement or a novel extraction algorithm.

There are **24 parent scenes and 48 views**: eight parents for each of the same
three policy families (joint approval, reversal exception, route lookup).
Every scene includes two requests; switching only the target in the header
changes the program-reference action. The record block and policy are byte
identical within a pair. Per family, four pairs switch between ALLOW and DENY,
and four between a determined action and INSUFFICIENT. Overall labels are
18 ALLOW, 18 DENY and 12 INSUFFICIENT; target slots are balanced within family.

Both IDs use `request-` plus five uppercase letters. Twelve pairs differ in
one character; twelve differ in all five. The first record belongs equally
often to each request within each ID-similarity stratum, with remaining order
deterministically shuffled. Within every family × pair-kind × ID-similarity
cell, the two scenes balance the first owner's action/status: ALLOW and DENY
for determined/determined pairs; DENY and INSUFFICIENT for
determined/insufficient pairs. An independent binary observation-pattern
schedule is also balanced inside every cell and applied to both owners.
It controls which reviewer/base field is missing or which route/site
orientation appears, so these patterns are not tied to near versus distant
IDs. The first owner in a determined/insufficient scene never has ALLOW;
this residual design restriction is explicit and does not vary by similarity.
The preparation manifest reports the crossed counts. The
scene references come from the existing finite possible-world solver and are
cross-checked using its separate direct solver and known-grammar text parser.
Neither program agreement nor a hash constitutes independent language review.

The [scenes](data/scenes.jsonl) contain construction records; the
[views](data/views.jsonl) contain displayed strings and evaluation references.
The prompt-builder API accepts **only state and policy strings**. It receives
no construction record, gold action, pair kind, target slot or scene identity.

## Prospective methods and shared queries

|Method|Planned forwards|Inputs and aggregation|
|---|---:|---|
|Joint routing, full records|200|One existing joint route per line, fixed primary option order; unchanged four-state aggregation and executor.|
|Joint routing plus visible-ID gate|Same saved 200|Mask foreign lines using the header and visible line alone, then aggregate saved routes. Adds no forward.|
|Direct, full records, call matched|200|For each view use as many distinct answer orders as full record lines (3–6); mean semantic candidate probabilities.|
|Direct, visible-ID filtered|100|Remove only DROP lines, then use as many distinct answer orders as retained lines (1–3); same direct scaffold and aggregation.|
|Direct single-order anchors|Subsets of each direct arm|Use mapping zero for all 48 views; no extra inference.|
|Known grammar / always defer|0|Separate transparent program and constant controls.|

The physical planned union is **500**, derived from the scenes rather than
adding every method row. `direct_full` matches joint calls. `direct_filtered`
has fewer calls and shorter evidence; this is a deployable-input comparison,
not equal total compute. The single-order direct anchors compare filtering
with one call per view. All input token counts are reported in the
[tokenizer manifest](preparation/token_manifest.json); no equal-token claim
is made. Actual wall time, CPU filtering time, GPU memory and model latency
remain unmeasured. There are no warmups yet; a later execution protocol must
specify warmups, scheduling, complete output validation and run costs.

The visible gate is [scope_gate.py](../fact-execution/scope_gate.py). It compares
the complete identifier in the header with the line's explicit identifier;
it may not read construction scope or an audit label. UNKNOWN lines are
retained by the filtering function, and this initial scene grid requires zero
UNKNOWN outcomes. A future broader grammar must report UNKNOWN coverage rather
than silently treating it as evidence of absence. No filtered prediction has
been observed. Full and filtered arms must both be retained regardless of outcome.

Direct aggregation averages conditional A/B/C probabilities after mapping
positions back to ALLOW/DENY/INSUFFICIENT. Exact ties use that action order.
These are conditional candidate distributions, not calibrated correctness
probabilities. All prompts use the previously declared field definitions and
policy scaffold; these definitions are not observations.

## Endpoints and decision rule

The primary endpoint is **complete pairs correct /24**. Report paired gains,
losses and ties between each proposed method and the full joint/direct
controls, plus separate results for near versus distant identifiers. Also
report view correctness /48, false commitments /12 uncertain views,
determined correctness /36, needless deferrals, wrong determined actions,
exact fact vectors, target-line retention, foreign-line acceptance, and gate
UNKNOWN coverage. Every correct-to-wrong action transition must be retained.
For the program gate, separately report lexical selection correctness and the
downstream model action; perfect lexical selection can still expose an error.

The gate's directional hypothesis fails this diagnostic if complete-pair
correctness does not improve or false commitments increase relative to the
ungated joint route. Passing only justifies a separately reviewed follow-up;
it is not a significance claim or confirmation. Use the 24 parent scenes as
the sampling units; 48 views, 500 forwards and individual lines are correlated
measurements. No old development threshold is reused as a retrospective pass.

## Limits, review and release boundary

This addresses the target/distractor prefix correlation and holds records
fixed during a target switch. It **reuses inspected language and policy
grammar**, so new scenes are not new policies, unseen natural-language
structures, independent confirmation, or evidence of Jev performance.
Request IDs, action balance and record lengths still come from a small
constructed design. A grammar-aware parser remains a strong zero-model control.

Implicit reference, aliases, mixed-owner lines, multiple facts per line,
cross-sentence resolution, quoted identifiers, unreadable IDs, policy changes
and genuine contradictory target records are omitted. They need a separate
contract and independently reviewed examples; this preparation does not claim
to solve them. No original reserved case or provisional rewrite is used.

The [visible review packet](review/visible_packet.json) and
[blank response form](review/blank.csv) omit gold labels, but parent identities
and public construction sources remain available. They are an audit aid, not
a fully blinded study. Independent reviewers must label actions and explain
evidence/ambiguity before confirmation; annotations currently number zero.
More general language transfer requires separately reviewed wording held out
from method design. Do not tune the gate or prompt on eventual confirmation scores.

```bash
python research/request-ownership/prepare.py build
python research/request-ownership/prepare.py verify
python research/request-ownership/prepare.py encode --cache G:/jev-lab/hf-cache
python research/request-ownership/prepare.py verify-tokenizer --cache G:/jev-lab/hf-cache
```

`build` writes only preparation artifacts. `encode` loads the cached pinned
Qwen3-4B-Base tokenizer with `local_files_only=True`, checks answer boundaries,
and writes tokens; it loads no model weights and makes no inference call.
Offline `verify` checks derivation and stored encoding integrity;
`verify-tokenizer` re-encodes independently from that cached tokenizer.
A distinct execution freeze, runtime validation and user review are still
required before scoring. Upstream Kev and Laya provenance remains documented
in [THIRD_PARTY_NOTICES.md](../../THIRD_PARTY_NOTICES.md).
