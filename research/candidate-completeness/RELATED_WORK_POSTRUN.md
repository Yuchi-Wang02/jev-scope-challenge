# Post-result novelty and reuse check

Checked 2026-09-30 **after the Jev/native results**, while the single repaired
reasoning control was running. These sources did not shape the original freeze.
This is a focused primary-source screen, not an exhaustive review or replication.
Paper results below remain the authors' reports; none are our measurements.

|Primary source and inspected scope|Overlap that we must acknowledge|What this pilot does not establish|
|---|---|---|
|[Ling et al., Abstention Inflation, arXiv v8](https://arxiv.org/html/2507.16199v8), method/control sections and [author repository](https://github.com/ZpLing/Abstention-Inflation)|Studies how an added uncertainty option changes answers, including option-position and reasoning controls. Unnecessary abstention caused by the prompt is already a research topic.|We keep three outcomes fixed and vary target/coverage evidence; we have not separated all linguistic triggers or measured internal representations. Do not claim discovery of over-abstention or its mechanism.|
|[Sato et al., Evidence Sufficiency Boundary Training, arXiv v1](https://arxiv.org/html/2609.01687v1), boundary definition, baselines and limitations|Studies transitions from insufficient to sufficient evidence and stability with redundant context; uses training and evidence-chain evaluation. It reports both unsupported answers and false abstention.|Our relevant/irrelevant omission controls are not a new evaluation principle. This pilot has no training method, wider multi-hop benchmark or established improvement.|
|[Luo et al., Agentic Abstention, arXiv v1](https://arxiv.org/abs/2606.28733v1), abstract, [author project](https://lhannnn.github.io/agentic-abstention/) and [repository](https://github.com/lhannnn/agentic-abstention)|Examines when agents should stop acting, seek information or answer. Tool budgets, delay and context-based stopping policies already have direct precedents.|Our static single-decision input has no retrieval trajectory, interaction policy or measured benefit from asking a clarifying question. Turning it into an agent loop is not automatically novel.|
|[Liu et al., AAAI 2026](https://ojs.aaai.org/index.php/AAAI/article/view/40496), official abstract|Reports reasoning-model abstention failures and a two-stage monitoring/intervention method.|A reasoning trace plus a decision checker is not inherently new. Our saved traces are observations, not faithful explanations of internal processing.|
|[Madhusudhan et al., COLING 2025](https://aclanthology.org/2025.coling-main.627/), official abstract|Evaluates answerable/unanswerable behavior and prompting, including chain-of-thought.|The 512-token control is a baseline check, not an algorithmic contribution.|

## Repository reuse status

The two linked author repositories were inspected as references. No GitHub fork,
checkout, package install, checkpoint download or execution of their code occurred.
No third-party source from them is incorporated in this repository. The Abstention
Inflation README declares MIT; any later actual reuse needs a pinned revision,
retained license and a changed-files inventory. We have not completed that reuse
audit for Agentic Abstention. A public code link is not by itself a reuse license.

Kev remains a separately credited historical dependency elsewhere in this project;
Laya remains a design reference and was not executed. The current coverage study
uses its own adapters, pinned Qwen weights and attributed simulated tau records.

## Current contribution judgment

The strongest current claim is a small, fully inspectable **diagnostic result**:
under the declared unique-target rubric, missing same-product candidates produce
unnecessary deferrals even for some exact-ID requests. Counterexamples, option-order
changes, code success and weak ordinary native readout are all visible.

This is useful public research material. It is not yet a competitive general
method or a broad benchmark contribution. Before developing a method, establish
that the contrast survives new human-reviewed wording and a capable ordinary
baseline, and determine whether code already solves the intended deployment task.
Do not turn the presence of an API failure example into a claim of novelty.
