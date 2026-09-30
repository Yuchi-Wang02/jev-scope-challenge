# Valid generated outputs do not close the decision gap

Subsequent [all-case source audit](SOURCE_AUDIT.md) flags four decisive-evidence
gaps and four rule-scope questions. These are outcome-aware AI review notes,
not adjudicated corrections. All original scores and denominators below remain
unchanged; they measure source agreement, not human-verified accuracy.

Completed all **648 frozen jobs**: 162 Jev requests, 162 Qwen prefills and 324
Qwen generations, including smoke. Freeze commit
[`eba5ba4`](https://github.com/Yuchi-Wang02/jev-scope-challenge/commit/eba5ba4671679b58f093174703fc52dd1d4905eb)
was published before calls. No retries, halt, budget overrun, protocol amendment
or new model download. [Machine report](report.json), [independent replay](verification.json),
[Jev raw journal](results/jev.jsonl), [Qwen raw journal](results/qwen.jsonl).

These are **source-agreement counts on 24 scenarios clustered in 12 new policy
trees**. Six answer mappings are repeated measurements, not 144 independent
examples. Source labels are no=13/maybe=6/yes=5; no project human review was added.

## All mappings, including invalids

Each entry is correct/24. Finite ties count as incorrect in this denominator.

|Mapping A/B/C (semantic route uses this label display order)|Jev native|Qwen finite letters|Qwen generated letters|Qwen generated semantics|
|---|---:|---:|---:|---:|
|yes /no /maybe|17|11 (1 invalid)|12|12|
|yes /maybe /no|17|16|16|14|
|no /yes /maybe|17|13 (2 invalid)|14|14|
|no /maybe /yes|16|15 (1 invalid)|16|14|
|maybe /yes /no|17|16|16|17|
|maybe /no /yes|17|14 (1 invalid)|15|16|
|Mean of six mapping counts /24|16.833|14.167|14.833|14.500|
|Agreement across 144 repeated decisions|101/144 (70.14%)|85/144 (59.03%)|89/144 (61.81%)|87/144 (60.42%)|

Both generated routes have zero invalids or truncations. All 324 generated smoke
and main outputs are one label token followed by EOS. This establishes contract
feasibility in this setting, not semantic reliability. All three constant-output
controls are disclosed: always yes 5/24, always no 13/24, always maybe 6/24. The
most frequent reference class was not used to select prompts or model outputs.

## What the bridge resolves

Finite and generated-letter prompts/input IDs match exactly. All 162 paired
first-step candidate-logit vectors, including smoke, match exactly too. In the
main grid, the 139 decisions with a unique candidate maximum have identical
mapped actions. Five finite ties are invalid; greedy generation chooses a token
in those cases, four reference-matching and one not. Thus **the four-count total
gain of generated letters is entirely tie handling, not changed unique-
maximum judgments**. Here "four-count" refers to the total over 144 repeated
decisions (0.667 more correct per 24-item mapping on average), not four additional
independent scenarios. This finding is specific to this frozen run.

Switching generated letters to generated semantics changes 23/144 decisions:
9 corrections, 11 regressions and 3 changes between wrong labels. Its mean source
agreement drops from 89/144 to 87/144, despite better across-mapping consistency.
One mapping ties Jev at 17/24; choosing that mapping would misrepresent the grid.
The design changes output vocabulary and its instruction together, so it cannot
identify a unique causal mechanism such as position bias or symbol binding.

## Stability and six-call aggregation

|Route|All six outputs valid /24|All six valid and identical /24|All six correct /24|Strict majority correct /24|Majority abstentions /24|
|---|---:|---:|---:|---:|---:|
|Jev native|24|23|16|17|0|
|Qwen finite letters|19|13|8|13|4|
|Qwen generated letters|24|15|10|15|2|
|Qwen generated semantics|24|18|12|14|1|

Strict majority requires four mapped valid votes out of six. Invalid votes never
become maybe; no denominator shrinkage. Every aggregate consumes six calls, all
charged. This is an established voting control, not a new method or a cost-matched
win over one call. More stable outputs can still be consistently wrong.

Strict two-scenario tree successes across the six mappings are Jev 5/5/5/4/5/5,
finite 3/4/3/4/4/3, generated-letter 3/4/3/5/4/3, semantic 2/3/3/3/5/4, each out of 12.
No population inference or significance test is claimed.

## Costs and smoke outcomes

|Backend|Actual decisions including smoke|Input tokens|Returned/generated tokens|Callback-session seconds|
|---|---:|---:|---:|---:|
|Jev1.13.0|162 HTTP attempts|87,006|6,156|26.156|
|Qwen3.5-4B BF16|486 local decisions|115,668|648|97.141|

Qwen's physical forwards total 810:162 finite plus 648 autoregressive forwards.
Model-byte verification 6.094 seconds and model load 3.547 seconds are separate;
imports and other process overhead are not fully included. Main callback sums
are 24.524 seconds finite,29.840 generated letters,29.875 generated semantics.
The two generated routes each use 288 output tokens on main items; finite uses 0.
Fixed sequential ordering, shared device context and different APIs mean this
is a descriptive ledger, not a randomized end-to-end speed comparison.

Smoke agreement is native 18/18, finite 17/18, generated letters 17/18, semantic 18/18.
Semantic smoke accuracy was explicitly not a launch gate. No run contract was
changed after these outcomes. No additional invocations were made for scoring.

## Verification and limits

The main analyzer replays durable journals and validates actions against raw
choices/logits and the strict parser. A separate counter reads pinned original
source JSON and public journals without importing those observation/parsing
helpers. It reproduces all 648 actions, six mapping tables, invalids, votes and
token totals. The pinned tokenizer independently decodes all 324 generated token
sequences. Original private/public journal bytes match. Source consistency and
this technical replay do not validate reference semantics.

```powershell
python research/qa4pc-answer-interface/analyze.py verify
python research/qa4pc-answer-interface/verify_counts.py --source-dir PATH_TO_PINNED_QA4PC
# Add --model-dir PATH_TO_PINNED_MODEL in the pinned environment to recheck token decoding.
```

Jev has higher mean source agreement and more stable decisions on this sample.
This does not establish specialized-model necessity: only one ordinary 4B
checkpoint, a short greedy nonthinking interface,12 policy clusters, no new
independent semantic adjudication, and no stronger or fixed-budget comparator.
The fairer interface control does not consistently repair Qwen here; this cohort
is now closed to further prompt, precision, label or decoding searches.
See [milestone audit and next decision](NEXT_DECISION.md).
