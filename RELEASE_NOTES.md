# Diagnostics closeout: valid answers, verified evidence

Milestone: `diagnostics-v0.2.0` · 2026-10-05 America/New_York.

This stage collects the completed capable-model reference, stopped candidate
studies, software reproductions and an arithmetic correction into one
inspectable research record. It is an exploratory diagnostics release, not a
new general method, independent confirmation or a model-replacement claim.

Start with the [technical report](TECHNICAL_REPORT.md) and
[interactive replay](https://yuchi-wang02.github.io/jev-scope-challenge/decision_boundary.html).
The [standalone HTML](docs/decision_boundary.html) needs no service or API key.

## What changes the interpretation

- **A stronger reference narrows the old shared-error finding.** Sonnet 5.5
  scores 107/108 and 108/108 on unchanged historical Qwen user prompts.
  The strict total is 215/216 repeated main decisions, with one invalid-format
  response and no valid wrong label. All 84 previously correct controls per
  order survive. The old Jev and nonthinking Qwen results remain 84/108 per
  order. Model, interface and inference compute differ; no causal or matched-cost
  ranking follows. All 222 supplementary calls and their costs are retained.
  [Results and raw records](research/rule-direction/capable-reference/RESULTS.md).
- **An inclusive 0.99 confidence threshold retains errors.** Decimal-exact
  comparison retains 173 historical Jev decisions, including 9 errors. The
  supplied review draft's 128/0 calculation omitted the exact 0.99 boundary.
  This corrects a post hoc calculation; it does not calibrate a deployment
  threshold or change the original model scores.
  [Recheck](research/series-closeout/confidence_report.json).
- **Unproductive candidates remain visible.** The retry-intent pilot passed
  clear-authorization and explicit-deferral cases; ambiguous references remain
  unvalidated. Bounded source screens did not produce a ready new comparison
  cohort. [Decision record](research/intent-retry-pilot/SOURCE_SCREEN_DECISION.md).
- **Software defects have their own evidence boundary.** ToolTalk checker and
  AgentAbstain environment reproductions, failed attempts and local repairs are
  retained with source pins and licenses. They do not establish aggregate
  benchmark-score impact, actual agent failure frequency or upstream acceptance.

## Reproduction and preservation

The saved-result replay covers all 108 inputs in both option orders, including
the strict format failure. Its builder checks 648 main results and all 666
results including smoke. Browser checks covered all 216 selector combinations,
desktop and narrow screens. Displayed thinking text is excluded.

Before publication, all 77 Python command steps from both CI jobs passed in an
isolated Git checkout on Windows Python 3.10.18 with exact requirements versions,
including 393 unit tests. No checkout files or the real staging index changed.
This local check did not execute GitHub Actions setup/install steps or establish
cross-platform replication. Remote run status is available through
[GitHub Actions](https://github.com/Yuchi-Wang02/jev-scope-challenge/actions).
See the [reproduction guide](REPRODUCIBILITY.md).

Scoped Git attributes preserve captured bytes. Default offline source checks
clearly distinguish shipped evidence from external caches that were not
reopened. Historical freezes, failures and review receipts are retained; their
timestamps describe earlier stages. Publication changes to current navigation,
this release note and the replay's draft label occur after the
[prepublication audit snapshot](research/series-closeout/release_audit.json).
That snapshot is not a manifest of every byte in the final release commit.

The [review packet](RELEASE_CANDIDATE.md) explains the one later README change
in an earlier 62-file preservation snapshot. Source/result freezes were not
rewritten. Human-review disagreements and uncompleted adjudication remain open.

Kev reuse, Laya's reference-only role, ToolTalk MIT code, AgentAbstain MIT runtime
and CC BY 4.0 data, and tau source terms are documented in
[third-party notices](THIRD_PARTY_NOTICES.md). This release creates no GitHub fork
or upstream contribution. Publication preparation adds no model calls.

The finite rule-direction candidate is closed. A future main study still needs
a motivated unresolved task, credible references and a comparison that can
disprove the proposed benefit. No next model experiment is automatically queued.
