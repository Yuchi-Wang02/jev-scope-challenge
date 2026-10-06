# A Valid Answer Is Not a Verified Decision

## A stage report from Jev Scope Challenge

Status: exploratory technical report, 2026-10-05 America/New_York. This report includes the completed Sonnet supplementary arm and a retrospective confidence-boundary recheck. It is not a submitted paper, a new benchmark, or a validated method. The linked study reports retain their original protocols, amendments, outputs and limitations.

**Question.** Can existing models become reliable software decision components through inference algorithms and program design, without updating their weights? What, if anything, requires a dedicated decision model?

**Current answer.** The series establishes several narrow configuration and interface boundaries. It has not established a general replacement advantage for ordinary small models, the necessity of dedicated training, or a new intervention that transfers beyond inspected language. Some program checks help substantially on restricted grammars; other decompositions add work without improving decisions. Stronger ordinary-model and program controls constrain how broadly the model failures can be interpreted.

**What is useful now.** A record of supported and unsupported decisions, successful controls, failed interventions, measurement defects and stopped candidates. The contribution currently lies in inspectable diagnostics and reproducibility. Scientific novelty and deployment value remain unproven.

The [interactive decision replay](https://yuchi-wang02.github.io/jev-scope-challenge/decision_boundary.html) compares the saved Jev, Qwen and Sonnet direction decisions across all 108 inputs and both mappings. It performs no inference and retains strict-format failures. The [standalone HTML](docs/decision_boundary.html) also opens offline; the [release review record](RELEASE_CANDIDATE.md) preserves preparation checks and limits.

## 1. The question changed as the evidence accumulated

The initial cancellation challenge asked whether a frozen 4B model could match Jev on twelve constructed scope cases. Jev passed all twelve complete cases; the chosen Qwen readout passed eight, while a parser tailored to the construction also passed twelve. That result did not justify the intended ordinary-model replacement story. [Original results](results/REPORT.md).

The next studies separated pretrained backbone, existing upstream Kev adaptation, readout, layout, missing evidence, fact extraction and execution. The main scientific obligation became more specific: determine whether a proposed gain comes from the model, added program knowledge, a different interface, additional computation, or assumptions embedded in the dataset.

The later payment and public-policy work introduced source records and human review. They exposed another obligation: source labels and program references can be conditional on an interpretation that the visible input does not uniquely establish. More inference does not resolve that reference problem. The latest strong-model arm then narrowed a shared logical failure to the configurations actually tested.

## 2. Five findings that survive the present review

These rows describe different datasets and units. Do not pool their denominators into one accuracy, significance test or sample count.

| Finding | Evidence | Practical limit |
|---|---|---|
| Correct execution can consume incorrect facts. | Historical Kev-LoRA N1 facts plus code scored 44/72 versus 31/72 direct, while asserting values for 14/18 missing target fields. Complete fact vectors were correct on 33/72 inputs. | Twelve familiar development parents, repeated views and program references. More correct actions do not establish faithful extraction. |
| Explicit object attribution helps one restricted composition. | On 24 target-switch pairs, the same saved joint routes went from 2/24 complete pairs to 23/24 after a visible-ID gate; wrong commitments on 12 uncertain views fell from 7 to 0. | Known-grammar code solved 24/24. Direct input filtering retained only 2/24 complete pairs. This is neither a general filtering benefit nor a new extraction algorithm. |
| The payment interference hypothesis did not materialize in the main grid. | Jev matched all 48 original references in each full/related-record and option-order condition; grammar code also scored 48/48. | Twenty-four product-reference inputs have an unresolved candidate-scope objection. The explicit-ID subset is 24/24 per condition. No main reference required `NOT_ESTABLISHED`. |
| Additional condition calls did not produce a stable source-agreement gain. | On the QA4PC stage cohort, Jev graph-direct scored 20/24 in both mappings; facts plus code scored 19/24 and 20/24. Qwen graph-direct scored 14/24 and 16/24; facts plus code scored 12/24 and 14/24. | Facts plus code used 2.33 times as many calls. These are source labels on twelve trees, with no new human adjudication; graph assistance and mapping effects matter. |
| The shared direction signature was configuration-bounded. | Jev and short nonthinking Qwen each scored 84/108 in both mappings. Sonnet 5.5 scored 107/108 and 108/108 on unchanged Qwen prompts: 215/216 strict repeated main decisions, with one invalid format and no valid wrong labels. | Different model, native wrapper and inference configuration. Twelve vocabulary families reuse three logical patterns. No matched-cost or mechanism claim. |

Sources: [facts and execution](research/fact-execution/RESULTS.md), [target ownership](research/request-ownership/RESULTS.md), [payment and amendment](research/payment-ownership/RESULTS_V02.md), [QA4PC stage attribution](research/qa4pc-stage-attribution/CONTINUATION_RESULTS.md), [original direction study](research/rule-direction/RESULTS.md), [capable-reference closeout](research/rule-direction/capable-reference/RESULTS.md).

### Extraction quality, action quality and refusal quality differ

The whole-state fact pipeline is not a validated success merely because 44/72 exceeds 31/72. Eleven correct N1 actions arose from incorrect fact vectors. The deterministic executor checks its finite truth tables; it does not establish that a model attached the right statement to the right request.

The line-evidence intervention reduced false commitments from 14/24 to 6/24, but correct determined decisions fell from 34/48 to 11/48, with total correctness falling from 44/72 to 29/72. Joint routing then reached 34/72 but failed both its prewritten safety and determined-accuracy conditions. These are retained failures, not intermediate versions to omit from a success narrative. [Line results](research/fact-execution/LINE_EVIDENCE_RESULTS.md), [joint results](research/fact-execution/JOINT_RESULTS.md).

The later ownership gate demonstrates a useful local engineering check. Its scope is explicit IDs and supported sentence shapes. It reuses saved model outputs, so it does not demonstrate the runtime or transfer performance of a newly executed retrieval system. Direct filtering produced four corrections and three regressions; deleting foreign records did not generally repair direct judgment.

### The strong reference corrects the interpretation, not the historical record

The Sonnet arm retained all 84 previously correct controls per mapping and resolved 23/24 and 24/24 old shared errors. One final response explained the underdetermination and then wrote `maybe`; the frozen exact-label contract rejected the explanation. Its loss remains in the 215/216 score. The old errors are still genuine observations under their declared references, but they are not evidence that a capable ordinary model shares the same boundary.

All 222 supplementary requests completed without retries. Returned usage was 58,288 input and 1,277 output tokens, yielding $0.129346 at the frozen standard prices, not an invoice. Adaptive/high was requested; four responses contained thinking blocks. Do not attribute the difference to reasoning alone or describe the output cap as actual computation. [Full costs and raw evidence](research/rule-direction/capable-reference/RESULTS.md#execution-and-resource-use).

## 3. Evidence corrections that change what can be claimed

**High reported confidence did not produce a zero-error subset at 0.99.** A supplied external retrospective draft converted binary floating-point confidence to an exact fraction. That excluded records displayed as exactly 0.99 from a nominal inclusive threshold. For the historical 216 main Jev direction decisions, the draft calculation retained 128 decisions with zero errors. Comparing the preserved decimal values correctly retains **173 decisions with 9 errors**. The exact-0.99 group contains 45 decisions and all nine additional errors. [Offline recheck and source hashes](research/series-closeout/confidence_report.json), [reproduction code](research/series-closeout/confidence_recheck.py).

This is a post hoc arithmetic correction on saved outputs. It is not threshold calibration, a new model run, a certified deployment error rate or a reason to select a different threshold after seeing errors. It does not alter the original 84/108 scores. The rest of the supplied retrospective patch, including statistical tests, is not incorporated by this correction.

**Conditional reviewer agreement is not adjudicated truth.** Two reviewers each returned the same 96 payment review items. Their decision labels agree under a displayed-candidate reading, but their ambiguity fields agree on only 48/96 items; a cover note also identifies the scope problem. The 48 affected review items represent 24 product-reference inputs. No reviewer-endorsed adjudication or reference revision has been completed. [Review disposition](research/payment-ownership/REVIEW_DISPOSITION.md).

**Public-source agreement is a separate metric from supported inference.** Source audits retain title-only rules, missing prerequisites and provisional label concerns without silently rewriting original scores. Composition checks, consensus and strict output validity cannot independently validate source semantics. [ShARC source review](research/source-label-screen/SOURCE_REVIEW.md), [QA4PC semantic audit](research/qa4pc-answer-interface/SOURCE_AUDIT.md).

**A weak baseline setting does not measure a model's ceiling.** Historical native readouts, nonthinking 32-token output, cap-truncated reasoning, exact ties and alternate label mappings must remain named configurations. The new Sonnet result supplies one missing capability reference for rule direction only; it does not repair the comparator or label limitations in other studies.

## 4. Closed, parked and unresolved work

| Branch | Current decision | What would justify further scientific work |
|---|---|---|
| Original cancellation and finite ownership grammars | Keep as diagnostics; no replacement or method claim. | A naturally motivated decision boundary with a serious code baseline and new language evidence. |
| Payment ownership | Original near-pass stop remains in force. | Resolve interpretation if revising labels; do not manufacture interference by escalating difficulty. |
| Rule direction | Close both original grid and single capable-reference supplement; retire as the current main paper candidate. | Independent evidence of a different substantive question, rather than additional versions of the same template. |
| Relation-loss candidate | Bounded source screen found insufficient evidence for the proposed mechanism. | A real implementation that loses a needed relation, rather than intentionally discarding a structure the system already keeps. |
| Retry versus additional intent | Park expansion. Jev matched 96/96 clear-authorization and 24/24 explicit-deferral decisions; 2/24 ambiguous-reference matches are not validated errors. | Independently interpretable natural contrasts and a source-native unresolved decision. The screened twelve-pair cohort is not ready for a model comparison. |
| ToolTalk and AgentAbstain defects | Retain as separate software maintenance findings and local repairs. | Appropriate upstream discussion and broader reproduction if pursued; they currently establish no aggregate benchmark-score impact or model failure rate. |

Sources: [relation-loss screen](research/topic-screen-2026-10-05/README.md), [retry results](research/intent-retry-pilot/RESULTS.md), [source-screen decision](research/intent-retry-pilot/SOURCE_SCREEN_DECISION.md), [twelve-pair screen](research/intent-retry-pilot/cohort-screen/README.md), [ToolTalk checker](research/intent-retry-pilot/TOOLTALK_CHECKER_AUDIT.md), [AgentAbstain reproduction and repair](research/intent-retry-pilot/cohort-screen/atomicity-repro/README.md).

The twelve-pair source screen yielded seven provisional controls, two pending contracts, three exclusions and no accepted substantive research item. These are suitability decisions for our proposed experiment, not a prevalence estimate. The AgentAbstain atomicity work uses one fixture and includes 32 local tool calls across preserved attempts and repairs, with zero model calls. A failed simulated update changed state before validation; the local correction validates before writing. This does not show how often an actual agent would trigger it.

## 5. What remains necessary for a paper

The original long-term goal remains open. A collection of diagnostics does not become a methods paper by adding a router, and a successful stronger-model comparison does not supply a new mechanism.

A future investment should answer one decision-relevant question: **after ordinary code and legitimate evidence acquisition have been supplied, what unresolved language decision benefits from a learned component, at what cost and with what residual errors?** Existing work on cascades, clarification, entity binding, abstention and verification already covers broad versions of this proposal. The [novelty matrix](NOVELTY_MATRIX.md) and [bounded implementation screen](research/topic-screen-2026-10-05/EVIDENCE.md) record this overlap; they are not proof that no valuable question remains.

Before another main study, require all three:

1. **A motivated task.** Preserve complete source records, visible information and action consequences. Demonstrate what code can solve once interpretation is supplied, and isolate what remains unresolved without supplying evaluator-private answers to the system.
2. **An interpretable evaluation.** Independent labels or explicit finite semantics appropriate to the claim; reviewed ambiguity and source scope; parent/task-family separation for new confirmation data; all invalids, refusals and stopped attempts retained.
3. **A comparison that can change our decision.** Direct code, cheap-model and capable ordinary-model arms with symmetric information and assistance, explicit compute/cost accounting, and a prewritten stop if the problem is already solved or the proposed intervention adds no value.

These are entry requirements, not an approved hidden queue of new experiments. No fresh task or novel method has passed them yet. For now, the useful public artifact is this qualified technical report with its reproducible cases. Publication acceptance, external attention and repository stars cannot be inferred from the amount of work completed.

## 6. Reuse, reproducibility and release state

Kev's pinned model module and trained adapter/head were reused and credited; no new training here means frozen weights during our runs, not absence of prior adaptation. Laya was inspected as related work; its model, code, dataset and scores were not incorporated into these experiments. Source/code inspection and local clones are distinct from a GitHub fork. Repository metadata checked during release preparation recorded no fork relationship; this consolidation creates none. [Detailed attribution](THIRD_PARTY_NOTICES.md).

ToolTalk MIT code and AgentAbstain MIT runtime / CC BY 4.0 data are separately identified in their study notices. Root licensing does not relicense third-party data. The supplied Claude retrospective is review input, not an automatically accepted patch. Reviewer disclosures, derivative-data terms and any new public release require their own documented disposition.

Original runs remain authoritative within their scope. The current synthesis and publication do not establish independent replication, human validation or paper submission. Publication scope and verification limits are recorded in the [release notes](RELEASE_NOTES.md). The last Sonnet run and this offline consolidation are separate stages; this consolidation adds **zero model calls**.

Start with the [research index](RESEARCH_INDEX.md), [claim ledger](RESEARCH_CLAIMS.md) and [reproduction guide](REPRODUCIBILITY.md) for individual study commands. New closeout checks, from the repository root:

```powershell
python -B research/rule-direction/capable-reference/prepare.py verify
python -B research/rule-direction/capable-reference/analyze.py verify
python -B research/series-closeout/confidence_recheck.py verify
python -B -m unittest discover -s research/series-closeout -p test_confidence_recheck.py -v
python -B verify_publication.py
```

These are offline evidence/software checks. Passing them verifies specific preservation and calculation properties; it does not establish semantic truth, research novelty or readiness for a main-conference paper.

The default confidence check reconstructs the analysis from repository records and retains the external review's saved hashes as prior provenance. It explicitly reports that the private review archive was not reopened. Supplying `--reference-zip` with that archive's path additionally rechecks the archive and recorded members. Reproducing the scientific counts does not require distributing the supplied review documents.
