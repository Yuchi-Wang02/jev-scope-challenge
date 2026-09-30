# Qwen3.5 interface and output-budget development calibration

2026-09-30. Freeze before all model outputs. This is engineering calibration on
new synthetic material, not an independent research test or a Jev comparison.

## Question, inputs and limits

Can this installed ordinary-model interface return complete, strictly parseable
answers at a finite budget? Twelve new, AI-authored elementary fixtures span
copying, age threshold/missing value, arithmetic, set intersection, event order,
Boolean conjunction, minimum, 96-record exact lookup, counting, alphabetical order
and nested fields. They contain no payment data, tau users or previous research
texts. Their exact program answers are balanced A/B/C, four each. They are
development fixtures with zero human reviews, not an independently labeled test.

The complete plan has 48 calls: 12 fixtures x seeds 17/43 x thinking off/on.
Direct allows 256 new tokens; thinking allows 2,048. Total ceiling 55,296 generated
tokens and 200,000 planned input tokens. A single 1,800-second generation deadline
starts before the first call and is checked at token boundaries and between calls.
Report kernel overrun if it occurs. Load time and verification are separate. No
paid API calls, dependency installs or weight downloads. One existing pinned BF16
Qwen3.5-4B load, same local environment as the completed technical smoke, SDPA and
native torch DeltaNet fallback. Offline loading only; no remote Python/kernel code.

No retries, alternate prompts or outcome-selected seeds. Stop on an execution
error or the deadline, preserve partial results, and require a documented repair
before further work. A stopped run cannot produce a qualified budget recommendation.
The old 72-input grids remain closed. This is a separate calibration stage; its
48 calls are additional to the completed six-call technical smoke.

## Interface and decoding policy

Use the pinned chat template with a single user message and no system message,
tools, examples, constrained decoding or forced answer tokens. The final output
request is a JSON object with exactly one key `answer`, value A/B/C. Never inject
the program reference into the input. Seeds reset per call; batch size one.

Explicit sampling: direct temperature 0.7/top-p 0.8, thinking temperature 1.0/top-p
0.95, both top-k 20/min-p 0/repetition penalty 1. Presence penalty 1.5 is now
implemented as a standard processor: subtract 1.5 from each distinct previously
generated token's logit, once, not proportional to count. Exclude prompt tokens.
Apply before temperature/top-k/top-p. Record and assert the processor order before
generation. This changes the earlier smoke's zero-presence-penalty setting, openly
and before outputs. It is not a new inference algorithm or a prompt search.

These follow the pinned model card's **general-task** sampling recommendations.
They do not reproduce a particular serving engine bit-for-bit, and 2,048 tokens
is below its general benchmarking length recommendation of 32,768. The card's
non-thinking reasoning recommendations differ across its sections; this stage
uses its consistent general-task row and claims no vendor benchmark reproduction.

The parser accepts only natural EOS-terminated responses. For thinking mode it
requires exactly one `</think>` in the generated text and parses only what follows.
For direct mode no generated thinking tags are accepted. The remaining response
must be exactly one JSON object with no markdown, extra keys, duplicate keys,
trailing prose, or multiple answers. Valid JSON visible only inside a truncated
thought is never a final answer. Keep format/termination failure separate from
a well-formed but incorrect content check.

## Predeclared budget selection and reporting

Report all 48 outputs, settings, inputs and token IDs, EOS/cap/deadline outcomes,
parse status, content-check match, seconds and peak memory. Seeds and modes are
repeated measurements of 12 fixtures, not 48 independent examples. These tiny
programmatic checks do not estimate general accuracy or uncertainty calibration.

For each mode, examine saved-trace completion at caps 256/512/1024/2048, restricted
to caps no larger than the executed mode cap. A trace counts ready at a cap only
if natural EOS and a strict valid final answer were reached by that token count.
No additional capped generation is run. These are trace-prefix availability
counts, not independently executed latency measurements or replicated generations.

Select the smallest listed cap at which **all 24 calls in that mode** are ready.
If none qualifies, report no supported cap. Content correctness does not enter
this selection. Never choose a best seed. The selected cap is only a development
starting point for similar short prompts; new research must still predeclare an
adequate budget and report truncations. It is not a capability ceiling or a safe
deployment SLA. No further calibration search follows an unfavorable result here.

## Software checks and provenance

Before weights: validate the 12 fixtures/references, JSON parser failure modes,
presence penalty for empty prefixes/repeated tokens/prompt exclusion/multiple rows,
effective generation configuration and actual processor ordering. CPU tensor
checks use no learned weights. Hash all local model files against the earlier
verified manifest and save code/data hashes at the clean execution commit.

Sources: [Qwen pinned model card](https://huggingface.co/Qwen/Qwen3.5-4B/blob/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a/README.md),
[vLLM standard penalty semantics](https://github.com/vllm-project/vllm/blob/v0.11.0/vllm/model_executor/layers/utils.py),
and the installed Transformers 5.3.0 `GenerationMixin._get_logits_processor`
implementation. vLLM is inspected as a reference, not installed/executed or forked.
Original code/fixtures here use the repository MIT license. No model weights or
upstream implementation are redistributed.
