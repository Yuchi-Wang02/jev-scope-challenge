# Historical release review packet: A Valid Answer Is Not a Verified Decision

**Disposition:** the author approved publication on 2026-10-05 America/New_York.
The preparation status below is retained as a dated review record. Current
release scope is in [RELEASE_NOTES.md](RELEASE_NOTES.md); publication-time
navigation changes do not rewrite the earlier review receipts or experiments.

Status: **local review candidate; not committed, pushed, tagged or released**.
Prepared 2026-10-05 America/New_York (verification extends into 2026-10-06 UTC).
Base: `022950f6dd6c6b1f9d1758293b8a9ba8f3fafeda`.

## What a reader gets

- [A stage technical report](TECHNICAL_REPORT.md) connecting the original question,
  the controls that constrained it, failed interventions and closed candidates.
- [A standalone case replay](docs/decision_boundary.html): all 108 authored
  rule-direction inputs in both option orders, saved Jev/Qwen/Sonnet decisions,
  exact final answers and finite reference worlds. It makes no network or model
  request. The historical two-model page remains unchanged.
- The completed [Sonnet supplement](research/rule-direction/capable-reference/RESULTS.md):
  107/108 and 108/108, one strict-format failure, 222 total requests including
  smoke, zero retries, nominal cost $0.129346. This is an unequal-compute reference
  on old inputs, not a matched-cost experiment or a new independent cohort.
- An [offline confidence correction](research/series-closeout/confidence_report.json):
  inclusive decimal confidence >=0.99 retains 173 old Jev decisions with 9 errors.
  The supplied review draft's 128/0 calculation excluded the decimal boundary.
- The retained [retry pilot](research/intent-retry-pilot/RESULTS.md), bounded
  source screens, and separately attributed checker/environment repairs.

The public message is: **structured answers, agreement and high confidence need
separate evidence checks**. The series is currently a collection of reproducible
diagnostics. It does not establish a novel general method, a model-replacement
advantage, a general failure rate, or paper acceptance readiness.

## Exact intended scope

Include the current root report/navigation/reproduction changes, scoped Git
attributes and ignore rule, the added offline CI job, the new replay page, and:

1. `research/rule-direction/capable-reference/`
2. `research/intent-retry-pilot/` excluding the ignored local `results/jev.lock`
3. `research/series-closeout/`
4. `research/topic-screen-2026-10-05/`

Keep source pins, licenses, raw journals, failed attempts, frozen requests and
verification code with their results. Exclude `.local/`, model weights, caches,
private Downloads attachments, virtual environments and browser QA screenshots.
The final [release audit](research/series-closeout/release_audit.json) records the
candidate file inventory and executed checks. Its own file is excluded from its
hash inventory to avoid a circular digest.

No new human review submission is introduced by this candidate. The two payment
reviewers' files were already tracked and remain unchanged; their scope objection
and uncompleted adjudication stay visible. AI review files are not human review.
Public synthetic source fixtures include fictional profile/contact fields. Saved
runtime evidence also contains workspace paths, GPU and model-cache names;
these are environment metadata, not distributed private files or weights.

## Reuse and preservation

Kev code and pretrained adaptation remain credited; Laya is related work only.
This stage creates no GitHub fork or upstream contribution. ToolTalk source is
MIT; AgentAbstain runtime/evaluator is MIT and its data/environment material is
CC BY 4.0. The tau screen preserves its source license and pins. See the
[full attribution ledger](THIRD_PARTY_NOTICES.md); the root license does not
replace third-party terms. Local proposed fixes are not merged upstream fixes.

New scoped `-text` attributes preserve the bytes of four evidence trees. Without
them, Git's first-add normalization would invalidate several saved raw-byte
hashes. The original files and frozen hashes were preserved, not resealed.
The cohort verifier now distinguishes shipped evidence from optional external
cache provenance and fails on missing/corrupt files when a cache is requested.

One historical preservation snapshot requires an explicit note. The
[portable-preservation manifest](research/intent-retry-pilot/cohort-screen/atomicity-repro/proposed-fix/portable-preservation.json)
recorded 62 files before a replay; its contemporaneous post-run check passed
62/62. **Currently 61/62 match** because the parent
[atomicity README](research/intent-retry-pilot/cohort-screen/atomicity-repro/README.md)
was subsequently updated with navigation and the completed follow-up. Its saved
hash is `adcd6c6446024d34f06b4505f2bd34b2c2170cb93ddb02267187ed587b539fff`;
its current hash is `1eba76a730da793d7fe805a058bd189fec39ad73cce3d868eade7e48343be78b`.
This is not a line-ending difference. The old full README was not retained in
the staged replay inputs, so a complete before/after text diff is not claimed.
The six current freeze contracts' 64 items and 21 vendored source files passed
the release audit; this README is not a member of those freeze contracts.

Likewise, [the preceding synthesis receipt](research/series-closeout/completion_audit.json)
captures that earlier stage. Later navigation and replay links legitimately
change current document hashes. That receipt is preserved as history and is
superseded for current release scope by the release audit, not silently edited.

## Verification and remaining limits

The [reproduction guide](REPRODUCIBILITY.md#local-closeout-candidate-2026-10-05)
lists all new offline commands. A temporary Git index and materialized checkout
test checks the representation a reader actually receives, including byte
preservation, without modifying the real staging index. The final audit records
which commands passed, browser checks and the exact candidate inventory.

These checks establish software and evidence consistency only. They do not
independently validate natural-language labels, reviewer independence, novelty
or external source truth. The confidence command explicitly retains prior
private-review provenance without reopening the ZIP by default. The cohort
and topic commands explicitly say when their external source caches were not
rechecked. Native environment replay is separately recorded historical work.

Initial affected-scope checks used Windows Python 3.13.5. A subsequent isolated
checkout ran **all 77 Python command steps** from both CI jobs on existing
Windows Python 3.10.18 with the exact required versions of httpx, numpy and
matplotlib: **77/77 passed, including 393 unit tests**. No materialized file was
changed or added, and the actual Git index remained unchanged. The release
audit records this follow-up separately from the earlier checks.

This did not execute GitHub Actions remotely, install dependencies afresh, or
reproduce an Ubuntu host; checkout/setup/install actions were replaced by the
existing local environment. Remote CI and Pages still need checking after
publication. No new model calls were made while preparing this package.

## Publication decision

The public repository was checked during preparation: `main` still pointed to
the base above; tags `prereg-v0.1` and `prereg-v0.1-final` already existed. The
public GitHub Releases API returned no releases. This is a dated observation,
not a live badge.

Suggested milestone name: **Diagnostics closeout: valid answers, verified evidence**.
Suggested new tag: **`diagnostics-v0.2.0`**, not created. Preserve existing
preregistration tags. After deciding to publish, commit the reviewed scope,
push it, check remote CI, verify Pages, then attach release notes to that actual
commit. The Pages URL for the new replay becomes meaningful only after it is
deployed. No Hugging Face data release or paper submission is part of this package.

After this closeout, a new main study still needs a motivated unresolved task,
credible references and controls that can stop the project. Additional model
runs are not queued by this document.
