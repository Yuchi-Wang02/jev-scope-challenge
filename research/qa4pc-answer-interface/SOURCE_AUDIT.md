# Consistent composition is not sufficient evidence

Status: all 24 scenarios /12 policy trees inspected. **AI-assisted and outcome-aware;
not independent human adjudication.** Zero reference changes, replacement scores,
new model calls or completed human reviews. The [original results](RESULTS.md)
and their 648 recorded decisions remain unchanged.

## What was inspected

For every selected scenario, including model successes, inspect the pinned policy,
question, scenario, annotated intermediate facts and rule graph. Compare those
notes with all six saved outputs from each of the four routes. The
[complete notes](source_notes.json) and [joined audit](source_audit.json) retain
every item in cohort order. Notes were written before the per-item output join,
but aggregate results and earlier project analyses were already known; this
ordering does not make the audit blind or prospective.

|Observation|Scenarios|Meaning|
|---|---:|---|
|Decisive evidence gap flagged|4/24|A fact needed for the supplied final answer is not established by the visible text in this audit's reading.|
|Rule scope flagged|4/24|The final answer depends on treating a stated route, condition or list as exhaustive.|
|No specific final-label flag in this pass|16/24|No objection recorded; not a certification of correctness.|
|Intermediate fact or graph concern|10/24|Overlaps the rows above; may be masked by a different decisive condition.|

These are qualitative review categories, not eight proven label errors. The unit
is a scenario nested in one of twelve policy trees. Repeated mappings and model
routes do not enlarge the independent sample. No significance claim is made.

## Concrete distinctions

- Favorable credit language does not establish an adverse credit-risk condition.
  A supplied negative final label relying on that condition needs human review.
- A large installation expense, by itself, does not settle cost-effectiveness;
  savings and the comparison horizon matter. An annual-saving comparison also
  does not automatically determine lifetime cost-effectiveness.
- Possession of a credential can establish a stated permission route. Absence
  of that credential does not, without an exhaustive-rule convention, establish
  that every other route is prohibited.
- A source graph can omit a policy branch or contain an unsupported intermediate
  label while another explicit condition still supports the final answer.
  Graph defects cannot explain a direct-route model's behavior through graph
  exposure: none of the four direct routes received the graph.

This is analysis of supplied historical text under the experiment's task
instruction, not an interpretation of current law, tax or benefit eligibility.

## Model consensus is not adjudication

Four scenarios have the same valid source-mismatching answer across all four
routes and six mappings. Three carry a final-review flag. The fourth,
`7e34e009da76d89cd6d962199b2f0a32ced9ebdb`, is an important counterexample:
the source says `maybe`, all model routes say `yes`, and the visible scenario
does not establish the geographic and small-business prerequisites. This audit
records no final-label objection there. Do not use majority or unanimous model
votes as a substitute for source evidence.

Jev has seven scenarios with a stable source mismatch across all six mappings;
five overlap final-review flags. That is a post hoc association, **not five
corrected Jev errors**. Do not subtract them from the error count, remove them
from the denominator or publish an adjusted model ranking.

## Relation to source construction

The [QA4PC paper](https://aclanthology.org/2021.emnlp-main.678/), sections 3.1 and
4.3, describes three-way entailment judgments and checks between direct answers
and answers composed from annotated questions. Such agreement checks address
internal consistency. They do not independently establish that each fact is
supported by its visible scenario. The project's earlier 429/429 complete
composition check therefore remains useful, with a narrower meaning than a
semantic validation certificate.

## Decision and remaining work

Keep this cohort closed to inference and retain source-agreement terminology.
Use the [source-only review package](REVIEW_PACKAGE.md) for retrospective human
assessment of all 24 cases. Hide source labels, graphs, model outputs and these
notes from reviewers who have not already seen them, and record prior exposure.
Do not convert retrospective assessment into independent confirmation of an
intervention developed from these outcomes.

The separate ShARC training review queue remains unscored. Future confirmation
requires new material and a frozen interpretation of evidence sufficiency. A
stronger ordinary-model comparison remains a separate gap. More calls on these
same closed inputs would not resolve the uncertainty about reference semantics.

## Reproduce without inference

Fetch the original pinned source locally following the existing source setup,
then run:

```powershell
python research/qa4pc-answer-interface/audit_sources.py verify --source-dir .local/qa4pc-audit-fresh
python research/qa4pc-answer-interface/analyze.py verify
```

The audit verifier checks the pinned source, complete item coverage, joins and
derived counts. It does not validate the qualitative notes as human truth.
Source prose is not redistributed here while explicit dataset redistribution
terms remain unresolved. This stage adds original analysis and review tooling;
no third-party repository was forked or vendored.
