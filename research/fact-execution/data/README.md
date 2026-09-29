# Fact-execution data card

This is a derivative view of our own [evidence-gap candidate corpus](../../evidence-gap/data/README.md).
It is not a new independent sample: `original_cases.jsonl` contains the exact
72 development texts from 12 parents used there. All construction metadata is
retained for audit. Only visible text/policy and program-provided schema
definitions enter the model prompts; labels and record IDs do not.

`reference_facts.jsonl` has 168 program-derived field-status references and
exact character spans in the original text. They are not human annotations or
model-generated citations. Four states distinguish a positive record, a negative
record, no record, and conflicting records. The 18 missing fields and 12 conflict
fields are repeated constructions within these 12 groups, not population samples.

`inputs.jsonl` contains 552 encoded query plans shared by the three evaluated
paths: 216 direct plans and 336 field plans. These include candidate rotations
and repeat the original text; they are not 552 unique language examples.
`executor_audit.json` covers all 96 four-state vectors of the three development
policies, checked against a separate direct solver of the same declared rules.

The [144 rewrite pairs](../review/) are AI-generated candidates that intend to
preserve facts. Their equality is not independently verified, and no rewritten
input has a model score. They must not be advertised as a validated benchmark.

The [multi-fact line stress set](../MULTIFACT_LINE_STRESS.md) contains 112
line-packed versions of 56 of the same development texts. Its program-derived
reachability scores describe the exclusive routing interface under faithful
labels; they are not model evaluations, new independent examples or human
annotations. The audit JSONL includes program references and must never be
supplied wholesale as a model prompt.

Original synthetic text and program-derived reference data, including these
provisional candidates, are CC BY 4.0. Attribute Yuchi Wang / Jev Scope Challenge,
cite the relevant version, link the [license](https://creativecommons.org/licenses/by/4.0/),
and identify changes. Upstream models/code have separate
[attribution and terms](../../../THIRD_PARTY_NOTICES.md). This data declaration
does not relicense model weights or claim ownership of provider output.

Current independent human annotations: zero. No personal or customer records.
All gold labels describe the finite constructed policy, with natural-language
interpretation still awaiting independent review. Version corrections and
preserve the historical labels and failures rather than replacing them to
improve scores.
