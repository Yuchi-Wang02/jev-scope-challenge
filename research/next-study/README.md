# Is the Decision Model Better Than the Model It Came From?

An exploratory follow-up to the cancellation probe. Compare a pinned Qwen3-4B
**Base** checkpoint through its original LM head before and after Kev's public
LoRA, then evaluate Kev's complete pointer path. The earlier instruct-model
result is a regression reference, not this study's unchanged parent.

See [the detailed plan](PLAN.zh-CN.md). Execution status, exact provenance, data,
scripts and real model records will be saved here as the study progresses.
The baseline design is informed by Kev's existing native/adapted probes; it is
not claimed as a new architecture or an independently reviewed benchmark.

Phase 1 has no new training. Later head-only training depends on this diagnosis
and requires its own data, controls and execution record.

## Execute

The tested local stack starts with Python 3.10.18, torch 2.8.0+cu128,
transformers 4.55.4 and peft 0.17.1. Historical Kev model code is vendored with
its Apache-2.0 license and exact provenance hash; today's full Kev package is
not installed. Install a CUDA-compatible torch build appropriate to your device.

```bash
python research/next-study/study.py build
# Download only these exact revisions into your private model cache:
hf download Qwen/Qwen3-4B-Base --revision 906bfd4b4dc7f14ee4320094d8b41684abff8539 --cache-dir /your/cache
hf download jaredpalmer/kev-4b --revision c4bfa11b0dc07691884f2d97f1c4c4c05c92e416 --cache-dir /your/cache
python research/next-study/study.py run --cache /your/cache
python research/next-study/analyze_study.py
python research/next-study/analyze_study.py --verify
```

Model weights (about 8.2 GB total) stay outside Git. For a new replication, use a
separate checkout and an empty study `results/` folder. The runner rejects existing
scientific records rather than selecting a successful rerun. Full execution,
probability metrics and limits belong in the saved report, not guessed scores.
