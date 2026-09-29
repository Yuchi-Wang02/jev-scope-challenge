# One line, one owner — unscored joint-routing preparation

**Status: prompt and cost preparation only. No new model forward has run.** This
candidate follows the failed [line-evidence pilot](LINE_EVIDENCE_RESULTS.md)
and its [post-hoc oracle error decomposition](LINE_ORACLE_DECOMPOSITION.md).
It tests whether forcing each visible line into at most one request/field/value
route improves factual decisions. The 68/72 oracle counterfactual is **not** a
prediction of this candidate's score. The method is an engineering combination,
not a claim of a new routing or entailment algorithm.

## Exact candidate and source boundary

The only planned scoring inputs are the same 72 public original development
texts from 12 six-view parents. The 144 provisional language rewrites and all
reserved inputs remain outside the runner. The original grammar and program
labels were already known during method design, so a development result cannot
confirm transfer or generalization. Independent human annotations remain zero.

For each of **228 visible record lines**, one query shows the original request
header, that line, the full original policy and the target-field definitions
compiled from those visible strings. It asks the frozen model to select exactly
one of: another request; no clear target observation; or positive/negative for
one named target field. The latter options contain the complete visible target
definition. Fields vary by family (two or three), yielding six or eight
candidate options. The primary order is fixed; a complete reverse order is
prepared for sensitivity, not chosen after observing results. Prompt metadata
such as source ID, family, variant and line offsets is not model input.

[`joint_route.py`](joint_route.py) contains the exact prompts and aggregation.
One selected positive/negative label contributes one program-located span to
one field only. Both polarities within a field yield CONFLICT; one polarity
yields TRUE or FALSE; no selected line yields MISSING. MISSING records a model
selection outcome, **not** an independently certified absence. Program offsets
show where a chosen line occurs, not whether its meaning supports the label.
The strict known-grammar parser may audit claims offline but must never correct
these runtime labels.

## Prepared budgets and controls

The pinned Qwen3-4B-Base tokenizer was loaded locally without model weights.
It checks that every answer letter A–H is a distinct single token at its prompt
boundary. The primary joint plan contains **228 forwards / 95,889 input
tokens** (maximum 539 tokens per prompt); the reverse plan has the same count
and token total. These are projected local input tokens, not billed usage.
The [query preparation](preparation/joint_route_queries.jsonl) includes all
456 primary/reverse prompts and a [manifest](preparation/joint_route_query_manifest.json).

The same preparation includes a [call-matched direct control](preparation/joint_direct_queries.jsonl):
one full-state direct prompt per visible source line, **228 distinct option-order
prompts / 76,855 input tokens**. Each direct prompt receives the original
policy and the same explicit field definitions. Two- to five-line inputs use
two to five fixed, distinct permutations of ALLOW, DENY and INSUFFICIENT.
Semantic probabilities would be aligned before any averaging. The direct arm
has equal *calls* but **19,034 fewer input tokens**, so it is not a matched-token
control. Both calls and actual input tokens must be reported.

Before a quality or cost-superiority claim, prepare and freeze a second direct
control that spends approximately the joint plan's input-token budget using
additional distinct direct option orders selected by an ID-only rule fixed
without labels. The resulting call count will differ and must be reported.
Do not pad prompts with meaningless text or count deterministic repeats as
independent trials. The older N1 direct (72 calls / 23,523 tokens), whole-state
facts (168 / 63,467) and failed line method (548 / 133,977) remain descriptive
anchors with unmatched budgets. A pure-code grammar parser is a separate strong
reference. Jev is not measured in this preparation.

## Evaluation and stop rule before any pilot

Use one N1/native primary-order path first, with no new training or model
download. Measure final decisions on all 72 texts, 24 uncertain and 48
determined; false commitments, false INSUFFICIENT, wrong supported actions,
field-status confusion, exact fact vectors, request/field/polarity line errors,
all six variants, parent-complete scores, calls, tokens and latency. Parent
groups are the comparison units; 228 line calls are not 228 independent cases.
Report every case and raw candidate logit. Candidate probabilities are not
calibrated correctness probabilities. Aggregation must not silently repair a
wrong route.

For a small **development screening** decision, retain the previously declared
threshold: at most 7/24 false commitments **and** at least 34/48 correct
determined decisions. Passing would only justify further independently
reviewed language and matched-budget study; failing would stop this exact
candidate from advancing unchanged. This threshold was chosen with prior
development results known, so it is not a fresh confirmatory test.

**Execution is not open yet.** The token-matched direct arm, encoded prompt and
answer-token plans, evaluator, immutable source/weight manifest, versioned
output directory and read-only raw-score checker must be finalized and committed
before any new inference. The runner must refuse unreviewed rewrites and
reserved inputs and must not overwrite historical results. This document and
the query manifest are reviewable *preparation*, not an execution freeze or
evidence of a successful model method.

Offline or tokenizer-only commands (no model inference):

```bash
python research/fact-execution/joint_route.py
python research/fact-execution/joint_route_plan.py verify
python research/fact-execution/joint_route_plan.py budget
```

The budget command needs the previously cached pinned tokenizer. The other
commands do not require model weights, an API key, or GPU access.
