# Next diagnostic: a finite-choice ordinary-model readout

2026-09-30. **Feasibility inspected; no execution freeze, new forward or API call.**
This is an outcome-aware follow-up to the completed
[source-label screen](../source-label-screen/INTERPRETATION.md), not a repair of
that grid or independent confirmation.

## What was checked locally

The existing pinned Qwen3.5-4B tokenizer was loaded with the established
`comparison_plan.checked_tokenizer` validator, using local files only and no
model weights. Revision: `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`.

|String, no added special tokens|Token IDs|
|---|---|
|A|32|
|B|33|
|C|34|
|D|35|
|Yes|9175|
|No|2665|
|Irrelevant|46508, 94205|
|ASK|7150|

The four action names are not equally tokenized. Comparing only their first
token would silently give Irrelevant a different scoring contract. Four mapped
single-token letters are feasible, but their new verbalizer and response
instruction are genuine prompt changes and must be disclosed.

## Proposed question

Can a single-prefill, constrained four-letter readout retain or improve the
ordinary model's decisions while reducing computation relative to its completed
direct JSON generation? The direct arm already returned 48/48 valid JSON outputs;
this is not a remedy for its formatting failure. Thinking-cap failures are also
not retroactively rescued by this different computation path.

Reuse all 24 already inspected inputs in both fixed action orders. Compare with
the existing direct-generation and shallow-control results on exactly that
cohort. Do not call these inputs new evidence or tune prompts against their
source labels. Retain Jev's existing native result as a contextual reference,
with the output-contract and serving differences stated.

## Requirements before execution

1. Write one exact task prompt and answer boundary. Freeze all 48 encoded inputs,
   both letter-to-action mappings, model/runtime pins and reference join hashes.
   Keep snippet, question, scenario and history identical to the previous grid.
2. Use no thinking generation, sampling or new training. One prefill supplies
   next-token logits; select the maximum of A/B/C/D. Declare tie handling and
   nonfinite-logit failure behavior before any call.
3. Save raw candidate logits, the full-vocabulary log-normalizer, unconstrained
   top token and total probability mass assigned to the four letters, alongside
   candidate-conditional probabilities. Conditional confidence is not calibrated
   correctness or proof that the model would freely choose a legal letter.
4. Use separate synthetic label-copy smoke inputs to test extraction/mapping.
   Set an explicit small attempt/input/time limit including smoke; no downloads,
   retries, generation-cap search or added examples. Publish the frozen plan
   before inference. Existing user authorization covers bounded local work.
5. Retain source agreement, pair agreement, mapping changes, regressions against
   direct generation, all five shallow controls and total setup/prefill costs.
   A valid answer by construction is not a semantic improvement. Do not count
   legal-output guarantees as an empirical accuracy result.
6. Close the diagnostic after the frozen grid. A weak result is a useful boundary
   for this readout; a stronger result still needs reviewed references and fresh
   material before any replacement or general-method claim.

This is an established finite-choice decoding approach, not an invented decision
head. The work should reveal an interface tradeoff at bounded cost. It does not
remove the source-evidence and human-review gaps identified in the parent study.
