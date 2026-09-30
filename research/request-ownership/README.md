# Same records, different request

**Unscored preparation.** This directory proposes a target-switch diagnostic:
keep the record block and policy fixed, then ask about either of two requests.
Both request IDs have the same prefix; half the scenes use near-matching IDs.

Read the [protocol](PROTOCOL.md), [data card](data/README.md),
[query manifest](preparation/manifest.json), and
[tokenizer-only budget](preparation/token_manifest.json).
There are 24 constructed parent scenes and 48 views, using the existing
inspected sentence and policy grammar. They are not independently reviewed
language examples. No model score, learned checkpoint or execution runner exists.

The design follows the [post-hoc visible-ID audit](../fact-execution/VISIBLE_ID_GATE_AUDIT.md),
which found both a naming shortcut and two cases where foreign evidence
compensated for an extraction error. Its 70/72 replay is not a result on this
new preparation.

```bash
python research/request-ownership/prepare.py verify
```

Verification requires no model weights or credentials. The review packet and
blank response form are an audit aid with zero completed annotations. A separate
execution freeze and user review must precede inference. Independent human
review and a fresh language-transfer design are required for confirmation.
