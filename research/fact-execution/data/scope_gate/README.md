# Visible-ID replay data card

This directory is a post-hoc overlay on our own completed historical Kev-LoRA
joint pilot. It adds no model inference and no independent observations.

- `decisions.jsonl`: 72 replayed decisions on the same 12 development parents,
  with original/replayed actions and fact vectors. Underlying cost refers to
  the 228 saved joint forwards, not new calls made by the replay.
- `lines.jsonl`: 228 gate decisions from visible header/line strings. The runtime
  gate reads neither program construction fields nor gold. Scope references
  are added only afterward for audit.
- `fields.jsonl`: 168 comparisons with existing program-derived fact statuses.
- `name_checks.jsonl`: 216 renamed versions of the same 72 texts. Each has
  `model_output: null`. These are software tests of identity comparison and
  shortcut rules, not model transfer results or independent new examples.
- `contract_cases.jsonl`: 16 constructed parser boundary tests. Unsupported
  forms yield UNKNOWN; no language model was run on these examples.
- `summary.json`: complete counts, costs, paired changes and source hashes.

The [report](../../VISIBLE_ID_GATE_AUDIT.md) retains both regressions and the
original failed screen. A newly selected post-hoc method does not inherit a
prospective validation claim. The original known-grammar parser remains 72/72;
no equally filtered direct model control has run.

Synthetic source text and new program-derived annotations follow this project's
CC BY 4.0 data terms: attribute Yuchi Wang / Jev Scope Challenge and cite the
version. Underlying raw model outputs remain experimental evidence with their
existing provenance; this card does not relicense model artifacts or provider
output. [Credits and boundaries](../../../../THIRD_PARTY_NOTICES.md).

All text is constructed, with no customer records. Independent human annotations
remain zero. Correct code on this explicit-ID grammar is not a guarantee about
unrestricted language, record authority, truth or freshness.
