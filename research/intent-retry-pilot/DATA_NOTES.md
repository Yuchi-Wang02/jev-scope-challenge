# Exploratory data and pre-inference checks

Prepared 2026-10-05. These 72 inputs were written by the AI assistant for this project. They are synthetic, not captured conversations and not independently human-validated. Labels are provisional references, not established gold. No source dataset or upstream code was copied to create the dialogues.

There are twelve parent contexts (three domains by four execution histories), with six latest-user-turn variants each. Only that last turn changes within a parent. There are 48 clear-authorization inputs, 12 explicit deferrals and 12 unresolved references to an assistant question offering two scopes. Two fixed ABC mappings give 144 science requests. Three unscored room-reservation interface checks precede them.

An additional AI agent reviewed the protocol and complete material. It found no contradictory clear-branch references and checked that timeout/failed additional-operation requests explicitly authorize both operations. This is a second AI check, not an independent human rater. Its concerns led to these pre-inference changes:

- Removed an ambiguous authorization instruction from the prompt.
- Removed the circular proposed intervention: explicit linking is already the task.
- Separated semantic choices, write attempts, effects, original obligations and additional obligations.
- Used two cyclic label permutations, with no claim of full positional invariance.
- Kept clarification strata separate, including the known history confound.
- Renamed the combined measure scope-and-effect success rather than full task success.

The unresolved-reference items use vague assent after a two-alternative question. In all six such parent contexts the additional-operation option is mentioned last. A recency interpretation may be defensible. Outputs on these twelve inputs must not establish an operation-binding defect without independent interpretation review. Their item IDs are:

`i-436a86cc864e`, `i-4c15e661fa86`, `i-9ccaa8be464b`, `i-6f7a46cb75c0`, `i-7b1c3f14f2c8`, `i-aeca538721f5`, `i-c49cc93dd0cc`, `i-a31b09933a2a`, `i-566e38e82b54`, `i-95fa12e0e4e9`, `i-8dfeb340f916`, `i-7d36272bf0e0`.

Reviewer materials are `data/visible.json` and `data/review_blank.json`. Give reviewers only those files plus the task definitions and review instructions; `data/references.json` and model outputs must remain hidden for first-pass labels. Each reviewer should assess intended count, continuing original authorization, ambiguity, plausible reason for repetition and supporting words. Record whether results or others' opinions were seen. If review changes a reference, retain this version and report the revision; do not retroactively turn exploration into confirmation.

The simple rule baseline was authored with knowledge of this pilot. It is a transparent cheap control, not a separately optimized or independently validated competitor. The always-reuse, always-add and always-clarify controls expose metric tradeoffs. A user-choice UI is a proposed engineering comparator; no users have tested one here.

## Pre-inference verification

`verify_pilot.py` checks counts, joins, common parent context, hidden-world consistency, exact prompt construction and hashes, both order mappings, 90 reference-assisted effect worlds, and deliberately wrong merge/split choices. These checks cannot establish natural-language correctness or ecological validity.

`test_runner.py` checks response mapping, malformed metadata, journal sequencing, retry limits, recovery, locking and frozen-request constraints with injected test responses. Those responses are software tests only and never appear in the scientific output logs.

The Jev arm can run under existing authorization. A capable ordinary-model reference is still needed. Environment-variable presence for another provider does not establish the user's authorized account, accessible model, billing or a configured comparative arm; no such provider is called by this pilot runner.
