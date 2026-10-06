# A capable ordinary-model reference: prepared, not run

Status at preparation: **zero model generations**. This is one proposed supplementary arm on the existing rule-direction inputs, not a new cohort or an independent confirmation. [Protocol](PROTOCOL.md) · [Exact requests](requests.json) · [Model metadata](model_metadata.json).

The original Jev and Qwen3.5-4B nonthinking configurations shared 24 errors among 108 inputs per mapping. This arm asks whether the same signature persists with one capable ordinary model using a normal reasoning configuration. It is not an equal-compute comparison, and success or failure would not establish a novel algorithm.

## Concrete scope

- `claude-sonnet-5-5`, adaptive thinking, high effort, up to 8,192 generated tokens per request including thinking.
- All 222 original Qwen prompts: 108 main inputs in two mappings, plus six independent smoke decisions. Text is unchanged; the native provider wrapper changes.
- One user message, no examples, special hints, tools, retrieval, new system instructions or schema-forced answers.
- Maximum 222 generation attempts, zero retries, $20 of standard-price reservation. Every job reserves its token-count estimate plus 2,048 input tokens and the full output allowance before dispatch.
- Only exact lowercase final labels `yes`, `no`, `maybe`, with surrounding whitespace removed. Thinking blocks are preserved but never parsed for an answer.

The full-stage cap is 600,000 reserved input tokens and 1,818,624 maximum output tokens, or $19.38624 at the checked standard prices. The exact request-specific reservation is computed by `prepare.py verify` from the [provider counts](token_counts.json), rather than treating old Qwen token counts as Claude counts. This is budget control, not an invoice. A credential and a successful model-list query establish availability, not spending approval.

Completed free counting covers all 222 inputs: **58,288 estimated input tokens**, **512,944 reserved input tokens** including allowance, and **$19.212128** of request-specific standard-price reservation. The preparation journal contains 222 successful counts and one preserved HTTP 429; it contains no model generation.

Generation requires direct user approval of this provider and budget. No approval record has been created during preparation. There is no generation journal or model-result report at this stage. Software tests contain fabricated transport fixtures solely for implementation checks and are not saved as model results.

## Preparation and execution

From the repository root, using an available Python 3 interpreter:

```powershell
python -B research/rule-direction/capable-reference/prepare.py compile
python -B -m unittest discover -s research/rule-direction/capable-reference -p test_runner.py -v
python -B research/rule-direction/capable-reference/prepare.py seal
python -B research/rule-direction/capable-reference/runner.py --dry-run
```

Compilation and dry-run are offline. The saved free token-count requests were sent only to the provider's `count_tokens` endpoint. Initial preparation stopped after 121 successful counts and one HTTP 429. The preserved [preparation correction](preparation-history/token-count-rate-limit.json) authorizes one paced continuation of remaining counts, retaining the successful prefix and error. This is a metadata-preparation retry, not a generation retry; it does not change any scientific input.

After direct user approval, an `approval.json` record must name this model, the $20 cap, the exact freeze SHA-256 and a nonempty summary of that authorization. The runner checks it before reading the environment credential or sending generation requests. Then the bounded execution command is:

```powershell
python -B research/rule-direction/capable-reference/runner.py --execute --max-usd 20
python -B research/rule-direction/capable-reference/analyze.py build
python -B research/rule-direction/capable-reference/analyze.py verify
```

The runner journals and flushes a start before each request, uses fixed two-second pacing, and never retries. Unresolved requests, unknown usage, protocol/transport problems or truncation stop further calls. Normal completed wrong answers and invalid final text remain observations and do not change the grid. A partially run arm remains incomplete; the analyzer does not create an apparent results artifact when no generation attempt exists.

## Interpretation and stop

Report the original nine cells and controls, both mappings, critical direction pairs, complete vocabulary families, errors resolved among the old 24 and new errors among the old 84 correct inputs, invalid/truncated outputs and all costs. The twelve lexical families reuse three logical patterns and are not independent real-world policy samples.

If the strong reference resolves the signature, narrow the earlier finding to the tested configurations. If it preserves the signature, first obtain independent review of the formal-versus-pragmatic interpretation before seeking fresh material. Either outcome ends this single arm; no automatic prompt search or additional model sweep follows. The original grammar program already solves the finite grid, so this closeout comparison may clarify an interpretation without yielding a paper contribution.

The old prompts, labels, protocol, freeze and model journals are preserved. The original synthetic inputs retain the repository's license. This preparation does not fork a provider repository, publish to GitHub, amend historical results or submit a paper.
