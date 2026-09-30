# Ordinary Qwen3-4B: frozen native readout comparison

Prepared after six Jev smoke responses (6/6 reference matches), before any Jev
main or new local model output. No prompt is selected from local performance.
This is a descriptive exploratory comparator, not an architecture-controlled test.

Use the already-cached Qwen/Qwen3-4B instruction checkpoint at revision
`1cfa9a7208912126459214e8b04321603b3df60c`, BF16 Transformers on one local RTX 5070 Ti.
No training, downloads, tools or additional evidence. Use the exact state,
question instructions and A/B/C criteria from the Jev plan, serialized in one
user message. The additional format instruction asks for exactly one letter.
Apply its official chat template with `enable_thinking=False` and the assistant
generation prefix. Read the native next-token logits for A/B/C, then normalize
only these three. Record all three raw logits, full-vocabulary probabilities,
candidate mass, spaced-letter mass and top token. Candidate-normalized probability
is not a calibrated probability or a proof of normal answer-format compliance.

The six smoke jobs precede all 144 main jobs, in the identical fixed order and
option mappings. Exactly one prefill forward per job; no generation, ensembling,
warmup forwards, retry, prompt search or best-of selection. Limit 150 forwards,
1,000,000 total prompt tokens, context <=8,192 per request. A semantic smoke error
is retained; invalid logits, tokenizer boundary failure, wrong checkpoint,
unfinished attempt or runtime failure stop the run. No automatic replay of an
unfinished attempt. Resuming completed jobs must make zero new forwards.

Freeze this document, runner, exact rendered prompts/token IDs, tokenizer/config
and weight hashes before inference. Disable TF32, seed 20260930, evaluation mode;
record library/GPU versions and actual attention implementation. These settings
do not promise bitwise reproducibility across devices. Latency includes GPU sync,
token transfer and readout; loading time is separate. Hosted Jev timing and local
GPU timing are not a fair production speed comparison. Tokenizers differ.

Use every endpoint and denominator in PROTOCOL.md for each model separately.
Show paired differences on the same 12 parents without inflating sample size.
Native no-thinking classification is one readout of one ordinary checkpoint;
it does not measure the ceiling of general instruction models or isolate training
as the cause of a difference. Any later generation control needs its own freeze,
timing disclosure and fixed budget. Stop this comparison after the declared grid.

Implementation reuses the approach of this repository's original Qwen adapter,
not Kev or Laya code. Qwen model license is Apache-2.0; this repository publishes
only original adapter code and derived evaluation records, not model weights.
