# The guard worked because it knew the policy

Post-hoc development analysis. The prior real scores were already known before
this follow-up was designed. No new model inference or algorithm novelty claim.

## Three different kinds of improvement

Score cutoffs can suppress uncertain actions, but incur unnecessary refusals.
The full fixed grid is reported. On the Kev pointer, the 0.99 maximum-candidate
probability cutoff lowers unsupported commitments from 66 to 14/72 while raising
false INSUFFICIENT from 18 to 95/144. Among the 63 retained actions, 20 are wrong.
That is not evidence of 99% correctness. Candidate softmax is uncalibrated, and
the protocol intentionally selected/fitted no operating threshold. Different
paths have different score distributions; a shared arbitrary cutoff is a
diagnostic control, not a fair comparison of calibrated operating points.

The naive schema gate suppresses every action with a missing target-schema field
or conflict. It achieves zero unsupported commitments on these cases, but also
refuses a decision when a missing approval is redundant to an explicit rejection,
or when a missing unselected-site permission cannot affect a known route.
Kev pointer correctness rises to 154/216, yet false INSUFFICIENT doubles from
18 to 36/144. Of the 66 corrected unsupported commitments, 18 previously correct
determined decisions regress. Base/native and LoRA/native incur 14 and 17
regressions, respectively. A syntactic completeness check is too conservative.

The policy gate knows the logic of these exact rules. It identifies all 72
uncertain decisions, passing all determined inputs unchanged. Pointer rises to
172/216 (66 corrections, zero regressions); Base/native to 157 (55 corrections),
LoRA/native to 164 (68 corrections). False INSUFFICIENT remains 26/18/18, and
wrong determined actions remain 33/34/26. The helper prevents one error class;
it cannot repair wrong actions or inappropriate raw refusal on determined
evidence. Only the pointer passes any complete parents: 2/12, versus 1/12 for
its naive schema gate and 0/12 raw.

## The code comparison changes the interpretation

The policy gate's determinate flag agrees with finite-world truth on all 96
partial/conflicting states of the three development policies. This is expected:
we hand-coded their semantics and supplied an exact grammar parser. The gate
uses only visible text, but it receives substantial programmer knowledge.
Its zero unsupported commitments are conditional on correct grammar extraction
and correct policy encoding; they are not a general model reliability guarantee.

With that same parser and known policy, the full pure-code solver scores 216/216
and 12/12 complete parents with zero model forwards. This is a construction-
specific reference using the same policy semantics that generated labels, not
independent human validation. Nonetheless, omitting it would give a misleading
picture of the hybrid pipeline's necessity. If rules and facts are completely
encodable, the model currently adds error rather than solving an otherwise
unavailable computation. Model value would need to be demonstrated in extracting
facts from variable language, interpreting an unseen policy or handling genuinely
unstructured evidence under the same information/helper budget.

## What was run and verified

The public source/protocol freeze is
`48e8d95d9632c1858017af6e251fd9ca98edad6d`. The run reused 648 immutable real
development main records and added zero model forwards. It generated 8,424
method decisions, 216 deterministic code rows and 72 per-text certificates.
The original null records were unused. No calibration fit, paid API, download,
training, GPU job or reserved model score was added. The CPU run was 0.47 seconds
including old-evidence verification and output writing, not a speed benchmark.

47 repository tests passed, including duplicate/foreign/reserved grid rejection,
exact visible-string gate entry, short-circuit redundancy, route agreement,
cross-request facts, conflicting target fields, unsupported grammar/policy,
undefined zero-action risk and read-only verification. All tables and replay
payloads recompute without inference. Software checks certify evidence consistency
and finite program contracts, not scientific transfer or language validity.

## Where this should steer the research

The immediate public hook is a precise failure-and-repair sequence: **“We removed
the deciding evidence; the model kept committing. A rule guard helped, and the
pure-code comparison exposed what knowledge we had supplied.”** Preserve all
three stages. Do not reframe this as a general new algorithm or Jev result.

Next, keep confirmation gated on independent review. During preparation, design
an extraction-versus-execution study that separates: original rendered grammar,
independently reviewed paraphrases with the same facts, and policy-composition
transfer. Freeze each representation and mark exact-parser rejection separately
from incorrect extraction. The exact grammar baseline must abstain/report
unsupported on unfamiliar syntax; do not silently patch it using test answers.
Compare a learned extractor plus the same rule solver with direct decision
readout and fixed-budget alternatives. Charge extraction/model calls and use
the same helper for decision endpoints. A perfect fact mask is an oracle reference,
never a deployable method. Review calibration, freeze settings, then release a
separate test execution protocol. No such transfer/extraction experiment ran here.

This direction can fail usefully: the learned extractor may add more errors than
it removes, code may remain sufficient, or instruction-tuned readout may solve
the gap without elaborate guards. Each outcome informs when a dedicated decision
model or hybrid pipeline is actually needed. Broader sources and independent
labels are required before publication claims.
