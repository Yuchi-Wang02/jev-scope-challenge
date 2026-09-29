# Is the Decision Model Better Than the Model It Came From?

Real local exploratory pilot. No new training or paid API. Gold labels are rule-generated and AI checked; no independent human audit.

## Exploratory test (12 parents, 144 decisions per model)

|Arm|Complete parents|Correct decisions|Missing false acceptance|Order-sensitive inputs|Raw NLL|
|---|---:|---:|---:|---:|---:|
|N0|0/12|85/144|36/36|15|0.913|
|N1|1/12|111/144|29/36|5|0.485|
|K1|0/12|98/144|35/36|2|0.737|

N0 is the unchanged Base/native LM head. N1 adds the public LoRA through the same native path. K1 uses that adapted backbone with the trained historical pointer path.

N0/N1 prompt, token and answer-slot identity is checked offline. K1 differs in layout and readout, so differences are system-level. Neither a small win nor a loss establishes general training necessity or model superiority.

All development/calibration/test scores, raw and separately calibrated probability metrics are in summary.json. The .9 acceptance threshold was fixed before inference. An empty accepted set has undefined risk, not zero risk.

The code oracle solves structured facts used to construct the labels; it is not a general parser. Parent groups and style splits, rather than individual decisions, define independent units.

These results are an exploratory extension of upstream Kev diagnostics. A paper requires independent label review, new sources, matched interventions and broader validation.
