# Public-source contrast results

This is source-label agreement on 12 selected public dev trees /24 inputs.
**Zero project human reviews.** The original strict API experiment stopped;
the final native-choice view follows two disclosed engineering repairs.
Source disagreement is not automatically a proved model error.
The [all-pair source audit](SOURCE_REVIEW.md) identifies a title-only rule and
necessary-versus-sufficient-condition concerns without replacing any labels.

## Per-condition source agreement

|Condition|Finished / planned|Item agreement|Both pair members agree|Invalid output|
|---|---:|---:|---:|---:|
|jev_native_order0|24/24|18/24|8/12|0/24|
|jev_native_order1|24/24|18/24|8/12|0/24|
|qwen_direct_order0|24/24|11/24|3/12|0/24|
|qwen_direct_order1|24/24|12/24|3/12|0/24|
|qwen_thinking_order0|24/24|5/24|0/12|19/24|
|qwen_thinking_order1|24/24|6/24|0/12|18/24|
|jev_unique_argmax_order0|24/24|18/24|8/12|0/24|
|jev_unique_argmax_order1|24/24|18/24|8/12|0/24|

Each order has 24 items /12 parent pairs; do not pool them as independent samples.
The unique-argmax rows re-read the same API responses and incur no new calls.
Invalid/truncated outputs remain in denominators. No score for incomplete conditions.
Each exact job has one response. Differences between the two mappings describe
observed sensitivity; this grid does not separately estimate backend nondeterminism.

## Non-model controls

|Control|Item agreement|Both pair members agree|
|---|---:|---:|
|constant_Yes|10/24|2/12|
|constant_No|8/24|1/12|
|constant_Irrelevant|0/24|0/12|
|constant_ASK|6/24|1/12|
|copy_last_history_answer|14/24|4/12|

These constants/copying controls are shallow checks, not complete natural-language rule interpreters.

## Resource and termination accounting

|Condition|Input tokens|Output tokens|Callback seconds|Median seconds|p95 seconds|
|---|---:|---:|---:|---:|---:|
|jev_native_order0|15098|1080|3.752|0.141|0.265|
|jev_native_order1|15098|1080|3.609|0.148|0.172|
|qwen_direct_order0|7088|268|12.986|0.532|0.594|
|qwen_direct_order1|7088|269|13.251|0.531|0.594|
|qwen_thinking_order0|7040|47020|1510.750|65.680|66.110|
|qwen_thinking_order1|7040|45002|1446.468|65.672|66.610|

All API phases together: 48 distinct requests, 30196 input /2160 output tokens. Input list-price estimate: $0.001268232 at $0.042/million, checked 2026-09-30. [Official model pricing](https://docs.typesafe.ai/models). This is not an invoice.

Local closed-session time: 2983.875 seconds. Usage incomplete: False; session time incomplete: False. Overruns: `{"input_tokens": 0, "output_tokens": 0, "session_seconds": 0}`.

|Local condition|Termination counts|Strict bare JSON / planned|
|---|---|---:|
|qwen_direct_order0|`{"natural_eos": 24}`|24/24|
|qwen_direct_order1|`{"natural_eos": 24}`|24/24|
|qwen_thinking_order0|`{"length": 19, "natural_eos": 5}`|5/24|
|qwen_thinking_order1|`{"length": 18, "natural_eos": 6}`|6/24|

All generated thinking tokens count. Shared verification/loading and peak memory are in the
raw session metadata; they are not arbitrarily allocated across conditions. Callback latency
is not whole-program elapsed time. Remote API and local GPU serving differ; no architectural
speed claim or assumption of free local computation follows from this table.

## Preserved API failures and alternative readouts

The original strict run completed 23 requests (22 accepted, one probability-sum failure).
The first repair completed seven new requests (six accepted, one native-choice/argmax mismatch).
The final policy completed the last 18 requests. No request was repeated.
Both stopped ledgers remain incomplete under their original rules.

Final metadata anomaly counts: `{"any_original_metadata_check_failed": 2, "invalid_confidence": 0, "native_choice_not_displayed_maximum": 1, "no_unique_displayed_argmax": 0, "nonunit_probability_sum": 1}`.

See [first repair](READOUT_REPAIR.md), [final policy](FINAL_READOUT.md), and [all-phase audit](results/jev_audit.json).
No probabilities were normalized and no native choice was replaced by the source label.

## Reproduction and limits

[Structured comparison](results/comparison.json) retains confusion matrices, changed/invariant
strata, order effects and every pair. [Original strict analysis](results/original_strict_analysis.json)
retains its missing grid. [Local raw journal](results/qwen.jsonl) and [token audit](results/token_audit.json)
support inspection. Inputs and [source attribution](ATTRIBUTION.md) are preserved.

Local capture re-runs the pinned tokenizer over every returned sequence. Ordinary offline
verification checks journal hashes, saved final-text parsing and score arithmetic; it does
not independently decode token IDs without the local tokenizer. To repeat that additional
check, supply the pinned local model directory (no weights are loaded for analysis).

```bash
python research/source-label-screen/report.py verify
python research/source-label-screen/report.py verify --model-dir /path/to/pinned/qwen35
```

This single-seed, selected source-labeled development screen has no project human adjudication,
source-Irrelevant stratum, semantic near-duplicate guarantee or pretraining-contamination control.
The 256/2,048 caps are fixed resource constraints, not established reasoning ceilings. The API
readout was adaptively repaired. No significance, population, new-method or dedicated-model
necessity claim is warranted. The separate training review queue remains unscored.
