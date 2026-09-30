# Source evidence audit before interpreting model scores

2026-09-30. This is an AI-assisted reading of all 12 selected source pairs,
performed after inference started but before inspecting the cross-model
source-agreement table. It is not a human review, blind adjudication, legal
interpretation of current policy, or a replacement reference set. Statements
below concern only what is written in the frozen historical benchmark inputs.

## Why the source-agreement boundary matters here

The deterministic selection and full source provenance do not establish that
the selected labels follow from the four fields available to each model. One
pair supplies only the title **"Child Car Seat Laws"** as its rule snippet,
yet both source actions are Yes. This is a concrete evidence-sufficiency issue,
not merely a generic disclaimer about dataset noise. Other pairs invite a
necessary-versus-sufficient-condition or question-scope objection.

All 24 saved rows were rechecked byte-content-equivalently after JSON parsing
against the official development records from archive SHA-256
`72dca3f4f3ba73b1d796b40e952a80d53cd2011ef90b2168b8bcaa818f5edd1e`.
The title-only snippet is present in the original source rows
`0ca136591dacd9c5a609f6f2c5e56af0726b0fbc` and
`6cc5b2c34d87b6eadccc7b04481e52339c1cbcd0`; it was not produced by prompt truncation.

All original references, model calls, failed outputs and denominators remain
unchanged. No preferred model, new label, filtered score or excluded cohort is
chosen from this audit. An independently adjudicated task could legitimately
disagree with the source while remaining a different evaluation target.

## Exhaustive pair inventory

IDs below join directly to `references.json` and `selection.json`. This is one
qualitative pass over every selected pair; it does not certify unflagged inputs.

|Pair ID|Frozen topic / source actions|Question for semantic review|
|---|---|---|
|1684dcbe3c670d4ed4ffd62e|Female Vietnam Veteran / ASK, ASK|The source's second follow-up asks whether the speaker is a veteran's child, while the original question concerns the speaker's child. Establish who the benefit concerns and whether either branch can still apply. ASK itself does not specify which clarification is valid.|
|1f6921ba38872b45dfc280f6|Federal grants / No, No|The snippet excludes grants to individuals for starting a business or personal expenses. When both purposes are denied, the broader question is not necessarily settled by that exclusion. Do not silently broaden a purpose-specific prohibition.|
|2e06c418c91ae0b22b00e33c|Payment in lieu / Yes, No|Leaving the job is explicit; the question does not separately establish untaken statutory leave. Review whether the question asks about the permitted route or actual entitlement. The unrelated scenario remains part of the original input.|
|3eb969b9fba197de8e61d35e|Maternity leave / No, ASK|The two listed requirements support an ordinary conjunction reading: one failed requirement versus one met requirement with notice unresolved. Confirm that reading and the task's treatment of an omitted requirement.|
|49c43c8cf5e2199809a4189b|Displaying a sign / No, ASK|A sign inconsistent with local rules is expressly prohibited. For a consistent sign, the source asks about misleading advertising; review whether the particular sign is established to be advertising and whether the licensed-person scope is assumed.|
|72f81bb33bd4928366bce9d8|Social-work information / No, Yes|The recommendation says to find out more if going through a difficult time. Its antecedent being false does not logically prohibit seeking information. The question's "should" and the source's No may reflect a benchmark convention rather than an explicit negative rule.|
|9d37e76cc7404ee007c1b49c|Zero-rating equipment / ASK, Yes|Two recipient alternatives support the intended branch change. Preserve the text's "may also be able" and the question's "May I be able"; this is not proof of an unconditional tax entitlement.|
|c1c77c8c33c8fe915c827751|Pension tax abroad / ASK, Yes|The snippet describes non-residents and exceptions. A UK-resident Yes response is not itself an explicit statement of all resident tax obligations. Review whether the source expects the converse or outside knowledge.|
|ddbc1d07a6c156a44de3bb03|Disaster personal property / Yes, No|The snippet excludes extraordinarily expensive or irreplaceable property. A generic Yes to damaged personal property may not settle those exceptions. Review the scope of "such as" and whether that answer establishes an included category.|
|dfafd6c2c3bf08cc9ef44d03|Child car seat / Yes, Yes|The entire rule is the title "Child Car Seat Laws". It contains no age, jurisdiction, vehicle or seat requirement. The negative answer to "Is this a child?" also conflicts with the question's "my kid" presupposition. No unconditional safety-seat rule can be extracted from this title alone.|
|e04ea602dfbf5af87eb8810f|Information for benefits calculator / Yes, Yes|The question asks whether information is needed, while the changed history answer concerns already having benefit information. An invariant requirement is plausible; distinguish the need for information from possession of it and resolve "this" against the scenario.|
|fa852bc7719887ea3c01db16|SBA loan approval / Yes, No|"Can only approve" establishes repayment ability as necessary, not sufficient. A Yes to ability does not by itself entail "Will my loan be approved?" The unrelated scenario supplies no additional approval conditions.|

## Consequence for the next decision

1. Publish the complete frozen source-agreement screen, including cap failures,
   order effects and both API readouts. Do not suppress the thin-title example or
   replace its label to improve any model's headline.
2. Separate output validity, consistency with the source label, and support by
   the visible rule. These are three different questions; neither a perfect
   parser nor a larger generation budget resolves questionable references.
3. Use this inventory to request reasons in any later semantic adjudication.
   New human review must see the actual snippet/question/scenario/history and
   specify its interpretation; it must not inherit automatic Yes/No/ASK labels.
4. Do not run an adaptive prompt or reasoning-cap search merely to match these
   24 source labels. A next intervention needs a distinct hypothesis, a frozen
   budget and a valid interpretation of the target being measured.
5. Keep the separate training-review queue unchanged and unscored. None of this
   reading supplies its missing human reviews or turns the development screen
   into an independent confirmation set.

The likely research value of this pilot is a transparent interface-and-measurement
diagnostic. A model-replacement or new-method claim remains unestablished even
if one interface has higher source agreement.
