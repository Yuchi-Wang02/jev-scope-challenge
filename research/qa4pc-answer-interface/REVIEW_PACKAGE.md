# Retrospective visible-evidence review

Preparation status: two local review slots, each covering the same 24 scenarios
in different deterministic orders. **Zero human submissions and zero reference
updates.** This is retrospective validation of a completed exploratory cohort,
not a new held-out experiment. It does not replace the separate unscored ShARC
training review queue.

## Contents and boundary

Each ZIP contains one standalone `review.html`. It shows the original policy,
question, scenario and exact task instruction. It hides source labels, source
graphs, model outputs and author audit notes. Reviewer IDs are pseudonymous;
the item mapping stays in an author-only local file outside both ZIPs.

Reviewers record a yes/no/maybe judgment, supporting evidence or its absence,
ambiguity, optional missing information and notes. They also identify their
relationship to the project and separately report prior exposure to summary
scores, case outputs, reference labels, another review and audit discussions,
plus AI assistance and discussion with others. No process answer is preselected.
An exposure disclosure is retained; it is not a reason to discard an opinion.

There are no remote scripts or network requests. Browser storage is a convenience;
exported JSON is the backup. Draft export is available before completion. Final
export requires all 24 judgments, evidence, ambiguity fields and process fields.
Client timestamps do not prove review duration, chronology or independence.

## Local preparation and use

```powershell
python research/qa4pc-answer-interface/prepare_review.py --source-dir .local/qa4pc-audit-fresh
```

Output directory: `.local/qa4pc-interface-review-v1/`. Give reviewer A only
`reviewer_A_package.zip` and reviewer B only `reviewer_B_package.zip`. Unzip and
open `review.html` in a browser. Do not share `private_item_mapping.json`, source
labels, results or the source audit with a reviewer intended to be blind.
Prior exposure cannot be undone by providing a new browser form.

Do not publish the filled source packets while explicit upstream redistribution
terms remain unresolved. The public repository contains the blank HTML template,
generator, validator, analytical notes and non-text manifest only. Source pins
are inherited from [cohort.json](cohort.json); no additional upstream code is used.

The generator verifies source and visible-input hashes and refuses to overwrite
a local artifact with different content. Review packages are not model requests.

## Returned file handling

Keep the received JSON byte-for-byte, calculate its hash and run:

```powershell
python research/qa4pc-answer-interface/validate_review.py path/to/submission.json
```

The validator rejects foreign or repeated IDs, duplicate JSON keys, schema drift,
invalid categories and incomplete final submissions. Drafts remain drafts. A
successful check establishes structural completeness, not human identity,
independence or correct judgments. Mechanical test fixtures are never reviews.

After both submissions, align by review ID and report decision agreement,
ambiguity agreement and substantive evidence disagreements separately, clustered
by policy tree. Preserve all originals. Any adjudication must name the chosen
interpretation, rationale, adjudicator and reviewer endorsement status. No labels
are adopted automatically and no adjusted model ranking is authorized here.

## Verification performed during preparation

- A and B contain exactly the same 24 source items in different orders.
- Each ZIP contains only the matching HTML; no model/label/graph fields are in
  its embedded packet. The author mapping is outside the ZIP.
- Browser check rendered 24 cases, showed 0/24 initially and disabled final export.
  A one-item mechanical fixture changed progress to 1/24 while final stayed
  disabled; an actual draft download passed the JSON validator as incomplete.
- The completed-export payload schema and rejection paths are tested offline.
  An end-to-end 24-item final browser download was not exercised in this check.
- There are no completed human reviews. The UI fixture is explicitly named as
  a software test and stored outside any submission archive.

Package hashes are in [review_manifest.json](review_manifest.json). They prove
which bytes were prepared, not who reviewed them or how.
