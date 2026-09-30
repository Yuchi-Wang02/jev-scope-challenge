# Two reviews received: conditional labels and reporting disposition

Date: 2026-09-30. This project reporting decision is AI-assisted. It is not a
third human review, a reviewer-endorsed adjudication, or a new reference-label set.

## Preserved submissions and process records

- [Yuchi original](review/submissions/yuchi/payment_review_yuchi_excel.csv) and
  [first receipt](review/submissions/yuchi/receipt.json): author reviewer, 96 items,
  aggregate-result exposure, self-reported no specific-answer exposure or AI help.
- [Tiancheng original](review/submissions/tiancheng/payment_review_tianchengi.csv),
  [receipt](review/submissions/tiancheng/receipt.json) and
  [date-normalized validation copy](review/submissions/tiancheng/validation_copy_iso_date.csv):
  96 items. The user relayed "都没有" in response to a bundled process question.
  We record this as no project involvement, prior result/first-review/discussion
  exposure, AI assistance or discussion reported. It is not independently verified
  and is not a separately signed statement from the reviewer.

Both originals are preserved byte-for-byte. Only the first date in the validation
copy changes from `9/30/2026` to `2026-09-30`. No time or timezone is invented.
The remaining 95 dates share `2026-09-30T06:40:00Z`, later than the local intake
receipt `2026-09-30T06:29:17.129207+00:00`. The reason is unestablished. Preserve
this metadata discrepancy; timestamps cannot prove review duration, chronology
or independence. This observation alone does not establish how the review was made.
The receipts are intake snapshots; their then-current publication/second-submission
fields are not today's project status.

## Agreement with a substantive qualification

|Field|Agreement across the same 96 review items|
|---|---:|
|Target order|96/96|
|Destination|96/96|
|Decision label|96/96|
|Ambiguity field|48/96|

The [row-level comparison](review/comparison.json) preserves all 48 ambiguity-field
differences. Yuchi marked all items `no` but raised a scope objection in the cover
note. Tiancheng marked the 48 product-reference items `yes`, retaining the visible-match
decision while explaining that a strict reading would be UNRESOLVED/NOT_ESTABLISHED.
Thus the apparent 100% label agreement is conditional, not unqualified validation.
The ambiguity-field difference does not mean one reviewer saw no semantic issue.
There are 192 annotation rows over 96 review items /48 inputs /12 parents, not
192 independent examples. The six smoke cases are outside both submissions.

## Reporting decision now

1. Retain both original forms, cover notes, original scores, inputs and model
   responses. Do not force a reviewer to rewrite a conditional judgment to agree.
2. Mark explicit-ID items as having no objection of this particular scope type.
   Their 24 underlying inputs match original references 24/24 in all four arms.
   This is not a blanket certification of every aspect of the task.
3. Mark product-reference items as **conditional references, scope unresolved**.
   The 24/24 per-arm original scores require a displayed-candidate interpretation.
   They are unsuitable as unambiguous, independently confirmed gold labels.
4. Preserve full-grid 48/48 as the historical original-reference score, displayed
   alongside the qualification. Do not announce 24 newly proven Jev errors or
   silently drop disputed items from a replacement headline score.
5. Adopt zero new reference labels. A stricter target-resolution interpretation
   would require a separately named sensitivity analysis, not a retroactive
   replacement score. No such alternate numerical score is claimed here.

These decisions handle publication without pretending the original wording had
a unique interpretation. Any final semantic adjudication must record which
interpretation was chosen, by whom, why, and which reviewers endorsed it. Neither
CSV alone supplies that endorsement. The original STOP_NO_FOLLOWUP remains in force.

## Consequence for future work

The original candidate is closed as an exploratory pilot with conditional scope
evidence. Do not spend its remaining budget to turn the disagreement into a failure.
The separate [new proposal](../candidate-completeness/PLAN.md) must explicitly
declare relevant candidate coverage and test irrelevant omissions as a control.
It has no generated dataset or model results. A proposal review is not execution.

Offline reproduction: `python research/payment-ownership/review_pair.py --verify`.
This verifies files and comparisons; it cannot certify reviewer independence or truth.
