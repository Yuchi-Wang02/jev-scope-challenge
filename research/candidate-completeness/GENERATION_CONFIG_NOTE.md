# An intended greedy run that sampled: the configuration check we missed

This is a reproducibility note about **our adapter**, not a claim of a new
Transformers vulnerability. Six local smoke outputs were generated with sampling
before the effective configuration was checked; they remain in the public record.
There were no main outputs from that attempt.

In our Transformers 4.55.4 / pinned Qwen3-4B environment, supplying a
`GenerationConfig(do_sample=False, ...)` was insufficient: default-valued fields
were merged with the checkpoint's generation defaults. The resolved mode was
`sample`. The official [versioned generation documentation](https://huggingface.co/docs/transformers/v4.55.4/en/main_classes/text_generation)
describes model-default inheritance and the precedence of direct generate kwargs.

Our repaired call makes the intended choice explicit:

```python
model.generate(
    **inputs,
    generation_config=config,
    use_model_defaults=False,
    do_sample=False,
)
```

The experiment additionally resolves and asserts the effective configuration
before the first forward, then saves it. See [CPU-only reproduction](generation_config_check.py),
[recorded configurations](generation_config_audit.json), and [v2 protocol](REASONING_GREEDY_V2.md).
The reproduction needs the pinned local configuration and Transformers version,
but it does not load weights or run model inference.

This repair does not guarantee identical floating-point outputs across devices,
batch sizes or library releases. It fixes the decoding-mode mismatch we observed.
The protocol, runtime version, effective parameters and actual work ledger should
be checked together; an intended setting in source code alone is incomplete evidence.
