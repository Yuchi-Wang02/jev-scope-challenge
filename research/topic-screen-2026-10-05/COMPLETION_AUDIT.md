# Completion audit against the accepted topic-screen plan

Authority: the accepted plan in conversation turn `01a10a34-0cd4-79b3-88f1-e5c87568d82d`, titled “下一阶段计划：先判断题目是否值得做，再投入实验”. Its success criterion permits selecting zero candidates and expressly prohibits automatic expansion, inference, publication or applying the retrospective patch during this screen. The subsequent instruction to continue executing the plan does not remove those limits.

Previous goal turn classification: **progress** — it created the source-preserving packet, inspected actual implementations, and produced a decision. This completion audit found and repaired two substantive gaps: trace 1 originally varied a preference rather than a relation; the STOP label and reopening requirement overstated what a zero-inference screen established. The final decision is **INSUFFICIENT EVIDENCE; no pilot**. These corrections do not alter original source objects or historical experiments.

## Requirement-to-evidence mapping

| Original requirement | Evidence inspected | Completion / boundary |
|---|---|---|
| At most two concentrated days; six primary papers, two research chains, six complete source cases | [Scope](screen_spec.json), [source ledger](sources.json), [evidence table](EVIDENCE.md) | Within the work limit and fixed source counts; no second literature search round or extra candidate |
| Per-paper question, method, assumptions, evaluation material, remaining boundary, overlap and evidence kind | Six method/boundary rows plus evaluation/provenance table in [EVIDENCE](EVIDENCE.md) | Recorded; author-reported experiments remain unreplicated |
| QA4PC and EntityBindingFailures: input → intermediate representation → checker → outcome | Pinned source line links and input/output boundary tables in [EVIDENCE](EVIDENCE.md) | Inspected actual source; no upstream code execution. No real business action is dispatched by the inspected entity evaluation runner |
| Algorithm-level PACT/SAGE comparison; do not invent official implementations | Paper-method rows and explicit “implementation not audited” status | Completed within the two-chain cap |
| Source eligibility, stable selection, no outcome-based cherry-picking or replacement | [Scope](screen_spec.json), all six [case cards](CASES.md), preserved source objects | IDs 0–2 in each family all retained for inspection. Each has linked objects/attributes and inspectable private/evaluator/public layers. Ambiguity and a broken reference remain disclosed; eligibility for source inspection is not pilot eligibility |
| Complete requests, rules, tool definitions, relevant records and reference conditions | [Packet](case_packet.json), original policies, pinned tool-source URLs in [EVIDENCE](EVIDENCE.md) | Exact six task objects and 58 related objects compared to cache; no source rewriting. Tool definitions are referenced, not republished as new code |
| Each case: user goal, relation, direct program sufficiency and remaining language step | [Case cards](CASES.md) | Present for all six; simulator-private intent is never treated as an observed agent message |
| Up to two paper diagnostics: relation change and irrelevant-content invariance | [Trace specification](paper_traces.json), two walkthroughs in [CASES](CASES.md), [verifier](verify_screen.py) | Relation trace explicitly exchanges two variant-availability bindings on a copy; invariance trace removes unrelated reservations after target resolution. Both preserve the actual full-object representation and are marked conditional analyst calculations |
| Separate controlled edits from source cases; enumerate edits | JSON operation paths and before/after values; original-packet hashes | Exactly two changed leaves; original source packet unchanged. No new independently sampled parent case is claimed |
| Read-only stronger ordinary-model / existing-method / direct-code feasibility | [Resource snapshot](resource_snapshot.json), paper/code interface findings | Existing local 4B files and GPU inspected; stronger-model access/cost/runtime unknown. No loading or inference. Deterministic filters/joins are feasible for formalized subproblems, not a claimed language understanding solution |
| Explicit go/no-go decision and strongest objection | [Judgment](README.md) | Insufficient evidence; no 8–12-parent pilot design required because the gate did not pass. No claim of model failure is required for screen completion |
| AI adversarial review of six specified inference mistakes | Checklist below and revised wording in core reports | Completed as AI review, not independent human validation |
| Versions, licenses, citation provenance, English public-facing files and Chinese explanation | [Sources](sources.json), [MIT notice](TAU_LICENSE), core files and conversation response | Sources traceable; paper/external research code not incorporated. Historical Kev/Laya attribution is not recertified by this screen |
| Three compact core artifacts, no framework/API adapter/release | README, EVIDENCE, CASES and supporting JSON/source files | Three core reports plus a small offline preservation/trace verifier; no inference framework or new repository |
| Existing review repairs separately listed, not silently applied | Closeout list below; tracked Git diff inspected empty | Listed only. Original protocols, results, root navigation and Claude patch remain unchanged |

## AI adversarial review

- **Fields versus relations:** trace 1 holds the variant set and availability counts fixed but changes their binding. A full-object filter changes its answer; the interface is not claimed to lose that binding.
- **Checker correctness versus language fidelity:** the deterministic calculations assume target/preference interpretation. They do not validate the Google Home/Google Assistant mapping, private intent or a model extraction.
- **Predicate versus full authorization:** neither the chosen replacement item nor the cancellation predicate establishes user confirmation, payment authorization or completion of all action requirements.
- **Correct supplied structure versus end-to-end performance:** target-resolved subset comparisons are marked analyst diagnostics, not oracle retrieval performance or an improved agent.
- **Repeated cases versus independence:** six source tasks have four user contexts; the retail trio is shared context. No independence-based statistical claim is made.
- **No located distinction versus proven novelty:** bounded literature inspection supplies overlap evidence. It proves neither absence of all relevant work nor a new contribution. The decision remains insufficient evidence.

## Separate retrospective closeout list — not executed in this screen

These items come from the earlier external-review assessment. Listing them is not a fresh verification or a claim that the proposed patch is accepted:

1. Repair and boundary-test the proposed retrospective `>=0.99` comparison before using its selective-decision tables; preserve historical raw runs and explain the added analysis.
2. Distinguish same-case comparisons from byte-identical prompts, and document which assistance/settings differ.
3. Replace blanket claims about Kev's “native” format with the specific upstream wrappers and historical checkpoint/configuration actually inspected.
4. Retain exact-tie sensitivity as supplementary analysis; qualify clustering, exploratory tests and unsupported sample-size generalizations.
5. Resolve the patch's missing audit-document dependency and check current index/status/release links before integration. Historical frozen “not yet run” text is not a current-status page to rewrite.
6. Reconcile root-level project claims and the novelty matrix with the overall evidence before any new public release. Audit historical Kev/Laya attribution on its actual reuse paths; no new fork or reuse occurred here.

## Verification meaning

[verification.json](verification.json) records the executed offline checks. Its pass status covers preservation, hashes, selected source facts, two conditional computations and local link targets. It does not prove semantic labels, statistical independence, model performance, novel mechanism or publication readiness. Git inspection confirms that this new screen directory is the only untracked change and older tracked files are unchanged. No external publication state was changed.
