# Same records, different request: bounded execution protocol

**Pre-inference execution freeze; awaiting a distinct run approval.** This
protocol adds a guarded runner and scorer to the existing unscored
[design preparation](PROTOCOL.md). It does not modify that historical artifact,
authorize itself, or contain model results. The previous 548- and 514-forward
approvals covered different completed experiments.

## Question and scope

Can a visible request-ID equality gate improve **complete target-switch pairs
correct /24**, without increasing false commitments, relative to the same
ungated saved joint routes? The 24 parents /48 views hold each pair's records
and policy fixed and change only the requested ID. Both IDs have the same
prefix. Twelve parents use IDs differing in one character and twelve use IDs
differing in all five characters. References are program-derived: 18 ALLOW,
18 DENY and 12 INSUFFICIENT views; 36 determined views in total.

This is a new-scene development diagnostic using inspected policy and sentence
grammar. It is not independent language transfer, a held-out confirmation,
a new Jev result, or an evaluation of current upstream Kev. The model remains
the **historical upstream-trained Kev-LoRA N1**: Qwen3-4B-Base revision
`906bfd4b4dc7f14ee4320094d8b41684abff8539` plus jaredpalmer/kev-4b adapter revision
`c4bfa11b0dc07691884f2d97f1c4c4c05c92e416`, read through its native causal logits.
No new training occurs. The upstream pointer head is not used for predictions.
See [attribution and license details](../../THIRD_PARTY_NOTICES.md).

## Frozen physical work and derived comparisons

|Physical scientific arm|Forwards|Input tokens|Purpose|
|---|---:|---:|---|
|Full joint routing|200|85,214|One fixed-order field/value/ownership choice per line.|
|Full direct decisions|200|71,050|Distinct option orders, matching joint calls per view.|
|Filtered direct decisions|100|32,533|Remove explicit foreign lines before direct reading.|
|**Unique scientific union**|**500**|**188,797**|Every row must be retained and validated.|

Two additional **unscored warmups** each contain only the pinned EOS token
151643. The total planned model invocations are 502 and total input tokens
including warmups are 188,799. There is no generated explanation, chat template,
thinking trace, sampling, retry, paid API, new download, old 72-view development
rescore, rewrite score or reserved score. Maximum scientific prompt length is
539 tokens. Existing local cached files are the only model source.

The six model methods derive from this physical union:

- `joint_full`: aggregate the 200 full joint routes and execute the unchanged
  four-state policy program.
- `joint_gated`: reuse those same 200 saved routes; mask DROP lines to
  OTHER_REQUEST using only the visible header and line. KEEP and UNKNOWN retain
  the model's selected route. No additional inference occurs.
- `direct_full` and `direct_filtered`: average conditional candidate
  probabilities after mapping each option position to its semantic action.
- `single_full` and `single_filtered`: use mapping zero for all
  48 views, subsets costing 16,314 and 14,974 input tokens respectively.

Known-grammar parsing and always-INSUFFICIENT are separate zero-model controls.
For direct aggregates, exact ties use ALLOW, DENY, INSUFFICIENT order. Each raw
choice uses the first maximum logit in its frozen candidate order. Conditional
candidate softmax values and candidate vocabulary mass are recorded; neither
is a calibrated correctness probability.

The gate selects 100 KEEP and 100 DROP line instances in this construction.
A hypothetical router skipping DROP lines would use 100 queries /42,627 tokens;
this is a **projected subset**, not a newly timed deployment or additional run.
The replayed `joint_gated` uses the full 200 /85,214 historical route outputs.
Filtered direct matches the hypothetical subset's call count, not its tokens
or measured latency. The full direct arm matches full joint calls, not tokens.
Filtered ensemble depth varies with evidence sufficiency (one or two orders
for uncertain views, two or three for determined views); the fixed single-order
anchors are necessary to interpret filtering apart from ensemble depth.
Method rows and anchors must never be added together as physical work.

## Source freeze, execution and failure contract

[execution.py](execution.py) merges each prepared prompt with its stored tokens
and attaches the dedicated split `new_scene_development`. Its
[execution manifest](preparation/execution_manifest.json) binds the exact query
union, prompt/token/candidate identities, source files, analyzer, tests, weights
checksum reference, cached model configurations, budgets and seed. The
[merged execution plan](preparation/execution_queries.jsonl) has 500 inspectable
rows. SHA-256 uses LF-normalized source bytes so Linux and Windows agree.
Raw rows preserve the full frozen job payload, including identifiers, tokens
and candidate ordering. Query IDs and evaluation metadata are not prompt text.

The original preparation artifacts remain byte-for-byte unchanged. Their
`execution_ready: false` describes that historical preparation; this separate
freeze supplies the later runner. `build` reads cached configuration files and
verifies existing preparation, with no weight loading or inference. It creates
freeze files once and refuses a differing existing freeze. `verify-freeze` is
read-only and requires neither model cache, tokenizer nor torch.

Fresh execution requires a clean committed checkout and the explicitly reviewed
configuration hash. The CLI hash is an accidental-execution guard, not evidence
of human approval. The runner verifies the existing freeze; it cannot silently
regenerate a new plan. It atomically reserves `results/v0.1` and refuses any
existing directory, including an empty or partially written one. There is no
resume, replacement, subset selection or automatic retry under one approval.

The existing Windows CUDA environment uses bfloat16 model weights and math-only
SDPA; flash, memory-efficient and cuDNN SDPA and TF32 are disabled. Library
versions, Python, GPU, CUDA and execution commit are recorded. The runner forces
offline Hugging Face/Transformers settings and loads local paths only. Before
any model invocation, it verifies historical weight hashes, model configuration
hashes and all **504 loaded adapter tensors /33,030,144 parameters** against the
cached artifact. The historical weight inventory also includes the unused
pointer-head file; checking its presence does not mean it is used for N1.

The two warmups precede a deterministic shuffle of the 500 scientific jobs with
seed **20261007**. Each job performs one forward at batch size one, reads final
position logits, and records logits, conditional probabilities, candidate mass,
chosen route/action and synchronized wall latency. Latency includes tensor
creation, forward/readout and synchronization, but excludes ledger writes and
subsequent CPU serialization. Total elapsed time includes setup, checksum work,
weight loading, warmups and file bookkeeping; peak allocated GPU memory is
recorded. Gate CPU overhead is not benchmarked by this study.

Before each invocation, the runner durably checkpoints an attempted-call count.
Successful counts advance only after output validation and durable JSONL write.
Attempt counts are conservative upper bounds if the process stops between the
checkpoint and the actual invocation. Exceptions preserve partial evidence and
mark the runtime failed. Failed or incomplete runs are not scored; any further
run needs separate authorization and a separately versioned, disclosed plan.
The complete run requires 500 attempted and 500 saved scientific records,
plus two attempted and two completed warmups.

## Fixed scoring and release content

[analyze.py](analyze.py) must validate the complete 500-row evidence set before
scoring: exact shuffled job order and identity, split, source and configuration
hashes, finite numeric outputs, candidate widths, probabilities reconstructed
from logits, deterministic choices, valid mass/latency, complete runtime,
weight/tensor audit and frozen source blobs at the execution commit. A missing,
duplicate, foreign, corrupt or invalid row cannot become INSUFFICIENT or be
discarded to make a successful subset. An absent run makes analysis fail clearly;
software-test fixtures are in-memory only and never create published model rows.

The primary paired unit is one of the **24 parent scenes**, each with exactly
two distinct target views and different reference actions. Both views must be
correct for complete-pair success. Merely changing the answer earns no credit.
Report each method's complete pairs /24, view accuracy /48, false commitments
/12, determined correctness /36, needless deferrals and wrong determined actions.
For every model method, report paired gains, losses and ties versus full joint
and full direct; retain all correct-to-wrong transitions. Include descriptive
near/distant and family breakdowns without treating small strata as independent
confirmatory tests. Repeated views, lines and queries are not new sample units.

For joint methods, report exact fact vectors, per-field correctness, accepted
target/foreign routes and field/value routing correctness. Report the lexical
gate's KEEP/DROP correctness and UNKNOWN coverage separately. Gate selection is
computed from visible strings before construction labels enter grading. Correct
actions or fact vectors alone do not establish correct supporting records.

The directional gate hypothesis passes this diagnostic only if
`joint_gated.complete_pairs > joint_full.complete_pairs` **and**
`joint_gated.false_commitments <= joint_full.false_commitments`. Otherwise it
fails. There is no reused old threshold, post-result method selection or
significance claim. A pass supports a separately designed follow-up; a failure
and all regressions remain public evidence.

After an approved complete run, the intended release contains raw N1 rows,
runtime, weight/tensor audit, summary, per-view decisions, paired comparisons,
line/fact audits and an English result report. Generated analyses must be
reproducible from saved evidence. No result file, success claim or mock model
measurement is included in the pre-inference release.

Independent human annotations remain **zero**. The visible review packet omits
gold labels but its source and parent identities are public, so it is not fully
blinded. Independent label/evidence review and separate language-transfer data
remain required before any confirmation claim.

## Commands

```bash
python research/request-ownership/prepare.py verify
python research/request-ownership/execution.py verify-freeze
python -m unittest discover -s tests -v
```

The first two commands are offline integrity checks, not model evaluations.
Creating the freeze uses `execution.py build --cache G:/jev-lab/hf-cache` once.
Only after separate human approval, the reviewed configuration can be passed to
`execution.py run --cache G:/jev-lab/hf-cache --approved-config-hash HASH` in the
existing CUDA environment. Read HASH from the committed execution manifest.
`analyze.py` derives outputs only from a complete validated real run;
`analyze.py --verify` subsequently checks those outputs without inference.
