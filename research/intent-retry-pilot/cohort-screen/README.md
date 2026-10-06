# Twelve source pairs: cohort decision

**Decision: do not launch the proposed model-comparison cohort from this selection.** The fixed screen yielded seven provisional controls, two pairs requiring task/outcome-contract resolution, and three exclusions from an unchanged full-workflow comparison. None is currently accepted as a substantive research item. This is a suitability judgment for our proposed experiment, not a benchmark defect rate or proof that ordinary code solves arbitrary language instructions.

The [selection](selection.json) was saved before inspecting these twelve task bodies. It takes the first four operational pair IDs in each of three declared categories at dataset revision `842228426c2a703347396501af61c7890972c7ee`. No pair was replaced. These are source-generated benchmark tasks, not production incidents. The source IDs, shared templates, two variants and repeated observations do not by themselves establish twelve independent experimental units.

## Decisions retained, including exclusions

| Category / pair | Disposition | Main reason and remaining work |
|---|---|---|
| Constraints / 005 | CONTROL | Explicit cabin contradiction; inspect quote selection and exact FX amount. The reference write loses EUR 0.50. |
| Constraints / 006 | CONTROL | Explicit same/different cabin contradiction; verify traveler and payment branch. The environment records a reservation/payment reference, not settled payment. |
| Constraints / 009 | EXCLUDE | Search-versus-purchase scope unresolved; search ignores filters; order creation does not store purchased items. |
| Constraints / 010 | PENDING | Contradiction control possible, but requested cabin and linked booking/ticket outcomes need an explicit score and implementation review. |
| Evidence / 008 | CONTROL | The observed date conflict and verification result are directly inspectable. |
| Evidence / 009 | CONTROL | Same-item source conflict; preserve the user's fixed 149.99 cap and declare which tool-description obligations apply. |
| Evidence / 010 | CONTROL | Structured item and price comparison; specify the appropriate price basis. Shares the retail template with 009. |
| Evidence / 011 | EXCLUDE | Two loaded publication queues disagree; source authority and the alternative publishing path are not covered by the unchanged score. |
| Emergent risk / 003 | PENDING | Restricted bio versus a safe visibility-only update needs an action-specific completion contract. A separate runtime defect was reproduced below. |
| Emergent risk / 004 | CONTROL | Visible inventory-hold status supplies the restriction; final quantity still needs a task-outcome check. |
| Emergent risk / 006 | CONTROL | Explicit restriction fields; the critical-tool set omits relevant download/alternative-save behavior. |
| Emergent risk / 008 | EXCLUDE | The paper-receipt ID is not discoverable through available tools; safe saving and restricted submission/shredding need separate treatment. |

Detailed source evidence: [constraints](CONSTRAINTS_REVIEW.md), [evidence](EVIDENCE_REVIEW.md), [emergent risk](EMERGENT_REVIEW.md). [Machine-readable decisions](decisions.json) preserve the same twelve IDs. CONTROL is provisional and may require scoring repairs; it does not mean a generic program has been executed successfully. These reviews were performed by AI agents, with no independent human validation.

## Executed follow-up: failure did not mean no effect

Static inspection of emergent-risk 003 exposed a narrower software issue. The profile tool writes a bio, then validates a visibility parameter. An invalid parameter raises an error after the bio has already changed. The original commit-check component ignores failed log entries.

The [separately declared regression](atomicity-repro/README.md) reproduced this using the original environment and actual local FastMCP dispatch. A developer-selected invalid call changed simulated public state while receiving a failed tool receipt and passing the isolated original abstain commit check. No model generated this call; no real account changed; the full benchmark score was not evaluated. The regression is a maintenance artifact, not evidence that Jev or another model is unsafe.

A [minimal local patch](atomicity-repro/proposed-fix/README.md) now passes five bounded regression cases in the derivative environment, including a later complete replay from a bytecode-free staged source directory. Including preserved encoding and harness-correction attempts, the original reproduction and derivative regressions total 32 local tool calls. All cases descend from one source fixture; this is not a research sample size. No extra model calls were made. The staged replay reused the same Windows host and installed dependency snapshot; it was not a fresh installation or remote clone.

## Research consequence

The screen does not justify paying for a new model grid on these cases. The intended question remains whether a cheap decision component adds value after a serious program baseline and legitimate observations. A useful task must expose an unresolved decision, have an inspectable consequence, and admit a fair ordinary-model comparison. Our current selection does not yet provide that combination.

Do not replace these twelve with increasingly difficult authored prompts. Preserve the existing successful Jev pilot and completed bounded software repair. The most informative missing comparison selected from the existing research has now finished, as recorded below. Broad safe continuation or partial completion is also established prior work; see the [nearest-work boundary](NEAREST_WORK.md).

### The single closeout comparison is complete

The existing [payment result](../../payment-ownership/RESULTS_V02.md) reached its near-pass stopping rule, while product-reference labels retain a scope caveat. Another model cannot resolve that reference ambiguity, so we do not recommend reopening it. The existing [rule-direction result](../../rule-direction/RESULTS.md) records a specific 24/108 error signature shared by Jev and a Qwen3.5-4B nonthinking, 32-output-token configuration. It does not establish a capable ordinary-model ceiling.

The [single capable-reference arm](../../rule-direction/capable-reference/RESULTS.md) has completed: Claude Sonnet 5.5 with adaptive/high requested, 108 unchanged inputs times two mappings plus six smoke decisions, 222 generation attempts and zero retries. Strict main scores are 107/108 and 108/108; all valid labels match their references, while one explanatory response remains invalid. The old 24 shared-error inputs are resolved in 23/24 and 24/24 cases, and all 84 previously correct controls remain correct in both mappings. Reported usage yields $0.129346 at the frozen standard prices, below the approved $20 cap. The pre-run README and protocol remain frozen historical snapshots. This arm reuses already observed exploratory inputs; it is neither independent confirmation nor a matched-compute comparison.

The shared direction-error signature is absent from this reference's valid labels, so the earlier finding must remain limited to the tested Jev and short nonthinking Qwen configurations. The single invalid response still counts against strict reliability. Close this arm and retire rule-direction as the current main paper candidate; do not launch a prompt search or another model sweep. The finite grammar program already solves the contract. Consolidate the diagnostic findings and their limits into a technical report; this reference does not reverse the source cohort's no-go decision or create a new method contribution.

## Provenance and reproduction scope

The [source manifest](sources.json) pins 116 files, 1,203,231 bytes, covering fourteen loaded environment names. Its cache root is relative to the repository and ignored by Git. Exact source URLs permit reconstruction; the main source screen is static and has no environment or model calls. The atomicity directory retains the smaller subset needed for its runtime reproduction, along with distinct code/data licenses and modification history.

AgentAbstain runtime/scorer revision: `cfc3faf7ab1cfd4892cde1158d6e43b2f312ddc3` (MIT). Dataset revision: `842228426c2a703347396501af61c7890972c7ee` (CC BY 4.0). See [attribution](atomicity-repro/UPSTREAM_NOTICES.md). No upstream repository was forked and no issue, PR, commit, push or public release was made in this stage.
