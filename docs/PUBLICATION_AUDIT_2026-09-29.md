# Publication and attribution audit — 2026-09-29

Scope: the six-study repository at the result state starting with commit
`3329358ab59b6aa5836deadf6d9307ed3651338f`, followed by documentation and review-tool
repairs. This audit does not change historical scientific inputs, models, raw
scores, frozen source or reported outcomes. No new model inference was run.

## Findings and repairs

|Finding|Evidence and action|
|---|---|
|Upstream credit existed but was hard to discover|The vendored Kev NOTICE and full Apache license were already present, and Laya was cited in related work. Added a prominent root credit section and THIRD_PARTY_NOTICES.md, distinguishing code, weights, design inspiration and installed dependencies.|
|Fork status could be confused with code reuse|GitHub metadata reported fork=false, with no parent/source repository. This project nevertheless vendors two historical Kev Python files. The proposed “research fork” in the old plan has not happened.|
|Historical Kev could be mistaken for current Kev|Added exact source/checkpoint/model-card links and explicit historical-release boundaries at the root and latest study. “No new training” describes our experiment; Kev's reused adapter/head were trained upstream.|
|No standard project citation file|Added CITATION.cff, validated against the official CFF 1.2.0 JSON schema. It identifies software rather than a published paper and includes upstream references.|
|Root documentation had fallen behind the series|Added a six-study research index, complete offline check entry points, full-history requirement, denominator/reuse notes and explicit incomplete work. Marked old publication notes as historical.|
|Newest derivative data lacked a local data card|Added the exact 72-text/168-field/552-plan provenance, provisional rewrite status and original-data license scope. Reference spans are not model citations.|
|Rewrite CSVs had no dedicated validation helper|Added a read-only, pack-fingerprinted CSV checker. Blank rows count as zero review; duplicates, foreign IDs and incomplete annotations fail; valid syntax never certifies independence or opens inference.|

## Upstream verification

Compared both active and archived Kev model/initializer copies with upstream
commit `29d71c78368657b3a522729a01c748ea15272abc`: model source and empty initializer
are byte-identical. The full licenses match after CRLF/LF normalization. The
pinned upstream tree has no NOTICE file; the local NOTICE.md is our provenance
note. See [the recorded checks](../provenance/attribution_audit_2026-09-29.json).

The exact Kev/Qwen model cards declare Apache-2.0. Weights remain outside Git.
The pinned Laya diagnostic and Kev native-probe source links were accessible;
they are research references, not a claim to have reproduced their benchmarks.
No Laya code, checkpoint, benchmark rows or model results are incorporated in
this project. Root MIT is explicitly scoped to our own work and does not replace
upstream licenses. This is an inventory and source check, not a universal legal
compliance certificate or a transitive dependency audit.

## Verification scope and remaining gaps

`verify_publication.py` checks relative Markdown/HTML link targets, vendored
source/license hashes, visible revision attribution, citation bytes matching the
schema-validated file, credential-like patterns and current review gates. It is
offline: it does not promise every external URL will remain available, check all
Markdown fragments, or independently establish the originality of every idea.
HTML link checks target rendered pages, excluding source templates whose
relative URLs are intentionally resolved from their generated output directory.

The scientific verifiers and tests remain the authority for record grids,
source freezes and derived metrics. CI is configured to run these checks and
the new publication/review checks without weights or credentials. The delivery
check uses a clean checkout fetched from public origin. Green CI establishes
artifact consistency, not label validity, research novelty or model reliability.

Remaining scientific gaps: zero independent human annotation; rewrites and the
new corpus's reserved sets unscored; no cited-extraction remedy evaluated; no
training, new checkpoint, HF release or paper submission from this project.
Read [the next development design](../research/fact-execution/CITED_FACT_PLAN.md)
for the bounded follow-up rather than treating these gaps as completed work.
