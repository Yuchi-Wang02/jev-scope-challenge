# Nearest-work update: what the next comparison must establish

## Additional check during the public-source screen

Checked 2026-09-30, before interpreting that screen's cross-model scores.
[Verma et al., EMNLP 2020](https://aclanthology.org/2020.emnlp-main.589.pdf),
sections 1–2, already identifies ShARC shortcuts involving the last history
answer, history length, clause order and empty context. It supplies a heuristic
program and a modified dataset. Our frozen last-answer-copy control is a limited
check of an established shortcut; it is not that full program or a novel idea.
No author code or data from that work was imported or executed in this check.

[Saeidi, Yazdani and Vlachos, EMNLP 2021](https://aclanthology.org/2021.emnlp-main.678/)
describes condition questions combined through expression trees, including
identification of missing information. Here the official abstract was inspected;
this addition is not a full implementation audit or replication. The generic
decomposition-plus-execution proposal therefore has an earlier direct precedent.

These precedents and our [12-pair source audit](../source-label-screen/SOURCE_REVIEW.md)
further narrow the contribution: a new interface comparison may be useful, but
shortcut detection, missing-information tracking and rule decomposition are not
new general methods. The source audit does not establish new gold labels.

## Earlier focused review

Checked 2026-09-30. Focused primary-source review, not an exhaustive novelty
search or reproduction. No task predictions, new labels or upstream training
runs were produced. The frozen review queue is unchanged.

## Evidence inspected

|Work|Primary evidence and inspection depth|Established precedent|
|---|---|---|
|Ramos and Lipani, EXtrA-ShaRC, UMAP 2024|[Official conference abstract](https://um.org/umap2024/proceedings/) and [author README at pinned revision](https://github.com/jeromeramos70/extra-sharc/blob/71dfc330a22983ca869b665845c4bb5c5a08d43e/README.md). The ACM full paper was not retrieved.|Counterfactual user profiles test whether conversational reading responses change appropriately. Explanation extraction is another task.|
|Erwin et al., Few-shot Policy (de)composition in Conversational Question Answering, 2025 (LDPC)|[arXiv v1](https://arxiv.org/html/2501.11335v1), targeted method sections 4.1–4.6, experimental setup 5.1–5.2, error-analysis text and limitations; not a complete replication audit.|Few-shot policy decomposition, logical formulation, three-valued execution and sampled-formula self-consistency. Section 4.5 explicitly fine-tunes the scenario entailment model on ShARC. The untrained-module claim concerns decomposition/formulation, not the entire pipeline.|

LDPC also uses an embedding relevance filter and in-context examples. These
components and all sampled calls belong in any training/help/cost inventory.
An implementation link was not established from the inspected paper; this is
not a claim that no implementation exists. Published scores are not our results.

The EXtrA author README identifies original/counterfactual data and credits
modified Discern and E3 code. GitHub reports Apache-2.0 for its repository license.
That metadata does not independently establish permission to relicense all
underlying datasets. No EXtrA code, checkpoint or data was imported, forked or run.
The inspected repository revision is
`71dfc330a22983ca869b665845c4bb5c5a08d43e`; LICENSE blob:
`261eeb9e9f8b2b4b0d119366dda99c6fd7d35c64`.
Our existing ShARC package retains its separate CC BY-SA 3.0 attribution.

### Follow-up: author thesis method check

The [UCL-deposited author thesis](https://discovery.ucl.ac.uk/id/eprint/10222976/2/Jerome_Ramos___UCL_PhD_Thesis_final.pdf)
provides a fuller EXtrA account. Sections 3.2.3–3.2.4 (pages 52–53) describe
100 sampled development conversations with one profile rule manually changed
and outputs/explanations updated as needed. Section 3.5.4 and Table 3.4
(pages 62–63) report aggregate original/counterfactual performance and identify
instance-level outcome analysis as future work. These pages were text-read;
pages 52 and 63 were also visually checked. This is an author thesis account,
not verification that its wording exactly matches the ACM conference version.
Local source: 2,392,604 bytes, SHA-256
`5e50f86f09fcfafb7f0b9e726ef00b62056314746f73d8b6cb76833fa48fec04`.
The PDF is not redistributed here.

Our selection changes a history answer rather than manually editing a profile,
but single-condition contrast is already present in that precedent. This is a
material overlap, not evidence of a new experimental paradigm. The aggregate
comparison also motivates retaining [paired correctness](PAIRED_METRICS.md).
That metric is ordinary evaluation practice, not our algorithmic contribution.

## Changes to our contribution judgment

The following are project inferences from those precedents, not statements by
the cited authors:

|Proposed story|Disposition now|Evidence needed to go further|
|---|---|---|
|We first test whether a ShARC response follows a changed condition.|Withdraw as a novelty claim.|A narrowly different intervention requires full-paper and implementation comparison, not just a different title or slice.|
|We introduce rule decomposition followed by explicit logic.|Not a new general method.|A concrete new component, a necessary baseline comparison and a reproducible benefit beyond established decomposition approaches.|
|All modules remain frozen, so our pipeline is novel.|A constraint to test, not proof of novelty.|Audit auxiliary models, demonstrations, prompt selection and other task adaptation; review further frozen-pipeline work.|
|A typed decision model replaces ordinary instruction models.|Open empirical question.|Same visible inputs, reviewed actions, comparable assistance, disclosed decoding and all-stage resource accounting.|
|One model scores better on this pilot, proving its architecture is necessary.|Unsupported causal and generalization claim.|Different causes can produce the same gap. New reviewed materials and interventions must distinguish them.|

The current defensible purpose is to measure a bounded replacement boundary,
if one exists. It is acceptable for the pilot to reveal no useful distinction.
Neither a public repository nor a collection of negative examples establishes
a paper contribution.

## Baseline obligations and sequence

1. Finish the existing independent review and human adjudication. Do not change
   the queue to manufacture distance from prior work. The current queue lacks
   deliberately invariant controls and source-Irrelevant cases; retain those
   limits in every comparison report.
2. Freeze a direct comparison first: pinned Jev and the pinned Qwen3.5 runtime,
   with declared direct/thinking conditions, exact prompts, mappings, completion
   handling and total budgets. The [live adapter smoke](../action-backends/README.md)
   establishes transport and output extraction only.
3. Include non-model controls with an honest input contract. Constant-action
   controls expose class imbalance but do not understand rules. A manually
   resolved graph plus executor is an assisted condition. A reusable text parser
   must disclose its supported language and failures; no per-item answer lookup.
4. Only if a concrete error pattern warrants it, design a decomposition arm.
   Compare access to intermediate information symmetrically. If Qwen compiles
   rules used by Jev, describe a hybrid pipeline and charge the compiler to it.
   Do not call a frozen substitute for LDPC's trained entailment module an exact
   LDPC reproduction. Name the adaptation and its deviations.
5. A later confirmation set needs new reviewed material, planned changed and
   invariant controls, and a contamination strategy. It is a separate study;
   the current public training slice cannot become an untouched test afterward.

For every pipeline, report compilation, relevance, fact extraction, execution,
verification and retries separately. Report both total cost without reuse and
any amortized cost with an explicit reuse count. Share preprocessing only where
the inputs are genuinely identical. Treat model probabilities, generated sample
frequencies and logical validity as different quantities.

These are design obligations, not a newly frozen executable run. No predictions
on the queued ShARC items are authorized by this document. Existing user API
authorization remains valid subject to the research gates already adopted.

## Remaining uncertainty and next decision

- The thesis method check establishes substantial single-condition overlap.
  The complete ACM paper and released-example construction still need comparison
  before claiming a narrower distinction or an exact reproduction.
- Establish implementation availability and exact components before promising
  a reproduced LDPC baseline. Do not install an old environment merely to claim
  reuse; choose reproduction or an explicitly named adaptation for a reason.
- Human reviews, final eligible pairs and task-specific inference budgets remain
  incomplete. Interface success is not evidence that those gates have passed.

See the [task card](TASK_CARD.md), [review protocol](SHARC_REVIEW_PROTOCOL.md)
and [current novelty matrix](../../NOVELTY_MATRIX.md).
