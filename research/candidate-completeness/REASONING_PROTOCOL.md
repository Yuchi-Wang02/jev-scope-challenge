# Outcome-aware control: 512-token deliberation plus native choice

Prepared after inspecting the complete Jev and no-thinking Qwen grids published
at `67583ee`. This is a new exploratory arm on already-inspected data. It is not
independent confirmation, a new dataset or a prespecified original comparison.

Question: does a fixed deliberation budget change the ordinary instruction
checkpoint's strongly accepting native readout? Use the same cached Qwen3-4B
revision and exact user-message content/options as LOCAL_PROTOCOL.md. Enable
thinking in the official chat template, then append the fixed `<think>\n` opening
marker (this checkpoint's template leaves that opening for the model to emit).
Greedily generate at most **512 tokens**,
stopping at the first `</think>` or the model EOS. No sampling, tools, selection,
prompt revision or retry. If the budget or EOS arrives without `</think>`, append
a fixed newline and closing marker. After exactly two newlines following the
closing marker, run one A/B/C next-token readout. No answer/rationale label or
resolved object is supplied. This is budgeted deliberation with a forced boundary,
not unconstrained natural-generation accuracy or the model's reasoning ceiling.

Retain raw generated token IDs/text including incomplete reasoning, stop reason,
whether the boundary was forced, final input IDs/hash, candidate/full-vocabulary
probabilities, every scored decision, errors, timing and physical forward counts.
Report truncated and naturally-ended subsets descriptively; neither is excluded
from the fixed denominator. A generated trace is not evidence of a faithful
internal causal explanation. Do not pick anecdotes as a mechanism proof.

Use all six original smoke jobs and all 144 main jobs, in the same plan order.
Batch consecutive jobs in fixed groups of four within each phase (last smoke
batch has two). Left-pad inputs; greedy batched arithmetic may differ from single
sequence arithmetic and is an additional comparison limitation. Smoke semantic
errors remain; schema, token boundary, checkpoint, nonfinite logits, memory or
execution errors halt. Do not resize/retry failed batches based on outputs.

Limits: **150 decisions**, at most **76,800 generated nonpadding tokens**,
**38 batches**, **19,494 physical model forwards** (=38*513), and
**1,000,000 padded token positions processed by model forward calls**. A complete
batch is reserved before model work using conservative prompt-length/decoding/
final-prefill bounds. The model forward hook records actual token positions and
counts, including batch padding. Main run needs six valid recorded smoke outputs.
No warmup forwards, external API calls, model downloads or paid service.

Freeze rendered prompts/token IDs, runner, this protocol, batch plan and prior
checkpoint freeze before this arm produces output; publish the freeze before
running. For continuation, do not regenerate a batch with an unfinished ledger
record or partial terminal writes. Reconciliation must preserve recorded output.

Analysis uses the original six-cell table, paired obligations, complete-parent
endpoints, error types, option-order disagreement and code baselines. Compare
within the same checkpoint to native no-thinking scores; disclose the extra
compute, prompt template and forced boundary. Jev has no matching reasoning arm
here; do not present this as an equal-budget superiority test.

Stop after this one arm irrespective of result. If improvement occurs, the useful
next question concerns transfer and cost, not another prompt search on these
inputs. If it fails, preserve the bound and do not imply all ordinary models fail.
Independent semantic review and new-material confirmation remain uncompleted.
