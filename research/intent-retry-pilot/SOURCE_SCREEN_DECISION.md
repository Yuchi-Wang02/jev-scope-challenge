# Source screen decision and the next research investment

Date: 2026-10-05 local / 2026-10-06 UTC. This is a post-pilot research decision, not a preregistration or a new model result.

**Current follow-up:** the [Stage A integration](integration/README.md) and [fixed Stage B screen](cohort-screen/README.md) are now complete. The latter does not produce a ready comparison cohort (seven controls, two pending, three excluded). The design below records the proposal that led to those checks; it is not an instruction to proceed despite their no-go result. A separately declared software regression and bounded repair remain maintenance work.

## Decision

**Park expansion of the current retry-versus-additional-operation dataset.** Keep the completed Jev result, including its successes and unresolved labels. The bounded source search did not supply a directly reusable natural contrast. Do not add harder paraphrases simply to obtain failures.

**Finish the ToolTalk checker reproduction as a small maintenance contribution. Do not turn it into an unbounded benchmark-bug hunt.** It matters because our measurements must be correct, but discovering this defect does not answer whether a small decision model is useful.

**The next candidate should test the marginal value of a decision component inside a source-native workflow, after giving ordinary code a serious baseline.** This returns to the original research question. A wrong-recipient guard would be a transfer experiment related to the earlier payment-ownership work, not a newly invented problem. Its broader value must come from a measured quality/cost trade-off and independent tasks.

## What this screen actually did

| Material | Scope | Result for the current candidate |
|---|---|---|
| Public incident reports | Four reports plus their available discussion and one relevant merged fix | Lifecycle/recovery/dispatch problems dominate. No complete natural retry/new-intent pair found in this screen. |
| BFCL multi-turn base | 200 conversations, 734 user turns, references and selected implementations | Useful source-native workflows; no selected case directly establishes the present same-payload semantic contrast. |
| Microsoft ToolTalk hard | 50 conversations, 194 user turns, relevant APIs and evaluation code | Repeated notifications change payload; intentional login recovery changes password. Found and isolated a recipient-check defect. |
| AgentAbstain | Four pairs: initial two informational exclusions plus first operational S2/S6 pairs | S6 supports an integration packet, likely solved by an explicit verification rule. S2 needs save/send and ambiguity review. |
| A separately published human-interaction dataset | Public card and terms only | Terms exclude reuse for this evaluation without a separate agreement; no gated data acquired. |

These are convenience/source screens, not prevalence estimates. BFCL and Microsoft ToolTalk material is benchmark construction, not captured production interaction. No new model calls, independent human labels, full upstream runtime executions, upstream messages, forks or publications occurred in this source-screen stage.

Detailed records: [incidents](NATURAL_INCIDENT_SCREEN.md), [dialogue sources](DIALOGUE_SOURCE_SCREEN.md), [AgentAbstain feasibility](AGENTABSTAIN_FEASIBILITY.md), [isolated checker reproduction](TOOLTALK_CHECKER_AUDIT.md), [standard caller path](TOOLTALK_CALL_PATH.md).

## Concrete artifact, limited claim

The pinned ToolTalk sender checker compares the predicted receiver with itself. Five offline regression cases pass our stated expectations: two wrong-receiver cases are accepted by the original and rejected by the one-line correction; positive, session and dissimilarity controls retain their behavior. Message similarity is a controlled scalar dependency. This is a software counterexample, not model inference.

The standard scoring call path reaches this override and does not add an outer receiver-equality check. That is a static source conclusion; it is not a full runtime replay. The headline **“Wrong recipient, full credit?”** must be accompanied by that scope. There is no measured published-score impact.

The source is retained unchanged under its Microsoft MIT notice. The local patch is not an upstream contribution until separately submitted and accepted. Original sources, full upstream tests, real trajectories and exact dependency execution are distinct evidence levels.

Auditing evaluators is already established: [OSWorld-Verified](https://xlang.ai/blog/osworld-verified), [WebArena-Verified](https://github.com/ServiceNow/webarena-verified), and [AgentRewardBench](https://arxiv.org/html/2504.08942v1) directly limit any novelty claim. [BetterBench](https://arxiv.org/html/2411.12990v1) provides broader evaluation-quality guidance. A future cross-checker study would need independent implementations, positive/equivalence controls and actual replay impact; that expansion is not the recommended next investment here.

## Recommended next experiment: does a model gate earn its cost?

Research question:

> Given the same visible user request, chronological tool observations and proposed action, when does adding a cheap model gate improve safe task completion beyond deterministic checks, and when is an additional observation more useful than more model reasoning?

This is a proposed capability/cost study. Neither model critics, tool guards, evidence collection nor hybrid rule/model systems are new by themselves. No new method is claimed. The working public question could be **“Does your agent need another model, or one more check?”** It permits a result in favor of code, Jev, an ordinary model, or extra evidence.

### Stage A: one integration pair, not a scientific cohort

Use pinned AgentAbstain S6 `critical_tool_failure/preview_002` solely to establish visible/private boundaries and real sandbox observations. Preserve the paired task files and license. After dependency review, execute only reservation discovery and verification in the offline environment. Save before-discovery, after-discovery and after-verification prefixes. Do not obtain IDs from the evaluator's DAG. The first two paired prefixes should be indistinguishable; the last may differ by the actual verification result.

Compare a deterministic verification gate with no gate and never-commit controls before invoking a model. This pair's verification tool does not truly compare supplied identity details, so report a verification-success condition, not identity authentication. If code solves it, record that as a successful control. This pair does not become evidence of a new research contribution and does not count as six independent tasks.

### Stage B: a finite source-native capability screen

Only if the integration and scoring contract are sound, select at most 12 operational parent tasks across at least two workflow families, using a declared source ordering and eligibility rules before reading new model outputs. Parent-task source availability and environment feasibility still need checking; 12 eligible independent parents are not yet established.

Retain explicit machine-checkable gates as controls and include tasks requiring reference resolution or interpretation of visible evidence. Do not construct the latter by discarding relations the source system already retains. If source eligibility produces too few tasks, publish the shortfall instead of silently substituting hand-written hard cases. Record developer-authored perturbations separately from original task variants.

For each eligible task, preserve the user goal and inspectable final-state contract. Use opaque model-facing identifiers, an original visible prefix and a proposed call with documented origin. Scripted proposals are valid for conditional screening but are not real agent mistakes. Model-proposed calls require actual new proposer runs and their full cost. A future complete workflow experiment must resume execution after interventions; fixed-prefix accuracy cannot stand in for safe task completion.

Compare on identical visible inputs:

1. No additional gate and never-commit controls.
2. A reusable deterministic contract gate: types, IDs, explicit prerequisites, quantities and observed success states. Report authoring effort and task-specific rules; do not give code reference labels.
3. Code plus Jev, routed only when code returns unknown.
4. Code plus an ordinary small instruction model.
5. Code plus a capable ordinary-model critic.
6. Where a relevant read-only observation exists, acquire it under the same tool-access budget and reapply the same gate. An oracle-selected observation is only an assisted ceiling; a real selection policy must be evaluated separately.

Keep user clarification separate from automated abstention. A clarification policy needs user-response assumptions and interaction cost; defaulting to refusal is not successful completion. A runtime should block an unsupported write while permitting useful read-only discovery, when allowed by the task.

Provider/model identities, templates, available local resources, inference limits and budgets are not configured by this document. Existing authorization permits bounded Jev work; it does not supply another provider's credentials or make an absent strong-model arm complete. Freeze the exact runnable comparison before execution. Do not indefinitely add models if the task is already solved.

### Outcomes that change the research decision

Report unauthorized actions, valid actions lost, additional observations/clarifications, complete task outcomes, model/tool tokens, latency and total cost. For a 12-parent exploratory cohort, show counts and all cases; do not make a statistical equivalence claim. Prefixes, variants and repeated decisions are clustered within the parent task.

- If deterministic rules handle all eligible tasks correctly, close this candidate with a code-sufficiency result.
- If all model arms pass the unresolved semantic cases, retain a limited cost/latency comparison; do not increase difficulty until one fails.
- If errors survive the audited code baseline and differ across models in multiple independent parents, collect new independently reviewed tasks before intervention search or a model-replacement claim.
- If extra tool evidence resolves the problem but more reasoning does not, investigate evidence-acquisition policy on new tasks. Do not claim that this pattern is already observed.
- If labels, scorer semantics or task interpretation disagree, preserve raw outputs and repair the measurement boundary before scoring those cases.

The ultimate paper-level target remains a **transferable quality/cost boundary for reliable decision components**. A useful future mechanism might route between code, a small model, an observation and a stronger model. Whether that routing adds anything beyond existing cascades is a separate prior-art and held-out experiment question. This screen has not demonstrated it.

## Work status

Completed: bounded source inspection, pinned provenance, isolated ToolTalk regression reproduction, local repair patch, caller-path review, original-runtime Stage A integration, and the fixed twelve-pair Stage B source screen. Follow-up artifacts preserve the later software counterexample and execution boundaries.

Not completed for this source-native candidate: independently human-reviewed cohort, capable ordinary-model comparison, learned routing/intervention, full workflow comparison, upstream submission or public release. The intended model cohort is currently no-go on the screened selection. These are gaps, not implied results or commitments to expand.

A separate [rule-direction capability reference](../rule-direction/capable-reference/RESULTS.md) has since completed all 222 frozen Sonnet 5.5 requests. Its strict main scores are 107/108 and 108/108, with one invalid format and no valid wrong labels. That closeout narrows the earlier shared-error claim; it is not a model experiment on this screened cohort and does not reverse its no-go decision.
