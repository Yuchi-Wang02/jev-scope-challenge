# One capable ordinary-model reference on the closed direction grid

Status at preparation: no model generations. This is a supplementary exploratory arm on previously observed material, not independent confirmation, a new benchmark, a new method, or a replacement for the closed original grid.

## Question and commitment

Does one capable ordinary instruction model, with its normal reasoning configuration, reproduce the two-cell error signature previously shared by Jev and the short nonthinking Qwen3.5-4B configuration?

Use every original Qwen prompt from `../request_plan.json`, byte-for-byte as a Unicode string: 108 main inputs in both original display orders, plus six smoke decisions, for 222 requests. Keep their original order, item/family identifiers and options. Only the provider's native chat wrapper and model configuration change. Do not add answer explanations, worked examples, rule-direction hints, retrieval, tools, prefill, or answer-schema constraints. Reference labels remain in analysis metadata, never in the transmitted request body.

Freeze one arm before generation. No prompt search, selective rerun, model sweep or post-result extension. The original Jev/Qwen results remain historical, noncontemporaneous comparisons with different interfaces and compute. Do not claim equal compute, equal reasoning budgets, a price-performance win, or a population-wide ordinary-model ceiling.

## Model and native settings

- Model ID: `claude-sonnet-5-5`; actual returned `model` must match.
- Messages API with one user message containing the unchanged original prompt.
- `thinking = {"type": "adaptive", "display": "summarized"}`.
- `output_config = {"effort": "high"}`; `max_tokens = 8192` including thinking and final answer.
- Omit sampling controls, tools, caching, system instructions, and batch/fast-mode options.

The official documentation identifies post-4.6 model IDs as fixed snapshots, while service infrastructure can still change. It lists adaptive thinking and high effort as the normal Sonnet 5.5 configuration, and standard prices of $2 per million input tokens and $10 per million output tokens. These facts were checked before preparation; this selection is a capability reference, not a claim of the best available model. [Versioning](https://platform.claude.com/docs/en/about-claude/models/model-ids-and-versions), [Sonnet 5.5](https://platform.claude.com/docs/en/models/sonnet-5-5/overview).

## Budget and operational stop rules

| Bound | Value |
|---|---:|
| Logical decisions / generation HTTP attempts | 222 |
| Automatic retries | 0 |
| Maximum generated tokens per attempt, including thinking | 8,192 |
| Stage input reservation, including counting allowance | 600,000 tokens |
| Standard-price reservation cap | $20 |

For every request, obtain the provider's free token-count estimate for its model, messages, thinking and output configuration, then add 2,048 input tokens of conservative allowance. Count estimates are not actual generation usage. This reservation total must remain below 600,000. The maximum bounded stage-price calculation is `600000*2/1000000 + 222*8192*10/1000000 = $19.38624`. This is a request-budget calculation, not an invoice or a prediction that the allowance will be consumed. No cache or batch discount is needed. [Token-counting documentation](https://platform.claude.com/docs/en/build-with-claude/token-counting).

Persist and flush a start record before each physical generation attempt. Reserve its full input/output allowance before dispatch. Persist raw responses, returned usage, latency, model, stop reason and provider request ID without credential headers. Reconcile observed usage after the response. Unknown usage consumes the reservation and stops the run. Exceeding an input reservation, unexpected cache accounting, missing/malformed usage, HTTP/transport failure, model mismatch, truncated generation or an unresolved started request stops execution. Do not retry or silently clear an uncertain request.

Resume only jobs with no start record, using the same frozen request list. Refuse to resume after a recorded operational stop. A normal completed but wrong label, invalid final text or API refusal is retained as an observation and does not justify changing the remaining inputs. Smoke semantic accuracy is not a launch gate. Never inspect correctness to decide whether to continue. The generation runner does not load main reference labels.

The prior standing authorization was for Jev exploration. This arm uses a different paid provider. Generation remains disabled until the user explicitly approves this concrete $20-bounded arm; the local approval record must bind that approval to the frozen plan. Read-only model metadata and free token counting are preparation, not model generations. Presence of a credential does not itself grant spending authority.

## Output and analysis

Preserve all content blocks. Score only the complete concatenation of final `text` blocks, with surrounding whitespace removed, matching the original case-sensitive parser. Exactly lowercase `yes`, `no` or `maybe` is valid. Do not extract favorable tokens from explanations, thinking summaries or redacted-thinking blocks. Truncation, refusal, tool use, empty/multiple answers and malformed responses receive their own status; none becomes `maybe` automatically. Treat a partially completed grid as incomplete and retain every attempt.

Report both mappings, the full nine-cell relation-by-fact matrix, the 24 critical inputs, critical direction-pair correctness by polarity, complete nine-input vocabulary families, unknown-fact controls, false commitments, unnecessary deferrals, invalids, truncation, usage, latency and nominal cost. Explicitly report how many of the old 24 shared-error inputs are resolved and how many of the old 84 correct inputs acquire new errors, separately from invalid outputs. Preserve always-maybe and known-grammar controls from the original study. Mapping repetitions do not enlarge the sample. Twelve vocabulary families reuse three logical templates; there is no population inference or independent human validation.

If the capable reference resolves the shared signature, narrow the old interpretation to the configurations actually tested. If the signature persists, retain one additional configuration's observation and require independent semantic/pragmatic review before expansion. Either outcome ends this arm. The finite grammar program already solves the task; this addition can clarify interpretation without supplying a paper contribution.

## Provenance and software validation

`requests.json` must retain exact source-job mapping and prompt identity. Preserve hashes of the original published request plan, cases, protocol and source freeze; preserve new model metadata, token-count records and this arm's code before generation. Do not alter the original grid, labels, freeze, journals or published results.

Software tests use clearly marked fabricated API fixtures solely to verify parsing, accounting, interruption and resumption behavior. Such fixtures are never model observations or analysis results. Local preparation and testing do not publish files, submit an upstream contribution, or constitute an actual model run.
