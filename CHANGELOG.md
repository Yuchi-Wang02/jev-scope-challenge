# Release notes

## 2026-09-29 — cost explorer baseline correction

Added always-defer and the existing visible-text known-grammar parser to the
post-hoc cost explorer. The previous version showed only three saved model
paths and emphasized their pairwise crossover. The line reader never minimizes
loss when only needless deferrals cost one unit; charging all deferrals gives
it a narrow four-path winning range, where the grammar-specific code is cheaper.
Both conventions now have exact rational intervals and boundary ties, with
outcomes and unmatched model budgets visible. No model prediction, frozen
protocol, model call or human annotation was added or changed.

## 2026-09-29 — series attribution audit and review preparation

Added prominent Kev/Laya/Qwen/TypeSafe credit, an exact-revision reuse inventory,
a schema-validated CITATION.cff, a six-study index, complete offline verification
instructions and the newest derivative-data card. GitHub metadata confirms this
is not a fork; the unchanged vendored Kev source and its Apache license remain
explicitly attributed. Laya is a research reference, not an executed backend.

Added a pack-fingerprinted, read-only rewrite-review CSV checker and a design-only
cited-fact extraction follow-up. Blank sheets do not count as annotations; valid
CSV syntax does not certify independence or open inference. No historical
scientific result, model input, frozen implementation or upstream code changed.
See [the publication audit](docs/PUBLICATION_AUDIT_2026-09-29.md).

## Complete v0.1 evidence publication and post-run tooling

The 2026-09-29 real results, inputs, frozen runner, analyzer, manifest and protocol
are preserved byte-for-byte modulo Git line endings. This release publishes the
previously missing data, results, figures, explorer, tests and pre-execution bundle.

Added after the experiment:

- `verify_evidence.py` independently checks manifest fingerprint, exact requests,
  raw response/logit-to-probability-to-choice consistency, prompt hashes, grids,
  and the complete original HTTP ledger. `provenance/postrun-verification.json`
  records this later audit, not an earlier preregistration.
- `replicate.py` is the recommended new-run entry point. It protects published
  results, skips backend construction on a full cache hit, uses immutable session
  directories, caps HTTP attempts per job across restarts, and stops for unknown
  request costs. Local model-directory overrides are deliberately not supported;
  it resolves the pinned Hub revision instead.
- Offline GitHub Actions and adversarial regression checks require no credentials
  or weights. Tests inject faults, not model outputs for scientific scoring.

`run.py` remains the historical source used for the original result. Its known
resume/runtime blind spots are described above; use `replicate.py` for new work.
New runtime/runner conditions are explicit and must not be attributed to v0.1.
