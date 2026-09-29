# Closest sources

- [Kev historical model source](https://github.com/jaredpalmer/kev/blob/29d71c78368657b3a522729a01c748ea15272abc/kev/model.py): exact vendored pointer/encoder, Apache-2.0.
- [Kev native/adapted probe](https://github.com/jaredpalmer/kev/blob/0c142becde423a0c68ec857f7831dac0315588a1/scripts/base_mmlu_probe.py): directly motivates N0/N1. Existing diagnostic, not ours to claim as first.
- [Laya Feishu diagnostic](https://github.com/NandhaKishorM/laya/blob/9d955671415fc19f069b9cc998928075c1f255ec/research/benchmarks/feishu_zh/README.md): close scope/current/quoted-instruction cases and committed historical Jev/Laya records. Not independently reproduced here.
- [ReflexBench](https://github.com/brida-ai/reflexbench): multi-backend decisions, calibration, candidate perturbations and deterministic-policy comparisons. Only source/README research in this project, not score replication.
- [CheckList](https://aclanthology.org/2020.acl-main.442/) and [Contrast Sets](https://aclanthology.org/2020.findings-emnlp.117/): behavioral and contrastive evaluation precedents.

This is a bounded source register, not an exhaustive paper literature review.
Public tests that have informed design must not be described as unseen confirmation.
