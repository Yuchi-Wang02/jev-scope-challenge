# Matched-base exploratory pilot v0.1

Freeze before scientific inference. No new training or paid API. This diagnostic
extends Kev's existing native/adapted LM-head probes; no method novelty is claimed.

24 original synthetic parents in three families: repository owner scope,
item-rank binding, and current versus superseded instructions. Each parent has
full, hold, flip and missing-evidence views. Three cyclic candidate orders give
288 decisions per arm. Groups, styles and entity names are disjoint across
development (6 parents), calibration (6), and exploratory test (12).
All labels are rule-generated and AI checked; **no independent human review**.
This split is an exploratory test, not a human-validated confirmation benchmark.

N0: pinned Qwen3-4B-Base, original LM head. N1: same model and LM head with the
pinned Kev LoRA unmerged. K1: the same adapted backbone with the trained pointer
head and exact historical encoder/model source (SHA recorded in manifest).
One question per example, no truncation, BF16 backbone, FP32 trained pointer
head and raw probability computation, SDPA, TF32 disabled. No quantization.
Native letter candidates are single tokens whose continuation boundaries must
match. N0/N1 use identical prompts and order. K1 changes representation/readout;
its difference from N1 is a system-path comparison, not an isolated head effect.

Primary read: complete-parent correctness on all four views and all three orders
in the exploratory test. Also report decision accuracy, missing-evidence false
acceptance, flip/hold correctness, candidate-order sensitivity and raw NLL/Brier.
Fit one positive scalar temperature per arm on calibration rows only, using the
predeclared grid [.25,.5,.75,1,1.5,2,3,4,6,8], report calibrated test NLL/Brier and
test error/coverage at a predeclared .9 confidence threshold. This small calibration
set provides no deployment guarantee. No threshold selection on the test.

C0 is a transparent structured-fact rule oracle and does not parse arbitrary
natural language. Its perfect labels reflect the construction rule, not general
language ability. Models receive rendered evidence, not gold or structured oracle
fields. No arithmetic or hidden derived facts are supplied.

Historical checksum verification and one-question packed-versus-standard-causal
pointer parity precede K1 scoring. Engineering warmup is excluded. Save all raw
candidate logits, token IDs, prompts/encodings, mappings, costs and runtime.
Do not silently resume partial scientific output or discard failures. Existing
result paths stop execution; amendments and reruns require separate versions.
Accept either model direction and no difference. No additional training until
there is an interpretable, repeatable signal beyond a presentation defect.
