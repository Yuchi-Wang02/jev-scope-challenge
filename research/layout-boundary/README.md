# Same Native Tokens. Different Pointer Boundaries.

Execution status: **designed and encoded, not yet scored**. This follow-up uses
previously inspected synthetic inputs from [the matched-base pilot](../next-study/).

What changes when the same evidence is placed in a decision model's `state`
versus its `question` field? Two controls yield byte-identical prompts/tokens for
the ordinary LM readout, but different inputs for Kev's historical pointer path.
The original layout is rerun as a regression anchor. This targets input allocation,
not an isolated proof about head capacity or training necessity.

Read the frozen [protocol](PROTOCOL.md), [manifest](manifest.json),
[tokenizer-only preflight](preflight.json) and [encoded input plans](data/inputs.jsonl).
No new labels, teacher facts, training, API calls or weight downloads.

## Layouts

|Layout|State|Question instruction|
|---|---|---|
|L0|Original evidence|Original policy|
|L1|Policy + evidence|Fixed generic query|
|L2|Policy|Evidence + fixed generic query|

L1/L2 have identical native serialization. In the pointer path, the state/question
delimiter moves and whitespace tokenization can change. The alternative field
assignments may be outside training distribution. Report all layouts and their
effects on supported decisions as well as missing-evidence abstention.

## Run and inspect

Use the preceding pilot's Python 3.10 / CUDA / package environment and pinned
cached weights. No network fetch is needed. Install its requirements separately
if creating a new environment; local GPU execution is not part of CI.

```bash
python research/layout-boundary/layout_study.py build --cache /your/cache
python research/layout-boundary/layout_study.py run --cache /your/cache
python research/layout-boundary/layout_analyze.py
python research/layout-boundary/layout_analyze.py --verify
```

A new replication needs an empty results folder in a separate checkout. Existing
partial or complete output is rejected. 2592 logical records correspond to 2016
scientific forwards and 576 explicitly shared identical native records; 864
additional standard-causal forwards check all pointer inputs. Original anchors
and parity gates stop at probability delta >= 1e-4 or changed predictions.

## Attribution and limits

Uses the pinned upstream [Kev historical encoder and pointer head](https://github.com/jaredpalmer/kev/blob/29d71c78368657b3a522729a01c748ea15272abc/kev/model.py)
via the unchanged Apache-2.0 source in the previous study. Its [native/adapted
probe](https://github.com/jaredpalmer/kev/blob/0c142becde423a0c68ec857f7831dac0315588a1/scripts/base_mmlu_probe.py)
motivates the three paths. No new architecture, calibration theory or general
benchmark novelty is claimed. Independent review and fresh confirmation remain
future requirements. Original synthetic data retain CC BY 4.0.
