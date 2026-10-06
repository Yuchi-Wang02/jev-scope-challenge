# Again is not always a retry

**Status: fixed exploratory Jev arm completed; clear scope cases passed, ambiguous-reference interpretation unresolved.** [Read the result](RESULTS.md). All 96 clear-authorization decisions and 24 explicit-deferral decisions matched provisional references. Only 2/24 ambiguous-reference decisions matched, but those labels were flagged before inference and remain unvalidated. The ordinary capable-model arm has not run. This candidate follows the earlier relation-loss screen; it does not reinterpret that screen.

**Source-screen follow-up: expansion of this candidate is parked.** The bounded incident, dialogue and task-source inspection did not provide a directly reusable natural retry/new-intent contrast. A separate ToolTalk recipient-check defect was isolated and a local repair prepared. [Current decision and next experiment design](SOURCE_SCREEN_DECISION.md). These are source and software findings, not additional model results.

**Integration follow-up completed:** [one AgentAbstain sandbox pair](integration/README.md) now has actual read/verify/profile observations, separate visible/private packets and authored program gates. Six task-tool attempts, one expected error, zero cancellations and zero model calls. This control distinguishes trusting a verification flag from checking observed identity fields; it does not establish a model benefit or original-task completion.

**Twelve-pair cohort screen completed:** [the fixed selection](cohort-screen/README.md) yielded seven provisional controls, two pending contracts and three exclusions, with no substantive item currently accepted for the proposed comparison. No new model grid ran. A separately declared [software counterexample](cohort-screen/atomicity-repro/README.md) shows a failed profile update changing simulated state while the isolated native commit check passes; original and corrected-encoding attempts are both retained. This is a bounded maintenance finding, not a new model failure or paper claim.

Working research question: **Can a conversational agent distinguish recovery of one intended operation from a genuinely additional operation with identical tool arguments, without excessive clarification?**

## Why investigate this seam?

After an unconfirmed purchase, “finish that purchase; I want only one” and “complete that purchase and place an additional identical purchase; I want two in total” can require the same tool and payload but different logical operation identities. A deterministic idempotency layer can enforce identities correctly and still execute the wrong number of intended operations if its caller assigns the wrong identities.

This distinction is established distributed-systems engineering, not our invention. The empirical candidate is the **dialogue-to-operation-identity boundary**, with both duplicate execution and suppression of legitimate repetition measured. Whether this is difficult for current models, common in natural use, or insufficiently covered by prior benchmarks remains to be established.

## Candidate comparison

| Candidate | Attractive question | Current assessment |
|---|---|---|
| Stale evidence before an action | Does an agent act on an earlier state after the world changes? | Direct overlap with TOCTOU-Bench and STALE. Keep as a future extension, not another generic stale-state benchmark. |
| Operation identity from dialogue | Does “again” mean recovering one operation, authorizing another, or needing clarification? | Selected for the completed pilot; clear cases passed. Subsequent source screening did not justify expansion. Novelty remains unestablished. |
| Verify, ask, or execute | When does extra checking help enough to justify its cost? | Useful evaluation axis within the chosen pilot; broad standalone framing overlaps existing clarification and memory-commitment work. |

See [source inspection](SOURCES.md) for primary sources, pinned implementations, and close precedents from Cordon and Irrevon. Irrevon's design already measures false suppression as well as duplicates; those metrics are not our contribution. This comparison is an analyst judgment, not an exhaustive literature review.

## What would be a contribution?

1. A reproducible measurement finding about dialogue-based operation-boundary inference, surviving strong baselines and fresh human-authored cases. Measuring duplicates and suppressed legitimate operations is necessary but already covered in prior designs.
2. If warranted by a future finding, evidence for a separately specified treatment improving the error/cost frontier on held-out material. Explicit linking is already this pilot's task and cannot serve as its own intervention.
3. If simple code or capable ordinary models solve the task, a concise boundary/reproduction note and reusable test cases. No forced method claim.

The composition “classify intent, then use idempotency keys” is engineering until comparative evidence establishes more. Transport retries with known stable IDs belong to deterministic code. We do not replace that code with a model.

## Completed here

- Inspected two upstream implementations at pinned revisions; read the nearest papers and engineering contracts.
- Prepared and froze a bounded [measurement protocol](PROTOCOL.md), 72 exploratory inputs and 147 Jev requests, including falsifiers and future capable-model/held-out requirements.
- Implemented an original offline simulator with nine illustrative, synthetic, **unreviewed** dialogue seeds and paired hidden commit states.
- Saved visible inputs separately from evaluator references. No upstream code or dataset is incorporated into the simulator; no repository was forked.
- Ran 3 real smoke checks and 144 fixed Jev scientific decisions. All outputs, returned usage and attempt records are saved; 0 retries or failures. Independent human reviews remain at zero for this new material.
- Rechecked actual Irrevon fixtures/code and ACRFence's proposed analyzer; see [prior-art audit](PRIOR_ART_CHECK.md).
- Screened four public incident reports, 200 BFCL and 50 ToolTalk conversations, and four AgentAbstain pairs. Detailed provenance and exclusions are linked in the [source-screen decision](SOURCE_SCREEN_DECISION.md).
- Reproduced a pinned ToolTalk receiver-check defect in five isolated software cases with explicitly controlled message similarity; prepared a one-line local patch and inspected its standard caller path. The unchanged source file and Microsoft MIT notice are retained under `audit_sources/`. This source is used only by the checker reproduction, not the independent operation simulator. No upstream contribution has been submitted.

Run from the repository root:

```bash
python research/intent-retry-pilot/demo.py
```

The generated `demo_results.json` verifies simulator invariants and documents deliberately simplistic control policies. **These are not model results, independent human labels, empirical failure rates, or evidence of scientific novelty.** The examples are deliberately easy to expose the measurement contract before testing natural language.

## Next decision

Do not tune a new method on this pilot: the clear cases did not expose the hypothesized problem. Preserve the result and park expansion after the bounded source search. Reopening this candidate requires new interpretation and ecological evidence. Reviewer inputs and a blank response structure remain under `data/`; reused exploratory examples cannot become a fresh confirmation set.

The [proposed source-native comparison](SOURCE_SCREEN_DECISION.md) asked what a model gate adds beyond ordinary code and further observations. Its [single-pair integration](integration/README.md) is completed and handled by the authored program; its [twelve-pair feasibility screen](cohort-screen/README.md) did not produce a ready scientific cohort. Do not launch that grid or silently replace excluded tasks. A separate [capable ordinary-model supplement](../rule-direction/capable-reference/RESULTS.md) on the existing rule-direction material is now complete: 222 Sonnet 5.5 requests, strict main scores of 107/108 and 108/108, one invalid format, no valid wrong labels and no retries. It narrows that historical shared-deficit finding; it does not supply the missing ordinary-model arm for this intent-retry pilot. Defensible task outcomes and comparative evidence remain prerequisites for broader claims.

This directory is local work. It does not update GitHub, publish a dataset, correct earlier retrospective issues, or establish any new result about Jev, Kev, or Laya.
