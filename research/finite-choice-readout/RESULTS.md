# Single-prefill finite-choice results

Source-label agreement on the same inspected 12 trees /24 inputs. **Zero new human reviews.**
This joint prompt/verbalizer/readout change is an outcome-aware diagnostic, not confirmation.
See the [protocol](PROTOCOL.md) and [source concerns](../source-label-screen/SOURCE_REVIEW.md).

|Condition|Finished|Item agreement|Both pair members|Invalid|Improved / regressed vs JSON|
|---|---:|---:|---:|---:|---:|
|prefill_order0|24/24|13/24|3/12|0/24|4 / 2|
|prefill_order1|24/24|10/24|2/12|1/24|1 / 3|

The prior direct JSON results are 11/24 and 12/24, with 3/12 fully matching pairs in each mapping.
Jev native context is 18/24 and 8/12 pairs in both mappings; this is not a new API run.

|Non-model control|Item agreement|Both pair members|
|---|---:|---:|
|constant_Yes|10/24|2/12|
|constant_No|8/24|1/12|
|constant_Irrelevant|0/24|0/12|
|constant_ASK|6/24|1/12|
|copy_last_history_answer|14/24|4/12|

## Candidate probability mass and work

|Condition|Raw candidate mass: min / mean / max|Unconstrained top is legal|Input tokens|Callback seconds|
|---|---|---:|---:|---:|
|prefill_order0|0.986163 / 0.992872 / 0.997199|24/24|7016|4.501|
|prefill_order1|0.982923 / 0.991663 / 0.996543|24/24|7016|4.406|

Smoke: 8/8 passed. Total attempts: 56; recorded physical prefills: 56; input tokens: 14448; generated tokens: 0. Closed session: 10.672 seconds.
Overruns: `{"input_tokens": 0, "output_tokens": 0, "session_seconds": 0}`. Status: `complete`.
Observed mapping differences: `{"available": true, "changed_valid_action": 3, "valid_in_both": 23}`.

Every condition keeps invalid outputs in its denominator. Raw candidate mass is separate from
probabilities renormalized among four letters; neither is calibrated correctness. The recorded
full-vocabulary normalizer is not independently reconstructible from four stored logits.
Setup, load timing, errors and peak memory are retained in the [raw journal](results/qwen.jsonl).
Prior JSON callback sums were 12.986 and 13.251 seconds in a different session. Hardware serving,
prompt changes and session conditions prevent a controlled architectural-speed claim.

[Structured report](results/report.json) contains all item transitions, confusion matrices and paired strata.
A legal output by construction is not evidence of semantic improvement. No source label was changed,
and no prefix search, retry, model download or training-review-queue inference was performed.

```bash
python research/finite-choice-readout/analyze_finite.py verify
```
