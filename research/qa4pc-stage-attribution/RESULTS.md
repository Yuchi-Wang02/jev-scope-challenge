# Jev completed; Qwen stopped at the frozen smoke gate

**Historical original-run report.** A separately frozen outcome-aware amendment
later completed only the unexecuted Qwen jobs. See [combined results](CONTINUATION_RESULTS.md).
The original failure and the original report's counts below remain unchanged.

**2026-09-30. Real execution: 262 Jev HTTP requests and two Qwen physical prefills.
No retries, new weights, new human labels, or Qwen main decisions.**

The complete 524-job plan was committed and pushed in
`543899f7e0e90c3ef7bb85d11233b203a3fedc80` before either model ran. The plan SHA-256
is `a6296efb34aa6e80d79b825152847a66c29060cb980a3fe213d7e7783cf2df29`.
Both journals record that execution commit. Read the [protocol](PROTOCOL.md),
[cohort](cohort.json), [public job hashes](plan_manifest.json),
[derived report](report.json) and raw [Jev](results/jev.jsonl) /
[Qwen](results/qwen.jsonl) journals.

## Jev source agreement

All 24 scenarios in each condition were evaluated; none had invalid outputs.
The two selected scenarios per tree are not controlled counterfactual pairs.

|Route|Mapping 0|Mapping 1|Strict trees, mapping 0 /1|
|---|---:|---:|---:|
|D: plain direct|19/24|19/24|8/12 /8/12|
|G: supplied graph, direct decision|20/24|20/24|9/12 /9/12|
|F: predicted facts, code execution|19/24|20/24|8/12 /9/12|
|L: supplied reference facts, model execution|24/24|24/24|12/12 /12/12|
|F intermediate condition labels|49/56|50/56|Not a new scenario denominator|

L receives source fact labels as inputs. Its perfect agreement is an assisted
execution result, not 100% end-to-end accuracy. The upstream annotations were
already checked for compositional consistency. This cohort has zero new project
human adjudications; all results are agreement with released references.

- G versus D improves three scenarios and regresses two in each mapping.
- F versus G improves zero and regresses one in mapping 0; improves one and
  regresses one in mapping 1. There is no consistent gain from the extra fact calls.
- D/G/L have zero action changes across the two mappings. F changes one final
  action. Only two permutations were tested.
- Source-maybe scenarios answered with a determined yes/no: D 3/7, G 2/7, F 2/7
  in each mapping. Source-determined scenarios answered maybe: D 2/17, G 1/17,
  F 2/17 and 1/17. These are reference-relative errors, not adjudicated truth claims.
- In each mapping, two scenarios contain wrong-but-valid predicted facts whose
  errors are masked at the final expression output. Final accuracy does not
  establish complete fact extraction.
- All 262 Jev responses report `jev-1.13.0`. Probability metadata had zero
  non-unit sums outside the predeclared tolerance, zero displayed top ties and
  zero native-choice/displayed-argmax disagreements in this run.

## Qwen: two smoke prefills, no main score

The frozen smoke gate required semantic correctness on three artificial
expressions in both mappings. Qwen passed the first but failed the second:

|Smoke, mapping 0|Expected|Observed|A/B/C candidate logits|
|---|---|---|---|
|`yes AND maybe`|maybe|maybe|22.25 /22.625 /25.625|
|`no OR no`|no|maybe|21.875 /24.0 /24.25|

Mapping 0 is A=yes, B=no, C=maybe. On the second input, C is the unique top
candidate and the unconstrained top vocabulary token. Conditional probabilities
are A 0.049692, B 0.416067, C 0.534241; candidate mass is 0.994803. This is neither
an exact tie nor an invalid token. The observed action is preserved in the raw
record, while the runner returns `protocol_error` for the **failed smoke gate**.
That operational status does not mean the model response was malformed.

The journal terminates normally with `recorded_failure_requires_repair`. All
256 Qwen main decisions and four remaining smoke decisions are **unexecuted**.
They have null accuracy, zero evaluated rows and explicit missing coverage in
the report; they are not counted as 0/24 or as 24 invalid model responses.
No execution handle remains live, and no attempt was replayed.

## Cost and work accounting

Jev total: 262 completed requests, 159,118 input tokens, 9,956 returned output
tokens, zero retries/unknown-usage calls, 42.640 callback-session seconds. Actual
invoice amount is not established by this ledger.

|Jev condition, both mappings|Calls|Input tokens|Output tokens|Summed callback seconds|
|---|---:|---:|---:|---:|
|Smoke|6|2,918|228|0.984|
|D|48|25,698|1,824|7.484|
|G|48|29,614|1,824|7.545|
|F|112|77,144|4,256|17.703|
|L|48|23,744|1,824|7.467|

F uses 2.33 times G's calls and approximately 2.60 times its input tokens, without
a consistent agreement gain. Callback timings are descriptive; sequential
conditions and uncontrolled service variation do not support a causal speed claim.

Qwen total: two physical prefills, 378 input tokens, zero generated tokens,
0.562 summed callback seconds /0.578 callback-session seconds. Model-byte
verification took 5.984 seconds and loading 3.485 seconds separately; imports and
other process overhead are not included. Existing BF16 CUDA/SDPA checkpoint,
native Torch fallback, no extra warmups or new downloads. The planned 77,528 input
tokens were not consumed. All recorded budgets remained within their limits.

## Verification and analysis correction

Raw journals are preserved byte-for-byte. The analyzer replays chronological
starts/finishes, recomputes native choices and saved candidate readouts, validates
the failed smoke output, and keeps all selected denominators. Tests explicitly
reject reporting absent main outputs as zero accuracy or invalid predictions.

The first analyzer attempt compared all floats bit-exactly across Python
versions. For one raw probability sum, the execution environment recorded 1.0
while the local analysis environment produced 0.9999999999999999. The analyzer
now permits 1e-12 absolute/relative tolerance **only for finite floating-point
fields**. Labels, integers, booleans, keys and raw execution files are unchanged.
This post-run analysis repair changed no action, prompt, reference or request.
The report verifies in both the system Python and pinned model environment.

A second count replay reads native choices directly from the published journal,
joins them to the pinned source by IDs, and executes expressions with a separate
explicit truth-table evaluator. It reproduces all eight Jev final-condition
counts and both fact counts without the tokenizer, weights or private plan.
This checks arithmetic/source joins; it does not independently validate semantics.

After reconstructing private inputs from the pinned sources/tokenizer, run:

```powershell
python research/qa4pc-stage-attribution/analyze.py verify
python -m unittest discover -s tests -p test_qa4pc_results.py -v
```

The lighter source-based count check requires only the three pinned dataset files:

```powershell
python research/qa4pc-stage-attribution/verify_counts.py --source-dir .local/qa4pc-audit
```

Source text/private request retention follows the [source audit](../qa4pc-audit/README.md).
Published outputs do not imply a new license for QA4PC. The synthetic offline
tests do not download or independently semantically adjudicate the source.

## Decision

The Jev portion does not justify more decomposition layers on this cohort.
Supplied-fact execution succeeds, while predicted facts and direct decisions
still disagree with some references. Fact interpretation, task framing and
reference semantics are candidates for later examination, not a proven single
causal mechanism.

The intended two-model comparison is incomplete. The smoke design also mixed
interface validity with semantic competence: excluding a model for a wrong but
well-formed answer can prevent measuring exactly the weakness under study.
Any continuation must be an explicit outcome-aware gate amendment, retaining
these two prefills and their costs. It must not be called a software fix, a
successful original gate, or an untouched confirmation study. See
[the stage reflection](INTERPRETATION.md).
