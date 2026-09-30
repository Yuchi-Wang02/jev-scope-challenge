# Frozen finite-choice prefill diagnostic

2026-09-30. Prospective for this new readout; outcome-aware relative to the
completed public-source screen. No new forward at protocol preparation.

Question: on exactly the same 24 inspected ShARC inputs, how do source agreement,
paired decisions, mapping sensitivity and compute change when Qwen3.5-4B uses a
single next-token prefill constrained to A/B/C/D instead of direct JSON generation?
This is a joint verbalizer/prompt/readout change, not a causal isolation of one
component. It is neither a novel algorithm nor confirmation data.

## Fixed computation

Use existing Qwen/Qwen3.5-4B revision
`851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, Transformers 5.3.0,
Torch 2.8.0+cu128, PEFT 0.18.1, BF16, CUDA0, SDPA, batch one. Hash all 11 local
model files before loading. No downloads, fine-tuning, generation or sampling.
Use the tokenizer's chat template with `enable_thinking=False`, no additional
assistant prefix, and require that appending each bare A/B/C/D preserves the
encoded prompt prefix and adds exactly its declared single token.

The semantic task instruction is reused. The output instruction changes from
semantic JSON to one letter with a displayed mapping. Only the previous four
visible state fields enter the task prompt. Freeze every exact prompt and token
sequence. Letters have IDs 32/33/34/35. Two orders are Yes/No/Irrelevant/ASK and
ASK/Irrelevant/No/Yes. No reference labels or model outcomes enter task prompts.

One `model.forward` per job, `use_cache=True`, `logits_to_keep=1`; discard its cache
afterward. Read the final-position raw logits without temperature or logits
processors. Select the unique exact maximum among A/B/C/D; an exact tie is an
invalid output (None), kept in the denominator. Nonfinite logits or inconsistent
metadata stop the run as a protocol failure. Do not reinterpret a tie or pick the
letter yielding better source agreement.

Save candidate logits, full-vocabulary logsumexp, unconstrained top token/logit,
candidate-conditional probabilities, total full-vocabulary candidate mass,
input tokens, zero generated tokens, physical forward count, synchronized
callback latency, session timing, setup/loading and peak GPU allocation.
The full vocabulary vector is not saved; its reported log-normalizer is model
output evidence, not independently reconstructible from four candidate logits.
Conditional candidate probabilities are not calibrated correctness estimates.

## Cohort, smoke and bounds

- Eight synthetic copy-a-declared-letter smoke inputs: all four letters under
  both mappings, fixed order before main tasks. They test extraction/mapping,
  not source-rule comprehension. Require 8/8 expected semantic actions before
  any main task. A smoke miss ends the diagnostic; no prompt repair or retry.
- Forty-eight main prefills: all 24 parent-screen inputs in both mappings.
  Source references are unchanged. Sort by a declared study/job-ID SHA-256 order;
  smoke cases remain first. No case selection based on previous performance.
- Maximum 56 attempts/physical prefills, 50,000 input tokens, zero generated
  tokens, 300 generation-session seconds. Hashing/loading are separately timed.
  Boundaries are checked between atomic prefills; record unavoidable overruns.
  No retries, parity forwards, warmups, new API calls or model downloads.
- Use the append-only shared journal with its OS lock and unknown-outcome stop
  behavior. Never restart under a new directory to evade an interrupted attempt.

The shared journal field `local_generations` is an attempt ceiling only; these
jobs perform prefills, not autoregressive generation. `max_new_tokens=0` and
`local_generated_tokens=0` explicitly record the distinction.

## Reporting and decision

Report both 24-item /12-pair conditions with invalid outputs included, changed
and invariant source strata, all five existing controls, and per-item transitions
against the matching prior direct-JSON condition (improved, regressed, unchanged
and action changed). Retain the existing Jev native result as context without
calling this output-contract change a matched API re-run. Probability mass and
unconstrained legal-token frequency describe the readout boundary; do not make
calibration claims. Do not score an incomplete condition as a completed grid.

Report known input tokens and synchronized callback/session seconds including
smoke and separate setup. Previous runtime measurements were a different session;
do not claim a controlled architectural speedup or equal end-to-end operating cost.

Close the grid after execution, whether better or worse than JSON/copying.
Do not search prefixes, verbalizers, temperatures or prompts afterward in this
diagnostic. A beneficial result would establish a bounded interface tradeoff,
not model necessity or a new method. Source-evidence objections and zero new
human reviews persist. The separate training-review queue remains unscored.

The parent dataset and derivative input plans retain the
[ShARC CC BY-SA 3.0 attribution](../source-label-screen/ATTRIBUTION.md).
Independently authored code remains MIT; no upstream implementation is forked.
