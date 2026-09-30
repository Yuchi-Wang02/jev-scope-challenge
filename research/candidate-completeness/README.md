# One visible match: is the candidate set complete?

Status: both fixed grids completed: 150 Jev requests and 150 ordinary Qwen3-4B
native prefills, including six separate smoke jobs per model. Jev scores 63/72
and 67/72 by option order; Qwen native scores 34/72 and 30/72. Strict complete
parents are 3/12 and 0/12. Jev's errors are unnecessary deferrals on explicit-ID
requests with relevant omissions. [Full results](RESULTS.md) retain every error,
baseline and limit; [replay](../../docs/candidate_coverage.html) shows exact inputs.
Twelve simulated source users are disjoint from the prior payment study. New human
review is pending. This is a static exploratory probe, not tau-bench agent
performance or a validated benchmark. [Neutral review package](review/README.md).

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

Offline checks: `python research/candidate-completeness/analyze.py --verify`,
`python research/candidate-completeness/publish.py --verify`, and
`python research/candidate-completeness/review_tools.py --verify`.
Preparation check: `python research/candidate-completeness/study.py verify`.
Its `new_model_calls: 0` field describes the preparation checks only; it is not
the current run count. Current counts come from the result/attempt ledgers.
After freezing: `python research/candidate-completeness/study.py verify-freeze`.
Never run preparation again over a frozen study. The live runner protects its
published directory through freeze and resume checks; it is not a general
isolated-output replication CLI. Use a separately versioned run for replication.
