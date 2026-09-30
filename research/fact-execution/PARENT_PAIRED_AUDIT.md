# Parent-paired audit: safer abstention, lost determined decisions

This is a **derived, post-hoc description** of the same 72 public
original-development texts. It adds zero model calls and zero human
annotations. Both methods use the historical pinned Kev-LoRA N1/native
path, but different prompts and budgets. The 12 six-view parents are
the paired units; 72 views and 548 line queries are not independent
research samples.

|Saved method|Correct /72|Determined correct /48|False commitments /24 uncertain|Forwards|Input tokens|
|---|---:|---:|---:|---:|---:|
|Whole-state facts + code|44|34|14|168|63,467|
|Line-by-line facts + code|29|11|6|548|133,977|

## Matched views within each parent

Each cell reads **whole-state → line-by-line**. Every parent has four
determined and two uncertain views. Smaller false-commitment counts are
better; larger correct counts are better.

|Parent|Correct /6|Determined correct /4|False commitments /2|
|---|---:|---:|---:|
|joint_approval-1|4 → 2|3 → 1|1 → 1|
|joint_approval-2|3 → 2|2 → 1|1 → 1|
|joint_approval-3|4 → 2|3 → 1|1 → 1|
|joint_approval-4|3 → 4|2 → 2|1 → 0|
|reversal_exception-1|3 → 3|2 → 1|1 → 0|
|reversal_exception-2|4 → 2|4 → 1|2 → 1|
|reversal_exception-3|3 → 2|3 → 1|2 → 1|
|reversal_exception-4|2 → 4|2 → 3|2 → 1|
|route_lookup-1|6 → 2|4 → 0|0 → 0|
|route_lookup-2|4 → 2|3 → 0|1 → 0|
|route_lookup-3|5 → 2|4 → 0|1 → 0|
|route_lookup-4|3 → 2|2 → 0|1 → 0|

At the parent level, overall correctness improved / worsened / tied in
**2 / 9 / 1** groups. Determined correctness
improved / worsened / tied in **1 / 10 / 1**.
False commitments decreased / increased / tied in
**8 / 0 / 4**.

On the 48 determined views, the old method was correct and the line
method wrong on **26**; the reverse occurred on
**3**. Both were correct on **8**
and both wrong on **11**. On the 24 uncertain views,
the line method repaired **8** old errors and
created **0** new ones. This is a real
abstention tradeoff on these saved decisions, not a single-parent artifact.

The line method correctly chose all 12 conflict views but chose
INSUFFICIENT on 37 determined views. In the route-lookup family it
got **0/16 determined** views right versus **13/16** for whole-state
facts + code. The mechanism remains a hypothesis: these outcome counts
do not reveal why the model selected a line or field.

There is no p-value or population confidence interval here. The
parents were synthetically constructed and repeatedly inspected during
development; the line method was designed after prior results. Calls
and input-token budgets differ substantially, and no Jev or held-out
ShARC result enters this audit. The prewritten line-method screening
rule remains failed; parent pairing sharpens that negative finding
without turning it into a generalization claim.

## Source integrity

The script requires matching IDs, parent/family/variant/gold fields,
one record per method and view, six views per parent, and agreement
with both saved summaries. LF-normalized SHA-256 of the two decision
files:

- Whole-state decisions: `6a3567da7a1ee925f4827fb8770c266ec2443382c43e1631d021525b1051deff`
- Line-by-line decisions: `fcca7fe5a1fec9ff5ef2eb2a3d06e17cdc8f868171a156087c105e96c328983f`

Recompute the report without models, credentials, or writes:

```bash
python research/fact-execution/paired_parent_audit.py verify
```
