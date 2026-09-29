# What 245 wrong bindings cost — an oracle diagnostic, not a new model result

The [line-evidence pilot](LINE_EVIDENCE_RESULTS.md) made 548 saved N1/native
line/field judgments on 72 original development inputs. This follow-up makes
**zero model calls**. It replaces chosen classes of wrong judgments with labels
from the program that constructed these synthetic cases, then re-aggregates
facts and reruns the same deterministic policy executor. The replacements are
unavailable to a real runtime method.

The observed pilot remains **29/72 correct decisions**, with 6/24 false
commitments and 11/48 correct determined decisions. Of 548 line/field judgments:

|Program-identified disagreement|Judgments|Affected inputs|Parent groups|
|---|---:|---:|---:|
|Selected a line from another request|73|55|10|
|Selected a line for another field on the target request|172|60|12|
|Selected the opposite polarity for the correct request and field|4|4|1|
|Missed a relevant line|0|0|0|

The categories are disjoint by priority: wrong request, then wrong field, then
wrong polarity. A correct target/field line selected with the wrong polarity
belongs only in the third row. The 73 and 172 counts are **line judgments**, not
independent examples. The zero in the last row describes this particular saved
run, not a general property of N1 or of line-wise methods.

|Program-oracle replacements|Correct /72|False commitments /24|Correct determined /48|Correct fields /168|Previously correct inputs made wrong|
|---|---:|---:|---:|---:|---:|
|None: actual model output|29|6|11|60|0|
|Other-request selections only|39|4|19|73|1|
|Other-field selections only|36|9|21|119|4|
|Both other-request and other-field selections|68|1|45|164|1|
|All disagreement classes|72|0|48|168|0|

The full [16-combination record](line_results/v0.1/oracle_decomposition.json)
shows that effects interact. For example, perfect field filtering by itself
would *increase* false commitments from 6 to 9 and turn four previously correct
inputs wrong. Replacing both binding-error classes recovers 40 baseline errors
but regresses one baseline success. Four remaining errors in that row depend on
the four polarity disagreements; replacing every disagreement gives the
program's own 72/72 reference, as it must. These are exact replay results, not
confidence intervals or estimates of a future method's accuracy.

## What this changes in the next experiment

The evidence favors testing **request and field binding together** before
spending more calls on polarity or adding a confidence threshold. A plausible
candidate would ask for an explicit line-to-target/field/value route (including
an uncertain or no-observation option). An [unscored joint-routing preparation](JOINT_ROUTE_PROTOCOL.md)
now makes that hypothesis reviewable; it has no model result. A future
protocol must pin its visible-only prompt, option mapping, aggregation, total
calls/tokens and a direct-decision budget control *before* inference. The
strict known-grammar parser remains a separate pure-code reference; using its
record labels as a runtime filter would simply put the oracle into the method.

All cases and their construction labels were already known during this
analysis. There are no independent human annotations, rewrite scores, reserved
scores, new Jev measurements, or budget-matched new-model comparisons here.
Passing a software verifier proves the arithmetic and provenance of this
post-hoc calculation, not that target binding can be achieved on unseen text.

Recompute from the saved, frozen raw model scores without model weights or an
API key:

```bash
python research/fact-execution/line_analyze.py --verify
python research/fact-execution/line_oracle_decomposition.py --verify
```

The script first invokes the line-pilot verifier, including the pre-inference
source freeze and raw-score checks. It then reconstructs all 16 replacements
from the original program records; it does not edit the scientific outputs.
