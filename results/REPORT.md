# Full result report

**Jev led this probe: 12/12 vs 8/12 complete cases.**

The direction persisted across both candidate mappings and the repeat. This identifies a gap for this frozen readout on these inputs, not all open models.

| System | Complete cases | Correct decisions | Wrong cancellations |
|---|---:|---:|---:|
| Jev 1.13.0 | 12/12 | 96/96 | 0/48 |
| Frozen Qwen3-4B | 8/12 | 83/96 | 10/48 |
| always_keep | 0/12 | 48/96 | 0/48 |
| keyword | 0/12 | 48/96 | 48/48 |
| known_grammar | 12/12 | 96/96 | 0/48 |

## Round and candidate-mapping breakdown

| Model | Round | Complete cases | A=CANCEL mapping | A=KEEP mapping | Correct /96 | Mapping disagreements /48 | Wrong semantics under both mappings /48 |
|---|---:|---:|---:|---:|---:|---:|---:|
| jev | 0 | 12/12 | 12/12 | 12/12 | 96 | 0 | 0 |
| jev | 1 | 12/12 | 12/12 | 12/12 | 96 | 0 | 0 |
| qwen | 0 | 8/12 | 8/12 | 8/12 | 83 | 1 | 6 |
| qwen | 1 | 8/12 | 8/12 | 8/12 | 83 | 1 | 6 |

## Complete case table

| Case | Family | Jev round 0 | Qwen round 0 | Jev round 1 | Qwen round 1 |
|---|---|---|---|---|---|
| Q01 | Quoted versus actual request | PASS | PASS | PASS | PASS |
| Q02 | Quoted versus actual request | PASS | PASS | PASS | PASS |
| Q03 | Quoted versus actual request | PASS | PASS | PASS | PASS |
| Q04 | Quoted versus actual request | PASS | PASS | PASS | PASS |
| S01 | Object scope | PASS | FAIL | PASS | FAIL |
| S02 | Object scope | PASS | FAIL | PASS | FAIL |
| S03 | Object scope | PASS | FAIL | PASS | FAIL |
| S04 | Object scope | PASS | FAIL | PASS | FAIL |
| T01 | Superseded versus current request | PASS | PASS | PASS | PASS |
| T02 | Superseded versus current request | PASS | PASS | PASS | PASS |
| T03 | Superseded versus current request | PASS | PASS | PASS | PASS |
| T04 | Superseded versus current request | PASS | PASS | PASS | PASS |

## Probability quality, repeat stability and cost

Binary Brier uses P(CANCEL); NLL uses the assigned gold probability. These are descriptive on this tiny selected probe.

| Model | Round-0 Brier | Round-0 NLL | Repeat disagreement /96 | Formal median latency (s) | Formal p95 (s) |
|---|---:|---:|---:|---:|---:|
| jev | 0.000106 | 0.002556 | 0 | 0.1467 | 0.2027 |
| qwen | 0.134289 | 2.046177 | 0 | 0.0465 | 0.0520 |

Jev latency includes network and hosted service; Qwen is local single-input execution after smoke. No latency-normalized architectural winner is inferred.

Jev usage including smoke: `{"account_bill_verified": false, "finished_attempts": 195, "http_attempts": 195, "includes_smoke": true, "known_input_tokens": 89563, "unknown_cost_attempts": 0, "usage_estimated_usd": 0.003761646000000004}`.

Qwen candidate mass: `{"low_mass_under_0.01": 0, "median": 1.000000000004262, "min": 0.9999997160630301}`.

Within-probe reweighting sensitivity: `{"interpretation": "Within these purposively constructed cases only; not population CI or equivalence.", "percentile_95": [-0.5833333333333334, -0.08333333333333333], "qwen_minus_jev_pass_rate": -0.3333333333333333}`. This is not a population confidence interval or equivalence proof.

## All errors — no selected failure montage

| Model | Case | Round | Mapping | Gold | Prediction | P(gold) |
|---|---|---:|---|---|---|---:|
| qwen | S02-B | 0 | keep_first | CANCEL | KEEP | 5.829126530443318e-05 |
| qwen | S03-A | 0 | keep_first | KEEP | CANCEL | 2.2447771723041465e-13 |
| qwen | S02-B | 0 | cancel_first | CANCEL | KEEP | 4.363462480228009e-09 |
| qwen | S04-A | 0 | cancel_first | KEEP | CANCEL | 0.00012339458044152707 |
| qwen | S03-C | 0 | cancel_first | KEEP | CANCEL | 5.905304023556823e-10 |
| qwen | S02-D | 0 | cancel_first | CANCEL | KEEP | 0.0024726232513785362 |
| qwen | S04-A | 0 | keep_first | KEEP | CANCEL | 0.09534946084022522 |
| qwen | S01-C | 0 | cancel_first | KEEP | CANCEL | 3.3982678893096363e-09 |
| qwen | S01-C | 0 | keep_first | KEEP | CANCEL | 4.139937814784389e-08 |
| qwen | S03-C | 0 | keep_first | KEEP | CANCEL | 7.287724433256357e-14 |
| qwen | S04-C | 0 | keep_first | KEEP | CANCEL | 0.0019267346942797303 |
| qwen | S04-C | 0 | cancel_first | KEEP | CANCEL | 2.510999053129126e-08 |
| qwen | S03-A | 0 | cancel_first | KEEP | CANCEL | 0.00015843621804378927 |
| qwen | S03-C | 1 | keep_first | KEEP | CANCEL | 7.287724433256357e-14 |
| qwen | S04-A | 1 | cancel_first | KEEP | CANCEL | 0.00012339458044152707 |
| qwen | S04-C | 1 | keep_first | KEEP | CANCEL | 0.0019267346942797303 |
| qwen | S02-D | 1 | cancel_first | CANCEL | KEEP | 0.0024726232513785362 |
| qwen | S01-C | 1 | cancel_first | KEEP | CANCEL | 3.3982678893096363e-09 |
| qwen | S03-C | 1 | cancel_first | KEEP | CANCEL | 5.905304023556823e-10 |
| qwen | S03-A | 1 | cancel_first | KEEP | CANCEL | 0.00015843621804378927 |
| qwen | S04-A | 1 | keep_first | KEEP | CANCEL | 0.09534946084022522 |
| qwen | S02-B | 1 | keep_first | CANCEL | KEEP | 5.829126530443318e-05 |
| qwen | S03-A | 1 | keep_first | KEEP | CANCEL | 2.2447771723041465e-13 |
| qwen | S02-B | 1 | cancel_first | CANCEL | KEEP | 4.363462480228009e-09 |
| qwen | S01-C | 1 | keep_first | KEEP | CANCEL | 4.139937814784389e-08 |
| qwen | S04-C | 1 | cancel_first | KEEP | CANCEL | 2.510999053129126e-08 |

## Limits

48 artificial inputs, 12 related templates, no independent human audit. Code with the declared grammar can solve them. Model readout, training histories and hosting differ. The results are a narrow probe, not a causal test of training, general ranking, production replacement or proof of equivalence. All extensions must be separately versioned.
