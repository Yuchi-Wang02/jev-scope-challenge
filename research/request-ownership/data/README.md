# Ownership-switch preparation data card

Created by Yuchi Wang with AI-assisted construction and program checks. All
scenes are synthetic; there are no customer records or personal information.

`scenes.jsonl` contains 24 construction objects in three existing finite-policy
families. Each has two request IDs in the same namespace, explicit records and
intended actions used only to construct and audit the scene. `views.jsonl`
contains 48 displayed inputs and program-derived references: the evidence
block and policy are identical within each pair, while the target header and
reference action change. Parent scenes are the unit of paired analysis.

Labels are cross-checked with existing possible-world enumeration, a separate
direct policy solver and a parser of the displayed grammar. Agreement between
these programs is not independent human validation. Independent human
annotations remain **zero**. The data were frozen before inference; the later
[completed diagnostic](../RESULTS.md) scores these 48 views with 500 scientific
forwards plus two unscored warmups. Preparation manifests retain their original
zero-inference creation-time state.

Only `state` and `policy` enter the prompt-builder API. Gold, construction
records, family, target slot and scene identity are not model evidence. Public
plans carry bookkeeping identifiers outside the prompt; do not send a whole
JSONL record as the model input. The encoded files are tokenizer-only query
plans, not model outputs.

These are new scene instances within already inspected sentence and policy
templates. They address a target/distractor prefix confound, but do not constitute
new policy families, independent natural language, held-out confirmation or
general entity-resolution coverage. Aliases, implicit references, mixed-owner
lines and contradictory target facts are outside this initial preparation.

The [review packet](../review/visible_packet.json) omits construction labels but
is not fully blinded: pair identities and public source remain available.
The [response form](../review/blank.csv) is empty. Neither a packet nor a valid
CSV counts as a completed independent annotation.

Original synthetic text and program-derived references are CC BY 4.0. Attribute
Yuchi Wang / Jev Scope Challenge, cite the specific version, link the
[license](https://creativecommons.org/licenses/by/4.0/), and identify changes.
Original code follows the repository MIT license; separate model/code
[credits and terms](../../../THIRD_PARTY_NOTICES.md) remain applicable.
