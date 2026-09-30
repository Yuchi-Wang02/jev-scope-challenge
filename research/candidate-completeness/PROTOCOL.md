# Candidate completeness: fixed exploratory execution v1

Prepared 2026-09-30 before any candidate-completeness model output. This is a new
run, not a continuation of the stopped payment grid. The user explicitly authorized
autonomous bounded Jev API and local-model work after each milestone audit.

## Change from the design-only plan

The [earlier plan](PLAN.md) required two human reviews before model inference.
Under the later user instruction to continue running bounded explorations, this
protocol permits the fixed Jev diagnostic after offline semantic/program checks,
with new human review still pending. This change precedes all new model outputs.
It is **exploratory, not independently confirmed**. The prior two submissions
reviewed different inputs and do not validate this new 72-input set. New local
model execution needs its own recorded readout freeze; no download is planned.

## Frozen question and data

Does the decision track whether omitted orders could match the request, rather
than merely reacting to the presence of omission language? Twelve new source users
are disjoint from the earlier payment study. Each parent has two request styles
(explicit order ID, product reference) crossed with complete coverage, relevant
omission and irrelevant omission: 72 inputs, 30 VALID, 30 INVALID, 12 NOT_ESTABLISHED.
Each coverage triple holds all fields except coverage_statement exactly fixed.
Explicit requests include the product name so the coverage declaration has the
same referent across request styles. The visible records remain structured JSON.

Selection is deterministic from the pinned simulated tau source, with one user
per parent and alternating original/other ordinary payment destinations. Source
objects are retained in vendor/selected_records.json; displayed projection omits
address, personal names, fulfillment and status uniformly. No real customers.
MIT attribution is retained. No Kev or Laya code is used in this study.

Coverage declarations are **constructed scenario premises**, not measured database
retrieval coverage. The incomplete scenarios add hypothetical omitted orders to
the scenario universe; they are not claims that the original source database has
those unseen orders. Auditor-only witnesses show two compatible worlds with
opposite destination outcomes, preserving all visible records. Witnesses and
construction targets are absent from API state. A unique target is required by
the explicit component rubric; ambiguous-identity but invariant-action decisions
are outside this task. No gift-card destination occurs in the main grid.

Labels are program-derived. Checks cover source disjointness, exact reconstruction,
paired-field identity, witness compatibility, reference counts and a grammar parser.
These are useful invariants, not substitutes for independent semantic review.

## API grid, budget and stop rules

Use `jev-1.13.0`, one A/B/C Choice question per HTTP call. Use the original label
order and its reverse, both fixed before outputs. Schedule all 144 main calls by
a fixed hash order after six separate smoke calls (two per semantic class).
All valid smoke responses are retained whether their answers are correct or wrong.
Semantic smoke errors prompt an input/reference check; API/schema/model errors or
confirmed task defects stop the run. Do not alter the grid based on smoke scores.

Maximum 150 scheduled calls, at most one transient retry per job and five retries
over the stage, hence **155 HTTP attempts**. Cap total reserved input units at
1,000,000; each unit reservation is serialized UTF-8 bytes +256, not exact tokens.
The current prepared schedule uses 522,016 units before retries. Known actual
tokens are logged separately. Unknown usage, unfinished attempts or a successful
ledger response missing from the terminal file require reconciliation before
another call. No silent provider retry layer. Every attempt is recorded before
transmission, with sanitized raw output, usage, latency, status, mapping and hash.

Official pricing checked on 2026-09-30 is $0.042 per million input tokens with free
output tokens: [TypeSafe model reference](https://docs.typesafe.ai/models). Actual
usage-based estimates are not invoices. The planning proxy is not a billing forecast.
This is not authorization for an unbounded API search or model downloads.

Stop after the fixed grid. No prompt search or adaptive follow-up is allocated.
A pass remains a useful limit on the proposed concern. An error remains in the
public record. Any data/reference defect requires a separately versioned correction
without deleting the original responses or silently changing the denominator.

## Analysis and baselines

Primary: complete six-input parents under mapping 0, denominator 12. Report mapping
1 separately and strict twelve-decision parent success. Report all six cells,
relevant-omission product pairs, irrelevant-omission controls, explicit-ID stability,
false commitments on 12 unknown inputs and unnecessary deferrals on 60 determined
inputs per mapping. Correctness requires agreement with the declared reference,
not merely changing answers. No aggregate may treat 144 calls as independent cases.

The exploratory screen requires >=10/12 complete primary parents, <=1/12 false
commitments and <=1/60 unnecessary deferrals. These are declared engineering
thresholds, not powered statistical tests. Report scores even when it fails.

Include scope-aware grammar code, scope-ignoring code, an omission keyword rule
for all requests, an omission keyword rule only for product requests, and all
three constant-label rules. The prepared code scores are 72/72, 60/72, 36/72 and
60/72 respectively for the first four. Every rule sees only the same visible state.
The complete grammar solver is an essential boundary: no model necessity follows.
One wording family and two option orders cannot establish general paraphrase or
permutation robustness. A simple template parser can recognize the conditions.

No calibrated probability or internal-mechanism claim follows from these scores.
Jev-only results do not establish superiority to general models. Any local
comparison must document the input serialization, thinking mode, next-token versus
generation readout, extra computation, and the fact that latency is hosted/local.

## Publication and next milestone audit

Freeze code, data, witnesses, requests, this protocol and dependency hashes, then
publish before calls. Retain raw and derived results, all baseline scores, exact
inputs, a case replay, review-only materials and a stage decision. At completion
audit: actual vs planned work; what the evidence supports; unresolved labels and
comparators; stop/continue decision; public presentation and next bounded action.
The [bounded related-work check](RELATED_WORK.md) is not a novelty certification.
