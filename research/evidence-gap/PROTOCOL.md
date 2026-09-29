# Missing Evidence Is Not Just Deleted Text

Exploratory development-stage diagnostic. New original synthetic policy corpus,
no independent human annotations or real document sources. No paper novelty claim.
Designed after the three preceding pilots; layouts/methods fixed before new scores.

## Corpus and truth

48 parents x six views = 288 inputs. Joint approval, reversal exceptions and
two-hop route lookup each contribute 12 parents. A fourth composed route +
approval + exception mechanism contributes 12 parents exclusively to reserved
test. Within the first three families, parents 1–4 are development, 5–8 reserved
calibration, 9–12 reserved test. Thus dev/cal/test counts are 12/12/24 parents.
Entity names and presentation styles are grouped; compound-policy integration
is held out from development/calibration. This is not an unseen real-world domain.

Views: full, reorder hold, decisive relation flip, decisive evidence deletion,
nondecisive deletion, conflict. Full/hold/nondecisive deletion preserve the answer;
flip changes ALLOW/DENY; decisive deletion and conflict require INSUFFICIENT.
The nondecisive deletion sometimes removes a relevant-but-redundant approval,
or an unselected-site permission. It is not always an obviously unrelated row.
No view marker, gold, split, family ID or construction metadata enters models.

Labels are computed by enumerating legal complete binary policy states. Only one
common outcome permits ALLOW/DENY; disagreeing possible outcomes or inconsistent
target-schema facts give INSUFFICIENT. An independent direct/three-valued solver
is exhaustively cross-checked over 1120 partial/conflicting states. A known-grammar
text parser must recover the same decisions from the rendered text. These checks
validate program semantics and generated rendering consistency, not human meaning.

## Human-review gate and execution scope

This release may score **development only**. Reserved calibration and test may
be tokenized for length/contract validation, never scored or used for method
selection. The CLI has no test execution switch. Independent human review of
policy/labels, recorded adjudication, and a separately versioned execution
protocol are required to open later inference. Blank/AI-populated forms and user
approval to execute do not constitute annotations. Public reserved text is not
secret; it remains model-unscored for these pinned weights, not globally unseen.

## Models, representation, methods

N0: exact Qwen3-4B-Base with native LM head. N1: same native inputs + historical
Kev LoRA. K1: same adapted backbone + historical pointer path. Exact revisions,
vendored source, BF16 body, FP32 pointer, unmerged LoRA, math-only SDPA, TF32 off
and no quantization match the preceding pilots. Cached weight digests rechecked.

Use L0's conventional contract: original rendered evidence in state, complete
policy in instruction. No prompt/layout search on new data; earlier layout
stress tests remain separate. All arms receive the same evidence/policy/options;
K1 serialization/readout differ, so this is a system comparison, not head causality.

Three fixed readouts use the same saved scientific forwards:

- R0 raw: argmax raw candidate probabilities. Nominal one evidence forward.
- R1 null-subtraction: softmax(z_evidence - z_null), coefficient 1, with matching
  candidate order. Null retains only the request line and `Evidence: no records
  supplied.` with the unchanged policy. Cache one null per parent/order/arm,
  shared over six views. Nominal two calls per decision, amortized 7/6 forwards
  under the complete six-view grid. This is an unvalidated prior-correction
  ablation, **not** faithful reproduction of DC-PMI/contextual calibration;
  null is a meaningful insufficient-evidence task and can penalize justified
  abstention. Do not name it a new algorithm or treat its normalized scores as
  calibrated correctness probabilities.
- R2 two-order ensemble: average semantic-label probabilities from order m and
  order (m+1) mod 3. Nominal two evidence calls per decision; all three order
  evaluations are retained. No extra teacher, generated reasoning or label fit.

Report nominal per-decision calls AND actual shared-grid computation. R2 needs
216 main forwards per arm for the three-order grid; R1 adds 36 null forwards.
Do not claim equal total compute just because all derived rows share one run.
No threshold/temperature fitting until calibration is reviewed and released.

## Counts, gates and outputs

Development: 72 evidence inputs x three orders x three arms = 648 main scientific
forwards; 12 parents x three orders x three arms = 108 null forwards. Total 756
scientific forwards, 252 extra causal-path parity forwards for K1, six warmups.
1944 method predictions are derived, not independent model calls or samples.
Every K1 main/null input must match ordinary causal path below probability delta
1e-4 with identical argmax. Stop, preserve raw output and record terminal failure
if any gate fails. Do not overwrite, retry/select a partial scientific run.

Primary measures: complete parent correctness (all six views x three orders),
paired decisive/nondecisive deletion correctness, unchanged decision after
nondecisive deletion, unsupported commitment on decisive deletion and conflict,
supported-view accuracy, option-order sensitivity. Report every family/variant
and method, with correction/regression counts. Always-INSUFFICIENT baseline has
1/3 decision accuracy and zero complete parents in this balanced construction.
Known-grammar solver is a construction-specific reference, not a general NLP model.

Publish code/data/protocol/encoded plans before inference, then all raw main/null
records, grouped summary/CSV/figure/replay/note and blank blind review forms.
CI/offline checks must prove zero reserved split records and source identity,
validate logits/probabilities/input plans/sharing/counts, and remain read-only.
Local cached GPU only; no new download, training, paid API or cloud deployment.
