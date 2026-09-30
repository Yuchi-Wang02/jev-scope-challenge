# Greedy execution repair, v2

This is a pre-main execution repair to [REASONING_PROTOCOL.md](REASONING_PROTOCOL.md).
The original runner/freeze and six smoke outputs are retained. No original main
job ran. Transformers 4.55.4 merged checkpoint generation defaults into an explicit
GenerationConfig and changed its default-valued `do_sample=False` to True. Thus
the first six outputs do **not** instantiate the declared greedy control.
See [the offline reproduction](generation_config_audit.json). This is an execution
defect, not a prompt/label change based on scores. No local retry hid those records.

V2 keeps exactly the same state, user text, thinking prefix, 512-token cap,
closing-marker/final-readout rule, schedule and batch sizes. The only inference
change is explicit `use_model_defaults=False, do_sample=False` at the generate
call. Before inference, resolve the effective configuration, assert greedy-search
mode, and persist it in the runtime log. A CPU-only reproduction must establish
the old sampling override and repaired greedy mode without loading model weights.

Freeze v2 code, this amendment, copied exact plans, prior protocol/freeze and the
configuration audit before all v2 outputs. Execute six v2 smoke and 144 main jobs.
Semantic smoke errors do not choose a version or prevent a valid schema grid.
The first version has no valid greedy primary comparison and is not pooled with v2.

V2 has the same caps: 150 decisions, 38 batches, 76,800 generated tokens, 19,494
physical forwards, 1,000,000 padded token positions. First-version spent work is
reported separately and added to total project cost. Aggregate decisions in this
control stage are at most **156**, including the six stopped sampled smoke jobs.
No third configuration, automatic retry or budget increase is allocated. New
runtime defects stop this control for inspection rather than launching a search.

All original interpretation limits remain: inspected data, program-derived
references, forced reasoning boundary, batched arithmetic, and more computation
than Jev/native. This is not an equal-budget or model-ceiling comparison.
