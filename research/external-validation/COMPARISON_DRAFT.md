# Reviewed ShARC pilot: direct comparison draft

2026-09-30. **Not an execution freeze.** No ShARC model predictions exist.
The [plan compiler](comparison_plan.py) can prepare private requests after
revalidating the saved human-review chain. It has no API client, credential
loader or model weight loader. A generated plan still leaves inference closed.

## Research decision and scope

Compare typed Jev decisions with the existing ordinary Qwen3.5-4B runtime on
the same reviewed rule/history contrasts. Measure correct paired decisions and
resource consumption. This is a fixed-budget development comparison, not a
model-family capability ranking, independent confirmation or new method.
The [nearest-work audit](NEAREST_WORK_UPDATE.md) rules out novelty claims for
single-condition contrasts and ordinary decomposition with logic.

The existing review protocol selects 24 primary pairs from 24 distinct trees,
with six ordered reserve pairs. Both reviewers judge all 60 items independently.
Adjudication and the frozen reserve procedure determine 48 eligible items.
Insufficient valid reserves stop the study; the compiler does not shrink or
reselect the cohort. Clear same-action judgments remain eligible even when they
disagree with provisional source strata. No post-result replacement is allowed.

The selection has no deliberately invariant controls or source-Irrelevant cases.
It is a public training slice, with possible pretraining exposure and a small,
selected sample. Do not estimate real-world error prevalence from it.

## Fixed candidate grid

|Condition|Items|Order variants|Planned calls|Generation cap per call|
|---|---:|---:|---:|---:|
|Jev `jev-1.13.0`|48|2|96|Native typed choice|
|Qwen3.5-4B direct|48|2|96|256 generated tokens|
|Qwen3.5-4B thinking|48|2|96|2,048 generated tokens|

The two orders are `Yes, No, Irrelevant, ASK` and its reversal. Jev maps these
to its A/B/C/D criteria; Qwen sees the same ordered action names and emits the
semantic action in JSON. This controls visible task content and displayed order,
not tokenizer identity or every difference between native-choice and generative
interfaces. Report order effects within each interface.

All conditions receive only `snippet`, `question`, `scenario` and the original
history question/answer fields. The task instructions are common, followed by
the format instruction each API requires. IDs, pair links, source answers,
source evidence, review opinions and adjudicated actions stay outside requests.
No examples, tools, retrieval, parsed graph, fact extractor or teacher help.

Qwen uses the pinned revision
`851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, BF16, batch size one and the existing
Transformers 5.3.0 environment. Reuse the checked sampling configuration from
[generation calibration](../generation-calibration/PROTOCOL.md): temperature
0.7/top-p 0.8 direct; temperature 1.0/top-p 0.95 thinking; top-k 20, min-p 0,
repetition penalty 1, generated-token presence penalty 1.5. Reset seed 17 for
each call. A single seed does not measure sampling variability. No seed search.

The cap is an explicit resource constraint. It has not been established as
sufficient on this task. Truncation is a scored failed output, not a reason to
silently extend the cap. Any later budget study requires a separate protocol
and cannot overwrite this grid.

## Work limits and accounting

- At most 96 HTTP attempts, zero automatic retries and 192 local generations.
- Qwen total generated-token ceiling: **221,184**. All thinking and final tokens
  count. At most 1,000,000 input tokens and 32,768 input-plus-output tokens per
  call; reject oversized input without truncating it.
- Jev planning ceiling: 1,000,000 serialized UTF-8 request bytes plus 256 per
  request. This is a planning proxy, **not a tokenizer count or proved upper
  bound**. Record returned usage separately; stop further requests when the
  500,000 actual input-token stage limit is reached. A response can cross the
  limit, so any crossing amount must be reported.
- Local generation-stage wall deadline: 7,200 seconds, checked at token and
  call boundaries. Report any unavoidable kernel overrun. Loading, hashing and
  tokenizer work are recorded separately; no warm-up forwards are added.
- Model files load from the existing local installation. No weights, packages
  or kernels are downloaded for this grid.

There is no requirement to consume unused budget. No cap or prompt changes
after outputs are inspected. Jev API latency and local device latency describe
different serving arrangements; report both without attributing the difference
solely to model architecture. Local computation is not economically free merely
because no API invoice is issued.

## Output, controls and stop behavior required in the execution freeze

Reuse the [final-action contract](ACTION_INTERFACE.md) and backend extraction.
Bare exact JSON and one complete lowercase json fence have the same semantic
score; report strict bare-JSON compliance separately. Incomplete generations,
boundary errors and invalid schemas remain visible and in denominators.
The future analyzer must use [paired metrics](PAIRED_METRICS.md) per condition,
verify identical cohorts and retain every pair record. No predictions are
available to score now.

The five [non-model controls](shortcut_controls.py) are implemented: four
constant actions and `copy_last_history_answer`. The latter trims whitespace,
case-folds the final history answer and returns Yes/No only for an exact match;
otherwise it returns ASK. It ignores snippet meaning, scenario and question.
They receive visible state only and run once per item, outside the model grid.
Score each separately against the same finalized cohort; no selecting the best
constant afterward as though it had been chosen beforehand.

Constant controls expose label imbalance. The copy control checks whether a
one-history-answer selection can be solved by repeating the changed answer.
These are declared shallow text controls, not a general-purpose deterministic
policy interpreter. A model beating them does not establish the necessity of
language models, neural reasoning or a new algorithm. A manually resolved graph
would be an assisted condition, not an end-to-end code baseline. A stronger
decomposition comparison remains necessary before broader method claims.

Before a real run, implement and test append-only start/finish records, a
single-attempt policy, resume rules that never automatically repeat an ambiguous
started request, and whole-stage budgets. Preserve partial grids after transport
or execution errors; do not omit inconvenient failures or report an incomplete
grid as a completed comparison. A wrong semantic answer is an observation, not
a trigger to stop selectively. Protocol/schema failures stop for diagnosis.
These runner behaviors are requirements, not claims about existing executable
task support. The completed technical smoke runner is not this task runner.

## What the compiler actually verifies

It requires three distinct existing review/adjudication files and all saved
review-stage artifacts before accessing the source. It then reproduces the
frozen source selection, checks both complete reviewer forms, reconstructs the
saved reconciliation, validates every adjudication row, applies the original
reserve rule and matches the saved final cohort exactly. It verifies pinned
tokenizer/configuration bytes and renders/tokenizes without weights.

It writes separate `comparison_plan.json` and `scoring_references.json` under
ignored `.local/`, preserving hashes of review inputs, final selection, source
selection, compiler, this draft and tokenizer files. Repeated generation must
match existing bytes; conflicting or partial output is preserved and rejected.
The plan's status is always `draft_only_inference_closed`. Distinct reviewer IDs
and matching hashes do not prove genuine human independence or semantic truth.
Process disclosures and adjudication still need human scrutiny.

After the existing review finalizer has succeeded, run with actual paths in
the pinned local environment (the following placeholders are not real reviews):

```bash
python research/external-validation/comparison_plan.py \
  --review-a .local/reviewer-a.csv --review-b .local/reviewer-b.csv \
  --adjudication .local/adjudicator.csv \
  --tokenizer-dir /path/to/existing/pinned/qwen35
```

The CLI has not been run on real completed ShARC reviews because none are
available. Tests use conspicuously named synthetic reviews, patched source
fixtures and a synthetic renderer. They are software checks only. A separate
local tokenizer-only check verified all nine non-weight files against the pinned
manifest and exercised both real chat-template branches. The exact synthetic
prompt `Synthetic tokenizer check only. Return a final JSON object with action Yes.`
encoded to 27 direct-mode input tokens and 25 thinking-mode input tokens; both
template boundary checks passed. Zero weights were loaded and zero forwards ran.
This does not establish token counts or budget adequacy for the pending cohort.
Before model execution, finish real-cohort tokenization,
runner/accounting checks, and publish a separately named freeze tied to the
finalized cohort, exact plan and execution code. Existing user API/local-model
authorization applies; this draft does not introduce another permission request.
