# Candidate language rewrites — not evaluated

144 AI-generated pairs vary the wording of the existing 72 development texts.
Their intended fact equality comes from the generator, not independent review.
No rewritten input has a model result. This is preparation, not language-transfer
evidence or a new held-out benchmark. The original study's blank review remains intact.

Use `blind_pairs.json` and `blank.csv`: read original/candidate/policy, mark same
facts yes/no/unclear, explain and propose a correction, record reviewer/date.
Do not view `candidate_rewrites.jsonl`'s intended-equality flag until independent
judgments are saved. Public source mapping means blinding is procedural only.
Review differences in permission, negation, target binding and conflict/absence,
not simply whether the final decision happens to be equal.

No export here automatically certifies independence or opens inference. Record
reviewer provenance and adjudicate disagreement; version changed inputs before
a new execution protocol. Current annotations and candidate model records: zero.

For a smaller first pass, [`starter_blind_pairs.json`](starter_blind_pairs.json)
and [`starter_blank.csv`](starter_blank.csv) contain 12 of the same 144 pairs:
both rewrite styles for the first development parent in each of the three
families, limited to decisive-missing and conflict variants. They are a
procedural review queue, not a statistical sample. The
[`starter manifest`](starter_manifest.json) records the exact source-pack
fingerprint and zero completed reviews. Run
`python research/fact-execution/review_starter.py --verify` to check that the
starter still matches the frozen pack. Do not use the source mapping during
blind review; the original full-pack fingerprint below also applies when
validating a partial starter CSV.

## Validate a later review export without changing the study

The read-only helper reports zero submitted annotations for the committed blank:

```bash
python research/fact-execution/review_pair_tools.py
```

Use a private copy such as `.local/rewrite-review.csv`; keep the six existing
columns. Write dates as YYYY-MM-DD and provide a reason, reviewer identity and
yes/no/unclear choice for each completed row. Leave unreviewed rows fully blank
after their ID. A partial export is allowed. Run:

```bash
python research/fact-execution/review_pair_tools.py --input .local/rewrite-review.csv --pack-sha256 3428b26a36bed72525d207a8e3e89b0bc5647e70a62e416a2efa0e66d921bd79
```

The digest binds the export to this exact `blind_pairs.json`. Duplicate/foreign
IDs, missing reasons, incomplete rows and mismatched packs are rejected. This
does not certify a human authored the export, judge reviewer independence or
open model inference. Objections and corrections require adjudication and a
separately versioned candidate set. Never fill the sheet with AI answers and
count those as independent human review.
