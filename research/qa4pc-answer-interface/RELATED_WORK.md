# Prior methods that constrain this study

Checked 2026-09-30 against the primary papers' method sections, not only their
abstracts. This is a focused methods check, not a systematic literature review
or an independent reproduction of the authors' implementations.

|Primary source and inspected section|Relevant established method|Consequence here|
|---|---|---|
|[Pezeshkpour and Hruschka, NAACL Findings 2024](https://aclanthology.org/2024.findings-naacl.130.pdf), sections 3 and 5|Measures sensitivity under answer reorderings; section 5 evaluates voting over ten random reorderings and an explanation-based calibration method.|Exhaustive six-way evaluation and voting are controls, not a proposed invention. Report individual mappings and the full cost of aggregation. Their oracle-order sensitivity range is not an executable label-free selector.|
|[Wei et al., ACL Findings 2024](https://aclanthology.org/2024.findings-acl.333.pdf), sections 3.3 and 4.1|Separates changing symbols while keeping content positions fixed, changing row order while keeping symbol-content pairs fixed, and changing both.|Our fixed A/B/C rows with permuted semantic labels change both binding and semantic position. Call this mapping/interface sensitivity, not an isolated causal estimate of position bias.|
|[Zhao et al., ICML 2021](https://proceedings.mlr.press/v139/zhao21c/zhao21c.pdf), section 5|Estimates prompt-dependent label bias on content-free inputs and applies a diagonal correction. Distinguishes this from confidence calibration.|A uniform null distribution is an assumption. In this task removing facts can legitimately mean `maybe`, so blindly forcing a uniform null is not a neutral correction. Contextual calibration is not in this initial grid.|

No author code was copied, executed, or forked for this methods check. The new
experiment uses this repository's existing source audit, tokenizer verification
and journal design. QA4PC is upstream data and must be credited independently of
code reuse. Its source labels are not new project human labels.

The prospective question is whether the observed dedicated/ordinary-model
comparison depends materially on its output interface. A fresh cluster sample,
an identical-prompt generated-letter bridge, and transparent cost/invalid-output
accounting make that comparison more interpretable. They do not establish a new
algorithm or make a small source-agreement experiment publication-ready.

Implementation availability has not been exhaustively searched; absence of an
inspected author repository must not be reported as absence of released code.
