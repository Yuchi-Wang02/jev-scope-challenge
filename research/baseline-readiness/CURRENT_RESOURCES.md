# Local comparator status after the interface study

Snapshot: 2026-09-30 14:21 UTC. This is a focused inspection of four known project
cache locations, not an exhaustive machine search. [Machine inventory](local_inventory_2026-09-30.json)
and [capture script](local_inventory.py). No model was loaded, downloaded or
called for this refresh; no credential was read.

## What the evidence establishes

|Candidate|Current evidence|Use boundary|
|---|---|---|
|Pinned Qwen3.5-4B|Config and two weight shards present; separately, the completed interface study records actual generation and prefill runs.|Usable measured 4B comparator; the directory alone does not establish stronger capability.|
|Pinned Qwen3-4B instruction|Config and three weight shards present; earlier candidate-coverage studies record actual runs.|Already measured historical comparator, not a new capability ceiling.|
|Qwen3-4B-Base and Kev adapter|Base shards and adapter present at the historical pinned revisions.|Trained adapter; not an unadapted ordinary instruction baseline.|
|Qwen3-0.6B and Qwen3-1.7B|Config and local safetensor files present.|Smaller-model controls, not evidence of a stronger reference.|
|User's DelaySentinel checkpoints|Several cached config/snapshot entries, including two config-only snapshots in the default cache.|Task-specific artifacts; not selected as general reasoning comparators.|
|8B or larger general instruction comparator|None found in these four inspected locations.|Absence is scoped to the inspected locations; not a whole-machine assertion.|

Ten config/adapter entries were found, not ten distinct runnable models. This
inspection reads config hashes and file sizes; it does not rehash weight content,
check every tokenizer/runtime dependency or certify model loading. Index-declared
missing files and config-only entries remain visible. GPU at capture was an
RTX 5070 Ti with 16,303 MiB total and 2,124 MiB allocated. These are transient
device readings, not expected model peak memory or throughput.

The first capture attempted to parse a Hugging Face `.no_exist` sentinel as JSON
and stopped before writing a snapshot. The repaired inventory excludes these
absence markers from checkpoint discovery. Neither attempt loaded a model or
changed any cache file.

## Decision for the next scientific stage

The [completed interface grid](../qa4pc-answer-interface/RESULTS.md) has already
tested three nonthinking output routes for Qwen3.5-4B. Another identical run
would not supply a stronger comparison. Its [semantic audit](../qa4pc-answer-interface/SOURCE_AUDIT.md)
also identifies a reference-interpretation gap that inference cannot adjudicate.

Proceed with source review and new-task specification in parallel. Before an
additional comparator run, record one of the following routes explicitly:

1. A capability-oriented configuration on new reviewed inputs, with a declared
   finite budget, supported decoding and all sampled seeds retained. This is a
   compute/configuration comparison, even if it uses the already cached 4B model.
2. A separately acquired stronger checkpoint or hosted ordinary model, with
   exact revision, access, download/spending scope, runtime/precision and an
   independent technical smoke. Larger parameter count alone is not evidence
   that it will perform better on the task.

No new acquisition or scientific run is frozen by this refresh. Preserve the
closed cohorts, independent review queue and raw failure records. The historical
[metadata snapshot](README.md) is retained with its original runtime and
availability statements; it must not be read as today's cache inventory.
