# A capable reference largely resolves the shared direction signature

**Completed: 222/222 generation attempts, no retries or operational stops.** On the 108 unchanged main inputs, Claude Sonnet 5.5 scored **107/108 in mapping 0 and 108/108 in mapping 1** under the frozen exact-label parser: **215/216 main decisions**, with mappings treated as repeated measurements. One response included an explanation and was invalid. Every valid main label matched its constructed reference. The six smoke decisions were 6/6.

This closes the single supplementary arm. The earlier shared signature belongs to the Jev and short nonthinking Qwen configurations actually tested; it does not establish a ceiling for capable ordinary models. This result is an exploratory capability reference on already observed synthetic inputs, with different provider interfaces and compute. It is not independent confirmation, an equal-cost comparison, a new method, or a general model ranking.

[Machine report](results/report.json) · [Raw journal](results/journal.jsonl) · [Independent AI recount](results/verification.json) · [Frozen protocol](PROTOCOL.md) · [Exact requests](requests.json) · [Authorization](approval.json) · [Historical original results](../RESULTS.md).

The [README](README.md), protocol and preparation audit deliberately preserve their pre-run state and are covered by the freeze. This page records the completed run; preparation statements such as “not run” are historical, not current status.

## Main comparison

Counts are per mapping. The historical baselines were not rerun in this arm.

| Configuration / control | Mapping 0 | Mapping 1 | Scope |
|---|---:|---:|---|
| Historical Jev | 84/108 | 84/108 | Original hosted decision interface |
| Historical Qwen3.5-4B, nonthinking | 84/108 | 84/108 | Original 32-output-token cap |
| Sonnet 5.5, adaptive/high requested | **107/108** | **108/108** | This arm; 8,192-token cap, one invalid final format |
| Always `maybe` | 60/108 | 60/108 | Reference-label control |
| Historical known-grammar program | 108/108 | 108/108 | Author-specified finite parser; not rerun here |

| Diagnostic | Mapping 0 | Mapping 1 |
|---|---:|---:|
| Old 24 shared-error inputs now correct | 23/24 | 24/24 |
| Old shared-error inputs with a valid wrong label | 0 | 0 |
| Old shared-error inputs with invalid output | 1 | 0 |
| Previously correct controls retained | 84/84 | 84/84 |
| Positive-fact direction pairs both correct | 12/12 | 12/12 |
| Negative-fact direction pairs both correct | 11/12 | 12/12 |
| Complete nine-case vocabulary families correct | 11/12 | 12/12 |
| Unknown-fact triples correct | 12/12 | 12/12 |
| False commitments on `maybe` references | 0/60 | 0/60 |
| Unnecessary deferrals on determined references | 0/48 | 0/48 |
| Full biconditional-like signature families | 0/12 | 0/12 |

Both mappings were executed for all 108 inputs. Both produced valid labels on 107 inputs, with **0/107 label disagreements among those valid pairs**. Both mappings were correct on 107/108 inputs. The remaining input had one invalid response and one correct response; do not describe the pairwise result as 0/108 valid-label disagreements or perfect interface stability.

## All nine cells

Each cell contains twelve vocabulary families. References follow the original explicit classical-constraint contract.

| Rule | Fact P | Reference | Mapping 0 correct /12 | Mapping 1 correct /12 |
|---|---|---|---:|---:|
| Q if P | True | yes | 12 | 12 |
| Q if P | False | maybe | 11 (1 invalid) | 12 |
| Q if P | Unstated | maybe | 12 | 12 |
| Q only if P | True | maybe | 12 | 12 |
| Q only if P | False | no | 12 | 12 |
| Q only if P | Unstated | maybe | 12 | 12 |
| Q iff P | True | yes | 12 | 12 |
| Q iff P | False | no | 12 | 12 |
| Q iff P | Unstated | maybe | 12 | 12 |

The invalid response is `r08_sufficient_negative_m0_qwen`; the identifier retains its original source-job name, but this arm's served model was Sonnet. Its complete final text was:

> The policy gives only a sufficient condition (verified address leads to qualification), not a necessary one. The account has no verified address, so that condition doesn't apply. Other routes to qualification may exist, and no stated rule rules them out, so both outcomes remain possible.
>
> maybe

The explanatory text is consistent with the constructed `maybe` reference. Nevertheless, the frozen parser accepts only the entire trimmed text `yes`, `no`, or `maybe`. This response therefore remains invalid and receives no credit. No answer extraction, retry, parser relaxation or post hoc 216/216 score was applied. This is a response-format failure, not an observed valid-label direction error.

## Execution and resource use

User approval was recorded against freeze SHA-256 `a8208904091b9f3548e4b67bfa57489ba6a9dfab5b1e095a30448218dd9c34d4` before the first generation. The prompts, labels, request order and frozen code were unchanged. Run timestamps were 2026-10-06 02:20:52–02:32:42 UTC, corresponding to the evening of 2026-10-05 in America/New_York.

| Phase | Requests | Reported input tokens | Reported output tokens | Nominal standard-price cost | Summed request latency |
|---|---:|---:|---:|---:|---:|
| Smoke | 6 | 1,402 | 24 | $0.003044 | 6.819 s |
| Main | 216 | 56,886 | 1,253 | $0.126302 | 256.565 s |
| Total | **222** | **58,288** | **1,277** | **$0.129346** | **263.385 s** |

Prices are the frozen standard rates of $2 per million input tokens and $10 per million output tokens. This arithmetic uses returned API usage, not an invoice. The $20 cap and $19.212128 request-specific reservation were conservative limits, not actual expenditure. Wall time was 709.963 seconds, including fixed two-second pacing between calls; the median request latency was 1.198 seconds. These measurements do not constitute matched-infrastructure performance comparisons.

All 222 responses returned the requested `claude-sonnet-5-5` ID. No generation retries, HTTP failures, unknown usage, unresolved starts, truncations or refusals occurred. The earlier free-count preparation did preserve one HTTP 429 and its separately documented continuation; that was not a model-generation retry.

Adaptive thinking and high effort were requested through the native interface. Four of the 222 responses contained a thinking block; all responses contained a final text block. The API's thinking-token detail fields summed to 232 tokens. Total reported output per request ranged from 3 to 90 tokens, with a median of 5. These observations do not imply that every request used thinking, that the full 8,192-token cap was consumed, or that visible summaries measure all internal reasoning. See the independent recount for complete content-block and output-usage details.

## What this changes, and where this arm stops

The old two-cell signature is not reproduced in the valid labels of this capable reference. The new arm preserves all 84 previously correct controls in each mapping while resolving 47 of the 48 repeated old-error decisions under strict scoring; the remaining observation is invalid format. This narrows the previous claim to the tested configurations. It does not identify whether model weights, inference configuration, provider wrapper or other differences caused the improvement.

The twelve vocabulary families reuse three logical patterns. Mapping repetitions are repeated measurements, not additional independent samples. There was no fresh held-out dataset, independent human language review, intervention comparison or natural-policy validation. The known-grammar program already solves this finite contract exactly. A strong model's success here is useful interpretive evidence, not a research contribution by itself.

**Decision: close this arm and retire rule-direction as the current main paper candidate.** Keep the original failure signature and this correction together in a concise technical report. Do not automatically tune the prompt, add harder cases, rerun the invalid response, or launch more models. The parked intent-retry source screen and the separate evaluator/environment repairs retain their own evidence boundaries; this result does not turn either into a demonstrated model-reliability contribution.

All new files remain local at this stage. No GitHub commit/push, upstream message, fork or dataset publication was made as part of this arm.
