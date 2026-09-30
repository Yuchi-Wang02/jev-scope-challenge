# Faster recorded decisions, no consistent source-agreement gain

2026-09-30. This is an outcome-aware development diagnostic using unchanged
public source references. It does not adjudicate source truth or add independent
test examples. [Full results](RESULTS.md) and [frozen protocol](PROTOCOL.md).

## What changed and what happened

The same existing Qwen3.5-4B now returns a decision from four next-token letter
logits in one physical forward. JSON generation previously returned all 48 valid
outputs. This experiment therefore tests a computation/readout alternative; it
does not repair a previous JSON-format failure. The letter mapping and prompt
also change, preventing attribution to the readout alone.

|Observation|Original mapping|Reversed mapping|
|---|---:|---:|
|Prefill source agreement|13/24|10/24|
|Earlier direct JSON source agreement|11/24|12/24|
|Fully matching prefill pairs|3/12|2/12|
|Improved / regressed source agreement vs JSON|4 / 2|1 / 3|
|Changed actions vs JSON, including invalid|10/24|9/24|
|Callback seconds, prefill|4.501|4.406|
|Callback seconds, earlier JSON session|12.986|13.251|

The last-history-answer copying control still reaches 14/24 and 4/12 complete
pairs. Prior native Jev reaches 18/24 and 8/12 pairs in both mappings. Prefill
does not exceed either on these source metrics. Across mappings, three of the
23 inputs valid in both change semantic action; another input becomes invalid.
Do not hide that fourth difference by reporting only the valid subset.

The invalid response is an exact stored-logit tie for item
`fa377358c07bcd8659f87d6c` in the reversed mapping. C=No and D=Yes both have logit
24.125 and conditional probability 0.41151387985899396. The full-vocabulary
argmax reports C through its token-index tie handling; the prospectively frozen
semantic readout explicitly rejects ties. We retain that invalid response and
do not rerun at a different precision or choose a favorable tie-breaker. This
is an observation in the BF16 run, not proof that BF16 caused the tie.

All 48 task outputs have their unconstrained top token among A/B/C/D. Candidate
mass averages 0.992872 and 0.991663, while source agreement remains low. Thus
in this run legal-letter probability mass does not explain the source-agreement
gap. Candidate probabilities are not calibrated correctness probabilities.
The saved four logits do not independently reconstruct the full-vocabulary
normalizer; that scalar remains a recorded inference output.

## Plan versus reality

- Freeze commit `47d77bd41a10488d8501e06444a1c008f4d36b28` was pushed before inference.
- Planned 8 smoke plus 48 main prefills; actual 56, smoke 8/8, no retries or repairs.
- Planned at most 50,000 input tokens and 300 session seconds; actual 14,448 and
  10.672. Zero generated tokens, API calls, downloads and budget overruns.
- File verification took 6.062 seconds; loading took 3.563 seconds, separately
  recorded. A cold process also has unmeasured import/initialization overhead;
  these sums are not an audited end-to-end serving latency.
- Each journal result reports exactly one top-level forward. Offline replay
  reconstructs decisions, metrics, costs and transitions without new inference.
- Lower callback time is observed in a different session with different prompts.
  We have not measured a controlled speedup, energy use, cloud price or deployment
  throughput. No positive semantic effect is consistent across both mappings.

## Stage decision and next work

Close this grid. No prefix, verbalizer, temperature, precision or prompt search
on these 24 inspected inputs. The ordinary one-prefill interface is now a measured
baseline for later studies, not a proposed novel method or replacement claim.

The project has obtained a reproducible interface comparison. It has not yet
obtained a new reliable decision algorithm. More variants on these source labels
would not resolve the larger gap: a separately reviewed natural-language task,
new confirmation material, and a capable ordinary-model comparator under a
common assistance/cost accounting scheme. The existing 30-tree training review
queue stays unscored. Its pending review must not be replaced with AI agreement.

Next preparation should audit the research decision against the accumulated
negative results: which user-facing decision needs language interpretation,
which uncertainty changes the action, and what baseline can already solve it?
Before another main run, specify the missing causal contrast and its possible
stop outcome. Public presentation should lead with the measured tradeoff and
provide all cases, rather than market this control as beating a dedicated model.
