# Six fixed source tasks and two paper-only traces

Source: [tau2-bench at 5bfa7e3](https://github.com/sierra-research/tau2-bench/tree/5bfa7e37b36656b37dc6d022156be6563c1007f3/data/tau2/domains). Selection: IDs `0`, `1`, `2` in numeric order from each of retail and airline, with no replacement. [Complete packet](case_packet.json); original [retail policy](retail_policy.source.md), [airline policy](airline_policy.source.md), [license](TAU_LICENSE).

These are simulated source tasks, **not six captured conversations, new gold labels, or model failures**. The three retail tasks share Yusuf's user context and orders. There are four distinct user contexts; independence has not been established. They qualify for source inspection but not automatically for a clean scored pilot.

## Visibility and reference boundaries

| Layer | Who can use it and when |
|---|---|
| `source_task.user_scenario` | Private user-simulator instructions. The agent learns only what the user actually communicates. No conversation was generated here. |
| `source_task.evaluation_criteria` | Evaluator reference actions, assertions and reward configuration. Not prompt material or evidence of an executed action. |
| `records` | Analyst-visible raw source database objects. Tool definitions determine which fields an agent can retrieve; the whole packet is not an agent observation. |
| Original policy | Agent-visible governing rules. Policy time in airline is fixed to 2024-05-15 15:00:00 EST, not the screen date. |
| Case notes and traces below | Analyst interpretation and deterministic inspection. No independent human review, model inference, or oracle-view validation. |

The packet retains complete task objects, all five orders of the selected retail user, all eleven reservations of the three airline users, and complete related product/flight objects. It preserves nine products and 29 flights, rather than copying the entire database. Full objects contain extra context intentionally; no fields were rewritten. One missing reference is recorded without repair.

## Case cards

| Case / user context | Decision-relevant source facts | What code can settle; what remains | Screen disposition |
|---|---|---|---|
| **retail/0**, Yusuf | Delivered order `#W2378156`; request to exchange keyboard for clicky/RGB/full-size, accepting no backlight if needed, and thermostat for Google Home compatibility. Product variants retain all options jointly. | Filtering can reject unavailable `9025753381` and identify available no-backlight `7706410293`. Thermostat `7747408585` is Google Assistant/black. Equating the user's Google Home wording with Google Assistant is a semantic mapping assumed by the source reference, not proved by an exact string filter. User confirmation/payment choice are still required. | Useful ordinary preference/variant matching case; no demonstrated representation loss. |
| **retail/1**, same Yusuf context | Same initial order and database, but if no clicky/RGB/full-size keyboard is available, exchange only the thermostat. | Same availability check; different explicitly stated fallback. Source expected action contains only the thermostat. This is a natural preference contrast, not an independent user or a controlled joint-correlation intervention. | Keep paired with retail/0; do not count as independent corroboration. |
| **retail/2**, same Yusuf context | Ask about available T-shirt options and return the vacuum, headphones and smartwatch from `#W2378156`. | Source T-shirt product `9523456873` has 12 variants, 10 available. Return membership and destination rules can be checked on IDs after intent is understood. Reference action `2_1` instead queries product `6086499569`, absent from the pinned database. | Retain the anomaly. Not a clean reference-based scored case until source adjudication. Do not silently substitute an ID. |
| **airline/0**, Emma | Explicit target `EHGLP3`, created May 4, basic economy, no insurance; future May 17 flights are available. User-private instructions claim a prior agency trip had insurance. | Joining the stated ID to its policy attributes defeats transfer of another trip's purported insurance. That historical claim is not a verified insured record here. Subject to the communicated reason, the visible target does not meet the listed cancellation grounds. | Useful binding/policy example; ordinary join plus policy checks. Reference no-cancellation assertion is not evidence of model compliance. |
| **airline/1**, Raj | PHL–LGA route identifies `Q69X3R` among this user's reservations; economy, no insurance, created May 14 09:52:38, future flights available. Other reservations include different cabin/insurance combinations. | At fixed policy time, creation was 29h 07m 22s earlier. Other trips' attributes and a claimed prior approval do not satisfy this reservation's cancellation conditions. Route interpretation and communicated reason precede a deterministic policy decision. | Useful wrong-object temptation; the real records retain the relation. No observed failure. |
| **airline/2**, Noah | User-script topic shifts from a new booking to a delayed earlier trip, says last reservation made and claims three passengers. Latest-created reservation is `SDZQKO` (two passengers); the other reservation `4OG6T3` (one passenger) contains a delayed leg. | Code exposes the conflicting cues and passenger counts; it cannot choose a unique user intent from that conflict. Policy also limits unsolicited compensation and requires a qualifying change/cancellation for the relevant certificate; the private script rejects those actions. | Natural interaction complexity, not a clean static target label. Retain ambiguity; do not quietly select the delayed record as unique gold. |

For airline/0, the reference action list is empty and its configured reward basis must not be confused with the mere presence of a natural-language assertion. For airline/2, reference read actions inspect both reservations; they do not establish a unique resolved target. A full action decision includes authentication, user communication/confirmation and other policy requirements beyond the bounded predicates discussed here.

## Trace 1 — controlled variant-to-availability relation change

**Purpose:** check that changing a relation changes the warranted variant selection, while retaining the actual object interface. This analyst-created counterfactual is separate from the original retail/0 task. It is not a source observation or a model experiment. Exact changes are in [paper_traces.json](paper_traces.json).

1. Hold retail/0's request, order, policy, all variant IDs, options and prices fixed. Original clicky/RGB/full-size variant `9025753381` is unavailable. Its accepted no-backlight fallback `7706410293` is available. The conditional variant-selection result is therefore `7706410293`.
2. On a copy only, exchange two availability values: `9025753381.available` changes from false to true; clicky/white/full-size variant `6342039236.available` changes from true to false. No other field changes. The set of variants and total numbers available/unavailable are unchanged; which variant is available changes.
3. Under this controlled database copy, the originally preferred RGB variant is now available. The conditional selection becomes `9025753381`. A complete-object filter handles both cases directly. No field-flattened interface is introduced.
4. The corresponding proposed exchange argument would replace the keyboard's `new_item_id`, after normal user confirmation and payment/price handling. Existing pairwise tool checks can accept the selected variant in each state. We do not execute the tool or claim the whole exchange is authorized; the selected variant's different price also requires the ordinary recalculation.
5. **Conclusion:** the task is relation-sensitive, but its native representation retains the needed relation. This trace provides no evidence of actual interface loss or model failure. A relation-sensitive task alone is insufficient grounds for the proposed method.

This replaces the first draft's preference contrast, which did not directly satisfy the plan's relation-change diagnostic. Retail/0 and retail/1 remain unchanged source cases in the packet. The evaluator's payment ID is not proof of user authorization.

## Trace 2 — irrelevant records versus an ordinary join

**Purpose:** inspect whether airline/1 needs a new representation method to avoid borrowing another reservation's eligibility.

1. Analyst inspection of Raj's complete reservation set connects the requested PHL–LGA trip to `Q69X3R`. In a live agent setting, identification and read-tool retrieval must happen first; a private scenario cannot be pasted in as if it were an observed user message.
2. This reservation records economy, no insurance and creation more than 24 hours before the fixed policy time. Its dated flight statuses are available. Other reservation objects retain their own IDs, cabins and insurance values.
3. A policy computation using **this ID's** fields therefore gives the same bounded cancellation-eligibility conclusion with all records present or after unrelated reservations are removed. The request/reason and necessary policy context must remain. This is an analyst comparison after reference resolution, not an end-to-end oracle retrieval result.
4. The actual cancellation mutation does not enforce all those policy conditions. Adding a deterministic check could be sensible engineering. It would address absent enforcement, not establish that an intermediate representation erased the reservation relation.
5. **Conclusion:** the selected case does not force a new method. It could still expose a model binding error, but none was measured and ordinary record joins are the first baseline.

## Eligibility result and next-use conditions

All six tasks were retained for inspection; none was replaced to obtain a more favorable case. None currently pairs an observed lossy research interface with a demonstrated source-grounded failure. Retail/2 has a reference/data mismatch; airline/2 needs intent clarification; retail/0–1 share context and include a semantic synonym assumption. These qualifications are part of the result, not exclusions hidden from a score.

Before any later reuse: define the live visibility boundary, resolve source defects without erasing original records, obtain independent semantic review, group repeated contexts appropriately, and freeze a distinct hypothesis and comparison. This packet itself grants no new-run protocol and no claim of benchmark validity.
