# Cancel the Right Thing: Jev vs a Frozen 4B

[Research map and status](RESEARCH_INDEX.md) · [Credits and reuse](THIRD_PARTY_NOTICES.md) ·
[Citation](CITATION.cff) · [Reproduction guide](REPRODUCIBILITY.md)

**Same words. Different scope. Opposite decisions.**

Can an off-the-shelf 4B handle the same cancellation decisions as Jev without fine-tuning?
We ran a direct live comparison on 12 predefined four-way cases. Swap the action's
target or the instruction's role, then swap the clause order. Every input, prompt,
prediction and failure is inspectable.

**Jev led this probe: 12/12 vs 8/12 complete cases.**

The direction persisted across both candidate mappings and the repeat. This identifies a gap for this frozen readout on these inputs, not all open models.

**[Play the four-line challenge online](https://yuchi-wang02.github.io/jev-scope-challenge/)**
before seeing the model decisions. A [standalone HTML copy](docs/four_line_challenge.html)
also runs offline. Both replay the saved S01 case; your choices trigger no model
or API call.
The reveal also shows the grammar-specific Python control that solved all 12
predefined cases; this synthetic probe does not show that Jev is necessary.

The separate [Can 548 calls beat always deferring? calculator](https://yuchi-wang02.github.io/jev-scope-challenge/risk_tradeoff.html)
compares three saved historical Kev-LoRA development paths with zero-model-call
always-defer and grammar-specific code controls. Charging only needless deferrals
makes the line reader never optimal; charging every deferral gives it a narrow
winning range among the model paths and always-defer, where the grammar-specific
code still has lower loss. These are hypothetical cost assumptions on 72 synthetic
views, not new Jev results or measured real-world utility. The controls correct an
earlier three-path comparison that emphasized a pairwise crossover.

![All predefined case results](assets/scope-results.png)

## The four-line challenge

Target: **mobile plan**. All four messages have the same word multiset.

| Version | Customer message | Correct decision |
|---|---|---|
| A | Cancel the phone insurance. Keep the mobile plan active. | KEEP |
| B | Cancel the mobile plan. Keep the phone insurance active. | CANCEL |
| C | Keep the mobile plan active. Cancel the phone insurance. | KEEP |
| D | Keep the phone insurance active. Cancel the mobile plan. | CANCEL |

A/B must flip correctly; A/C must hold correctly. A keyword count cannot tell
them apart. There are also quoted-example and superseded-request cases.
The [interactive challenge](https://yuchi-wang02.github.io/jev-scope-challenge/) reveals both candidate
mappings for every S01 message after you answer; the full explorer below covers
all 12 predefined cases and both rounds.

## Actual results — primary round

| System | Complete cases | Correct decisions | Wrong cancellations |
|---|---:|---:|---:|
| Jev 1.13.0 | 12/12 | 96/96 | 0/48 |
| Frozen Qwen3-4B | 8/12 | 83/96 | 10/48 |
| always_keep | 0/12 | 48/96 | 0/48 |
| keyword | 0/12 | 48/96 | 48/48 |
| known_grammar | 12/12 | 96/96 | 0/48 |


A complete case requires **8/8 correct decisions**: four messages under both
A/B candidate mappings. The 96 decisions are repeated measurements of 48 texts,
not 96 independent samples. Round 1 is a repeat check, never selected over round 0.
Both models produced 192 formal records; see [full results](results/REPORT.md),
[decision CSV](results/decisions.csv), and [raw records](results/).

The known-grammar parser is explicitly tailored to this controlled grammar;
it is not a general natural-language replacement. Its success is part of the result.

## Where the research went next

The live Jev comparison above is the original study. Later diagnostics use a
**historical pinned Kev/Qwen checkpoint**; they are not new Jev measurements or
evaluations of current Kev. Kev's reused code and trained artifacts are credited
separately. Laya was inspected as related work and was not run here.

|Follow-up|What it established|Status|
|---|---|---|
|[Matched base](research/next-study/) and [input boundary](research/layout-boundary/)|Performance changes with adaptation, readout and input layout.|Completed synthetic diagnostics; see exact records and budgets.|
|[Evidence gap](research/evidence-gap/) and [evidence guards](research/evidence-guards/)|Missing evidence, missing fields and abstention are distinct tests.|Development results and post-hoc controls; reserved inputs unscored.|
|[Correct Code, Wrong Facts](research/fact-execution/)|Facts plus a verified executor reached 44/72 versus 31/72 direct, but asserted values for 14/18 missing fields.|Original development only; 144 provisional rewrites await human review.|
|[Line evidence pilot](research/fact-execution/LINE_EVIDENCE_RESULTS.md)|548 forwards reduced false commitments to 6/24 but yielded only 11/48 correct determined decisions.|Failed its prewritten screening rule; [inspect every line judgment](research/fact-execution/docs/line_explorer.html) and the [12-parent paired audit](research/fact-execution/PARENT_PAIRED_AUDIT.md).|
|[Joint routing results](research/fact-execution/JOINT_RESULTS.md)|514 new forwards: joint 34/72 versus 31/72 for both matched direct controls; 60/66 other-request lines became target evidence.|Failed both screening conditions. [Inspect all saved queries online](https://yuchi-wang02.github.io/jev-scope-challenge/joint_route.html); no rewrite, reserved or Jev scores.|
|[Visible-ID gate replay](research/fact-execution/VISIBLE_ID_GATE_AUDIT.md)|An ordinary text-ID gate changes saved joint outcomes from 34/72 to 70/72: 38 corrections and two regressions. Full grammar code remains 72/72.|Post-hoc, zero new forwards; original screen stays failed. Reveals a perfect ID-prefix shortcut in the joint-pilot inputs.|
|[One Line, Two Facts](research/fact-execution/MULTIFACT_LINE_STRESS.md)|With faithful one-owner routing, two target facts on one line allow 0/56 exact fact vectors versus 56/56 in a mixed-scope control.|Software reachability only; zero model calls or new independent examples.|
|[Flip one answer](research/external-validation/SHARC_PAIR_AUDIT.md)|The public ShARC train split contains 3,334 strict one-history-answer contrasts; 3,037 change provisional action label.|A [30-pair blinded review queue](research/external-validation/SHARC_REVIEW_PROTOCOL.md) is frozen; zero reviews, model calls or new benchmark claims.|

The [post-hoc oracle decomposition](research/fact-execution/LINE_ORACLE_DECOMPOSITION.md)
motivates the joint-route test but uses unavailable construction labels; its
counterfactual 29/72 to 68/72 change is **not** a model score. The executed
[joint-route protocol](research/fact-execution/JOINT_EXECUTION_PROTOCOL.md) stays
unchanged as a historical pre-inference artifact. Its
[scope audit](research/fact-execution/JOINT_ROUTE_SCOPE_AUDIT.md) still applies:
the completed run scored no packed multi-fact line. The
[research map](RESEARCH_INDEX.md) separates every completed result, derived
analysis, pending review and unrun plan.

The next [target-switch diagnostic](research/request-ownership/)
holds each two-request record block fixed and changes only the requested ID.
Both IDs share one namespace. Its 24 constructed scenes / 48 views and query
plans remain unscored. The [guarded execution protocol](research/request-ownership/EXECUTION_PROTOCOL.md)
now freezes 500 scientific forwards /188,797 input tokens plus two unscored
warmups, with a paired scorer and overwrite protection. A distinct local run
approval is pending; this is not independent confirmation.
The [interactive input explorer](https://yuchi-wang02.github.io/jev-scope-challenge/request_switch.html)
lets you switch every target, inspect exact planned prompts and reveal
program-derived references. It displays prepared inputs, with no model predictions.

## Inspect or reproduce without an API key

Use Python 3.10 (the executed environment was Python 3.10.18):

```bash
pip install -r requirements.txt
python -m unittest discover -s tests -v
python verify_evidence.py
python analyze.py --verify
python analyze.py
```

This checks and recomputes the committed real results; it makes no model calls.
Download/open [the standalone result explorer](docs/explorer.html) to inspect
all four variants, mappings, rounds, probabilities and exact requests offline.
It replays saved results; changing a selector does not run a model.

## Run your own live comparison

```bash
python replicate.py --backend jev --phase smoke --output .local/my-replication --dry-run
# Set TYPESAFE_API_KEY privately in your shell, then:
python replicate.py --backend jev --phase smoke --output .local/my-replication
python replicate.py --backend jev --phase formal --output .local/my-replication
```

Use a fresh output directory: the replication entry point protects the published
results and stores each execution's runtime in its own session directory. A full
cache hit creates no backend and makes no model calls. Unknown HTTP costs stop
execution until reconciled. See [post-run tooling changes](CHANGELOG.md).

For Qwen, install the CUDA-compatible PyTorch 2.8.0 build for your platform
([official instructions](https://pytorch.org/get-started/locally/)) plus
`transformers==4.55.4` and `accelerate==1.10.1`; then:

```bash
python replicate.py --backend qwen --phase smoke --output .local/my-replication
python replicate.py --backend qwen --phase formal --output .local/my-replication
```

The pinned weights require about 8 GB on disk and were already cached for our
run. They are not included. With no local override, the runner resolves the pinned
HF revision. The historical runner accepted a local snapshot path override.
Actual runtime versions, tokenizer/template hashes and hardware are in `results/`.
Fresh inference installations and other hardware have not been independently reproduced.
`run.py` is preserved as the original frozen runner, including its historical
limitations. The newer replication entry point does not accept local path overrides.

## Matched-base follow-up (completed)

The follow-up asks **Is the Decision Model Better Than the Model It Came From?**
We completed 864 real forward records using a matched Qwen Base, its original
LM head before and after Kev's public LoRA, and the trained pointer path. On its
12-parent exploratory test, the three paths scored **85/144, 111/144, 98/144**
correct decisions, but only **0/12, 1/12, 0/12** fully correct parents. This is
an exploratory synthetic diagnostic with AI-reviewed labels, not a broad model
ranking. See [the research note and result explorer](research/next-study/README.md).
The stopped first attempt and numerical-control amendment are preserved too.

## Cost, scope and provenance

- Live Jev: `jev-1.13.0`; frozen Qwen: `Qwen/Qwen3-4B` at revision
  `1cfa9a7208912126459214e8b04321603b3df60c`, BF16, thinking disabled, native
  next-token A/B readout. No fine-tuning, teacher, calibration or test-time search.
- Jev used 195 HTTP attempts including smoke,
  89,563 known input tokens, and
  **USD 0.003762 usage-estimated API cost**.
  This is not an account invoice. Local GPU time/memory are reported separately.
- Short, original, synthetic English messages; **no independent human label audit**.
  Labels were constructed from rules and AI reviewed. Approval to execute does
  not mean a human audited every label.
- Purposive templates and explicit markers make this a small diagnostic probe.
  It does not establish production safety, equivalence, general model superiority,
  or whether dedicated training is necessary. Hosted/local latency is not a
  controlled architecture comparison.
- [Protocol](PROTOCOL.md) and [freeze manifest](manifest.json) were saved before
  live calls. The data were not made harder after inspecting predictions.

## Extend the challenge

Recompute the published results first, then [open a structured challenge or
reproduction issue](https://github.com/Yuchi-Wang02/jev-scope-challenge/issues/new/choose).
A useful contribution is a new clear four-way case, a label objection with its
reasoning, or results from another backend with exact prompts and costs. The
[contribution guide](CONTRIBUTING.md) explains the minimum evidence and how to
keep a versioned extension separate from this fixed v0.1 test. Report wins,
losses and mapping sensitivity.

The series asks *You Might Not Need Jev*; this release does not announce that
Jev is useless. Independent project, not affiliated with or endorsed by TypeSafe.
Paired behavior tests and native logits are established ideas; see
[CheckList](https://aclanthology.org/2020.acl-main.442/) and
[SemIf](https://github.com/TheoLeeCJ/SemIf-OpenJev).

Created by Yuchi Wang with AI-assisted experiment design, implementation and
analysis. Original code: [MIT](LICENSE). Original synthetic data: [CC BY 4.0](data/README.md).
The vendored Kev implementation remains **Apache-2.0**, with its full license,
exact source commit and unchanged-source checks. Kev/Qwen model weights retain
their upstream terms. [Credits and reuse](THIRD_PARTY_NOTICES.md) distinguish
copied code, executed weights and research inspiration, including Laya.
Use [CITATION.cff](CITATION.cff) and the relevant study commit when citing this
work; also credit the upstream components used in that result.
