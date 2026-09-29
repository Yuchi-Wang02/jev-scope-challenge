# A second direct control matches input tokens, with a disclosed call difference

**Status: tokenizer-only preparation, zero new model forwards.** This adds a
second direct-decision control to the [unscored joint-routing protocol](JOINT_ROUTE_PROTOCOL.md)
without changing its published prompts or manifest. The original 228-call
direct control uses 76,855 input tokens, compared with 95,889 for the 228-call
joint-routing candidate. Calling those two arms budget-matched would hide a
19,034-token advantage for the candidate.

The pinned local Qwen3-4B-Base tokenizer was therefore used to count all **six
distinct answer-option permutations** of the same visible-only, schema-assisted
direct prompt for each of the 72 original development texts. That produces
[432 prospective direct prompts and token counts](preparation/joint_direct_all_token_costs.jsonl).
The first two to five permutations per text are exactly the previously
published 228-call control. No model output, case gold or structured source
record participates in selection.

For additional calls, cases are ordered by `SHA256(source_id)`. The selection
passes through each case's next unused permutation in rounds and includes a
query only when its measured input-token count fits under the joint-routing
target of 95,889. This fixed ID-only rule selects **58 additional calls**. The
[resulting 286-query direct plan](preparation/joint_direct_token_matched.jsonl)
uses **95,849 input tokens**, 40 fewer than joint routing. Each prompt/order
pair is distinct. This is a close *input-token* control with **58 more calls**,
not an equal-compute or equal-latency claim. Together, the call-matched and
token-matched controls expose the two resource tradeoffs rather than collapsing
them into one misleading ranking.

The [manifest](preparation/joint_direct_token_manifest.json) pins the source
files, all prompt/cost rows, selected rows, rule and totals. Offline `verify`
reconstructs every prompt, checks the stored cost ledger and reruns selection
without a model or tokenizer. It cannot independently prove that a stored
token count came from the pinned tokenizer. Local `verify-tokenizer` re-encodes
every prospective direct prompt, checks A/B/C answer-token boundaries and
rechecks the joint target using the pinned cached tokenizer. Neither command
loads model weights or performs inference.

```bash
python research/fact-execution/joint_token_control.py verify
python research/fact-execution/joint_token_control.py verify-tokenizer
```

These controls remain on the same publicly exposed synthetic development set.
Independent human labels, language-transfer and reserved scores are still
absent. Encoded execution plans, a runner, a raw-score recomputation checker
and a source freeze covering them must be committed before any new model run.
Only actual measured calls, tokens and latency may support a later cost claim.
