# One visible match: is the candidate set complete?

Status: 72 constructed inputs and 150 planned Jev calls prepared; no model results
at preparation. Twelve simulated source users are disjoint from the prior payment
study. New human review is pending. This is a static, exploratory decision probe,
not tau-bench agent performance or a validated benchmark.

Read the [execution protocol](PROTOCOL.md), [source register](source_manifest.json),
[initial design and revisions](PLAN.md), and [related work](RELATED_WORK.md).
The execution protocol records the later user authorization to run bounded
exploration before the new two-person review is complete.

Coverage triples hold records and requests fixed. Product-reference decisions
should change only when omitted records can match the requested product; explicit
order IDs should remain stable. Coverage assertions and omitted-world witnesses
are synthetic premises layered over preserved public simulated records. They are
not factual claims about missing rows in the upstream database.

Source: pinned Sierra tau2-bench revision `5bfa7e37b36656b37dc6d022156be6563c1007f3`.
Copied records retain [MIT](vendor/LICENSE). Original study code and constructed
text use this repository's MIT license. No GitHub fork was created. The runner
adapts this repository's earlier payment adapter; the historical source helper
is a hashed dependency. No Kev/Laya source or model is executed here.

Offline check: `python research/candidate-completeness/study.py verify`.
After freezing: `python research/candidate-completeness/study.py verify-freeze`.
Never run preparation again over a frozen study. The live runner protects its
published directory through freeze and resume checks; it is not a general
isolated-output replication CLI. Use a separately versioned run for replication.
