# Ordinary-model comparator readiness

Historical metadata-only stage. The subsequent [Qwen3.5 technical smoke](QWEN35_SMOKE_RESULTS.md) adds a real local load and six generic generation calls; it is not a research evaluation. The snapshot and counts below retain their original scope.

Captured 2026-09-30T08:04:43.999317+00:00. **Metadata and installed-runtime inspection only: zero inference, zero weight downloads.**

## What is available versus what remains untested

The existing environment uses Transformers 4.55.4, PyTorch 2.8.0+cu128, CUDA 12.8, and NVIDIA GeForce RTX 5070 Ti with 15.92 GiB total memory. GPU display/other allocations further reduce free memory. The inspected caches contain Qwen3-4B instruction, smaller Qwen checkpoints and the historical Base/Kev pair, but none of the three uncached alternatives below. This is a focused cache check, not a scan of every user folder.

|Candidate|Pinned revision|Weight files, GiB|Architecture registered in existing runtime|Decision|
|---|---|---:|---|---|
|[Qwen/Qwen3-4B](https://huggingface.co/Qwen/Qwen3-4B/tree/1cfa9a7208912126459214e8b04321603b3df60c)|`1cfa9a7208912126459214e8b04321603b3df60c`|7.492|True|Existing measured comparator; not a capable-model ceiling.|
|[Qwen/Qwen3-8B](https://huggingface.co/Qwen/Qwen3-8B/tree/b968826d9c46dd6066d109eabc6255188de91218)|`b968826d9c46dd6066d109eabc6255188de91218`|15.256|True|BF16 weights alone leave little total GPU headroom and exceed current free memory; offload/quantization changes the comparator.|
|[Qwen/Qwen3-8B-FP8](https://huggingface.co/Qwen/Qwen3-8B-FP8/tree/220b46e3b2180893580a4454f21f22d3ebb187d3)|`220b46e3b2180893580a4454f21f22d3ebb187d3`|8.789|True|Smaller stored weights, but FP8 loader/kernel/peak memory are untested. Not a BF16 parity result.|
|[Qwen/Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B/tree/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a)|`851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`|8.680|False|Potential new-generation small comparator; requires a separate supported environment and load test. Capability on our task unmeasured.|

All four Hub metadata records report Apache-2.0. No weights are redistributed. Storage totals come from the pinned index and Hub file metadata, not a memory estimator. Configuration support does not establish that a model will load or execute, especially with FP8. See [snapshot.json](snapshot.json) for exact bytes, configurations and source hashes.

Metadata discrepancy: the FP8 index declares 9,438,648,320 tensor bytes, while the listed weight files sum to 9,436,628,784 bytes (2,019,536 fewer). Both raw declarations are retained. The initial consistency check incorrectly assumed the index was always a lower bound and failed. Download estimates here use listed file sizes; neither declaration proves actual loaded tensor memory. The discrepancy was not resolved by downloading weights or silently replacing upstream metadata.

## Material correction to the interpretation of our 512-token control

The [Qwen3-4B model card at our exact checkpoint revision](https://huggingface.co/Qwen/Qwen3-4B/blob/1cfa9a7208912126459214e8b04321603b3df60c/README.md) advises sampling in thinking mode and explicitly warns against greedy decoding. It also recommends much longer output allowance for general benchmarking. Our frozen control deliberately used a 512-token greedy budget and a forced final native readout. That is a bounded engineering configuration, not the vendor-recommended reasoning baseline.

Its measured 58/72 and 59/72 remain unchanged and its truncated outputs remain counted. The original six sampled smoke outputs still do not implement the frozen greedy protocol; preserving them was correct. However, repairing the implementation to match a protocol does not make that protocol a strong or recommended comparator. The card cannot establish that sampling or a larger budget would fix any particular error. Do not silently pool, rescore or rerun the closed 72-input grids.

## A fair next comparison needs two separate questions

1. **Capability reference:** on new reviewed material, use a supported ordinary-model interface with predeclared sampling, output format and adequate finite output budget. Record incomplete outputs, seeds and all work. If it samples, use a small fixed set of seeds and report variation at the parent level; never choose the best seed.
2. **Budget-constrained component:** compare named configurations at fixed calls/tokens/latency or cost levels. Different tokenizers and hidden hosted compute make these different budget axes, not interchangeable fairness guarantees. A 512-token control belongs here, alongside the no-thinking readout.

For both, freeze the same visible evidence, policy, tools and external help. Keep the known-grammar code baseline. Report final-answer parsing failures separately; a forced A/B/C logit readout is not natural generated-answer accuracy. Model family/size, precision, template, runtime version, generation settings and readout are separate factors.

No new model has been selected or acquired by this audit. A prospective Qwen3.5-4B setup would require roughly the listed weight bytes plus dependencies, isolated from the frozen Transformers 4.55.4 environment. The download scope, disk destination and smoke budget must be recorded before acquisition. The user has also been asked whether another capable API/local model is already available; no such resource is assumed.

## Reproduce the audit

```powershell
python research/baseline-readiness/preflight.py verify
```

Verification is offline snapshot consistency, not a fresh availability, license or compatibility check. The capture implementation allows only four named models and four metadata filenames, caps 20 logical fetches and 8 MiB final response bodies, and refuses to overwrite the historical snapshot. Raw fetched metadata is kept in ignored local storage; only the derived snapshot and source hashes are published. The capture imports the installed runtime to inspect its registry/GPU but never loads model weights. No credential is required or collected.

Completion pass: 2 new logical fetches, 2 redirects, 153,857 new final-response bytes; 17 saved payloads / 230,305 bytes reused. Zero model forwards.

The initial capture stopped on a 404: Qwen3.5-4B has no generation_config.json in its pinned file listing. Seventeen successful payloads were retained, and the failed fetch adds one initial attempt. The recovery reads those payloads and fetches the two remaining metadata files; it does not restart model acquisition. The missing configuration is recorded as absent, not invented as defaults. Initial redirect counts and failed-body bytes were not retained. This software repair has no model outputs or inference cost.
