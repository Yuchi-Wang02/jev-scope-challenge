# One Line, Two Facts: a software stress test for exclusive routing

The [frozen 514-forward joint-route pilot](JOINT_EXECUTION_PROTOCOL.md) uses
original development text in which each evidence line expresses one structured
record. This separate stress test asks a prior question: **can its exclusive
one-label-per-line interface represent two facts on the same line even if the
line is read perfectly?** It makes no model call and is not part of that pilot.

For each of 56 eligible original development texts, the generator creates a
pair. `cross_field` replaces the newline between the first two target records
with a space when their fields differ. `mixed_scope_control` instead joins the
first target record with the first other-request record. Every original source
sentence appears exactly once in each version; the policy, target, records and
program decision are unchanged. Six otherwise suitable texts have no
other-request record, so they are excluded from the **paired** set. These are
112 transformations of 56 existing texts in 12 parent groups, not 112 new or
independent examples.

The [generator and verifier](multifact_line_stress.py) enumerates only
**semantically faithful** choices: a packed line may receive one label
warranted by one of its constituent records. It then runs the existing
[`aggregate`](joint_route.py) and policy executor. It never lets a hallucinated
label repair a missing fact. This tests representational reachability under
perfect routing, not a model's ability to choose the label.

|Packing|Paired items|Exact program fact vector reachable|Program decision reachable|
|---|---:|---:|---:|
|Two target fields on one line|56|0|30|
|Target and other-request record on one line|56|56|56|

The result is deterministic: an exclusive label cannot carry both target
fields, although some decisions remain correct because the omitted field does
not affect that policy outcome. The mixed-scope control shows that simply
removing a newline is not sufficient to cause the same loss. This is an
**interface impossibility on a constructed transformation**, not N1 accuracy,
Jev performance, language transfer, independent confirmation or a new
extraction algorithm. The source texts and program labels were already public
during design, and zero independent human annotations exist.

For example, the original `joint_approval-1-full` record states that reviewer
A and reviewer B both approve the target request. Once those two sentences
share a line, the faithful one-owner choices can record A **or** B, but not
both. The unchanged policy returns `INSUFFICIENT` for either choice, although
the program decision from both stated approvals is `ALLOW`. When the same
target A sentence is paired with an other-request sentence, the target A fact
and the separate target B fact remain representable.

All [112 audit rows](data/multifact_line_stress.jsonl) include construction
metadata and program references for inspection; future model prompts must use
only visible `state` and `policy`. The [summary](data/multifact_line_stress_summary.json)
is reproducible offline:

```bash
python research/fact-execution/multifact_line_stress.py verify
```

A future empirical comparison would need a separately frozen model protocol,
review of the transformed text, and matched-cost nonexclusive, fieldwise or
span-level alternatives. The 56 source texts remain development material;
their transformed versions must not be called held-out data.
