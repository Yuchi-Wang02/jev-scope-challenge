# Jev Scope Challenge

**From cancellation scope to evidence ownership.**

[Research map](RESEARCH_INDEX.md) · [Current claims](RESEARCH_CLAIMS.md) ·
[Novelty and reuse](NOVELTY_MATRIX.md) · [Reproduction guide](REPRODUCIBILITY.md) ·
[Credits](THIRD_PARTY_NOTICES.md) · [Citation](CITATION.cff)

[Milestone audits and next decisions](STAGE_LOG.md) ·
[New candidate-coverage preparation](research/candidate-completeness/README.md)

This is an exploratory research series about how models and programs turn
language into decisions: which request a fact belongs to, whether evidence is
sufficient, and how input representation and rule execution affect the outcome.
The longer-term question is whether existing small models can become reliable
software decision components without new training. That question remains open.

The project began with a live **Jev vs frozen Qwen3-4B** cancellation challenge.
Jev won that probe, and a parser tailored to its grammar also solved every case.
The intermediate studies examine **historical pinned Kev/Qwen checkpoints**.
N1 uses an already-trained Kev LoRA with native causal logits; no new training
does not mean an unadapted model. The latest payment-ownership diagnostic returns
to live Jev with a new, publicly sourced simulated task.

**Current evidence: real, replayable synthetic diagnostics; two reviewers have
submitted judgments on the same 96 payment-study items, with a scope objection;
no reviewer-endorsed reference update or held-out confirmation of a general method.** Several
experiments reuse the same development texts. New forwards, candidate orders
and derived analyses are not additional independent examples.

## Latest: Right Payment, Wrong Order?

**Jev matched all 48 original main references. Two reviews question the
candidate scope of 24 product-reference inputs. One ambiguity smoke case failed.**
A static refund-destination diagnostic uses 12 distinct simulated users from a
pinned tau retail database. Switching target orders should change the answer in
six parent scenes and preserve it in six. Requests include explicit IDs and
constructed item/card references; the underlying records stay structured.

|System / condition|Matches to original references /48|Complete parents under original references /12|
|---|---:|---:|
|Jev, full records, primary mapping|48|12|
|Jev, program-selected related records, primary mapping|48|12|
|Finite-language parser + policy code|48|12|

The reversed option mapping also scores 48/48 in both input conditions.
The prewritten main-grid stop rule was triggered; **no follow-up was run**.
Under the original interpretation, this construction did not expose the
hypothesized foreign-order interference.
It does not establish that Jev or a learned solution is necessary.

**Review update:** Yuchi submitted 96/96 full/related review items. IDs and labels
agree with the construction, but the cover note identifies an unresolved issue:
the displayed orders are called a selected subset without guaranteeing that the
target is among them. This affects 48 product-reference review items /24 inputs.
Explicit-ID inputs remain 24/24 in every condition; the remaining scores depend
on a displayed-candidate interpretation. Tiancheng has now submitted the same 96 items, agreeing on conditional labels
and marking all 48 product-reference items ambiguous. No references have been
changed. Read the [comparison and reporting disposition](research/payment-ownership/REVIEW_DISPOSITION.md).

The independent smoke score is **5/6**. With two Mug orders and no unique target,
Jev selected VALID with returned probability 0.97 against the provisional
NOT_ESTABLISHED reference. The original launch prerequisite stopped there.
An explicit amendment was published **after smoke but before all main calls**;
it changed the launch gate, not the main inputs or scoring. That outcome-aware
change and the single failure are retained, not hidden behind the main score.

Actual execution: **198 requests, 245,241 input tokens, zero retries**, estimated
**$0.010300122** from reported usage (not an invoice). Two-reviewer adjudication
is pending; no strong ordinary-model comparison in this study; main data contains
no intended insufficient-evidence answers. No tau-bench agent score is claimed.

- [Read the completed report and execution amendment](research/payment-ownership/RESULTS_V02.md).
- [Replay exact requests, all six smoke cases and actual responses](https://yuchi-wang02.github.io/jev-scope-challenge/payment_ownership_v02.html).
- [Review the inputs independently](research/payment-ownership/review/README.md).
- [Download the second-reviewer handoff only](research/payment-ownership/review/reviewer_B_package.zip), without results or the first review.
- [Read the proposed candidate-completeness study](research/candidate-completeness/PLAN.md): design only, no new calls.
- [Inspect source, license and scope](research/payment-ownership/README.md).

## Earlier diagnostic: right facts, wrong request

Keep a two-request record block fixed and change only the requested ID. Both
IDs use the same prefix. A complete pair requires both resulting decisions to
be correct; changing the answer alone earns no credit.

On 24 constructed scenes /48 views, the historical Kev-LoRA N1 joint reader
correctly routed **99/100 target lines**, but also accepted **85/100 foreign
lines** as target-field evidence. An explicit-ID program gate vetoed foreign
contributions to the same saved routes:

|Method|Complete pairs /24|False commitments /12 uncertain views|
|---|---:|---:|
|Joint routing + program execution|2|7|
|Same joint routes + visible-ID gate + program execution|23|0|
|Direct full-record ensemble|2|9|
|Direct ID-filtered ensemble|2|10|
|Known-grammar program|24|0|

The gate corrected 30 view decisions without a regression in this run; one
wrong-field extraction remains. Direct filtering produced four corrections
and three regressions. The complete report includes all eight fixed methods,
including single-order anchors and always-defer.

This **passes the prewritten directional diagnostic**. It does not establish
statistical significance, unseen-language transfer, a new extraction algorithm,
or the necessity of a model: the known-grammar program solves every pair. New
scene instances reuse inspected sentence and policy grammar.

- [Read all results, failures and actual costs](research/request-ownership/RESULTS.md).
- [Explore all paired inputs and exact prompts](https://yuchi-wang02.github.io/jev-scope-challenge/request_switch.html). This page shows program references, not model predictions.
- [Inspect raw outputs and derived records](research/request-ownership/results/v0.1/).

Actual work was **500 scientific forwards /188,797 input tokens plus two
one-token warmups**. Gated routes and single-order anchors share those outputs;
they are not extra calls. No new Jev call, download or training occurred.
The [study README](research/request-ownership/README.md) explains the preserved
pre-execution protocols and the later completed runtime.

## Original study: cancel the right thing

**Same words. Different scope. Opposite decisions.** Can a frozen 4B handle the
same cancellation decisions as Jev? Twelve predefined cases change the action's
target or instruction role, then the clause order. Every prompt and result is
inspectable, including both candidate mappings and a separate repeat.

**[Play the four-line challenge](https://yuchi-wang02.github.io/jev-scope-challenge/)**
before revealing the saved S01 model decisions and grammar-code reference.
The [standalone copy](docs/four_line_challenge.html) also runs offline.

|System|Complete cases /12|Correct decisions /96|Wrong cancellations /48|
|---|---:|---:|---:|
|Jev 1.13.0|12|96|0|
|Frozen Qwen3-4B|8|83|10|
|Always keep|0|48|0|
|Keyword rule|0|48|48|
|Known-grammar program|12|96|0|

A complete case requires all four texts correct under both candidate mappings.
The 96 primary decisions are repeated measurements of 48 texts. Round 1 repeats
the result; it is not selected instead of round 0 or added as independent data.
The comparison identifies a gap for this readout on these inputs, not a ranking
of all open models or a demonstration that Jev is necessary.

See the [original report](results/REPORT.md), [decision CSV](results/decisions.csv),
[raw evidence](results/), [protocol](PROTOCOL.md), and
[complete saved-result explorer](docs/explorer.html). The original local freeze
preceded inference; public release followed execution. It was not an externally
timestamped preregistration.

The original Qwen run used revision `1cfa9a7208912126459214e8b04321603b3df60c`,
BF16, thinking disabled and native next-token A/B readout. Jev used 195 HTTP
attempts including smoke and 89,563 known input tokens, with **USD 0.003762
usage-estimated API cost**, not an account invoice. Local GPU resources are
reported separately; hosted/local latency does not isolate architecture speed.

## What the intervening studies show

The [research map](RESEARCH_INDEX.md) separates completed inference, saved-output
analyses, software checks and unrun preparations. It records the matched-base
and input-layout controls, missing-evidence studies, facts-plus-code experiment,
failed line and joint pilots, and post-hoc ID replay with two regressions.

The [cost calculator](https://yuchi-wang02.github.io/jev-scope-challenge/risk_tradeoff.html)
compares saved development decisions with always-defer and known-grammar code.
It exposes how hypothetical deferral costs change the comparison; it does not
measure deployment utility or make new model calls.

The [current claim ledger](RESEARCH_CLAIMS.md) links supported observations and
unsupported broader claims. The [novelty matrix](NOVELTY_MATRIX.md) distinguishes
upstream work, ordinary program composition, our diagnostic evidence and untested
extensions. Independent human review, language transfer, multi-model confirmation,
new training, Hugging Face releases and a project paper remain incomplete.
Prepared review packs do not select or authorize the next experiment.

## Inspect results without a model or API key

Clone with full Git history, use Python 3.10, then:

```bash
pip install -r requirements.txt
python verify_evidence.py
python analyze.py --verify
python research/request-ownership/execution.py verify-freeze
python research/request-ownership/analyze.py --verify
python research/request-ownership/plot_results.py verify
python verify_publication.py
```

These commands check the original and latest evidence without inference or
rewriting results. The [reproduction guide](REPRODUCIBILITY.md) contains the
complete series checks and the distinction between offline recomputation,
fresh inference and independent scientific replication.

## Run a separate original-study replication

```bash
python replicate.py --backend jev --phase smoke --output .local/my-replication --dry-run
# Set TYPESAFE_API_KEY privately in your shell, then:
python replicate.py --backend jev --phase smoke --output .local/my-replication
python replicate.py --backend jev --phase formal --output .local/my-replication
```

Use a fresh output directory and your own API budget. This entry point protects
the published evidence; a full cache hit makes no model calls. Unknown HTTP costs
stop execution until reconciled. The historical `run.py` stays frozen; see
[post-run tooling notes](CHANGELOG.md).

For the original Qwen backend, install CUDA-compatible PyTorch 2.8.0
([official instructions](https://pytorch.org/get-started/locally/)),
`transformers==4.55.4` and `accelerate==1.10.1`, then use `--backend qwen` with
its own fresh output directory. It resolves the pinned revision; approximately
8 GB of weights are required and are not included. Other hardware and fresh
inference installations have not been independently reproduced.

This CLI covers the original cancellation study. Later frozen GPU runners
preserve their published output directories and require separately versioned
replications; this repository is not yet a unified live evaluation framework.

## Contribute and credit

[Challenge a case or report a reproduction](https://github.com/Yuchi-Wang02/jev-scope-challenge/issues/new/choose).
Name the study, commit and record ID; include visible evidence, your reasoning,
exact prompts and costs where applicable. Read [CONTRIBUTING.md](CONTRIBUTING.md)
for the distinction between a label objection, a reproduction and a new extension.
Wins, failures and mapping sensitivity all belong in the record.

Created by Yuchi Wang with AI-assisted design, implementation and analysis.
This repository is not a GitHub fork of Kev or Laya. It vendors pinned Kev code
and has executed upstream-trained artifacts, with **Apache-2.0** retained.
Laya is related work only: no Laya code, weights, data or scores are used here.
Original code is [MIT](LICENSE); original synthetic data are [CC BY 4.0](data/README.md).
Upstream models and provider materials keep their own terms. See
[exact credits and reuse](THIRD_PARTY_NOTICES.md) and [CITATION.cff](CITATION.cff).
No affiliation or endorsement by TypeSafe or upstream authors is implied.
