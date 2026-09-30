# More evidence calls, fewer commitments, worse decisions

The predeclared line-by-line N1 pilot **failed its screening rule**. It lowered
false commitments on uncertain inputs from 14/24 in the earlier whole-state
facts pipeline to 6/24, but correct decisions on determined inputs fell from
34/48 to **11/48**. Overall it reached 29/72 correct, versus 44/72 for the
earlier facts pipeline. It also cost 548 rather than 168 model forwards and
133,977 rather than 63,467 input tokens. This is a negative result for this
specific candidate on the already public original-development grammar, not a
claim about all evidence-selection methods or about Jev.

|N1/native path on the same 72 original texts|Correct decisions|False commitments / 24 uncertain|Correct / 48 determined|Calls|Input tokens|
|---|---:|---:|---:|---:|---:|
|Direct, one call (previous run)|31/72|23/24|30/48|72|23,523|
|Whole-state facts + code (previous run)|44/72|14/24|34/48|168|63,467|
|Line-by-line facts + code (new run)|29/72|6/24|11/48|548|133,977|

The line method produced 37 false INSUFFICIENT decisions on the 48 determined
inputs and no wrong non-abstaining action on those inputs. Its 12/12 conflict
views were correct, while only 1/12 full and 1/12 hold views were correct.
This pattern is consistent with overproducing CONFLICT when independently
classifying lines: 56 truly TRUE and 35 truly FALSE fields became CONFLICT.
The observation describes outputs; it does not establish the model's internal
reason for those choices.

## Citations did not make the selected facts trustworthy

The model selected 407 evidence lines as POSITIVE or NEGATIVE across 548
line/field queries. Against the program-derived construction records, 73 selected
lines referred to another request, 172 to a different field on the target
request, and 4 expressed the opposite value. These mutually exclusive counts
are **line selections**, not independent cases; 249/407 selected lines were
unsupported for the queried target field. Only 60/168 aggregate field statuses
and 13/72 complete fact vectors matched the program reference.

An offline strict known-grammar audit accepted 28/168 aggregate field claims,
rejected 139 and left one empty-citation MISSING claim as absence-unverified.
That audit can parse the entire synthetic text; using it to repair predictions
at runtime would make the system a pure-code reference, not a model citation
method. Exact program-assigned offsets show where a *model-selected* line is,
but do not prove that it supports the model's label.

## What was run and what the result means

The [protocol and screening rule](LINE_EVIDENCE_PROTOCOL.md), [1,096 proposed
query objects](preparation/line_query_plans.jsonl), [548 encoded primary
queries](preparation/line_native_primary.jsonl), runner and evaluator were
published in source freeze commit
[`66513e5`](https://github.com/Yuchi-Wang02/jev-scope-challenge/commit/66513e5ae256d1b7f688c951c7f9e98bf8215afb)
before model inference. The predeclared continuation gate was at most 7/24
false commitments **and** at least 34/48 correct determined decisions. The
first condition passed; the second failed. Therefore this method should **not**
advance to a rewrite/confirmation claim in its current form.

The run used the pinned historical Kev-LoRA N1/native path on cached
Qwen3-4B-Base, 548 scientific forwards plus two warmups. The run was 50.14 s
on an RTX 5070 Ti, peak allocated GPU memory 7,982 MiB; summed individual
forward latency was 41.36 s. Exact adapter-tensor and cached-weight checks
passed. There was no new training, model download, Jev call, paid API or cloud
job. No rewrite or reserved input was scored. Independent human annotations
remain zero. A PEFT warning about newer optional adapter-config keys was
observed, as in the earlier run; all 504 loaded adapter tensors were checked
exactly against the pinned checkpoint.

The source texts, program labels and previous N1 scores were already known, so
this remains a post-hoc development comparison. Call and token budgets differ
substantially; the table does not establish which method wins at a matched
budget. The Base and pointer arms, an instruction-tuned model, independently
reviewed paraphrases and a new confirmation set were not run. The method's
failure here does not establish that a specialized decision model is necessary.

Inspect the [raw N1 records](line_results/v0.1/N1.jsonl),
[per-text decisions](line_results/v0.1/decisions.jsonl),
[per-field claims and citation audits](line_results/v0.1/fact_claims.jsonl),
[complete summary](line_results/v0.1/summary.json) and
[runtime/provenance](line_results/v0.1/runtime.json). The
[offline evidence explorer](docs/line_explorer.html) displays every one of the
72 cases and all 548 saved line/field judgments, including errors from other
requests and fields. Download and open it locally; changing filters does not
call a model. Recompute all reported
values without a model or credential:

```bash
python research/fact-execution/line_run.py verify-freeze
python research/fact-execution/line_analyze.py --verify
python research/fact-execution/publish_line.py --verify
```

The next method should address *target and field binding* before buying more
line-level calls. A genuine comparison would need a fixed total budget and
independently reviewed language variation; repeating this failed primary path
on unreviewed rewrites would not make the evidence stronger.
The [post-hoc oracle decomposition](LINE_ORACLE_DECOMPOSITION.md) quantifies
which program-labeled line errors would need correction. It is a diagnostic,
not a tested repair.

## Cost sensitivity correction: include the zero-call controls

The later [interactive cost explorer](../../docs/risk_tradeoff.html) initially
compared only the three model paths. Adding always-defer and rerunning the
existing visible-text grammar parser offline changes the interpretation without
changing any saved model prediction. The constant baseline reads no reference
label at runtime, and the grammar parser receives only state and policy text;
program-derived labels grade their outputs afterwards.

|Path on the same 72 views|Wrong actions|Needless deferrals|All deferrals|Model calls|
|---|---:|---:|---:|---:|
|Direct|36|5|6|72|
|Whole-state facts + code|20|8|18|168|
|Line-by-line facts + code|6|37|55|548|
|Always defer|0|48|72|0|
|Known-grammar code|0|0|24|0|

Let a wrong action cost `r` units and a charged deferral cost one, excluding
computation. If only needless deferrals are charged, the line method's loss
`6r + 37` never reaches the four-path minimum for any `r >= 0`: whole-state
`20r + 8` beats it through `r = 2`, and always-defer's constant 48 beats it
from there onwards. If every deferral is charged, including correct uncertainty,
line loss becomes `6r + 55`; it is the unique minimum among the three model
paths and always-defer only for `37/14 < r < 17/6`, with ties at the endpoints.
Known-grammar code has loss 0 under the first convention and 24 under the second,
so it beats the line method throughout that interval. This control knows the
synthetic grammar and does not establish a general language parser.

These are post-hoc hypothetical loss calculations, not measurements of human
handling quality, money, harm or end-to-end runtime. Zero model calls does not
mean measured zero CPU time. The exact range calculation and source fingerprints
are in [the page builder](../../docs/build_risk_tradeoff.py); it adds no model
inference, independent annotation or confirmation claim.
