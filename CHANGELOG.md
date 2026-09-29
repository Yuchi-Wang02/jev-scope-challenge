# Release notes

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
