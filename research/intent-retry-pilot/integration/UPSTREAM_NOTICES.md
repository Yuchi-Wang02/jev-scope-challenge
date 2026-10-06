# Upstream attribution and modifications

This directory includes **14 unchanged source files**, each identified by its original URL, revision and SHA-256 in [sources.json](sources.json).

- `upstream/github/`: AgentAbstain runtime and package initialization files, from [AntiQuality/agentabstain](https://github.com/AntiQuality/agentabstain/tree/cfc3faf7ab1cfd4892cde1158d6e43b2f312ddc3). Copyright 2026 The AgentAbstain Authors. MIT license retained at `upstream/github/LICENSE`.
- `upstream/dataset/`: environment implementation/schema, task instructions and simulated initial state, from [antiquality/agentabstain](https://huggingface.co/datasets/antiquality/agentabstain/tree/842228426c2a703347396501af61c7890972c7ee). Attribution: Xun Liu, Yi Evie Zhang, Vira Kasprova, Parisa Rabbani, Pardis Sadat Zahraei, Tianyu Zhang, Ali Ebrahimpour-Boroojeny, and Varun Chandrasekaran, *AgentAbstain: Do LLM Agents Know When Not to Act?*, 2026, [arXiv:2607.10059](https://arxiv.org/abs/2607.10059). The retained dataset card declares [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/). These dataset files are not relicensed as MIT by the companion code's license or this repository's default license.

Our added files implement a scripted controller, task-specific gates and software checks. We do not modify the upstream source or task records. Derived trace packets use local direct-class dispatch, opaque record mappings, and an additional profile lookup explicitly identified in the protocol. Preserve the dataset attribution and license for these derivatives. This is not an endorsed or official AgentAbstain release. No repository fork, issue or PR has been created.

The fixture's names, dates, travel records and identity fields are synthetic public benchmark data. They are not real account credentials or user records.
