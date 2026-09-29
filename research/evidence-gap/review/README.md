# Independent review, when reviewers are ready

Current status: **zero independent human annotations**. The pack, CSV and page
are blank preparation, not completed review. No external reviewer was contacted.

Open `review.html` in a browser. Start with six items, then select all 288. The
page embeds only opaque item IDs, policy and evidence; it has no gold, model
outputs, split/family/view names or paired-case metadata. The starter samples
the two deletion views of three development parents. All items are shuffled.
The repository's `answer_key.json` is a separate public program key: this is
procedural blinding, not secrecy, a secure annotation service or a real-world
held-out corpus. Reviewers should avoid it and result pages until labels are saved.

Read the rule literally, using only target records. Assign ALLOW when the rule
and evidence determine permission; DENY when they determine rejection;
INSUFFICIENT when the decision is undetermined or target-schema facts conflict.
Missing records do not automatically mean INSUFFICIENT if an explicit rejection
already determines DENY. Explain the deciding or missing facts and flag ambiguity.
Review each item independently; do not copy the program key.

The page stores drafts locally and downloads a JSON export. No API or upload is
used. Labels are not transmitted to us automatically. A completed export can be
checked with Python 3.10:

```bash
python research/evidence-gap/review_tools.py ingest --input path/to/human-review.json
```

This reports incomplete coverage, program-label disagreements and ambiguities.
It never marks the corpus human-validated or opens reserved inference. Reviewer
independence/provenance must be recorded separately; disagreements need a
documented adjudication. Changes require a versioned corpus/protocol and invalid
items must not be silently dropped based on model performance. Reserved
calibration/test remain unscored until that process and a new protocol are complete.

`blank.csv` is an alternative blank form. Its 288 ID rows are not annotations.
The current ingestion command accepts the browser's JSON format, not CSV.
