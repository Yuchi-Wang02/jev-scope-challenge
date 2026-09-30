# Credits, reuse and license boundaries

This is an independent research repository by Yuchi Wang, developed with AI
assistance. It is not a GitHub fork of Kev or Laya. GitHub repository metadata
reported `fork: false` on 2026-09-29. Copying a small upstream module into a
repository (vendoring) is still code reuse and needs attribution regardless of
the GitHub fork relationship.

## What we actually used

|Project / artifact|Role in this repository|What was copied or executed|
|---|---|---|
|[Jared Palmer's Kev](https://github.com/jaredpalmer/kev)|Upstream implementation, trained artifact, and research precedent|The historical `kev/model.py` and empty `kev/__init__.py` are vendored unchanged. The pinned public LoRA and pointer-head weights were executed locally; weights are not committed. Kev's native/adapted probe informed the N0/N1 design.|
|[NandhaKishorM's Laya](https://github.com/NandhaKishorM/laya)|Related work and design reference|We inspected its [Feishu scope/current/quoted-instruction diagnostic](https://github.com/NandhaKishorM/laya/blob/9d955671415fc19f069b9cc998928075c1f255ec/research/benchmarks/feishu_zh/README.md). No Laya implementation, checkpoint, dataset or result records are incorporated in our experiments. No Laya model scores were collected here.|
|[Qwen](https://huggingface.co/Qwen)|Pretrained model and tokenizer provider|The original cancellation comparison used Qwen3-4B; the later matched-base series used Qwen3-4B-Base. Exact revisions appear below. We did not train these base models.|
|[TypeSafe / Jev](https://typesafe.ai/)|Hosted comparison system|The original cancellation study called `jev-1.13.0`. Later Kev/Qwen studies are not new Jev measurements. No Jev implementation or weights are included.|

Inspecting or locally cloning an upstream repository for research is different
from creating a GitHub fork. No fork is needed merely to preserve this evaluation
repository. A future upstream code contribution should be developed and attributed
as such; none of the proposed head-training/upstream-contribution work is claimed
as completed here. The historical plan's phrase “research fork” describes a
possible later phase, not an existing fork.

## Vendored Kev source: Apache-2.0

Source commit: [`29d71c78368657b3a522729a01c748ea15272abc`](https://github.com/jaredpalmer/kev/tree/29d71c78368657b3a522729a01c748ea15272abc).
The active copy is [research/next-study/vendor/kev](research/next-study/vendor/kev/).
An identical source copy is retained with the [stopped v0.1 attempt](research/next-study/attempts/v0.1/vendor/kev/).

- [Original model source](https://github.com/jaredpalmer/kev/blob/29d71c78368657b3a522729a01c748ea15272abc/kev/model.py): SHA-256 `839dd7632ec291ac4740035c86f780f8f13da2b74b54a146ce90ff0ce8de527b`.
- The initializer is the upstream empty file: SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
- The full [Apache-2.0 license](research/next-study/vendor/kev/LICENSE) is retained beside each copy. Its text matches the [pinned upstream license](https://github.com/jaredpalmer/kev/blob/29d71c78368657b3a522729a01c748ea15272abc/LICENSE), allowing CRLF/LF normalization.
- [NOTICE.md](research/next-study/vendor/kev/NOTICE.md) is our provenance note, not a claim that upstream provided that file. The inspected pinned source tree contains no upstream NOTICE file.

Both `model.py` copies were byte-for-byte compared with the pinned upstream
source on 2026-09-29. We wrote evaluation loaders, controls and reports around
that implementation. Those additions do not make the pointer architecture our
invention. The loader uses the historical unmerged BF16 path; results are not a
reproduction of upstream's FP32 benchmark scores or an evaluation of today's
default Kev release.

## Model artifacts: exact revisions and separate terms

|Artifact|Revision actually used|Pinned license declaration|
|---|---|---|
|[Qwen3-4B](https://huggingface.co/Qwen/Qwen3-4B/tree/1cfa9a7208912126459214e8b04321603b3df60c)|`1cfa9a7208912126459214e8b04321603b3df60c`|[Apache-2.0 model card](https://huggingface.co/Qwen/Qwen3-4B/blob/1cfa9a7208912126459214e8b04321603b3df60c/README.md)|
|[Qwen3-4B-Base](https://huggingface.co/Qwen/Qwen3-4B-Base/tree/906bfd4b4dc7f14ee4320094d8b41684abff8539)|`906bfd4b4dc7f14ee4320094d8b41684abff8539`|[Apache-2.0 model card](https://huggingface.co/Qwen/Qwen3-4B-Base/blob/906bfd4b4dc7f14ee4320094d8b41684abff8539/README.md)|
|[Kev-4B adapter + pointer head](https://huggingface.co/jaredpalmer/kev-4b/tree/c4bfa11b0dc07691884f2d97f1c4c4c05c92e416)|`c4bfa11b0dc07691884f2d97f1c4c4c05c92e416`|[Apache-2.0 model card](https://huggingface.co/jaredpalmer/kev-4b/blob/c4bfa11b0dc07691884f2d97f1c4c4c05c92e416/README.md)|

These weights/tokenizers are downloaded separately into a private cache, not
redistributed in this Git repository. Their licenses are not replaced by the
root MIT license. The [weight checksums](research/next-study/results/weight_checksums.json)
and each study's runtime identify the artifacts actually loaded. All later
N1/K1 paths reuse already-trained upstream weights; “no new training” never
means the Kev adapter/head was untrained.

## Other research credit and dependencies

Kev's [native/adapted probe](https://github.com/jaredpalmer/kev/blob/0c142becde423a0c68ec857f7831dac0315588a1/scripts/base_mmlu_probe.py)
predates our N0/N1 comparison. Laya's diagnostic is a close neighbor to the
scope/current/quoted-instruction questions. See the matched-base
[source register](research/next-study/related_work.md) and
[study-specific novelty matrix](research/next-study/novelty_matrix.md), plus the
[current series-wide matrix](NOVELTY_MATRIX.md). CheckList, Contrast
Sets, SemIf/OpenJev, ReflexBench and Binder are research precedents, not systems
whose published scores we independently reproduced here.

PyTorch, Transformers, PEFT, Hugging Face Hub, safetensors, accelerate, HTTPX,
NumPy and Matplotlib are separately installed dependencies. Their distributions
retain their own notices and terms. This document inventories direct source and
model reuse; it is not a complete transitive dependency SBOM.

## Our material and citation

- The root [MIT license](LICENSE) covers our original software and documentation,
  subject to the explicitly identified upstream source exceptions above.
- Original synthetic input datasets and program-derived reference annotations
  are CC BY 4.0, as recorded in their data cards. This includes the explicitly
  provisional fact-execution rewrite candidates; a license does not certify
  their semantic correctness or label quality.
- Raw model/service outputs are published as experimental evidence. We do not
  claim ownership of upstream models or replace any applicable provider terms.
- Cite this project using [CITATION.cff](CITATION.cff), with the relevant study
  and commit. Also credit the upstream implementation, checkpoint and research
  sources relevant to the result you use. Citing only this repository is not
  an adequate attribution for Kev or Qwen.

No affiliation or endorsement by TypeSafe, the Kev or Laya maintainers, or Qwen
is implied. No trained checkpoint, peer-reviewed paper, or general-purpose
reliability guarantee is claimed by this repository.
