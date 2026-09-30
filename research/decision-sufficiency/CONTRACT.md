# Two questions, two contracts

Status: **executable specification prototype, zero model runs and zero independent
human annotations**. Written after inspecting the candidate-coverage experiments.
This is not a preregistered evaluation, a replacement for their policy, or a new
decision algorithm. All examples here are newly authored artificial objects.

## Question to answer

The destination predicate is true when the requested destination is the intended
order's original payment method or an existing gift card in the supplied profile.
The prototype exposes two distinct interfaces on exactly the same structured input:

1. `predicate_only`: return VALID if the predicate is true in every consistent
   possibility; INVALID if false in every possibility; otherwise NOT_ESTABLISHED.
   A target must be guaranteed to exist and a destination must be identified.
2. `unique_target_required`: additionally require the same known order ID in
   every possibility before returning a determined label. This intentionally
   retains an identity requirement that the first interface does not impose.

Neither interface authorizes a refund. `execution_authorized` is always false:
authentication, consent, delivery, return eligibility, amount, tool permissions
and transaction state have not been checked. A known predicate is not a tool call.
Even a known order ID plus a valid destination is only a component result.

The previous candidate-coverage experiment explicitly chose the second kind of
contract. Its refusals on ambiguous identities must not be rescored under the
first contract. This prototype does not relabel any historical input or output.

## Supplied evidence and finite scope

- `request.selector` is a parsed exact order ID or product string. Parsing natural
  language is outside this prototype; a future model must not receive a privileged
  parse unless the same help is part of every comparator's interface.
- `payment_methods` is a complete synthetic profile. `original_method_universe`
  is a nonempty, closed finite set of ordinary methods. Each order has exactly one
  original method, represented by a nonempty domain of possibilities. Multiple
  captures, split payments, refunds, currencies and transaction chronology are
  not modeled. The existing-gift-card exception is explicit in the toy policy.
- `records` may include irrelevant products; IDs are unique. Product equality
  and ID equality are exact string equality, not semantic or fuzzy matching.
- `retrieval.query` must equal the request selector. Its assertion is scoped to
  that query, not to all of the user's orders. `additional_matches` is `none`,
  `possible` (zero or more), or `at_least_one`. The omitted original-method domain
  constrains every additional matching order. These are supplied synthetic facts,
  not facts produced by the model or verified against a real service.
- For an already visible exact ID, `possible` cannot add another matching order
  because IDs are unique. `at_least_one` would instead be inconsistent and is
  rejected. An exact unseen ID with guaranteed existence can establish identity.
- If matching candidates exist, the intended target is one of them; no prior
  probability over targets is asserted. If none may exist, that possibility must
  remain. A known nonexistent destination ID is different from a null/unresolved
  destination. Unknown IDs are outside the closed original-method universe and
  the complete gift-card profile, so cannot satisfy this toy restriction.

Before a deployment claim, the service must establish the query, owner, snapshot,
pagination/completeness and original-method constraints. A JSON shape check cannot
establish that a coverage assertion is true. None of those operational guarantees
is implemented here.

## Decision-relevant projections and witnesses

For every consistent full database and intended target, project to
`(target_exists, target_id, original_method)`. Visible targets retain their IDs.
An omitted product match has an unspecified identity, represented by null; an
exact-ID selector retains that ID even when its record is omitted. Null identity
is distinct from no target (`target_exists=false`). No row count is a probability.

The implementation unions all allowed original methods for every visible matching
target, adds allowed omitted-target possibilities when permitted, and includes a
no-target possibility when existence is unestablished. More than one omitted order
does not add new predicate outcomes: the predicate uses only one intended target's
original method and the fixed gift-card profile. Multiple unknown identities still
cannot establish one known ID. This is why a finite projection suffices under the
declared factorized domains; it does not solve arbitrary database constraints,
aggregate predicates or cross-record dependencies.

Every emitted projection can be realized by assigning that original method to the
chosen candidate and choosing any allowed methods for the other records. Conversely,
every allowed target in a full completion is visible, omitted, or absent, and is
included by the corresponding branch. The argument assumes all supplied domains
are nonempty and independent. The independent brute-force audit constructs complete
databases with up to two visible and two omitted records to check this reasoning
on a finite fragment; that audit alone is not a proof for arbitrary databases.
"Independent" here describes a second enumeration implementation, not independent
people: both implementations and examples were authored with AI assistance.

All-true and all-false projections yield determined predicate labels. Mixed outcomes
or a possible nonexistent target yield NOT_ESTABLISHED. Empty domains, duplicate
IDs, impossible exact-ID existence or mismatched query scope produce
`INVALID_CONTRACT`, outside the three decision labels. The implementation never
uses vacuous truth to accept an impossible contract.

The output retains every projection and one representative witness per outcome.
Opposite witnesses demonstrate why a predicate is unresolved; they are artificial
possibilities, not discovered records. They need not be available as evidence in
a future model prompt. A unique-target determined result always agrees with the
predicate-only result, but the converse need not hold. Additional consistent
information can resolve an unknown; it cannot reverse an already certain predicate
without changing the policy or contradicting the earlier evidence.

## A decision before any new model experiment

First review whether users actually need a predicate answer before target identity,
or simply need a unique order to proceed. If only the latter is useful, this branch
has no new operational need. If the first is useful, a fresh natural-language task
needs reviewed policy wording, examples with both invariant and changing answers,
existence controls, capable ordinary baselines and fixed costs before inference.
Do not reuse these illustrated answers as uninspected confirmation. No additional
model allocation or score table is created by this specification prototype.
