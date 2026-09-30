# Independent review — two separate reviewers

**Completed independent annotations: zero.** The two blank templates are not labels.
Download [the reviewer-only package](https://github.com/Yuchi-Wang02/jev-scope-challenge/raw/refs/heads/main/research/payment-ownership/review/review_package.zip). It excludes model results,
construction labels, source-case mapping and pairing IDs; do not use the result
replay as the review interface. The package does not prevent browsing public results.
These materials cover 48 inputs in full and program-selected related forms: 96
individually shuffled review items. Repeated forms are not independent samples.

Give each reviewer only `inputs.jsonl`, their own copy of a reviewer CSV, this
instruction sheet, and the standalone `review.html` produced by report.py. That
viewer contains neither model outputs nor program references. Do not send the
result replay as a review interface. Full public-repository access means blinding
is procedural only; reviewers should record any prior exposure to the results.

For each item independently record:

1. The target order and requested payment method, or `UNRESOLVED`.
2. VALID_DESTINATION, INVALID_DESTINATION or NOT_ESTABLISHED for this component.
3. All relevant evidence paths and a reason connecting them to the target.
4. Whether the request or source interpretation is ambiguous, and why.
5. Reviewer identity and review date. Record author/reviewer overlap and exposure
   to models or program labels separately in the submission cover note.

Use only displayed evidence and the component policy. Do not infer absent payment
history from the other version or the full upstream database. Check whether the
related view preserves enough information to resolve the same request.

Do not overwrite frozen blank templates. Save completed exports as separate files
outside the frozen input set. The browser saves locally under the reviewer ID;
export the CSV to retain a portable copy. Do not share a browser profile/reviewer ID
between reviewers. Discuss disagreements only after both original exports exist.

Validate exports with `python research/payment-ownership/review_check.py path.csv`.
Validation checks format and completeness, not honesty or independence. Preserve
both original exports, adjudication reasons, and all exclusions. Never silently
remove a case after seeing which model wins. Later reviewed labels require a
versioned reanalysis retaining all original outputs. These development inputs
cannot become untouched confirmation by being reviewed later.
