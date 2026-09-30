# Reuse audit: inspect the input contract before another model run

2026-09-30. Completed source/code inspection and an executable audit of 100
released EXtrA-ShaRC pairs. **No model calls, new human labels, upstream code
execution, repository forks or weight downloads.** This is preparation for a
better controlled comparison, not a new algorithm or benchmark result.

## What the released counterfactual files actually contain

Source: [Ramos and Lipani's EXtrA-ShaRC repository](https://github.com/jeromeramos70/extra-sharc/tree/71dfc330a22983ca869b665845c4bb5c5a08d43e),
specifically the pinned [original](https://github.com/jeromeramos70/extra-sharc/blob/71dfc330a22983ca869b665845c4bb5c5a08d43e/data/original_samples.json)
and [counterfactual](https://github.com/jeromeramos70/extra-sharc/blob/71dfc330a22983ca869b665845c4bb5c5a08d43e/data/counterfactual_samples.json)
JSON files. The following counts are our own byte-pinned file analysis, not
reported paper metrics. Pair by unique utterance ID, never by row position.

|Inspection|Count|
|---|---:|
|Paired records|100 pairs /200 records|
|Distinct source tree IDs|40|
|Only scenario changes among the four visible fields|92 pairs|
|Scenario and history both change|3 pairs|
|No visible field changes|5 pairs|
|Of those five: entire JSON record unchanged|3 pairs|
|Of those five: answer and evidence change, visible fields do not|2 pairs|
|Semantic action changes after mapping follow-up text to ASK|69 pairs|
|Distinct exact visible inputs across both files|194|
|Tree overlap with our prior 12-tree public screen|7 trees|
|Exact utterance-ID overlap with that screen|0|

Here visible means exactly `snippet`, `question`, `scenario`, `history`, as in
our existing end-to-end input contract. Strings are compared without trimming,
case folding, paraphrasing or Unicode normalization. Object key ordering is
irrelevant; list ordering is retained. No source label was repaired or adopted
as new ground truth.

Two release IDs expose the incompatible references directly:

|Utterance ID|Original action|Counterfactual action|Changed fields|
|---|---|---|---|
|`a467d8fb237fcc4867457307ccc5939b94485507`|No|Yes|answer, evidence|
|`6bcfe58b999c0dc3caf065f06aa342938e90078f`|ASK|Yes|answer, evidence|

For a fixed deterministic action function of only those four visible fields,
at least two of the 200 record labels cannot simultaneously be matched. The
computed maximum is 198/200 across all exact-input groups. This is a conditional
consistency bound, not a model score or a claim about stochastic systems supplied
with extra context. Feeding the changed annotation evidence or split identity
would change the task. We have not determined which label should be corrected.
This finding does not invalidate an entire paper or establish the behavior of
the authors' full evaluation pipeline, which we have not run.

The 100 pairs are not 100 independent policy units and are not disjoint from
our already inspected policy trees. They therefore cannot be relabeled as fresh
confirmation. Source-level correction and explicit overlap controls would be
needed before using this release as a new scored cohort. No API experiment was
launched merely to show that a model could not infer an invisible change.

## Which existing implementations could be reused?

|Candidate and inspected evidence|Input/help boundary|Decision for this project|
|---|---|---|
|[Verma author repository](https://github.com/nikhilweee/neural-conv-qa/tree/fc8f7e6c7d2704feda2a6e6875cde70b48e4a373): README and `scripts/heuristic.py`, inspected as text.|`create_dev_trees` aggregates history and annotation evidence questions by tree; `smart_model` receives those trees. It uses more than our four-field single-instance interface. Repository-level SPDX license was not detected; no root license found in the inspected tree.|Do not silently run it as a same-information baseline or present our copy-last control as its reproduction. A full reproduction needs its declared data construction and dependencies; a restricted adaptation must be named and tested separately. No author code was imported into our package.|
|[IBM/UrcaNet](https://github.com/IBM/UrcaNet/tree/ce3f41eba23c24506ea2cf9e77cd3898a4eafbaf): metadata, file inventory and README only.|Archived repository with Apache-2.0 and a `rule.ipynb` baseline. Its README points to the 2019 arXiv work; the author repository separately identifies the EMNLP 2020 scripts.|Do not substitute one implementation for the other based on matching title. Notebook algorithm and parity were not audited or executed.|
|[EXtrA-ShaRC](https://github.com/jeromeramos70/extra-sharc/tree/71dfc330a22983ca869b665845c4bb5c5a08d43e): README, metadata, two data files and `fix_questions.py`.|README credits Discern/E3 code and specifies an older training environment. The fix script constructs question mappings using annotation evidence and follow-up answers, not only visible input.|Use its released contrast as prior work and audit material. We did not run preprocessing or training. Repository Apache-2.0 metadata does not independently settle underlying ShARC data rights.|
|[QA4PC](https://aclanthology.org/2021.emnlp-main.678.pdf): sections 3.2–5 inspected; [author-associated data card](https://huggingface.co/datasets/Marzipan/QA4PC) and API file inventory checked.|Expression trees are provided at evaluation in the paper. The available files include trees and per-question references; those are auxiliary human help, not an end-to-end text-only input.|Promising for separating decomposition errors from fact judgment. Inspect data consistency, source overlap and reuse terms next. No QA4PC data rows or model weights downloaded in this audit.|
|[LDPC](https://arxiv.org/html/2501.11335v1): sections 4.1–4.6 and methods inspected.|Uses exemplars, relevance filtering, sampled formulas, strong Kleene logic and an entailment module additionally trained on ShARC. Paper pseudocode can guide an explicitly named adaptation.|Targeted title/author searches did not establish an author implementation. This is not proof that no code exists. Do not promise an exact replication or call the entire method training-free.|

QA4PC metadata was checked at revision
`2b1de7c5e588ec70afa1e753394ae25531e0d182`. The API reports a public, ungated
repository, but no card metadata; its displayed README and file inventory do
not supply an explicit dataset license. Public access alone is not a new license.
The card names QA files differently from the actual inventory, so any loader
must inspect the files rather than assume README filenames. This is a data
candidate, not an already reproduced baseline.

## Reproduce our audit

Only Python's standard library is needed. The two downloads total 216,565 bytes,
are pinned by revision, byte count and SHA-256, and remain outside tracked source.
`fetch` downloads only missing pinned data, validates it and prints counts. It
does not execute author scripts or write a result report. `verify` recomputes
the full report from those original bytes and our saved prior-cohort selection.

```bash
python research/implementation-audit/extra_audit.py fetch --source-dir .local/implementation-audit
python research/implementation-audit/extra_audit.py verify --source-dir .local/implementation-audit
python -m unittest discover -s tests -p test_extra_audit.py -v
```

[Machine-readable audit](extra_release_audit.json) retains all 100 pair IDs,
exact-visible-input hashes, changed fields, source-action transitions and overlap
IDs. These are derived inspection records, not new annotations or predictions.
Ordinary offline CI tests the audit logic on synthetic fixtures; source replay
requires the pinned upstream data download above. A passed fixture test does not
independently verify upstream data content.

Our audit script is original MIT code. The downloaded source data and scripts
are not redistributed or relicensed here. Cite Ramos and Lipani (UMAP 2024),
Verma et al. (EMNLP 2020), Saeidi et al. (EMNLP 2021), and Erwin et al. (2025)
for their respective materials; follow the links and the existing
[ShARC attribution](../source-label-screen/ATTRIBUTION.md) for provenance.

## Milestone decision

The intended next step was to find a reusable baseline, not to launch another
score search. The audit found both useful building blocks and concrete input
contract mismatches. We did not obtain a drop-in verified reproduction.

Next, inspect QA4PC's policy graphs and per-question labels as a possible
diagnostic scaffold: compare direct decisions, predicted facts plus a supplied
graph, and supplied facts plus execution. Charge human graphs as help and give
the same helper to Jev and the ordinary model. Only after validating that
scaffold should an automatically generated graph enter a separate arm. This
could locate the bottleneck; it would not by itself be a novel decomposition
method. Existing review and confirmation requirements remain outstanding.
