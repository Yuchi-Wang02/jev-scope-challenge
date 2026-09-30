# Qwen3.5 local technical smoke protocol

Frozen before weight acquisition and model outputs, 2026-09-30. This is an
installation/interface check, not a research evaluation or a capability ranking.
The previously scored 72 candidate-coverage inputs remain closed.

## Resource and implementation boundary

- Model: Qwen/Qwen3.5-4B at `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`.
- Download allowance: 15 GiB of requested model/dependency payloads, zero paid API
  calls. Account separately for file bytes and unmeasured HTTP overhead/retransmits.
  Do not repeatedly redownload weights. Expected weight bytes: 9,319,828,096.
- External model destination: `G:/jev-lab/models/qwen35-4b-851bf6e`.
  No weights enter the research repository.
- Isolated Python 3.10 venv reuses the existing torch 2.8.0+cu128 installation
  through system-site-packages. It installs Transformers 5.3.0, tokenizers 0.22.2
  and huggingface-hub 1.33.0 locally. The old environment is not upgraded.
- Import/config compatibility succeeded before this freeze, without model weights.
  Pip dry-run and install fetched/reused three wheels, approximately 14.3 MB.
- Use the checkpoint's Qwen3_5ForConditionalGeneration class, BF16 on one CUDA
  device, SDPA, no quantization, CPU offload, remote Python code or kernel downloads.
  Native fallback operators are allowed and must be reported.
- One load attempt followed by at most six generation attempts. Stop on model
  load/inference error. Repairs require a separate recorded amendment before any
  new model work. Preserve failed attempt records. Never retry a completed prompt.
- Each prompt allows 256 generated tokens, at most 1,536 total. The inference
  deadline starts immediately before the first generate call: 600 seconds, checked
  at decoding boundaries and before each prompt. A single kernel cannot be
  interrupted by this check; record any overrun. Model load time is separate.

## Fixed inputs and generation

Run these three prompts first with thinking disabled, then enabled. No system
message, tools, few-shot examples, research records or answer-forcing readout.
Use seed 20260930 at the start of each call, one sequence and batch size one.

1. `Reply with exactly the word READY.`
2. `Return only a JSON object with key color and value blue.`
3. `Choose one letter. Which number is even? A: 3. B: 4. C: 5. Reply with only the letter.`

Explicit generation configuration: sampling on, top_k=20, min_p=0.0,
repetition_penalty=1.0, temperature=0.7 / top_p=0.8 for non-thinking;
temperature=1.0 / top_p=0.95 for thinking. EOS and pad IDs come from the local
tokenizer. Pass use_model_defaults=False and assert the prepared configuration
before generation. There is no generation_config.json at this model revision.

The Transformers 5.3.0 generation interface has no built-in presence penalty.
This technical smoke uses no added presence processor (equivalent to zero).
This differs from the model card's general-task recommendation of 1.5 and uses
a much shorter output cap. Do not call this the vendor-recommended capability
baseline. No search over generation settings is allowed in this check.

## Records and interpretation

Save exact chat-rendered inputs, input/output token IDs, decoded outputs including
special tokens, effective generation settings, seed, generation/load durations,
EOS versus cap/deadline termination, CUDA peak memory and errors. Record local
model-file SHA-256 values and compare safetensors against Hub LFS SHA-256 before
loading. Save environment versions and the freeze commit. Do not treat naturally
ended output as necessarily correct, or a truncated thought as a final answer.

The outcome is whether this pinned model can load and generate in this environment,
with observed limits. The three simple content checks are not benchmark accuracy.
Before research use, new independently reviewed material, a capable-model protocol,
sampling policy, output parser, adequate budget and fair controls remain necessary.

Sources: [pinned checkpoint](https://huggingface.co/Qwen/Qwen3.5-4B/tree/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a)
and [Transformers 5.3.0 architecture documentation](https://huggingface.co/docs/transformers/v5.3.0/model_doc/qwen3_5).
Weights remain under upstream Apache-2.0 terms; no upstream code is copied into
this probe and no model artifacts are redistributed.
