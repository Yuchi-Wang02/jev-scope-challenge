# Execution supplement to the prospective design

Read [DESIGN.md](DESIGN.md) for the complete research contract. All choices in
that document remain in force. This supplement specifies the implemented
execution boundary, before any smoke or main call in this study.

- The [cohort](cohort.json) selects 12 of 40 eligible development trees, two
  scenarios each: source labels no13, maybe6, yes5. These counts were observed
  after the label-independent selection; no reranking followed.
- The [plan manifest](plan_manifest.json) commits 648 jobs: 162 Jev, 486 Qwen.
  It records exact input IDs' hashes, per-job hashes, six mappings and 115,668
  planned local input tokens. The Jev planning proxy is 837,792 serialized UTF-8
  bytes plus 4,096 per request; this is not a measured server token count.
- Greedy generation's effective configuration is obtained using Transformers'
  pretrained configuration path without weights, saved in
  [generation_audit.json](generation_audit.json), and checked against the loaded
  model. The actual logits processor list must be empty. No sampled-setting
  carryover, presence penalty or hidden grammar processor is permitted.
- Every Qwen job records physical forwards and raw first-step letter logits,
  full-vocabulary normalizer, top token and top-tie count. Generated routes also
  save every output token, decoded body, EOS status and exact-parser outcome.
  Only first-step raw logits are retained; later distributions are not published.
- Finite and generated-letter jobs have byte-identical rendered prompts and
  input IDs, but are separate physical invocations. Greedy output can resolve a
  raw tie according to the library's behavior; finite ties remain invalid by
  design. The report must keep this contract difference visible.
- Main outcomes, generated invalids and semantic smoke errors never choose
  subsequent jobs. Structural failures stop the relevant backend. Backends have
  independent journals; a stop in one is not permission to amend either plan.
- The unchanged durable journal from the previous study is imported and hash
  pinned. It records successful calls with `action: null` for model-output
  invalids, preserving costs and denominators. Exceptions retain only their
  type to avoid credential-bearing diagnostics.
- The [freeze](freeze.json) pins implementation and dependencies. Verification
  requires a clean committed checkout and recompiles source/token plans without
  inference. Publish the commit before running Jev, then Qwen sequentially.
- Keep upstream prose in `.local`; public reproduction fetches the pinned
  source. Publish raw derived journal outputs and all failures after execution.
  No new human review is implied by tests, CI or program consistency checks.

Preparation and execution (the final two commands consume authorized resources):

```powershell
python research/qa4pc-answer-interface/cohort.py verify --source-dir .local/qa4pc-audit
# The remaining commands require the already-installed pinned Qwen environment.
python research/qa4pc-answer-interface/compile_plan.py verify --source-dir .local/qa4pc-audit --model-dir PATH_TO_PINNED_MODEL
python research/qa4pc-answer-interface/freeze.py verify --source-dir .local/qa4pc-audit --model-dir PATH_TO_PINNED_MODEL
python research/qa4pc-answer-interface/runner.py --backend jev --source-dir .local/qa4pc-audit --model-dir PATH_TO_PINNED_MODEL
python research/qa4pc-answer-interface/runner.py --backend qwen --source-dir .local/qa4pc-audit --model-dir PATH_TO_PINNED_MODEL
```
