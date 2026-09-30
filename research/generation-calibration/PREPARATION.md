# Preparation log

Before the execution freeze, five parser/data regression tests passed. The CPU
penalty check and actual Transformers processor-order assertions also passed,
but printing the check report initially failed: `_prepare_special_tokens` adds
private tensors to GenerationConfig, which are not JSON serializable. Capture
the serializable configuration before that helper mutates it. This logging fix
used no model weights or forwards and changed no prompt or decoding setting.
The successful CPU check is retained as cpu_checks.json. The same checks rerun
before loading weights in the execution script.
