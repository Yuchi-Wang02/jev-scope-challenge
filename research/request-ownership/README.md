# Same records, different request

**Frozen for review; unscored.** This directory prepares a target-switch diagnostic:
keep the record block and policy fixed, then ask about either of two requests.
Both request IDs have the same prefix; half the scenes use near-matching IDs.

[Open the interactive input explorer](https://yuchi-wang02.github.io/jev-scope-challenge/request_switch.html)
to switch all 24 pairs /48 views and inspect their exact planned prompts.
References are computed from visible text using the declared grammar; the page
contains no model predictions and makes no inference call. Its references are
public and available on demand, so it is not a blinded review instrument.

Read the new [execution protocol](EXECUTION_PROTOCOL.md),
[execution manifest](preparation/execution_manifest.json), and
[500-row execution plan](preparation/execution_queries.jsonl).
The [original design](PROTOCOL.md), [data card](data/README.md),
[preparation manifest](preparation/manifest.json) and
[tokenizer-only budget](preparation/token_manifest.json) remain available.
There are 24 constructed parent scenes and 48 views, using the existing
inspected sentence and policy grammar. They are not independently reviewed
language examples. A guarded runner and fixed paired scorer are now prepared.
No model score or newly learned checkpoint exists. The planned model uses the
existing historical upstream-trained Kev adapter, credited in
[THIRD_PARTY_NOTICES.md](../../THIRD_PARTY_NOTICES.md).

The physical budget is **500 scientific forwards /188,797 input tokens plus
two one-token unscored warmups**. Three physical arms produce six model methods
through shared outputs and single-order subsets, plus two zero-model controls.
The primary endpoint requires both target views correct in a pair, out of 24
pairs. A complete, separately approved local run is required before scoring.

The design follows the [post-hoc visible-ID audit](../fact-execution/VISIBLE_ID_GATE_AUDIT.md),
which found both a naming shortcut and two cases where foreign evidence
compensated for an extraction error. Its 70/72 replay is not a result on this
new preparation.

```bash
python research/request-ownership/prepare.py verify
python research/request-ownership/execution.py verify-freeze
```

Verification requires no model weights or credentials. The review packet and
blank response form are an audit aid with zero completed annotations. The
execution freeze is complete; explicit approval for this run is still pending.
Earlier approvals covered completed studies and do not transfer. Independent human
review and a fresh language-transfer design are required for confirmation.

The earlier design manifests describe their creation-time state as
`execution_ready: false`. They remain immutable; the separate execution manifest
provides the later runner/scorer freeze. `analyze.py --verify` requires complete
real evidence and intentionally fails before a run; CI uses the preparation
and execution-freeze checks plus in-memory software tests instead.

The explorer can also be opened from the standalone [HTML file](../../docs/request_switch.html).
`python docs/build_request_switch.py verify` checks that it exactly matches the
frozen inputs and its [template](../../docs/request_switch_template.html), without
reading scientific model outputs or changing the execution freeze.
