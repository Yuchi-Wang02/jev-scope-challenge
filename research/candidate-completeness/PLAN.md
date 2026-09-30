# One visible match: is the candidate set complete?

**Status: proposal for review. No dataset, frozen request manifest, new labels,
model calls or results exist for this study. Do not run from this plan alone.**
Revised 2026-09-30 after both payment-study submissions. The previous four-input
proposal is retained in Git history at `0cbf005`. This revision adds irrelevant-omission
controls before any dataset construction or inference. The proposed ceiling changes
from 107 to 155 attempts; no calls are authorized or made by publishing this design.
Prepared following the payment-study review. This design is
informed by inspected development results and a discovered specification issue.

## Question and falsifiable prediction

Can a decision model distinguish a unique match in the records it sees from a
uniquely established target when matching records may be omitted? Keep visible
business records fixed and change only an explicit completeness statement. Test
whether product-reference judgments change from determined to NOT_ESTABLISHED,
while an explicit-ID request for a visible order remains determined.

This is a test of stated evidence scope and instruction following. It does not
prove a latent binding mechanism, detect real-world omissions, or propose a new
algorithm. A finite parser can solve this controlled grammar; it must be included.
Related work and novelty need a fresh focused check before any paper claim.

## Candidate construction

Use the same pinned tau retail source revision and MIT attribution as the
[payment study](../payment-ownership/source_manifest.json). Select 12 source users
disjoint from its 12 users using a deterministic hash ranking fixed before any
new output. Require two distinct existing ordinary payment methods per user so
unseen-order payment histories can differ without inventing an unavailable method.
If 12 eligible users cannot be obtained, report that feasibility failure before
changing the selection rule or proposed sample size.

For each parent, construct six inputs:

|Request identifies target by|Candidate coverage statement|Expected reference after review|
|---|---|---|
|Explicit visible order ID|Complete|Determined VALID or INVALID|
|Explicit visible order ID|Incomplete|Same determined label|
|Product name with one visible matching order|Complete|Same determined label|
|Same product-name request|Incomplete for the requested product|NOT_ESTABLISHED|
|Explicit visible order ID|Omissions only for an unrelated product|Same determined label|
|Same product-name request|Omissions only for an unrelated product; all requested-product candidates visible|Same determined label|

Use six valid and six invalid determined parents. This gives 72 proposed inputs:
30 VALID, 30 INVALID and 12 NOT_ESTABLISHED. Twelve parents, not 72 independent
samples. Keep records, destination, policy and request identical within each
completeness pair. Use IDs for destinations in the first pilot to avoid adding
card-description resolution as another factor. No gift-card destinations in this
pilot: their exception can make validity independent of target identity.

The three statements must unambiguously specify their scope. Use one predeclared
wording family for the pilot; do not choose a paraphrase after model feedback.
Draft wording:

- Complete: "For requests identified by product name, the displayed orders
  include every order of this user containing that product."
- Incomplete: "For requests identified by product name, at least one additional
  order of this user contains that product and is not displayed. Its payment
  history is not provided. The product-name request does not distinguish the
  displayed order from an omitted matching order."

- Irrelevant omission: "For requests identified by product name, every order
  containing that product is displayed. At least one order containing a different
  product is not displayed, but no omitted order contains the requested product."

All conditions explicitly state that an exact order ID uniquely identifies its
displayed order, displayed payment histories are complete, and the user payment
method list is complete. The refund-destination rule stays identical. Final
wording requires human review and a versioned freeze; these drafts are not a
frozen model prompt. The completeness statement is supplied evidence, not a
prediction produced by a retrieval system.

For every incomplete product-reference input, construct two auditor-only possible
worlds compatible with the visible text: an omitted matching target paid using
the requested destination, and one paid using a different existing method.
Both worlds must preserve the visible records. These are explicitly synthetic
counterexamples, not claims about the upstream database's actual omitted orders.
Do not send these worlds or resolved target metadata to the model. Verify that
one world yields VALID and the other INVALID. This establishes insufficiency
under the task semantics instead of merely assuming every truncated list is unknown.

## Baselines, interface and proposed budget

Primary model: pinned `jev-1.13.0`, with the same three semantic labels and two
fixed option mappings. Record the actual returned model, raw probabilities,
token usage, latency and all errors. Use full visible records only; no oracle
filtering arm, adaptive prompt improvement or extra model reasoning calls.

Include: (1) scope-aware known-grammar parser plus policy code, (2) the same parser
ignoring completeness, (3) always VALID, always INVALID and always NOT_ESTABLISHED.
These zero-model-call baselines receive exactly the declared visible information.
No code baseline may consume auditor-only worlds or hidden construction labels.

A stronger ordinary instruction-model comparator is necessary before making a
dedicated-versus-general-model claim. Its checkpoint, thinking setting, readout,
hardware and budget are not chosen here; it has no results and is outside this
pilot's call allocation. A Jev-only pass or failure cannot settle substitution.

Proposed pilot: six separate smoke requests plus 72 inputs x two mappings = 150
scheduled HTTP requests; at most five retry attempts across the stage, hence
**155 total attempts**, and at most 1,000,000 conservative planned input units.
Use the original serialized UTF-8 bytes +256 accounting proxy per attempt,
including retries. Actual tokens and cost are reported separately. Verify current
provider pricing before execution, without treating this proxy as exact tokens.
This is a new proposed allocation, not automatic use of the prior study's remainder.

## Metrics and stop rules

Primary descriptive endpoint: parents correct on all six inputs in the primary
mapping, denominator 12. Report the reversed mapping separately, plus strict
twelve-decision parent correctness. Never choose the better mapping after viewing
results. Also report complete product-reference pairs, stable explicit-ID pairs,
false commitments on the 12 unknown inputs, unnecessary deferrals on the 60
determined inputs, wrong acceptance/rejection, mapping disagreements, and costs.
Changes alone earn no credit; both answers must be correct. Report all baselines.

An exploratory engineering screen would require at least 10/12 primary complete
parents, at most 1/12 false commitments and at most 1/60 unnecessary deferrals.
These cutoffs are proposed decision thresholds, not significance tests, power
calculations or population guarantees. Freeze them before outputs. Report raw
counts even if a screen passes. Token length and salience differ between the three
scope statements; a contrast cannot isolate the internal reason for a difference.

Stop after the fixed grid regardless of scores. A near-perfect pass is a boundary
result. A failure motivates classification into scope handling, request resolution,
policy execution or option mapping; it does not authorize a prompt search. Label
or program errors halt scoring pending a versioned audit preserving every output.
There is no adaptive follow-up allocation. Transient transport failures may use
the bounded retries; permanent errors, invalid responses, unconfirmed model
identity or unreconciled billing stop execution. Semantic smoke failures remain
reported and do not alone bar the grid; unresolved input/reference defects do.

## Required before execution and deliverables

1. Preserve the original study's [reporting disposition](../payment-ownership/REVIEW_DISPOSITION.md)
   and both initial submissions. Do not reuse their agreement as validation of
   the new wording or label semantics.
2. Review this proposal, select and freeze the source users, exact requests,
   possible-world witnesses, scoring code, smoke inputs, mappings and call list.
3. Obtain two independent initial reviews of the new inputs and witnesses, record
   author overlap and prior exposure, and resolve wording/label disagreements
   before model outputs. Agreeing labels alone do not certify independence.
4. Validate candidate completeness logic, ID controls, label mapping, resume,
   shared retry count and stop conditions. Disclose all AI-authored text.
5. Only then execute the bounded, approved version and publish all outcomes.

Expected deliverables: versioned data/problem card, source and mutation manifest,
review originals and adjudication, frozen protocol and requests, raw API ledger,
all baseline outputs, paired result table and replay. New source users reduce
direct scene reuse, but the task grammar and hypothesis are development-informed.
No broad confirmation or novel method follows from this pilot alone. Hugging Face
publication remains a later packaging decision after review and license checks.

## Design review: shortcuts and limits

A rule that refuses product-reference queries whenever any order is omitted can
solve the original four-cell design without checking which product is affected.
The irrelevant-omission control contains omission language but requires the
determined answer. Include this request-type-plus-omission heuristic and a simpler
baseline that rejects every record mentioning an omitted order, alongside the
semantic scope-aware program. Freeze literal token triggers before outputs.
Report needless deferrals on explicit-ID and irrelevant-omission controls.

This addition does not eliminate every lexical shortcut. A finite program that
recognizes the three statement templates and the request type can solve all cases.
The study can measure compliance with explicit coverage evidence; it cannot
establish general reasoning about unknown retrieval recall. Sentence length and
wording still vary, and only two option mappings are tested. These limits remain
even after a perfect score. Do not broaden them into mechanism or model-necessity claims.

The target-resolution requirement must be explicit in the frozen rubric: a unique
target is required for this pilot's determinate labels. Gift-card exceptions and
multiple ambiguous targets sharing a decision raise a different question (action
validity without identity). They are outside this pilot, not automatically errors
or a general rule that every uncertain identity requires refusal in every task.

Before implementation, verify the 72-input label counts, that irrelevant omissions
cannot add a requested-product candidate, and that all incomplete-relevant witnesses
preserve each visible field while supporting opposite decisions. Reviewers must
judge those properties before seeing model outputs. The proposal adds no new
literature search or novelty evidence; that check remains necessary for a paper.
