# Candidate coverage: nearest-work boundary

Primary abstract/project-page check on 2026-09-30, before this pilot's model
outputs. This is a bounded screen, not a systematic review or reproduced result.

|Source|Established topic|Our boundary|
|---|---|---|
|[Sufficient Context, arXiv v3](https://arxiv.org/abs/2411.06037v3) and [official implementation](https://github.com/hljoren/sufficientcontext)|Distinguishes context that supports an answer from context that does not, with sufficiency-guided abstention analysis.|Evidence sufficiency and guided abstention are already studied. Here coverage is explicitly supplied in a synthetic decision premise, not inferred for open-domain RAG. No code or data from that project is used.|
|[Wen et al., EMNLP 2024](https://aclanthology.org/2024.findings-emnlp.197/)|Tests abstention under removed, irrelevant and additional science-QA context.|Relevant/irrelevant context controls are precedents. Our product-specific omission contrast is a narrow adaptation, not a new testing principle.|
|[Contrastive Decoding with Abstention, ACL 2025](https://aclanthology.org/2025.acl-long.479/)|A training-free decoding method and controlled knowledge-access settings.|This pilot introduces no decoding correction and does not replicate CDA. Native finite-choice scoring is not a newly invented method.|
|[Reasoning Trace Inversion, ACL 2026](https://aclanthology.org/2026.acl-long.608/)|Studies abstention failures through answering a different question and a reasoning-trace method.|We have no trace intervention or internal evidence. Output differences cannot establish that mechanism.|
|[Earlier project source register](../payment-ownership/RELATED_WORK.md)|Entity binding, behavioral tests, contrast sets and tau retail provenance.|Those precedents and attribution remain applicable. The new users do not create a new language family or independent confirmation.|

Potential value: an inspectable, source-attributed diagnostic showing whether
given coverage evidence affects a typed refund component, with irrelevant-omission
and pure-code controls. Limits: artificial templates, supplied coverage truth,
no new method, no model-necessity result, and no independent labels at execution.
Do not describe the concept of incomplete evidence or abstention as our novelty.
