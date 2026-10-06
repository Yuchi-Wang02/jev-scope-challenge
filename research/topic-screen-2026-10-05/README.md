# Topic screen: does a real interface discard decision-relevant relations?

**Decision: INSUFFICIENT EVIDENCE — do not enter a model pilot.** No inspected implementation and source case jointly establish the hypothesized relation loss. The nearest work also covers much of the proposed solution space. This completes the bounded screen; it does not disprove the hypothesis.

Screen date: 2026-10-05 (client date; retrieval times are recorded in UTC). Repository base: `022950f6dd6c6b1f9d1758293b8a9ba8f3fafeda`. [Scope](screen_spec.json), [evidence and interfaces](EVIDENCE.md), [six-case review](CASES.md).

## Question and strongest objection

Can an intermediate representation erase relations between otherwise correctly extracted fields, causing a correct downstream checker to approve a wrong action or request unnecessary clarification?

The strongest objection is **that we would manufacture the bottleneck by discarding structure that the real system already keeps**. Full candidate objects, identifier joins, and ordinary policy predicates may solve the proposed task. A deliberately flattened representation losing information is an elementary observation; it is not, by itself, a new end-to-end method or a realistic failure finding.

## What the screen established

| Evidence | Consequence |
|---|---|
| The existing QA4PC fact pipeline compresses full-context model judgments into separate yes/no/maybe labels before a Strong Kleene executor. | A real compression boundary exists. We have not shown that cross-condition dependence caused its errors, and replacing its stipulated semantics would change the task. |
| The pinned EntityBindingFailures runner gives the model complete candidate entities and requests a binding map. Its provenance gate is mainly a prompt condition; its evaluator scores returned IDs. | It does not demonstrate the proposed factorization loss. A prose request for provenance also does not constitute an independently enforced action certificate. |
| Six fixed tau2 source tasks retain relational records. Retail exchange code already checks old/new variants pairwise. Airline tools leave important policy checks to the agent. | Ordinary joins, filtering, and missing policy enforcement must be separated from representation loss. None is automatically a new research contribution. |
| The first three retail tasks share one user and database context. One reference action points to a missing product. One airline task contains competing target cues. | These are six source tasks across four user contexts, not six independent samples or six clean gold test questions. |
| Six nearest papers already address binding, provenance, uncertainty-aware clarification, sufficient information, and semantic verification. | A broad “extract, check, clarify” proposal has substantial overlap. No defensible residual novelty was demonstrated here. |

These are source/code observations and AI analyst judgments. There are **zero new model calls, zero model-weight downloads, and zero independent human reviews**. Two paper-only traces check a controlled relation change and removal of irrelevant records. The controlled change is explicitly synthetic. Neither is a captured agent trajectory or a model-performance result.

## Decision boundaries

| Option | Decision |
|---|---|
| New relation-preserving method pilot | **INSUFFICIENT EVIDENCE.** Actual relation-loss witness, distinct contribution and strong-baseline feasibility are not established. No pilot is prepared or run. |
| Reproduction of a nearest paper | Not started. Could be a separate engineering project, but would need an explicit reproducibility question and would not resolve novelty by itself. |
| Engineering note about interfaces and evidence | Worth retaining in this repository as a transparent selection record. No publication was performed in this stage. |
| Broad claim that relation loss is unimportant | **INSUFFICIENT EVIDENCE.** This screen is too small and narrow for that claim. |

Reopen the investment decision only with a concrete, independently motivated interface that cannot express a needed relation, natural cases in both task families, a defensible difference from prior work, and a feasible strong-baseline plan. A pilot would then test whether an error occurs and survives fair controls; **observed model failure is not a prerequisite for this zero-inference screen**. Do not manufacture the interface defect by deleting existing structure. This stage does not automatically search additional sources or pivot to another topic.

## Deliverables and verification

The [case packet](case_packet.json) preserves original task/record objects and the known missing reference. Original policies and the [MIT notice](TAU_LICENSE) accompany it. [Paper traces](paper_traces.json) keep the synthetic change separate. [Sources](sources.json) record versions/hashes; the [resource snapshot](resource_snapshot.json) checks availability only. The [completion audit](COMPLETION_AUDIT.md) maps the original plan to evidence and lists unresolved retrospective repairs.

Run the offline integrity check from the repository root:

```bash
python research/topic-screen-2026-10-05/verify_screen.py
```

For exact comparison with the downloaded pinned sources, also pass `--source-dir .local/topic-screen-2026-10-05`. See [verification record](verification.json) for what was actually checked. Integrity checks do not validate natural-language labels, scientific novelty, or independence.

Only this new directory was added. Earlier experiments, the Claude retrospective patch, historical results, and public navigation were not changed. No commit, push, fork, release, or API experiment was performed.

Completion-audit correction: the first draft said STOP and used a preference contrast for trace 1. The final draft uses the plan's insufficient-evidence category and an explicitly controlled relation contrast. Original source tasks were not altered.
