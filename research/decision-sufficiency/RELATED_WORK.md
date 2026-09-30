# Certain answers precede this prototype

Primary-source screen on 2026-09-30. It is focused, not exhaustive. The first two
papers' definitions/introduction were inspected; the two language-model papers
were screened at abstract level. No paper result is a measurement from this repo.

|Primary source|Established idea relevant here|Consequence for this work|
|---|---|---|
|[Leonid Libkin, PODS 2011, Incomplete Information and Certain Answers in General Data Models](https://homepages.inf.ed.ac.uk/libkin/papers/pods11a.pdf), Section 2.1|Queries can have answers that hold across all complete databases represented by incomplete information.|Possible-world consensus and our finite enumeration are applications of established semantics. Neither is a new algorithm. Our false result also checks that the predicate's negation holds everywhere.|
|[Simon Razniewski and Werner Nutt, PVLDB 2011, Completeness of Queries over Incomplete Databases](https://www.vldb.org/pvldb/vol4/p749-razniewski.pdf), abstract and introduction|Completeness assertions about parts of a database support reasoning about completeness for a particular query.|Query-scoped coverage and irrelevant omissions already have foundations. Our JSON contract is a deliberately small example, not a new completeness theory or an operational retrieval guarantee.|
|[Kuhn, Gal and Farquhar, CLAM, arXiv 2212.07769v2](https://arxiv.org/abs/2212.07769v2), abstract|Language models can be prompted to recognize ambiguity and ask selective clarification questions.|Adding a clarification action is not novelty. We have not run conversations or shown a benefit from asking fewer questions.|
|[Sedova et al., To Know or Not To Know? arXiv 2407.17125v3](https://arxiv.org/abs/2407.17125v3), abstract|Examines model consistency under ambiguous entities.|Entity ambiguity is a direct neighboring topic. This structured program demonstration does not establish model behavior under natural-language ambiguity.|

See also the earlier [sufficiency and abstention screen](../candidate-completeness/RELATED_WORK_POSTRUN.md).
The independent dimensions here are a **task specification choice**: establish
target identity, establish a component predicate, and authorize an operation.
Their separation can make a diagnostic clearer. It is not sufficient novelty for
a paper by itself. A contribution would need a demonstrated unmet task, reviewed
materials and transferable evidence beyond a program that solves its own schema.

## Provenance and reuse

All contract examples and code in this directory were authored for this project
with AI assistance. They contain no real customer data, copied source database
rows or downloaded paper text. No repository was forked or executed for this
prototype; no third-party implementation is bundled. The refund-destination
motif follows the project's attributed tau retail work, but this is a simplified
independent toy policy with finite original-method domains, not a tau benchmark
task or reproduction of its environment. Original code is [MIT](../../LICENSE);
the authored synthetic contract examples follow the repository's
[CC BY 4.0 data policy](../../data/README.md). Primary literature is linked and
retains its own rights.
