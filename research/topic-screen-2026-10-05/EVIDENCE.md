# Nearest work, actual interfaces, and feasibility

This is a six-paper topic screen, not an exhaustive literature review. Paper descriptions below are attributed claims; their experiments were not reproduced. Implementation findings are limited to the two named research pipelines. Inspection of tau2 source data and tool definitions establishes the six cases' source semantics, not a third agent-method reproduction.

## Six fixed nearest papers

| Pinned primary source | Relevant contribution already present | Boundary and consequence for this proposal |
|---|---|---|
| [Entity Binding Failures, v1](https://arxiv.org/html/2606.30531v1) | Separates correct tool selection from correct entity binding; studies clarification and provenance-oriented prompts. | Section IV-C qualifies confidence gating as structured prompting. The inspected runner retains candidate objects and has no independent post-response provenance authorization check. An entity-binding challenge or “ask if ambiguous” rule alone is not our novelty. |
| [PACT, v1](https://arxiv.org/html/2605.11039v1) | Carries value provenance and checks argument-specific authority contracts before calls, under an indirect-prompt-injection threat model. | Formal guarantees depend on conservative provenance and correct contracts. Automatic inference is outside that guarantee. Semantic consistency among trusted values is a different question, but merely proposing a provenance checker overlaps directly. Paper method/limitations inspected; implementation not audited. |
| [Provenance Sensitivity, v1](https://arxiv.org/html/2607.20827v1) | Matched changes to textual authority cues while holding other task elements fixed; includes tau2 retail and airline materials. | Cue sensitivity is not automatically an action error. Controlled records and textual source markers do not establish deployed provenance or prevalence. A new matched source/target perturbation needs a contribution beyond another sensitivity test. Implementation not audited. |
| [SAGE-Agent, v2](https://arxiv.org/html/2511.08798v2) | Schema-grounded clarification using partial candidate calls and an information-value stopping rule. | Candidate calls retain assignments jointly; the weighting approximation does not itself erase the candidate structures. Its question-generation stage can see the query and history. A generic factorization accusation would misdescribe the inspected method. Implementation not audited. |
| [QuestBench, v2](https://arxiv.org/html/2503.22674v2) | Formalizes what missing information is sufficient for a goal; distinguishes ambiguity from underspecification and constructs question-selection tasks. | Primarily 1-sufficient tasks; it already defeats a broad claim that “only ask for decision-relevant information” is new. More complex joint relations could be a distinction, but a constructed distinction is not evidence of an unmet practical need. Implementation not audited. |
| [Instantiation-based Formalization of Logical Reasoning Tasks using Language Models and Logical Solvers, IJCAI 2025 paper 516](https://www.ijcai.org/proceedings/2025/0516.pdf) | Introduces Semantic Self-Verification (SSV): checks generated solver constraints with independently elicited positive/negative instantiations and well-formedness checks, with repair. | Section 4 explicitly allows mutually consistent but wrong programs/examples and missing constraints. Therefore solver success does not guarantee fidelity to natural language. A generic “verify the formalization” method would overlap. Implementation not audited. |

Evaluation materials and evidence provenance are explicit here to avoid treating author reports as our runs:

| Paper | Author evaluation materials inspected in the paper | Evidence used by this screen |
|---|---|---|
| Entity Binding Failures | Controlled enterprise-style tasks for email, calendar, documents, customer records and issues | Paper plus pinned prompt construction/evaluator code; no reproduced model score |
| PACT | Oracle-provenance diagnostic suites and AgentDojo deployments | Paper algorithm, deployment distinction and stated guarantee assumptions; no code audit |
| Provenance Sensitivity | Authored workflows, tau2-style tasks and BFCL examples | Paper interventions and labeling/visibility qualifications; no generated-action replication |
| SAGE-Agent | ClarifyBench with simulated multi-turn users; also When2Call training experiments | Paper candidate-call and question-selection algorithms; no simulator or training replication |
| QuestBench | Logic-Q, Planning-Q, GSM-Q and GSME-Q question-selection tasks | Paper constraint formulation, dataset construction and limited sufficiency setting |
| Instantiation-based Formalization / SSV | AR-LSAT, FOLIO, LogicalDeduction, PrOntoQA and ProofWriter | Paper method, tables and explicit shared-error limitations; dataset-correction qualifications retained |

Sections inspected cover the papers' problem definitions, relevant methods, evaluations and stated limitations, with targeted appendix inspection; no claim of exhaustive supplementary-material verification is made. The Hugging Face Markdown endpoint for the first paper returned 404, so the versioned arXiv primary source was used. Lack of an implementation audit does not imply lack of released code.

## Two implementation chains

**Chain A: this repository's QA4PC stage attribution.** Revision `022950f6dd6c6b1f9d1758293b8a9ba8f3fafeda`.

| Boundary | Actual source behavior | What it does and does not establish |
|---|---|---|
| Input to per-condition prediction | [plan.py lines 101–115](https://github.com/Yuchi-Wang02/jev-scope-challenge/blob/022950f6dd6c6b1f9d1758293b8a9ba8f3fafeda/research/qa4pc-stage-attribution/plan.py#L101-L115) supplies policy, question, scenario, condition graph, and selected condition ID. | Each leaf prediction sees the original context. It is incorrect to describe its model input as isolated, context-free fragments. |
| Predictions to executor | [analyze.py](https://github.com/Yuchi-Wang02/jev-scope-challenge/blob/022950f6dd6c6b1f9d1758293b8a9ba8f3fafeda/research/qa4pc-stage-attribution/analyze.py#L65-L86) maps each prediction to a fact label and calls the executor with those facts and the expression. | The downstream checker lacks the scenario and general joint-state constraints. This is a real information boundary, but no relation-loss causal attribution follows from it. |
| Execution | [audit.py lines 56–73](https://github.com/Yuchi-Wang02/jev-scope-challenge/blob/022950f6dd6c6b1f9d1758293b8a9ba8f3fafeda/research/qa4pc-audit/audit.py#L56-L73) implements Strong Kleene logic, rejecting missing variables. | Correct evaluation is conditional on supplied facts and stipulated semantics. Replacing the reference semantics with possible-world reasoning would need a separately justified task, not a claim that the current evaluator is broken. |

The current source code was read; no old model experiment was rerun. The reference-fact arm is assisted computation, not an end-to-end semantic solution. We have not demonstrated a pair of real source cases whose correct intermediate outputs coincide while their warranted downstream decisions differ.

**Chain B: EntityBindingFailures.** Revision `af311d10f52680576d83cdaf3d05d5b090445de4`; [runner](https://github.com/R-Suresh/EntityBindingFailures/blob/af311d10f52680576d83cdaf3d05d5b090445de4/code/run_entity_binding_experiment.py).

| Boundary | Actual source behavior | Fair interpretation |
|---|---|---|
| Task to prompt, lines 48–63 | All methods receive `task["entities"]`. Two methods filter the tool menu using `gold_tool`; required slot names come from `gold_bindings` keys. | Complete candidate entities remain visible. Oracle tool filtering and supplied slot names are external assistance and need equivalent controls in a comparison. This is not disclosure of the gold entity values. |
| Prompt to model response, lines 13–39 | Returns decision, tool, binding map, clarification question and provenance. Method differences are instruction strings; several arms force ACT, others allow clarification. | The schema can retain the full predicted binding combination. Allowed abstention differs, so raw accuracy alone is not a fair gate comparison. No separate retriever is implemented in this runner's `entity_retrieval` arm. |
| Response to score, lines 84–144 | Parses JSON and compares bindings to the hidden reference. Provenance is not used by `evaluate` to authorize an action. | This is an offline evaluation runner. It is not a business-action executor with an independently verified provenance certificate. The paper's prompting qualification matters. |

No upstream Python was executed or incorporated. Its code license is MIT; its [data license](https://github.com/R-Suresh/EntityBindingFailures/blob/af311d10f52680576d83cdaf3d05d5b090445de4/LICENSE-DATA.md) has separate terms. We copied neither its dataset nor its code into this research directory and created no fork. Future reuse must retain the applicable notice and describe the actual assistance and modifications.

## Source task/tool boundary

All case-source links use tau2 revision `5bfa7e37b36656b37dc6d022156be6563c1007f3`.

- [Retail exchange tool](https://github.com/sierra-research/tau2-bench/blob/5bfa7e37b36656b37dc6d022156be6563c1007f3/src/tau2/domains/retail/tools.py#L208-L284) pairs old/new IDs, checks the new variant within the old product, and checks availability. Complete product variants are already linked objects. Determining natural-language user preferences remains separate from these mechanical checks.
- [Airline cancellation](https://github.com/sierra-research/tau2-bench/blob/5bfa7e37b36656b37dc6d022156be6563c1007f3/src/tau2/domains/airline/tools.py#L339-L384) mutates the reservation without implementing all cancellation policy conditions. The policy explicitly places responsibility on the agent. This is missing policy enforcement, not proof that a representation discarded a relation.
- [Certificate issuance](https://github.com/sierra-research/tau2-bench/blob/5bfa7e37b36656b37dc6d022156be6563c1007f3/src/tau2/domains/airline/tools.py#L488-L514) accepts a user and amount. It does not establish which reservation warrants compensation.
- [Flight status lookup](https://github.com/sierra-research/tau2-bench/blob/5bfa7e37b36656b37dc6d022156be6563c1007f3/src/tau2/domains/airline/tools.py#L721-L735) returns a status string. The packet's entire flight database objects, including schedule fields, must not be mistaken for this tool response.

## Ordinary-model feasibility

A fresh [read-only inventory](resource_snapshot.json) inspected the four previously known cache roots, config metadata and file sizes. It found the same ten config/adapter entries, including complete index-declared Qwen3.5-4B shards and historical Qwen3-4B/Kev resources. The GPU reports RTX 5070 Ti, 16,303 MiB. No weight was loaded or rehashed, and no runtime was certified anew. Previous loading and generation are documented in the [historical smoke report](../baseline-readiness/QWEN35_SMOKE_RESULTS.md).

No 8B-or-larger general instruction checkpoint was found in these four locations. This is not an exhaustive machine search. Hosted stronger-model access was not probed and no credentials were read. A stronger baseline is therefore **not established**, rather than impossible. A future authorized pilot would need a precisely identified capable ordinary model, full original evidence, a declared reasoning budget, and all truncations/costs retained. Merely running the available 4B configuration again cannot establish a capability ceiling. Current evidence does not justify entering a pilot; no larger model is acquired by this screen.

## Attribution and outstanding retrospective work

The six task objects, selected raw database objects and two policies are derived from Sierra Research's tau2-bench under its included MIT notice. Original source objects are preserved; the subset, visibility metadata and analyst comments are our additions. No new dataset license is imposed on those original objects. Paper prose is summarized and linked; full paper copies and external research code stay in the ignored local inspection cache.

This screen neither forks nor extends Kev or Laya. Historical use elsewhere in the repository must continue to be described in the existing project attribution; this statement does not certify every older file's licensing or claims. The Claude retrospective patch remains unapplied. Corrections to historical confidence-boundary accounting, current navigation/status, and retrospective claims belong in a separately scoped closeout. This screen does not silently revise frozen protocols or certify that all earlier audit issues have been repaired.
