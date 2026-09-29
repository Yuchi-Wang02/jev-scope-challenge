# Next development question: does a citation actually support the extracted fact?

Status: contract-control code and adversarial software tests prepared; the model
comparison is still design only. No new model scores, reviewed labels or
successful remedy are reported here. This follows the existing development failures and uses the
same attribution boundaries as [the completed study](RESULTS.md).

The next falsifiable question is whether a bounded evidence-selection step can
reduce unsupported field assertions while preserving decisions on supported
inputs, under a fixed total query/token budget. A correct-looking citation is
not a proof that the asserted fact is true or about the right target.

## Contract to distinguish several kinds of failure

For a TRUE/FALSE claim, require a source span and an explicit target-field binding.
For CONFLICT, require separately identified positive and negative observations
for that same target field. MISSING has no supporting observation: an empty
citation by itself does not prove absence. The system must declare its inspected
source scope, and uncertainty in evidence selection must remain distinguishable
from a known missing fact.

Evaluate exact source location, target binding, value support, conflict coverage,
missing-fact handling and final action separately. String matching proves only
that quoted characters occur. A quote about another request or a policy
definition can exist verbatim and still be invalid evidence. Preserving the
final decision across a rewrite is weaker than preserving the facts.

## Smallest useful comparison after semantic review

1. Freeze a reviewed subset of original/rewrite pairs before new scores. Treat
   this as language-transfer development, not fresh confirmation of a method
   already designed against these parents. Keep groups intact and report every
   accepted, rejected or unresolved pair.
2. Keep direct decisions, the existing four-state pipeline and the exact-grammar
   code reference. Report unknown-grammar rejection explicitly for the code
   reference; do not silently broaden its parser after inspecting test failures.
3. Add one bounded evidence-selection candidate. Selecting existing record IDs
   avoids free-text quote fabrication, but still requires validating which
   target and value the selected record supports. Any model assistance to that
   validator is an additional call, not free program verification.
4. Match external schema/policy help across paths. Include direct inference
   with the same query budget and record actual tokens, calls, latency, false
   commitments, abstentions and supported-decision regressions. Report extraction
   order sensitivity rather than choosing the best order after scoring.
5. Only a method that improves these development tradeoffs earns a separate,
   independently reviewed confirmation protocol. Instruction-tuned alternatives,
   new downloads, training or paid backends require explicit resource planning.

## Adversarial checks to prepare

Use a genuine quote from the wrong request; a policy definition mistaken for an
observation; an omitted opposing record in a conflict; a true quote that does not
entail the asserted value; an irrelevant deletion; and a decisive deletion.
Program-created fixtures can test software rejection behavior but are not model
results or independent semantic labels.

The automated review-export validator is now available. Independent semantic
review and the new-run protocol remain open. There is no claim that adding
citations has already repaired the observed failures.

## Prepared pure-code control

[`cited_contract.py`](cited_contract.py) checks exact offsets, target/field/value
binding, full conflict coverage and declared inspection scope against the
**entire known-grammar visible state**. It explicitly rejects unsupported
paraphrases. An empty quote for MISSING remains `absence_unverified` unless
the caller separately enables a full-parser absence certificate. That option
is marked `pure_code_reference`: the parser already knows all source records,
so this is a strong code baseline, not evidence that a model selected or
understood a citation. The software tests are adversarial program fixtures;
they are not independent annotations or model results.

The [`12-pair starter`](review/starter_blind_pairs.json) reduces the first
human-review workload to missing/conflict cases across the three development
families. Its selection is procedural, clustered by parent, and not a random or
held-out sample. The full 144-pair pack remains available; neither pack has
independent human judgments or rewrite inference.
