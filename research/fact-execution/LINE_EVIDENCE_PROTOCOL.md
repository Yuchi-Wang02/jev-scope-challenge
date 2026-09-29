# Proposed development diagnostic: classify each evidence line

**Pre-run protocol:** this file and its preparation manifest contain no model
forwards or scores. Results, if run, belong in a separate versioned result
directory with raw records and an independent read-only recomputation.
This is a post-hoc follow-up to [Correct Code, Wrong Facts](RESULTS.md), on the
same 72 public original development texts. It is neither a preregistered
confirmation nor a language-transfer result. The 144 provisional rewrites and
all reserved inputs remain unscored. The method is an attributed engineering
combination, not a claim to have invented line-wise entailment. Sentence-level
evidence and verification have clear precedents in
[FEVER (NAACL 2018)](https://aclanthology.org/N18-1074/); attribution plus
revision also predates this project in
[RARR (ACL 2023)](https://aclanthology.org/2023.acl-long.910/). Those tasks
are not identical to this finite-policy decision setting.

## Question and mechanism

Can a complete, line-by-line scan reduce unsupported target-field assertions
relative to the existing whole-state four-status extractor without collapsing
correct supported decisions? Each model query receives the original request
header, **one** visible evidence line, the full original policy and both
target-field value definitions. It chooses POSITIVE, NEGATIVE or IRRELEVANT for
that one line and target field. Program code aggregates all line choices:

|Selected target-field line labels|Aggregate status|
|---|---|
|Positive only|TRUE|
|Negative only|FALSE|
|Both|CONFLICT|
|Neither|MISSING|

The program locates each supplied line in the visible state; it does not infer
that the line supports the model's label. POSITIVE/NEGATIVE choices become exact
line-span citations with `model_line_classification_with_program_offsets`
provenance. MISSING means every line was *classified* irrelevant, not that
absence has been independently certified. The complete scan and the header
format are external procedural assumptions. The [strict known-grammar
control](cited_contract.py) may audit claims offline via
`audit_claim_known_grammar` on the original synthetic
text but must not silently correct model outputs at runtime: it already knows
the facts and would turn this into a pure-code oracle.

## Fixed dry-run scope and budget

[`line_evidence.py`](line_evidence.py) currently refuses a changed original
corpus, rewrites and reserved inputs. The 72 original texts yield **548 queries
per candidate order** (one per field × visible line) or **1,096** for both the
canonical and reversed three-label order. The primary order is canonical;
reverse order is a sensitivity analysis, never chosen after looking at labels.
The same cached Qwen3-4B-Base tokenizer revision
`906bfd4b4dc7f14ee4320094d8b41684abff8539` produced **133,977 native
input tokens per order**, maximum 277 per query, in a tokenizer-only local
preflight. These are planned inputs, not billed inference or model records.
All 1,096 proposed query objects, including their exact prompt strings, are in
[`preparation/line_query_plans.jsonl`](preparation/line_query_plans.jsonl).
[`line_plan_tools.py`](line_plan_tools.py) rebuilds them deterministically and
checks the [preparation manifest](preparation/line_query_manifest.json). The
manifest is a reviewable **preparation artifact**, not an execution freeze or
evidence that a model ran. Its IDs and source offsets are audit metadata; only
the `prompt` string is planned model input.

The first scored pilot uses the pinned historical Kev-LoRA/native
N1 path, with no new model downloads, training, paid API or cloud job. Its
primary candidate would need 548 forwards and 133,977 input tokens, compared
with 168 forwards / 63,467 input tokens for the old N1 canonical whole-state
facts pipeline and 72 forwards / 23,523 input tokens for old N1 direct single.
These costs are **not matched**. Report the full quality/cost tradeoff and do
not call a quality gain budget-matched superiority. Before any such claim,
specify and run a credible direct inference budget control with the same
schema help, total calls and token accounting; repeating identical deterministic
prompts is not an independent control. A later multi-arm comparison should
predeclare Base/native and Kev pointer encoding/parity rather than treating
N1-only findings as system-wide. Jev is not part of this proposed pilot.

## Evaluation and go/no-go rule

Use the existing 12 parents as clusters, not 72 independent examples. Preserve
the same 24 uncertain / 48 determined split and report all six variants, field
confusion, exact vectors, wrong-request citations, conflict coverage, missing
fields reported as values, final decisions, false commitments, supported-input
regressions, abstentions, calls, input tokens and measured latency. Publish raw
scores and exact prompts, not merely a selected example or a success total.

The existing N1 facts pipeline had 14/24 false commitments and 34/48 correct
determined decisions on these texts. As an **exploratory screening rule fixed
before new scores**, continue to the independently reviewed rewrite study only
if the primary line method reaches at most 7/24 false commitments and at least
34/48 correct determined decisions. This gate does not establish statistical
significance or cost effectiveness; even a pass requires the language-transfer
and budget controls. A failure is a useful result and should stop claims of a
working citation remedy on this path.

## Pre-inference and release gates

Before running models, create a versioned output directory and freeze exact
encoded plans, prompt and answer-token boundaries, local cached weight digests,
this protocol, the evaluator and the source commit. Refuse overwrite and
resume/partial-result cherry-picking. A checker must recompute every prediction,
cost and metric from raw records and prove zero rewrite/reserved queries. The
old fact-execution manifest and outputs must remain unchanged. Review the
frozen method and its known budget disadvantage before the scored run.

Execution preparation uses [`line_run.py`](line_run.py) to pin the 548 encoded
primary-order queries in `preparation/line_native_primary.jsonl` and a separate
execution manifest. The runner writes only under `line_results/v0.1`; the
[`line_analyze.py`](line_analyze.py) checker recomputes it from raw scores.
`line_run.py verify-freeze` is read-only and needs no local tokenizer; `build`
requires the cached tokenizer and must be committed before `run`.

The public hook, **if supported by real outputs**, is “The quote is real. The
fact may still be wrong.” Until then it describes an adversarial software
fixture, not an observed model citation. Release a small failure gallery only
with raw-record links, denominators, counterexamples and cost. No Hugging Face
dataset release or paper-level claim follows from this development pilot alone.

Dry-run commands (no model inference):

```bash
python research/fact-execution/line_evidence.py
python research/fact-execution/line_plan_tools.py verify
python research/fact-execution/line_evidence.py --native-token-budget
python -m unittest discover -s tests -p test_line_evidence.py -v
```

The tokenizer command requires the already cached pinned tokenizer; the other
commands are dependency-light and run in CI. No command above loads
model weights or a Jev credential.
