# Same Native Tokens, Different Pointer Boundaries

Status: exploratory follow-up designed after inspecting the preceding pilot.
No untouched holdout, independent labels, new training or paid API is claimed.

## Fixed comparison

Reuse all 96 rendered inputs / 24 parent groups from matched-base-pilot-v0.2,
with all three cyclic candidate orders and its exact checkpoint/source revisions.
All three paths N0 (Base/native), N1 (LoRA/native), K1 (LoRA/pointer) are tested.
Reuse BF16 backbone, FP32 pointer head, unmerged adapter, math-only SDPA, no
quantization, no TF32, one question per forward, strict no-truncation encoding.
The upstream historical encoder/head remain byte-identical and attributed.

For evidence text E, existing policy P, and fixed query G =
`Select the option justified by the supplied evidence and policy.`:

|Layout|Pointer state|Pointer question instruction|
|---|---|---|
|L0 original|E|P|
|L1 policy-first/state|P + two newlines + E|G|
|L2 policy-first/question|P|E + two newlines + G|

Native serialization always concatenates state, two newlines, instruction,
candidate descriptions and `Answer:`. Thus L1 and L2 have **byte-identical
native prompts, tokens and candidate slots**, while the pointer encoder places
its state/question delimiter differently. No evidence, policy, option, label
or teacher information is added to only one arm. G is the same in L1 and L2.
L0 versus either new layout bundles policy relocation and a generic query;
it is not an isolated ordering intervention. L1 versus L2 is the primary
boundary contrast. It changes pointer delimiter positions, whitespace
tokenization and state/question allocation, not just an abstract output head.
All layouts contain the complete policy and evidence. Unusual field allocation
can be outside the checkpoint's training distribution; this is a contract stress
test and not proof of a universal model defect or recommended serving layout.

## Units, metrics and computation

2592 logical decisions = 96 inputs x 3 orders x 3 layouts x 3 arms.
2016 scientific forwards: N0/N1 each execute L0 and L1, then explicitly reuse
their identical L1 forward for L2 (576 shared records); K1 executes all layouts.
Sharing is within the identical native input, never across models or cases.
Every record has a physical forward ID and sharing flag. It cannot be counted
as an independent repetition, additional inference or extra reliability evidence.

An additional standard-causal backbone forward checks every one of the 864 K1
encodings against packed-mask logits. Stop on probability delta >= 1e-4 or a
prediction disagreement. Log both logits and every delta. Math-only kernel
settings are fixed; do not relax the gate to complete the run.

L0 reruns all 864 original decisions. Check exact input identity and stop on
probability delta >= 1e-4 or changed prediction relative to the preceding saved
records. This is a deterministic regression check, not an independent replication
or new statistical sample. A failure preserves output and terminal runtime.

Report every split/layout/arm: counts, complete-parent correctness (all 12
decisions), full/hold/flip/missing scores, false commitment on missing evidence,
candidate-order sensitivity and paired changes between layouts. Report 12 old
exploratory-test parents as a named panel, not unseen confirmation. The primary
boundary statistic is per-input/per-parent disagreement between L1 and L2,
accompanied by correction/regression counts. Native controls must be identical.
No significance claim or population inference from repeated order decisions.

Raw probability metrics use the existing analyzer; also report temperatures
already fitted in the preceding pilot without refitting for these layouts.
Transferred calibration is a diagnostic, not an OOD guarantee. No best-layout
selection on the inspected test panel. Display all results, including harm to
supported decisions and successful abstention; always abstaining is not success.

## Freeze, inputs and outputs

Freeze code, protocol, all encoded plans, prior data/source/weights identities
and prior anchor records before scientific execution. Publish that freeze first.
Tokenizer preflight may encode all inputs but must perform no model scoring.
Exact pinned local weight SHA256s are rechecked before loading; no alias/network
download. Capture package versions, GPU, source commit, actual counts and time.

The runner rejects any existing runtime/scientific records and never overwrites
a completed or partial run. Version an amendment/attempt if needed; preserve
failed output. `run` writes terminal failed/complete status and all gates.

Outputs: manifest, tokenizer preflight and encoded plans; three raw record files;
runtime/weight/adapter audits; read-only offline verifier; grouped report, CSV,
figure, replay page and bounded research note. Independent review remains pending;
a blind sheet may prepare that work but does not constitute human annotation.

Local ceiling: one complete declared grid, no paid calls, no training, no new
weight downloads, six engineering warmup forwards. If a scientific or regression
gate fails, stop and diagnose rather than silently retry or pick successful rows.
