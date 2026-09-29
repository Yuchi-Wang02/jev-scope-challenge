# Does the model need to decide, or only extract facts?

Exploratory development study designed after prior pilots. No confirmation,
fresh domain claim, calibrated probability or new neuro-symbolic algorithm.

## Scope and human-review gate

Only the 72 original evidence-gap development inputs from 12 six-view parents
may receive new model scores. Reserved calibration/test and the composed policy
remain unscored. 144 AI-generated rewrite pairs are **review-only**: intended
same-fact semantics are provisional, not human-verified. They never enter the
runner or input plans. Original labels and fact references are also program-
derived, with zero independent human annotation. A new reviewed version/protocol
is required before testing rewrites or reserved mechanisms.

## Interface and external knowledge

Compile target/schema from the visible request header and original policy.
Fields have four observation states: TRUE (positive only), FALSE (negative only),
MISSING (neither recorded) and CONFLICT (both recorded for the same target field).
Absence is not negation; other-request observations do not fill target fields.
The schema defines the positive/negative meaning; route TRUE means second site,
FALSE first site. An explicit field definition is not an observed value.

Both the scaffolded direct baseline and each extraction query receive the same
original policy and complete explicit field definitions. Extraction additionally
asks about one field, direct asks for the final action. Known schema/compiler/
executor are hand-written external knowledge; apply them to all N0/N1/K1 paths.
Never pass corpus gold, split/view IDs or structured construction facts to a model.
Models choose statuses but do not generate evidence spans in this pilot. Their
interface sets `evidence_spans: null`. Program-derived reference quotes/character
offsets are audit labels only; never attach them to model claims as citations.

The executor enumerates legal complete policy states consistent with extracted
statuses. A unique outcome determines ALLOW/DENY; disagreement or conflict yields
INSUFFICIENT. It cannot repair an incorrect extracted fact. Fully correct facts
must produce the program reference decision; cross-check all 96 status vectors
of the three development policies. No policy induction or learned program compiler.

## Fixed models, inputs and calls

Exact cached Qwen3-4B-Base, the same historical Kev LoRA, and same adapted pointer
as the prior studies. BF16 body, FP32 pointer, unmerged adapter, math-only SDPA,
TF32 off; no training, thinking/generation, new weights, paid API or cloud job.
Recheck cached SHA digests and every loaded adapter tensor.

- Scaffolded direct: 72 texts x three candidate rotations x three arms = 648
  scientific forwards. Ordinary single, two-order (0+1), three-order averages
  are derived from these scores, with semantic labels aligned.
- Fact extraction: 168 field queries x two candidate orders (canonical and
  reverse) x three arms = 1008 scientific forwards. Four-status logits, two
  orders, not every possible permutation. Native A/B/C/D boundaries checked.
- Total 1656 scientific forwards (552 per arm), 552 extra ordinary-causal K1
  parity checks and six warmups. All main jobs are original development inputs.
  Per-record pointer parity delta <1e-4 and identical argmax; preserve a failed
  run rather than retry/select or overwrite output.

Derive two single-order extraction pipelines and a semantic two-order field
ensemble. Single-order pipeline needs two field calls for approvals/exceptions,
three for routes; average 7/3 per input. Ensemble needs four/six calls, average
14/3. Direct single/two/three need 1/2/3 calls. Charge all queries/tokens and
report both nominal decision costs and actual shared-grid run counts. No shared
multi-question cache/packing optimization is evaluated. Legacy direct scores
are context anchors; scaffolded baselines control explicit schema assistance.

## Evaluation and outputs

Primary canonical pipeline: extraction order 0. Also report reverse and ensemble,
every direct order/ensemble, every field/status/family/view, and all regressions.
Use 72 text decisions per method; complete parents require all six views (not
the preceding 18-order definition). Report 24 uncertain and 48 determined texts,
false commitments, false INSUFFICIENT, wrong supported actions, action coverage/
risk and paired decisive/nondecisive deletion correctness /12. Parent groups are
the sampling units; no independent-trial inflation or significance claims.

Report field correctness /168, exact fact-vector correctness /72, missing facts
turned into reported values/conflicts, missed conflicts and status confusion.
Separate wrong extraction with wrong final action from wrong extraction whose
error is masked by policy redundancy. Exact facts plus wrong execution is a
program defect and must be zero. Correct action does not prove correct extraction.
Do not interpret conditional candidate probabilities as calibrated correctness.

Freeze source/protocol/reference labels/encoded plans before inference. Publish
all raw scores/prompts/tokens, runtime, parity/load audits, derived pipelines,
fact claims with null citations, error attribution, full tables and a figure.
Read-only verification must prove original-only input membership, exact prompts,
zero rewrite/reserved scores, no input-label leakage, finite scores, source
identity and all derived values. No inference in CI.

## Prior work and limits

Combining language-model calls with symbolic execution is established; see
[Binder, ICLR 2023](https://arxiv.org/abs/2210.02875). We do not reproduce Binder's
program parsing/API framework, learn a compiler or claim this architecture is
new. The question here is error attribution and budgeted behavior of frozen
small-model pipelines under supplied finite policies. Exact grammar remains a
strong pure-code reference. Language transfer, instruction-tuned alternatives,
span generation and independent labels remain future work. Kev is not Jev.
