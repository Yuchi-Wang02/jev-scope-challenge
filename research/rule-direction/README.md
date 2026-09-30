# One "Only". Different Decision.

Status at preparation: **108 authored inputs, 444 planned decisions, zero model
calls**. [Frozen protocol](PROTOCOL.md), [full request plan](request_plan.json),
[cases and possible-world witnesses](cases.json), [budget manifest](manifest.json),
[implementation freeze](freeze.json).

Does adding `only` to `Q if P` change the decision when it should? This narrow
diagnostic distinguishes sufficient, necessary and equivalent fictional rules.
An exhaustive four-world oracle and a separate known-grammar program agree on
all108 cases. That establishes constructed software semantics, not independent
human validation or a natural-language reasoning breakthrough.

The two backends use the same visible facts, rule and question: Jev native choices
and the existing Qwen3.5-4B short greedy semantic-label configuration, each with
two display orders. Full equivalence and unstated-fact controls are retained.
Twelve vocabulary families repeat three logical patterns; they are not twelve
independent real-world policies. Always-maybe scores60/108 by construction.

This is separate from the [closed QA4PC source audit](../qa4pc-answer-interface/SOURCE_AUDIT.md)
and does not confirm or repair its labels. The [earlier decision-sufficiency lab](../decision-sufficiency/)
concerns uncertain object identity and is not reused as a model leaderboard.

No external data or author implementation was copied/forked. Original synthetic
material follows the repository license. The protocol credits RuleTaker,
ProofWriter and FOLIO; logical implication and truth tables are established.
Existing project adapters, tokenization checks and journal are reused unchanged.

## Reproduce preparation

```powershell
python -m unittest discover -s tests -p test_rule_direction.py -v
python research/rule-direction/plan.py prepare --model-dir PATH_TO_PINNED_QWEN35
python research/rule-direction/plan.py verify --model-dir PATH_TO_PINNED_QWEN35
```

The tokenizer/configuration checks require the existing pinned runtime.
Verification requires a clean committed tree. The public request plan is an exact
copy of the compiled local plan; its SHA-256 is recorded in the manifest.
Execution is bounded by the protocol and journals every physical attempt.
No automated follow-up or result-dependent expansion is authorized by this grid.
