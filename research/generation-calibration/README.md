# Qwen3.5 output-budget calibration: completion is separate from correctness

Development-only calibration on twelve newly authored elementary fixtures. This is not a Jev comparison, new independently reviewed research dataset, capability ceiling or a model ranking. The earlier 72-input research grids remain closed.

Execution status: **completed**. Protocol, prompts, seeds, settings, parser and cap-selection rule were frozen at `e907e7c7c15c4c66cf06616aaa5c458e01fe4b2f` before outputs.

## What ran

Each of 12 fixtures was run with seeds 17 and 43 in direct and thinking modes: 48 planned calls. These are repeated measurements of 12 synthetic development fixtures, not 48 independent research examples. Exact program references are balanced A/B/C, four each; no human labels are claimed.

|Mode|Completed calls|Natural EOS|Valid final JSON|Strict valid + content match|Token-cap stops|Generated tokens|Generate seconds|Selected development cap|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|direct|24/24|24/24|24/24|22/24|0|201|10.824|256|
|thinking|24/24|24/24|11/24|11/24|0|11,262|357.585|None qualified|

The strict match column counts parser failures as unsuccessful delivery, not proven wrong answers. Content among accepted outputs and the rejected final wrappers are examined separately below.

Total generated tokens: 11,463 /55,296; planned input tokens: 8,128 /200,000. Generation-stage wall time: 368.783 seconds /1,800; load time: 3.468 seconds. Peak allocated/reserved PyTorch memory: 8.843/8.957 GiB. Zero paid API calls, new weights or dependency downloads. No execution retries.

## Predeclared cap selection

A cap qualifies only when all 24 calls in the mode have naturally ended and yield strict final JSON by that token count. Correctness does not enter the selection. Lower-cap entries below are saved-trace availability checks, not additional model calls or measured lower-cap latency.

|Mode|256 tokens|512 tokens|1,024 tokens|2,048 tokens|
|---|---:|---:|---:|---:|
|direct|24/24|Not executed|Not executed|Not executed|
|thinking|0/24|6/24|11/24|11/24|

For thinking, every call reaches natural EOS, but 13 final response(s) fail the strict format contract. No cap qualifies for this interface. This is a format gate failure, not evidence that increasing the token cap would fix it.

A selected cap is only a starting point for similar development prompts. It is not a demonstrated adequate budget for unseen reasoning tasks, long contexts or realistic policy decisions. If a mode has no qualifying cap, this run supplies no recommendation; do not extend it in search of a passing configuration. Content errors remain visible even if every output parses.

## Every fixture and both seeds

Cells list seed 17 then 43 as answer/status and generated-token length. Program references are elementary construction checks, not independent human judgments. Do not turn these counts into a benchmark headline.

|Fixture|Reference|Direct, seeds 17 /43|Thinking, seeds 17 /43|
|---|---|---|---|
|copy|C|C (7) / C (6)|C (383) / C (621)|
|threshold|B|C (7) / B (7)|invalid_json (347) / B (759)|
|missing|C|C (7) / C (7)|invalid_json (384) / invalid_json (360)|
|sum|A|A (12) / A (12)|invalid_json (252) / A (906)|
|intersection|B|B (11) / B (11)|B (719) / invalid_json (406)|
|latest|A|A (11) / A (7)|A (658) / invalid_json (439)|
|conjunction|B|B (12) / B (12)|invalid_json (517) / invalid_json (1197)|
|minimum|A|A (6) / A (6)|invalid_json (133) / A (365)|
|lookup|C|C (6) / C (6)|invalid_json (259) / invalid_json (293)|
|count|C|C (11) / B (11)|invalid_json (299) / invalid_json (485)|
|alphabetical|A|A (7) / A (7)|A (463) / A (351)|
|nested|B|B (6) / B (6)|B (351) / B (315)|

## Post-run format inspection, outside the primary gate

Inspection after all outputs found 13 rejected finals consisting of exactly one json-marked Markdown code block. After inspecting only that final block, 13 inner objects match their program references. This descriptive normalization was chosen after outputs and is not the frozen parser, a replacement primary score, or a new model run. It does not change cap qualification. No content is extracted from an unfinished thought.

For each mode, accepted content matches / accepted strict outputs: direct 22/24; thinking 11/11. Distinguish a wrong answer from a correct answer in a rejected wrapper. A future interface may reasonably allow one final JSON fence or constrain the final schema, but it must declare that contract before new evaluation. Do not attribute this format mismatch to deficient reasoning or advertise it as a dedicated-model advantage.

## Interface and scope

Pinned Qwen3.5-4B revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, BF16 on RTX 5070 Ti, Transformers 5.3.0 and torch 2.8.0+cu128. No quantization, CPU offload, constrained decoding or forced answer readout. The saved runtime and prior hash-verified model manifest identify the installation.

Sampling follows the pinned card's general-task row: direct temperature/top-p 0.7/0.8, thinking 1.0/0.95, top-k 20, min-p 0, repetition penalty 1 and presence penalty 1.5. A tested standard processor subtracts the presence penalty once for each generated token type, excludes the prompt, and is asserted before temperature/top-k/top-p in every actual generation. This is established decoding logic, not an algorithmic contribution. It differs from the earlier smoke's zero-presence-penalty configuration; that smoke is not a matched causal control. These finite caps remain below the vendor's general benchmarking length recommendation.

The parser requires EOS, a completed thinking boundary where applicable, and exactly one final JSON object. It rejects duplicate keys, multiple answers, markdown fences, trailing prose and incomplete thoughts. The generation code never receives the reference answer. Later content checking does not modify an output or choose a different seed.

## Evidence, reproduction and next gate

- [Frozen protocol](PROTOCOL.md), [complete input/call plan](plan.json), [preparation log](PREPARATION.md), [CPU checks](cpu_checks.json).
- [All raw inputs/outputs and token IDs](results/run.json), [derived summary](summary.json), [execution script](run.py). [Local-tokenizer audit](token_audit.json) reconstructed all 48 rendered inputs/input IDs and decoded output IDs without a model forward. Its [optional replay](audit_tokens.py) requires the local tokenizer; the CI audit checks its raw-record hash, not a fresh tokenizer run.
- Sources: [pinned Qwen card](https://huggingface.co/Qwen/Qwen3.5-4B/blob/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a/README.md), [vLLM penalty semantics](https://github.com/vllm-project/vllm/blob/v0.11.0/vllm/model_executor/layers/utils.py). No vLLM source was copied, forked or executed.

Offline checks require full Git history, no weights or credentials:

```bash
python research/generation-calibration/prepare.py
python research/generation-calibration/analyze.py --verify
python -m unittest discover -s tests -p test_generation_interface.py -v
```

Live replication uses the previously documented isolated Qwen3.5 environment and model directory, a clean committed checkout and a new output path. It performs additional local inference; no automatic rerun is part of verification:

```bash
python -X utf8 research/generation-calibration/run.py --model-dir MODEL_DIR --output NEW_RUN_DIR
```

Milestone audit: the interface, strict parser and finite-budget selection are now exercised on saved real outputs. The remaining scientific gap is new, independently reviewed material and evidence that the task matters beyond a known-grammar program. Neither a valid JSON response nor a successful elementary check establishes reliability on that target. Next decisions must address task semantics and a capable comparison, not enlarge this calibration until it looks impressive. The previous research grids and human-review statuses are unchanged.
