# One Base, Three Decision Paths

## Finding

In this exploratory synthetic pilot, the original Qwen3-4B-Base/native path
correctly decided 85/144 exploratory-test questions. Adding the public historical
Kev LoRA through the identical native input and LM head raised this to 111/144.
The same adapted backbone with Kev's historical pointer path scored 98/144.

The strict complete-parent metric was 0/12, 1/12 and 0/12, respectively. Every
parent required all four evidence views and three candidate orders to be correct.
The decision-level ordering is therefore a diagnostic signal, not evidence of a
reliably solved task. It does not establish general model superiority or training
necessity.

![Verified exploratory counts](assets/matched-base-results.png)

## Question and controls

The preceding cancellation probe found a gap between a frozen instruct model
and Jev on object scope. That black-box comparison could not isolate training
from representation or readout. This study uses an open checkpoint and its
unchanged Base parent, following Kev's existing native/adapted LM-head diagnostics.

N0 uses `Qwen/Qwen3-4B-Base@906bfd4b4dc7f14ee4320094d8b41684abff8539`.
N1 adds `jaredpalmer/kev-4b@c4bfa11b0dc07691884f2d97f1c4c4c05c92e416` unmerged
and preserves the LM head, prompt, token IDs and candidate tokens. K1 attaches
the trained pointer head using the exact historical model/encoder source
`29d71c78368657b3a522729a01c748ea15272abc` to that same adapted backbone.

All arms use a BF16 backbone, math-only SDPA, no quantization, no TF32, one
question and no evidence truncation. Raw probabilities and the trained pointer
head are FP32. Candidate letter token boundaries are checked. The installed
stack, architecture metadata and weight checksums are committed.

N1 versus N0 measures the effect of this adapter on this fixed measurement path.
K1 versus N1 also changes serialization, token positions and readout. That
difference cannot isolate the head alone. This is not a reproduction of upstream
FP32 published scores, and does not measure current default Qwen3.5-based Kev.
No Jev or Laya score was collected on this new dataset.

## Data and analysis

24 synthetic parents cover owner authorization scope, item-rank binding, and
current versus superseded instructions. Each has full evidence, reordered
equivalent evidence, a decisive relationship change, and missing evidence.
The missing view requires `INSUFFICIENT` under the stated policy. Labels come
from structured construction facts and an AI-checked rendering; no independent
human annotation has occurred.

Whole parents/styles are assigned to development (6), calibration (6), and
exploratory test (12). This holds out styles and entities within three known
construction families, not entire unseen mechanisms or real document sources.
Three cyclic candidate orders are repeated measurements. The complete study
contains 864 actual scientific forward records; the test contains 144 per arm.

Raw and calibrated NLL/Brier, flip/hold correctness, missing-evidence false
acceptance, and candidate-order sensitivity are reported for every split.
Each arm's temperature is fitted only on calibration records using the same
predeclared grid. Error/coverage uses a fixed .9 threshold. The six calibration
parents do not provide an operational risk guarantee.

The deterministic C0 oracle solves the original structured construction facts.
It is a truth/checking reference, not an arbitrary-natural-language parser. Its
perfect score is not counted as model inference or a general code replacement.
A separate post-run known-grammar text parser was then implemented on the same
rendered text as the models. It solves 48/48 test inputs / 12/12 parents. This
shows these renderings are programmatically parseable when their grammar is
known; it is not a pre-run independent general-language baseline. Its timing
and construction knowledge are explicit in C0_text_summary.json.

## What the errors suggest

On missing-evidence test decisions, N0 incorrectly committed on 36/36, N1 on
29/36, and K1 on 35/36. This is a prominent failure of abstention under these
explicit synthetic policies. A generated explanation or high candidate
probability would not repair that decision by itself.

K1 had only 2 order-sensitive test inputs versus N1's 5 and N0's 15, while its
decision accuracy was below N1. Option-order stability and semantic correctness
are distinct measurements. The full test records, including correct cases and
failures, are committed and replayable in explorer.html.

These observations motivate independently reviewing missing-evidence cases
and testing representation/readout controls before attributing the difference
to head capacity or launching additional training.

## Stopped attempt and numerical control

The initial v0.1 attempt produced 288 N0 and 288 N1 scientific records, then
stopped before K1 scientific scoring. An engineering check found a probability
delta of .0091283 between packed and standard-causal SDPA paths. The stopped
run, code and manifest are preserved under attempts/v0.1.

On that engineering input, forcing math-only SDPA made the delta zero without
relaxing the 1e-4 gate. All 504 public LoRA tensors (33,030,144 parameters)
exactly matched loaded values. Newer PEFT configuration fields ignored by the
installed version were null/default; broad historical-library parity is not
claimed. v0.2 reran all arms with the same math kernel. Its engineering check
passed with delta zero. This is a one-input check, not universal path parity.

The amendment followed exposure to v0.1 N0/N1 scores, so this remains an amended
exploratory study. Dataset/labels/prompts/splits did not change. There were no
new paid API calls or training. Peak allocated GPU memory was about 7,988 MiB.
Model/cache storage and engineering reruns are real local costs; no artificial
zero-dollar total-compute claim is made.

## Next decision

Keep this release as a transparent diagnostic. Before head-only versus joint
training, independently audit labels, add distinct natural-language sources,
and predefine representation controls. Then build new grouped train/dev/test
data, initialization and tuning budgets; the already inspected pilot is a
regression set, not fresh confirmation.

A valid result may favor trained models, a simple head, interface changes or
code. The public artifacts allow that direction to be questioned and extended.
The present work contributes an attributed diagnostic and reproducible records;
it does not claim a new architecture or established paper novelty.
