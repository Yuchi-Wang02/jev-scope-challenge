# Same scenarios, different answer mappings: completed amended comparison

**Completed, 2026-09-30.** The named Qwen continuation ran exactly 260 previously
unexecuted jobs, with zero replay, retries, additional cases or new weights.
Together with the original two Qwen prefills and 262 Jev requests, this completes
the original 524-decision coverage under an explicitly outcome-aware gate amendment.
It does **not** mean the original smoke gate passed.

The [amendment](CONTINUATION_PROTOCOL.md), [manifest](continuation_manifest.json)
and [freeze](continuation_freeze.json) were committed and pushed in
`cebac574d7b7123f151957f3c521ebd7a2fc1446` before successor execution.
Successor plan SHA-256: `da098eb6605aa498591f609938a3bb28f09d21df16341210dceef663299c7937`.
All 260 successor job hashes equal their original planned hashes. Model input,
token sequence, checkpoint, precision, readout and scoring did not change.

Evidence: [new raw journal](results/qwen_continuation.jsonl),
[combined report](continuation_report.json), [original stop](RESULTS.md).
Original journals/report remain byte-preserved; Jev results are reused, not rerun.

## Main results: source agreement, all 24 selected scenarios

Mapping 0: A=yes, B=no, C=maybe. Mapping 1: A=maybe, B=no, C=yes.
Parenthetical numbers are invalid final decisions, retained in denominators.

|Route|Jev mapping 0|Jev mapping 1|Qwen mapping 0|Qwen mapping 1|
|---|---:|---:|---:|---:|
|D: plain direct|19/24 (0)|19/24 (0)|13/24 (1)|19/24 (2)|
|G: graph-assisted direct|20/24 (0)|20/24 (0)|14/24 (0)|16/24 (3)|
|F: predicted facts + code|19/24 (0)|20/24 (0)|12/24 (0)|14/24 (3)|
|L: supplied reference facts + model execution|24/24 (0)|24/24 (0)|19/24 (1)|22/24 (0)|
|F intermediate fact labels|49/56 (0)|50/56 (0)|22/56 (0)|38/56 (3)|

Strict two-scenario tree success: Jev D 8/12,8/12; G 9/12,9/12;
F 8/12,9/12; L 12/12,12/12. Qwen D 4/12,7/12; G 4/12,6/12;
F 3/12,5/12; L 7/12,10/12. Trees are the 12 clusters, not 48 independent cases.

**Extra condition calls did not consistently improve either model over G.**
Qwen F loses two correct final decisions relative to G in both mappings. In
mapping 0, it fixes zero and regresses two; in mapping 1, it fixes two and
regresses four. Jev has zero fixes/one regression and one fix/one regression.
All F combinations use the same standard executor and the model's own facts.
In each Qwen mapping, six scenarios have wrong valid facts masked by their final
formula result; final agreement does not certify correct fact interpretation.

L is explicitly label-assisted. Its outcome cannot be compared as unassisted
policy reasoning. All references are upstream annotations with consistency
checks, not new independent human adjudications by this project.

## Answer-mapping sensitivity and invalids

For Qwen, valid final actions change across mappings on:

|Route|Changed actions among valid-both scenarios|Invalid in either mapping|
|---|---:|---:|
|D|9/21|3/24|
|G|14/21|3/24|
|F|12/21|3/24|
|L|3/23|1/24|

Corresponding Jev changes are D 0/24, G 0/24, F 1/24 and L 0/24, with no invalids.
Qwen fact agreement moves from 22/56 to 38/56 while source facts stay fixed.
This supports an **interface-sensitivity observation for this exact checkpoint,
prompt and finite readout**, not a universal inability to interpret facts.
Do not select only Qwen's better mapping or pool repeated mappings as new samples.

There are ten exact next-token maximum ties among Qwen's 256 main physical
prefills: D three, G three, F three, L one. The three tied F questions make three
composed finals invalid; those final invalids are not additional model calls.
Ties remain invalid under the original rule. No precision rerun or tie break was
performed, and this audit does not establish that BF16 caused them.

Candidate vocabulary mass across Qwen main calls ranges from 0.984698 to
0.999321 (mean 0.996942). High legal-candidate mass does not imply semantic
correctness or mapping stability. Nor do these observations establish a simple
fixed-letter preference: for example, the unchanged B=no option is never selected
in G mapping 0 but is selected 12 times in G mapping 1.

## Smoke history and cost

All six Qwen smoke observations are now available: three match their expected
values, three do not. `no OR no` fails mapping 0 but passes mapping 1; `NOT no`
is answered no in both mappings. The original second-smoke gate failure stays
in its original journal. Later semantic misses are recorded under the amended
policy; no infrastructure error was promoted to successful execution.

Qwen successor: 260 physical prefills, 77,150 input tokens, zero generated
tokens. Original plus successor: **262 prefills, 77,528 input tokens**, zero
retries and zero budget overruns. Both model loads are included separately:
verification 5.984 +5.953 seconds; loading 3.485 +3.516 seconds. Aggregate callback
session time is 48.734 seconds. Imports/process overhead are not fully measured.

|Qwen phase/route, both mappings|Prefills|Input tokens|Summed callback seconds|
|---|---:|---:|---:|
|Smoke|6|1,116|1.499|
|D|48|11,306|8.106|
|G|48|14,666|8.734|
|F|112|41,180|21.152|
|L|48|9,260|7.719|

Qwen F uses 2.33x G's calls and about 2.81x its input tokens, while source
agreement is lower. Jev F uses 2.33x G's calls and about 2.60x its inputs without
a consistent gain. These are within-model work comparisons, not controlled
cross-model latency or monetary-cost rankings. Jev's 159,118 input and 9,956
returned output tokens are charged once in the combined ledger; no new API
request was made during continuation.

## Verification and boundary

Original and successor journals replay independently against their respective
plan hashes. Their Qwen job sets are disjoint and the ordered union equals all
262 originally planned Qwen jobs. Saved choices/logits reproduce actions and
exact ties. A separate source-based evaluator reconstructs every main/fact count
from raw native choices or maxima and pinned source labels, without model weights
or the private execution plan:

```powershell
python research/qa4pc-stage-attribution/verify_continuation_counts.py --source-dir .local/qa4pc-audit
```

The full analyzer additionally checks chronological records and cost after private
plan reconstruction: `python research/qa4pc-stage-attribution/analyze_continuation.py verify`.
The original analyzer still verifies the original stopped report unchanged.

Share with caveats: 24 selected scenarios /12 trees, two mappings, outcome-aware
gate amendment, upstream references, no new human adjudication, only this Qwen
finite no-thinking configuration, and human graphs/facts explicitly supplied in
assisted arms. There is no stronger ordinary-model, all-permutation, generated
label, or matched-budget result here. See [the next decision](NEXT_DECISION.md).
