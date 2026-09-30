# Public-source rule contrast screen v1

2026-09-30. Prospective protocol under the [explicit amendment](EXPLORATION_AMENDMENT.md).
Preparation-time statements remain historical after execution. This is exploratory
source-label agreement, not independently reviewed correctness or confirmation.

## Question and selection

On unchanged public ShARC dev inputs, how often do Jev and Qwen follow source
action labels when exactly one history answer changes, including cases where
the source action remains invariant? What do direct and thinking modes cost?

Use the existing official archive SHA-256
`72dca3f4f3ba73b1d796b40e952a80d53cd2011ef90b2168b8bcaa818f5edd1e`.
Parse train/dev only. Exclude any dev tree sharing a train tree ID or a rule
snippet after case folding and whitespace normalization. This includes all
training-review trees. Within dev, collapse equal visible inputs to the smallest
utterance ID if actions agree; exclude conflicting-action groups. Require equal
tree, rule, question, scenario, history length/questions, and exactly one No/Yes
history-answer difference. Do not edit source text or invent a contrast.

Map literal Yes/No/Irrelevant to themselves; other nonempty source answers to ASK.
Select four invariant pairs first, then four ASK/decisive pairs, then four No/Yes
pairs. Within each group, rank trees by SHA-256 of canonical JSON
`[study_id, "tree", tree_id]`. For each available tree, select the pair ranked
first by `[study_id, "within-tree", group, sorted_utterance_ids]`. Use one pair
per tree and per normalized rule snippet across groups. Stop if the requested
allocation cannot be filled; do not shrink the study. Study ID is
`sharc-dev-source-label-screen-v1`. Pair member order is lexical utterance ID.
This deterministic, source-stratified sample is not a random population sample.

The statistical unit is 12 parent trees, comprising 24 visible inputs. Repeated
orders/modes do not increase that sample size. There is no source-Irrelevant
contrast group, unseen-test claim, human adjudication or question-generation score.

## Fixed interfaces and calls

Use the common historical-rule action instruction and visible-field allowlist
from `research/external-validation/comparison_plan.py`. Only snippet, question,
scenario and history question/answer fields enter requests. Source answers,
evidence, IDs and pair links stay out. No examples, external tools, retrieval,
teacher help, chain-of-thought hints or prompt adaptation.

|Backend/mode|Inputs|Orders|Calls|Output cap|
|---|---:|---:|---:|---:|
|Jev `jev-1.13.0`|24|2|48|Native typed choice|
|Qwen3.5-4B direct|24|2|48|256 generated tokens|
|Qwen3.5-4B thinking|24|2|48|2,048 generated tokens|

Orders: Yes/No/Irrelevant/ASK and its reversal. Job order is SHA-256 of canonical
JSON `[study_id, "job-order", job_id]`, fixed before results. Each backend executes
its own ordered subsequence. Preserve all returned versions, probabilities,
token IDs, settings, timing, errors and unknown outcomes.

Qwen revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, existing local weights,
Transformers 5.3.0, Torch 2.8.0+cu128, PEFT 0.18.1, BF16/CUDA0/SDPA, batch one.
Seed 17 reset each call. Direct temperature 0.7/top-p 0.8; thinking temperature
1.0/top-p 0.95. Both top-k 20, min-p 0, repetition penalty 1, generated-token
presence penalty 1.5. No downloads, new kernels or warm-up forwards. Existing
eight-call-per-backend label-copy smoke and subsequent raw-record audit supply
interface evidence; this new orchestration has not yet run a live task at freeze.

## Limits and failure behavior

- 48 total HTTP attempts, zero retries; 96 local generations, zero retries.
- Jev planning proxy: serialized UTF-8 request bytes plus 256 per call <=250,000;
  this is not an actual tokenizer upper bound. Stop when actual cumulative input
  tokens reach 100,000 and report any response crossing the threshold.
- Local input tokens <=500,000; generated-token total <=110,592; each input plus
  cap <=32,768 tokens with no input truncation. Exact planned counts are in freeze.
- Local generation-session wall time <=3,600 seconds, checked at token and call
  boundaries; report unavoidable overrun. Hashing/loading are separate costs.
- Jev input-price estimate at the 100,000-token work limit is $0.0042 using the
  official $0.042/M input tokens on 2026-09-30. Output tokens are free according
  to the [official model page](https://docs.typesafe.ai/models). Actual usage is
  recorded; this is a list-price estimate, not an invoice or guaranteed hard cap.
  Local time is not economically free; report time without inventing energy cost.

Use the append-only journal and stop/resumption rules in the existing execution
core. A recorded wrong semantic action cannot trigger selective stopping. Ordinary
malformed/truncated final text stays a null-action observation. Schema/version,
adapter-invariant and transport/execution failures halt. Unmatched started calls
and unclosed sessions are never automatically retried. A separate reviewed repair
would be required; never erase a failed attempt or silently make a fresh ledger.

## Analysis and decision

Use the common paired scorer and raw-record analyzer. All six conditions must
share identical items. Incomplete conditions have no full-grid score. Failed
outputs stay in denominators. Report per-condition item and both-members-of-pair
source agreement, changed/invariant strata, confusion, null outputs, ASK versus
decisive mismatches, valid-action order changes and invalid-in-either counts.
Report condition input/output tokens and latency sum/median/nearest-rank p95,
alongside shared setup, whole-session time, unknown usage and any limit overrun.
Shared scorer fields named accuracy/correctness mean source agreement here.

Score each of four constant actions and last-history-answer copying separately.
These shallow controls are not complete rule interpreters. A win over them does
not establish that neural reasoning is necessary. No confidence interval,
significance claim or population extrapolation is specified for this selected
development screen. Single-seed sampling does not quantify sampling variability.

After the whole fixed grid or a required failure stop, inspect outcomes:

1. If all interfaces broadly agree with sources, publish the boundary result and
   end this screen; do not keep adding difficulty to find failures.
2. If differences are mostly formatting, cap or order effects, report those
   interface/resource limits rather than inventing a reasoning mechanism.
3. For semantic source disagreements, preserve the source and model output, then
   separately examine whether source ambiguity, label problems or model inference
   explain them. Any AI-assisted assessment is not independent human adjudication.
4. Any later intervention needs a named hypothesis and new protocol. This screen
   cannot be reused as independent confirmation after adaptive changes.

Both no-gap and failed-grid results must be retained. Publication includes the
freeze, traceable licensed inputs, raw successful/failed records, source-agreement
report and a stage audit. The reviewed training queue remains unopened.
