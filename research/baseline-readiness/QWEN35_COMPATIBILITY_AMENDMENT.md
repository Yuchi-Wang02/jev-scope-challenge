# Pre-load generation API compatibility correction

2026-09-30, after download and before any weight load or inference. The original
protocol and runner commits remain available (`9ec62b8`, `604f3c3`).

Source inspection of installed Transformers 5.3.0 shows that
`GenerationMixin._prepare_generation_config` no longer accepts
`use_model_defaults` as a dedicated parameter. Its keyword arguments are routed
through configuration update and unknown ones remain model kwargs. Unlike the
earlier 4.55.4 interface, version 5.3.0 fills only values that are None, preserving
explicit sampling values.

Remove the obsolete `use_model_defaults=False` argument from this smoke runner.
Keep the explicit GenerationConfig and assert prepared sampling/cap/temperature/
top-p values and an empty set of unused kwargs. No prompt, seed, model, precision,
budget or intended decoding policy changes. This is a software correction before
outputs, not an inference retry or an outcome-driven configuration change.

A CPU-only unbound GenerationMixin configuration check records both the obsolete
argument behavior and the corrected settings. It allocates no model weights and
performs no forward pass. The smoke record identifies its actual runner commit.
