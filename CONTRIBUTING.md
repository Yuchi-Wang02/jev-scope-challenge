# Contribute a challenge or reproduction

This repository welcomes concrete objections as well as confirmations. Start
with the [research map](RESEARCH_INDEX.md) to identify the study and its status,
then [open an issue](https://github.com/Yuchi-Wang02/jev-scope-challenge/issues/new/choose).
Use **Challenge a case or claim** for a disputed label, a minimal paired
counterexample, or an interpretation error. Use **Report a reproduction** for
a rerun or a new backend comparison. Ordinary questions can use a blank issue.

For a case challenge, name the study, commit and exact record ID. Include the
visible text and policy, your expected decision, and the shortest reason that
the published interpretation fails. If two cases differ in one condition,
show both and state which behavior should flip or stay fixed. A model vote is
useful diagnostic evidence but does not independently establish a human label.

For a reproduction, report the exact source commit, model/provider and revision,
prompt and candidate order, thinking mode, decoding/readout, number of attempts,
input and output tokens, latency and cost when available. Give the denominator
and parent grouping behind each score, and link raw records or a reproducible
script. State any deviation from the published protocol. A rerun on a public
development set is valuable, but it is not held-out confirmation.

Do not rewrite a frozen protocol or overwrite past outputs to accommodate a
new result. Propose a versioned extension and preserve the old failure and
provenance. The existing synthetic data are CC BY 4.0; original code is MIT,
while [Kev, Qwen and provider materials keep their own terms](THIRD_PARTY_NOTICES.md).
Do not include private customer text or credentials in public issues.

We will distinguish a reported observation, an independently checked
reproduction, a program-derived label, a human review and a new hypothesis.
Opening an issue starts discussion; it does not silently change the published
scores or certify a label.
