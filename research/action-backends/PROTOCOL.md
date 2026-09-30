# Four-action backend integration smoke: frozen before execution

2026-09-30. Technical checks only, not a ShARC evaluation or a new benchmark.
The user has authorized bounded Jev API and local-model use. This phase makes
at most **8 HTTP attempts and 8 local generations**, with no retry or new download.

Four AI-authored JSON records each name one `selected_action` and a different
`distractor_action`. The instruction is to copy the selected field. Labels span
Yes, No, Irrelevant and ASK. These records are not independent research examples;
their exact references are programmatic. No ShARC, payment, or prior calibration
record is used. This diagnostic checks transport and readout, not reasoning.

The [plan](plan.json) fixes every prompt, mapping, seed and call. Jev uses both
ABCD-to-action orderings on each record, pinned `jev-1.13.0`. Save actual version,
complete request, sanitized response, probability map, confidence, token usage,
latency and failure type. Validate finite probabilities and their sum, chosen
argmax, four semantic labels, and integer nonnegative usage. Confidence is a
service quantity, not an observed probability of correctness.

Use direct HTTP with no SDK retry, redirects or transport retry; 60-second timeout.
Persist started attempts before sending. Stop that backend after the first
transport/schema error or content mismatch and retain the incomplete run.
An interrupted attempt has unknown billing unless a response is saved; do not
retry or silently resume it. A new output directory is mandatory and must not
replace old results. This phase has no automatic repair or second run.
The input work cap is 50,000 returned Jev input tokens; a preflight UTF-8 byte
count plus 256 per request is only a conservative planning proxy, not the Jev
tokenizer. Stop before another call if the reported cap is reached. Tiny fixed
requests and eight attempts bound work even if the proxy is inaccurate.
At the [checked official price](https://docs.typesafe.ai/models), 50,000 input
tokens corresponds to $0.0021; actual usage and pricing estimate are reported.
The [API specification](https://docs.typesafe.ai/api) supplies the schema.

Qwen uses the already acquired Qwen/Qwen3.5-4B revision
`851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, BF16 CUDA, Transformers 5.3.0,
torch 2.8.0+cu128, PEFT 0.18.1, SDPA with the existing native DeltaNet fallback.
Run each record once with direct (256 generated-token cap) and thinking (2048),
seed 17. Reuse the committed calibration settings: sampling temperatures .7/1.0,
top-p .8/.95, top-k 20, min-p 0, repetition penalty 1, generated-token presence
penalty 1.5. Total generated cap 9,216, input cap 50,000, generation wall deadline
600 seconds. GPU loading is separately timed. No weight or dependency changes.

Save rendered prompts, all input/output IDs, effective generation configuration,
actual logits-processor order, final-channel boundary result, completion state,
parsed action, latency and work. Inspect the pinned tokenizer/template before
weights. Direct prompts already close thinking; thinking prompts open it.
Exactly one generated EOS at the final position establishes natural completion.
Require exactly one closing think marker for thinking, none for direct; do not
select an answer from reasoning. Parse only the extracted final text with the
[prospective contract](../external-validation/ACTION_INTERFACE.md). A malformed
boundary, truncated output, format failure or wrong copied label stops that
backend. EOS at the token cap is still natural completion.

Both backends run their fixed list independently; one backend's failure does not
cause additional calls in the other. All started work is counted. A passed
smoke does not open ShARC inference: the human-review, adjudication and separate
task protocol gates remain. Old grids and scoring rules remain closed.

Freeze the code/plan in Git before either backend command. Source hashes and
the commit are recorded at startup. Outputs are first written under ignored
`.local/` and published verbatim after secret-pattern and offline consistency
checks. Report success/failure counts as **interface checks**, not task accuracy
or a Jev-versus-Qwen capability ranking.
