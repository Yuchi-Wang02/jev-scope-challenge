# Stage reflection: execution succeeded, comparison is incomplete

## Objective and reality

We intended to compare where Jev and an ordinary small model lose agreement:
reading scenario facts, using a supplied graph, or executing supplied facts.
Jev completed the full grid. Predicted facts plus code did not consistently
improve on graph-assisted direct judgment, despite more than doubling calls and
input tokens. Supplied-fact model execution matched all 24 final labels in both
mappings. The source-label and human-assistance qualifications remain essential.

Qwen stopped on its second semantic smoke. Its main outputs do not exist. This
is a material plan-versus-reality gap, not evidence that Jev beats Qwen on the
24 selected scenarios. Both completed and failed work are published.

## What the gate taught us about our design

The second smoke output has valid logits, a valid mapping and a unique selected
letter, but a wrong truth value. The frozen protocol deliberately stopped there,
and we honored it. This should not be retroactively described as an API or parser
bug. The smoke gate conflated two distinct things:

1. Can we obtain and interpret a model decision with reliable accounting?
2. Does the model correctly solve a simple instance of the target capability?

Requiring the second before measuring the main capability can censor weaker
models. A useful future continuation would preserve the same prompts, precision,
readout, source cohort and mapping, but treat semantic smoke misses as reported
observations rather than infrastructure failures. Structural errors, unknown
usage and unresolved calls must still stop execution.

## Next bounded action

Prepare a separately named, prospective continuation amendment before any new
forward. It should schedule only the four unexecuted Qwen smoke jobs and 256
unexecuted main jobs. Do not replay the original two jobs or rerun Jev. Preserve
the original stopped journal and its freeze, hash the exact successor jobs,
and carry original plus successor costs into any eventual comparison.

The amendment is outcome-aware. Its result must be reported alongside the failed
original gate, not substituted into a story that the original protocol completed
without deviation. No new prompt, model, precision or verbalizer search is needed
to measure the already defined 24 scenarios. At this reflection's publication,
the continuation has not been implemented or executed.

## Longer-term judgment and presentation

This stage strengthens the case for testing the source of error before proposing
another reasoning mechanism. It does not yet establish that the remaining errors
are factual misunderstanding rather than reference/framing differences. No new
human review was obtained, and no stronger ordinary-model or budget-matched
comparison is complete.

Public framing: **"The rules executed. Extra fact calls did not reliably help."**
Show the full table, the cost increase, and the stopped comparator together.
Do not promote supplied-fact 24/24 as unassisted accuracy, or the smoke failure
as a broad model ranking. QA4PC's decomposition/execution framework remains prior
work; this repository contributes bounded, inspectable comparisons and failure
records, not an established novel method or a paper-ready finding.
