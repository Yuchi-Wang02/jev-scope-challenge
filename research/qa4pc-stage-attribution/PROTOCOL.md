# Frozen execution protocol: QA4PC stage attribution v1

Prospective protocol, 2026-09-30. No output existed when this version was written.
The cohort is the existing 12-tree /24-scenario hash selection. This remains
exploratory source-label agreement, not independent semantic confirmation.

## Grid and assistance

Two models, Jev `jev-1.13.0` and existing local Qwen3.5-4B revision
`851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`; two mappings `(yes,no,maybe)` and
`(maybe,no,yes)` onto A/B/C. This checks two permutations, not all six.

- D: historical policy, main question and scenario; 24 decisions per mapping/model.
- G: D plus supplied condition questions and expression; 24 per mapping/model.
- F: G plus one selected condition ID; 56 per mapping/model. Compose predicted
  condition labels with the fixed strong Kleene executor. Invalid facts produce
  invalid composition; no answer-label substitution or semantic auto-repair.
- L: expression and released fact labels only; 24 per mapping/model. Explicit
  label-derived assistance isolates execution and is not end-to-end accuracy.

Both models receive corresponding identical state fields and task instructions.
The Qwen prompt additionally renders a letter mapping and output-format request;
Jev uses native choice criteria. Neither sees reference labels in D/G/F. Both
receive the same explicit three-valued definitions. Human graph construction
cost is unmeasured, and this is an assisted diagnostic, not automatic rule parsing.
The core contrast is G versus F; D versus G measures supplied structure together
with its presentation. F uses more calls; no fixed-budget superiority claim.

Main grid: 256 Jev requests plus 256 Qwen physical prefills =512 decisions.
Three independent artificial logic smoke cases cover yes/no/maybe in each
mapping for each model: six each, twelve total. All smoke decisions for a backend
precede its main grid and must pass; the first failure halts that backend. These
are simple execution/interface checks, not a broad semantic-validation gate.

## Readout and execution

Jev uses its native returned choice as primary. Actual model version, choice
schema and nonnegative integer usage are mandatory. Raw probability metadata
is retained separately, including sums, displayed ties and disagreement with
native choice. Probability anomalies do not correct the primary action or
silently normalize probabilities. Unique displayed argmax is secondary only.

Qwen uses one BF16 CUDA/SDPA prefill with thinking disabled, no generated tokens,
and the next-token logits of A/B/C. Store three logits, full-vocabulary normalizer,
top token, conditional probabilities and candidate mass. Exact maximum ties
are invalid, not resolved using a label or a precision rerun. This continues
the prior finite-readout baseline; it is not a new decoding method. Full vocab
vectors are not retained, so the normalizer cannot be independently reconstructed
from the three saved logits alone. Count physical forward hooks; require one.

Jobs run in deterministic cohort/scenario order, then mapping, D/G/F/L order
within each scenario. There is no random crossover or causal latency claim.
Run each backend sequentially; no concurrent GPU workloads. No warmups beyond
the six reported smoke prefills; report loading/verification separately.

Hard limits per backend: 262 total attempts/prefills; **zero automatic retries**.
Total planned Jev serialized UTF-8 bytes plus 4,096 bytes per call must fit
2,000,000 planning units. This is a conservative planning proxy, not an exact
server-token guarantee. Stop at 500,000 actual input tokens; report a possible
last-call overrun. Qwen: at most 500,000 known input tokens, 32,768 per context,
zero output tokens, 600 callback-session seconds. Planned Qwen inputs are counted
with the pinned tokenizer before launch. No downloads or training.

OS lock plus append/fsync journal records every start before its request/forward.
Unknown interrupted calls/sessions, unknown usage, protocol errors, transport
failures and smoke failures stop the backend. Never restart from a new directory
to bypass a stop. Completed jobs are not replayed. Software repairs require a
named prospective amendment preserving prior raw evidence. Do not continue by
quietly changing the frozen contract.

## Freeze, publication and scoring

Freeze all jobs, full private inputs/references, public per-job hashes and input
counts, code/protocol/tokenizer pins before calls. Commit and push the freeze
before execution. Retain full source text and raw private requests locally;
publish derived journal outputs and hashes without redistributing upstream text
while explicit QA4PC dataset terms remain unresolved. Reproduction retrieves
the exact upstream files. Existing user API/local-compute authorization applies.

Primary denominators are all 24 selected scenarios in every main arm, even if
invalid; F also reports all 56 condition decisions. In a stopped/incomplete run,
report coverage and unexecuted jobs explicitly rather than shrinking denominators.
Report per-class agreement, maybe-to-determined and determined-to-maybe errors,
strict all-selected-scenarios success per tree, order changes and G-to-F paired
improvements/regressions. Policy trees are the 12 clusters; repeated mappings
and facts are not independent examples. No p-value or population claim planned.

For F: wrong facts may be masked by the expression; separate fact correctness
from final correctness. For L: success only establishes supplied-fact execution.
Record all costs, including smoke, failures and load time. Source labels and
graphs have undergone upstream consistency checks, not new project adjudication.

Stop after this grid. Publish passes, failures and no-improvement alike. No
same-cohort prompt/precision/verbalizer search. If D saturates, treat that as a
boundary result. If facts dominate errors, do not add composition machinery.
Any budget-matched control or new semantic confirmation requires a separately
frozen study; this run alone cannot establish model replaceability or novelty.
