# Both models missed the same one-word boundary

All **444 planned decisions completed**: 222 Jev requests and 222 local Qwen
generations, including 6 smoke per backend. Both smokes were 6/6. No retries,
execution amendments, failed calls, invalid answers or budget overruns. The
[prospective freeze](https://github.com/Yuchi-Wang02/jev-scope-challenge/commit/5bd967516217b9d38078ec487f0daa740917421d)
was published before calls. [Protocol](PROTOCOL.md), [machine report](report.json),
[independent recount](verification.json), [Jev journal](results/jev.jsonl),
[Qwen journal](results/qwen.jsonl), [all requests](request_plan.json).

**Under the stated classical-constraint contract**, both backends returned the
same answer on every corresponding main input in both mappings. Each scores
84/108 (77.78%) per mapping. The 24 errors concentrate exactly on the two
critical direction cells. This is a reproducible diagnostic result, not a
population estimate or evidence that every configuration of either model fails.

## Complete nine-cell matrix

Each row contains 12 vocabulary families. Counts and answers below are identical
for both backends and both mappings; no favorable ordering was selected.

|Rule|Fact P|Constructed reference|Both models' answer|Correct /12|
|---|---|---|---|---:|
|Q if P|True|yes|yes|12|
|Q if P|False|maybe|no|0|
|Q if P|Unstated|maybe|maybe|12|
|Q only if P|True|maybe|yes|0|
|Q only if P|False|no|no|12|
|Q only if P|Unstated|maybe|maybe|12|
|Q iff P|True|yes|yes|12|
|Q iff P|False|no|no|12|
|Q iff P|Unstated|maybe|maybe|12|

Both critical sufficient-to-necessary pairs are 0/12 correct per mapping and
backend. All unknown-fact triples are 12/12 correct; no complete nine-case family
is fully correct. Mapping disagreements are 0/108 for each backend, within the
two tested orders only. False commitments are 24/60 on maybe-reference cases;
unnecessary deferrals are 0/48 on determined-reference cases. Invalids are 0.

The always-maybe control is 60/108 (55.56%). The known-grammar program is 108/108:
it has an author-specified parser and solves the finite contract exactly. Its
success is not evidence of a general natural-language system or a new algorithm.

## Inspect a failure and its countermodels

Policy: the parcel qualifies for priority dispatch **only if** it carries a blue
inspection seal. Visible fact: it carries the seal. This restricts Q => P.
Both (P=true,Q=true) and (P=true,Q=false) satisfy the rule and fact, so the
specified reference is maybe. Both models answer yes.

Conversely, with **if** and an explicitly absent seal, P => Q permits either
eligibility value. Both models answer no. The complete [possible-world witnesses](cases.json)
make those underdetermined cases inspectable without appealing to external policy.

The output pattern is exactly what interpreting every connector as equivalence
would produce on this grid. Call it a **biconditional-like error signature**,
not proof of internal rule representation, a causal mechanism or intentional
disregard of instructions. It meets the frozen exploratory replication screen
on 12/12 families for both signature types and both models.

## Actual work and cost

|Backend / phase|Decisions|Input tokens|Output tokens|Summed callback seconds|
|---|---:|---:|---:|---:|
|Jev smoke|6|2,718|228|0.970|
|Jev main|216|100,836|8,208|31.410|
|Qwen smoke|6|936|12|1.718|
|Qwen main|216|36,684|432|48.482|

Jev session 33.468 seconds; Qwen session 51.437 seconds, with verification/load
timings separately retained in metadata. Qwen generated 222 sequences, each with
one answer token and EOS: 444 output tokens and 444 physical forwards. Different
hosted/local systems and tokenizers prevent a matched-compute or price-performance
claim. Jev's output-token usage is API-reported, not visible chain-of-thought.
Model version and all raw probability metadata are preserved; probability
calibration is not established by this run.

## Stage audit and decision

Goal: isolate whether explicit rule direction survives a one-word change, after
the prior source audit exposed uncertainty about policy scope. Reality: a stronger
and cleaner signature than isolated errors, shared by both measured backends.
Unknown facts and equivalence controls pass; the measured problem is narrower
than a general inability to output maybe.

Limits: 12 authored vocabulary families reuse 3 logical patterns; no independent
human language review, alternative phrasing, stronger-model baseline, reasoning
configuration, or causal intervention. The two display orders do not exhaust
permutations. Classical constraint semantics is explicit, but pragmatic readings
of ordinary policy language can still differ; that distinction deserves human
review before claims about natural business policies. This experiment neither
adjudicates QA4PC references nor establishes a dedicated-versus-general advantage.

Stop this grid as promised. No repair prompt was searched and no harder examples
were added. A possible next study is a *new*, predeclared comparison of ordinary
policy wording, explicit direction explanations and symbolic constraints, with
the same help for both backends, reviewed labels and a stronger ordinary baseline.
Any improvement would first establish instruction/representation sensitivity,
not a new algorithm. This result can be shown as a compact reproducible boundary
with all controls beside it, rather than a claim that Jev is uniquely defective.
