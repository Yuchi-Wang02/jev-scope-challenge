# Preserve pre-load failure and repair inherited PEFT dependency

2026-09-30. The first executable attempt is preserved in
[qwen35-smoke-run/run.json](qwen35-smoke-run/run.json). All eleven model files
passed size/hash checks, including both safetensor LFS digests. Importing the
complete runner dependencies then failed: Transformers' set_seed import reached
trainer_utils, which imported inherited PEFT 0.17.1; PEFT requested HybridCache,
removed from Transformers 5.3.0. Zero weight loads, zero generation attempts and
zero model forwards occurred. The earlier narrower architecture import had passed.

Install PEFT 0.18.1 only in the probe venv, a 556,952-byte wheel according to pip's
download display (exact wheel bytes will be checked in the acquisition record).
Retain the original environment's PEFT 0.17.1. The complete import list and local
tokenizer construction now pass without model weights. A terminal-only Unicode
display failure while printing token strings was resolved with Python -X utf8;
it did not affect model artifacts or inference.

Permit the still-unused single weight load and six generation attempts, recording
them in a new qwen35-smoke-repaired directory. No failed artifact is overwritten.
The prompts, seed, sampling settings, 256-token cap and 600-second deadline are
unchanged. No new weight download or prompt search is authorized by this repair.
The old original-checkpoint environment remains available and will be rechecked.
