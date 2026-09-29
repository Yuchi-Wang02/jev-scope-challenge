# Same Native Tokens, Different Pointer Boundaries

Real local diagnostic on previously inspected synthetic data; no independent labels or new training.

2592 logical decisions; 2016 scientific forwards, 576 explicitly shared native records; 864 additional parity forwards.

## Prior exploratory-test panel (12 parent groups)

|Arm|Layout|Correct / 144|Complete / 12|Correct missing / 36|Order-sensitive inputs|
|---|---|---:|---:|---:|---:|
|N0|L0|85|0|0|15|
|N0|L1|106|0|3|6|
|N0|L2|106|0|3|6|
|N1|L0|111|1|7|5|
|N1|L1|121|2|19|5|
|N1|L2|121|2|19|5|
|K1|L0|98|0|1|2|
|K1|L1|119|3|15|4|
|K1|L2|127|5|19|2|

## Primary boundary contrast L1 → L2

|Arm|Changed decisions / 144|Changed inputs / 48|Changed parents / 12|Corrected|Regressed|
|---|---:|---:|---:|---:|---:|
|N0|0|0|0|0|0|
|N1|0|0|0|0|0|
|K1|8|4|3|8|0|

L1/L2 native tokens are identical and reused explicitly. Pointer field boundaries, delimiter positions and whitespace tokens change. This is not a head-only causal intervention.

All layouts, splits, variant scores and prior-temperature transfer metrics are in summary.json. No layout was chosen as a new test-time method.

No new independent sample, broader distribution claim, head-only training, current default Kev evaluation or Jev/Laya call. The original labels still await independent review.
