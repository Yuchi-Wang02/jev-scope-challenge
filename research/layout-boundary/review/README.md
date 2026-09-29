# Independent label review — prepared, not completed

`blind_review.csv` contains 96 original evidence/policy pairs, shuffled under
opaque IDs. No model predictions or rule labels are in that file. The answer key
is separately public for reproducibility; reviewers should not inspect it or
model outputs before submitting their judgments. This is procedural blinding,
not access control. The present status is **zero human annotations**.

Judge only the supplied evidence and policy, using ALLOW, DENY or INSUFFICIENT.
ALLOW means evidence supports the action/claim; DENY means it contradicts it;
INSUFFICIENT means neither conclusion is determined. Flag ambiguous wording,
unjustified defaults, missing policy, conflicting evidence or an objection to
the three-way event definition. Provide a short reason and reviewer/date.

Suggested process: two independent reviewers, then explicit adjudication of
disagreements with all objections retained. Keep originals and version any data
correction. A corrected label set is a new version, not a silent replacement of
the exposed pilot. One user's approval to run/upload is not case-level annotation.
AI-filled forms do not count as independent human review.

This sheet reviews the existing inspected pilot. Fresh confirmation still needs
new sources/relation combinations and a separately frozen protocol.
