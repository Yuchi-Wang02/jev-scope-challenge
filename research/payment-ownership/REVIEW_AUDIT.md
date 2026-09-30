# Author review received; candidate scope remains unresolved

**Historical first-submission audit.** For the later second submission and current
reporting decision, read [REVIEW_DISPOSITION.md](REVIEW_DISPOSITION.md). Counts below
describe receipt of the first submission.

Date: 2026-09-30. This is a post-run semantic audit, not a protocol amendment,
new inference run, or completed two-reviewer adjudication.

## Submission and provenance

Yuchi submitted all 96 shuffled review items. The [unaltered CSV](review/submissions/yuchi/payment_review_yuchi_excel.csv)
and [receipt with the original cover note](review/submissions/yuchi/receipt.json)
are retained. The CSV's byte SHA-256 is
`fa33f9f4761af2e5b517657a3cbbf6378c5bb495d9ea29b20c6bb458b26ebfb2`.

Yuchi is the project author. Aggregate model results had appeared in the project
conversation. The reviewer reports no exposure to specific model answers or
program labels and no AI assistance in making the judgments. These are
self-reports, not independently verified facts. Discussion with others was not
explicitly reported. A second reviewer has not submitted. The timestamps in an
export do not establish the duration or independence of the work.

Current status: **one author review, 96 completed item annotations; zero
non-author reviewer submissions; no adjudicated reference update**. Other
studies' review counts remain unchanged. Original freeze-time statements about
zero reviews retain their historical meaning.

## Checks and what agreement means

The CSV has 96 unique expected IDs, complete required fields and valid categories
and dates. Its target IDs, destination IDs and labels each agree with the original
construction on 96/96 items. Labels are 48 VALID and 48 INVALID. All 96 ambiguity
fields are `no`. All 552 cited evidence paths resolve, including 24 wildcard paths.
These checks establish file consistency, not semantic truth or reviewer independence.

The cover note is part of the submission, not an optional comment. It qualifies
48 product-reference items: the reviewer resolved the request to the unique
matching **visible** order. If the intended scope includes unseen matching orders,
the reviewer would instead mark the target UNRESOLVED and the decision
NOT_ESTABLISHED. Do not summarize the CSV as 96 unqualified approvals.

## The missing candidate-scope guarantee

The input policy says both "Use only visible records" and "The orders shown are
a selected subset". Those statements can coexist, but neither guarantees that
the request's target belongs to the displayed candidate set. The frozen protocol
only establishes item uniqueness among the two displayed orders. Construction
metadata is not additional evidence available to the model or reviewer.

Under a displayed-candidate interpretation, the submitted judgments match the
construction. Under an interpretation allowing an unseen matching order, visible
uniqueness need not establish target identity. The original wording does not
adequately choose between these interpretations. This is a task-specification
issue requiring adjudication; it is not presently a confirmed set of model errors.

## Effect on the saved results

|Request style|Review items across full/related views|Underlying inputs|Saved Jev matches to original references in each of four conditions|
|---|---:|---:|---:|
|Explicit order ID|48|24|24/24|
|Product-name reference|48|24|24/24, conditional on displayed-candidate scope|

The four conditions are full/related records crossed with original/reversed
option mapping. They are repeated measurements of 12 source-user parents.
The explicit-ID subset is unaffected by this particular objection, not thereby
certified against every possible objection. The full-grid 48/48 scores remain
historical scores under original references. Treating every product-reference
answer as a newly proven failure, or treating full-grid success as unconditionally
human-validated, would both exceed the evidence.

No row is removed, no CSV entry or reference label is overwritten, and no model
response is rerun. The 5/6 smoke result and the earlier launch amendment remain
unchanged. The six smoke cases were not included in this 96-item submission.
The operational STOP_NO_FOLLOWUP decision is not reopened by this audit.

## Next steps

Give the second reviewer only the [standalone handoff package](review/reviewer_B_package.zip).
Do not send this audit, the first review, result replay, or new experiment plan
before their initial export. Public availability makes blinding procedural only.
Preserve both submissions before discussing disagreements. Adjudicate the scope
question separately and version any later reference changes and sensitivity
analyses while keeping original scores accessible.

The [candidate-completeness proposal](../candidate-completeness/PLAN.md) is a
separate, unrun study design. It does not retroactively clarify these inputs.

Reproduce the checks without inference:

```bash
python research/payment-ownership/audit_review.py --verify
```
