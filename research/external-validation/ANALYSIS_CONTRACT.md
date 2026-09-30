# Offline analysis of the prospective comparison

Status: implemented and checked on synthetic journals and preserved technical
smoke records on 2026-09-30. No ShARC predictions or new model calls were produced.
This is a prospective reporting contract, not a result for the pending cohort.

## Evidence used by the analyzer

`analyze_comparison.py` requires the separately committed execution freeze and
exact plan/reference hashes. It snapshots both journals under the execution
locks, validates their event sequences, and stores their hashes with the report.
Reports are immutable per journal snapshot. Conflicting existing bytes are
preserved and rejected, not replaced. Analysis imports no API key or model weights.

Every condition must cover the same reference item IDs and use the same visible
state. The six conditions are Jev, Qwen direct and Qwen thinking, each under two
declared option orders. Requests are reconstructed from the common task contract.
The five shallow controls are recomputed from visible inputs without model calls.
Reference labels remain separate from the execution inputs.

Jev decisions, probabilities and usage are rechecked against the raw response.
Qwen input rendering, input IDs, output IDs, final-channel extraction, token usage,
sampling configuration, presence penalty and processor order are rechecked with
the pinned local tokenizer/runtime. A stored action is never sufficient evidence
by itself. These checks establish consistency of saved records, not that an
arbitrary fabricated record could be authenticated as a real model execution.

## Completion and failure are separate

- A condition receives paired metrics only when every planned item has a finished
  result. Missing results are reported as not started or started without a result;
  an incomplete condition has no full-condition score.
- A finished malformed or truncated answer remains a null action in the scoring
  denominator. Execution and protocol errors are counted separately. A final-call
  protocol error can leave a complete grid, so grid completion is not success.
- Order changes count only items with valid actions in both orders. Invalid in
  either order is a separate count, not a semantic answer change.
- Resource reports retain attempts, unresolved calls, status counts, known input
  and output tokens, incomplete usage, closed-session duration, incomplete session
  time, per-call latency sums, setup metadata and observed overruns. Known usage
  with an unresolved attempt is a partial sum, not the complete cost.
- Each condition additionally reports its own input/output tokens, started and
  unresolved attempts, error counts, and recorded callback latency sum, median
  and nearest-rank p95. The percentile is observation at rank `ceil(0.95 * n)`
  among finished callbacks, including failures; no observations means unavailable.
  Partial observations are not a full-grid latency estimate. Thinking/direct and
  option orders are never pooled for this view. Backend loading and verification
  remain shared setup costs rather than an arbitrary per-condition allocation.
- `complete_grid_within_recorded_budgets` and
  `complete_grid_without_execution_or_protocol_errors` are distinct flags. Neither
  means answers are correct or human reference truth is automatically verified.

Scoring follows [paired metrics](PAIRED_METRICS.md): one parent tree is the unit,
all output failures stay in item/pair denominators, and zero eligible denominators
have unavailable rates. Six conditions do not multiply independent sample size.
The analyzer does not infer monetary charges or make a statistical superiority
claim from a small development pilot. Failed backend setup time is not currently
durable; that execution-core limitation remains in [runner design](RUNNER_DESIGN.md).

## Observed configuration mismatch and repair

The first audit of saved real Qwen records failed strict configuration equality.
Only `output_attentions` and `output_hidden_states` differed: saved `null` versus
the older CPU stub's `false`. Inspection of the installed Transformers 5.3.0
`GenerationMixin.adjust_generation_fn` identified the exact load-path difference.
The pinned local model has no `generation_config.json`; actual `from_pretrained`
falls back to reading the original `config.json` as a generation configuration.
The older CPU stub instead converted an initialized `AutoConfig` object, which
adds those defaults.

`qwen_configuration.py` now calls the same library adjustment method on a
weight-free stub, using local files and disabling remote code. It rejects an
unexpected unpinned `generation_config.json`. No null/false equivalence exception
was added. Full configuration equality remains required. The prospective backend
also checks its actual loaded configuration against this path before generation.
Historical settings, records and scores remain unchanged.

The repaired check passed all eight historical Qwen and eight Jev technical-smoke
records. Five in-memory mutations were rejected: temperature, null-to-false output
flag, presence penalty, processor order and generated-token IDs. Original files
were not edited. These are four existing label-copy fixtures with repeated
conditions, not sixteen independent research examples or new generations.

|Preserved source|SHA-256|
|---|---|
|`research/action-backends/results/jev/run.json`|`746065434596e8163ab20ed6a49147b91ea4a9a469eedaad5787354dc9039690`|
|`research/action-backends/results/qwen/run.json`|`2a0f2e7d49ad78936761dcd156e3d98fa676e37deeb92e66e988c42f8bfcbebc`|

Nine synthetic analyzer tests additionally cover cohort/input drift, invalid
answers, incomplete grids, unknown outcomes, stored-action changes, tokenizer
requirements, budget overruns, final-call protocol failure and disaggregated
cost accounting (including unknown outcomes). Synthetic journals
are software fixtures, never model results.

```bash
python -m unittest discover -s tests -p test_rule_comparison_analysis.py -v
# Existing pinned local environment and files; no downloads or forwards:
python research/external-validation/audit_saved_interfaces.py --model-dir /path/to/pinned/qwen35
# Only after the reviewed-cohort execution freeze and a run exist:
python research/external-validation/analyze_comparison.py --model-dir /path/to/pinned/qwen35
```

## Stage decision

The plan, execution core and analyzer now exist. The unresolved research work is
two human ShARC reviews, adjudication, exact-cohort tokenization, a published
execution freeze and a real comparison. The new orchestration has not itself
completed a live task. Replaying old records does not remove that limitation.
Do not convert additional software tests into a substitute for the research gate
or advertise the pending pilot as a demonstrated model-replacement result.
