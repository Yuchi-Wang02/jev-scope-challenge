# Missing Evidence Is Not Just Deleted Text

An exploratory development diagnostic, not a confirmed benchmark or paper claim.

## What changed our research question

Earlier pilots showed that an apparent native/pointer gap could change greatly
when evidence and instructions moved across the input boundary. This pilot fixes
the conventional state/evidence + instruction/policy layout and uses new finite
policy mechanisms. It asks whether a decision component treats a missing deciding
fact differently from a missing nondeciding fact. Always abstaining fails the
second obligation; always choosing a decision fails the first.

Four families contribute 48 six-view parents. Only the 12 development parents
from joint approval, reversal exception and linked route lookup were scored.
The composite mechanism is wholly reserved for later testing. Source, protocol,
truth audit and encoded input plans were publicly frozen at commit
`4809a5b2ea9aa8aef803f2875ad064998f60dd0b` before this execution.

## Observed results

The raw Base/native, Kev LoRA/native and Kev pointer paths scored 102, 96 and
106/216. All scored zero complete parents. Pointer scored 31/36 on nondecisive
deletion but 3/36 on decisive deletion, yielding 1/36 correct deletion pairs.
Base/native scored 7/36 correct pairs, adapted/native 0/36. These are 12 parents
under repeated option orders; no significance or general superiority is inferred.

The null-subtraction ablation highlights a metric trap. Adapted/native overall
correctness rose from 96 to 111/216 (19 corrected, four regressed), but unsupported
commitments rose from 68 to all 72 uncertain decisions. Pointer rose from 106
to 108/216 (eight corrected, six regressed), while unsupported commitments rose
from 66 to 72. Base/native dropped from 102 to 97, with commitments rising from
55 to 70. No null-subtraction path exceeded 1/36 correct deletion pairs.
Subtracting the meaningful insufficient-evidence control can penalize the very
abstention this diagnostic needs. This is an observed failure of this fixed
ablation, not proof against contextual calibration or DC-PMI in their settings.

Two-order averaging raised Base/native to 114/216 (26 corrected, 14 regressed),
adapted/native to 98 (11 corrected, nine regressed), and left pointer at 106
(one correction, one regression). It solved no complete parent. Ordinary extra
compute is useful to report, but these development results do not select a
deployable method. See [every family and view](results/ALL_COUNTS.md), including
weak reorder/flip performance and option-order sensitivity.

## What the truth checks prove

Finite-world enumeration agrees with a separately implemented direct solver on
1,120 partial/conflicting structured states. A pre-freeze direct-solver bug on
14 composed states was fixed and archived in [provenance](provenance/preflight-repair.md)
before model scoring. Corpus labels were unchanged; composed policy wording was
clarified. No failed scored run or selected retry is hidden.

The frozen parser reference received the declared family/site schema. A post-run
verification helper also derives that schema from the policy text and recovers
all 288 labels using only rendered state and policy. Both are deliberately
tailored to this synthetic grammar and use the known policy solver. They do not
validate general language understanding, independent labels or broad transfer.
Checking reserved labels with a deterministic grammar is not reserved model inference.

The model-input plans contain evidence, policy and options, never gold, view IDs,
split names or structured construction facts. All 1,008 plans have fixed token
sequences and no truncation. Every pointer main/null forward agreed with the
ordinary causal computation (maximum probability delta 0). All 504 saved LoRA
tensors loaded exactly. The historical PEFT loader warned about newer optional
config keys; the tensor audit passed. Source/output identity, counts, token
contracts, scoring inputs and derived rows are checked offline.

## Limits and next experiments

This corpus and these prompts were designed by AI after preceding pilots. Zero
independent human annotations exist. Development parents use plain line styles;
reserved parents add numbered/bullet styles. That intentional grouped variation
will mix presentation transfer with later case/mechanism transfer. Twelve
parents are far too few for a model ranking. Native candidate logits and the
pointer serialize/read the same supplied information differently; this is a
system comparison, not a causal estimate of changing only the head. No Jev API
was called here, and a Kev checkpoint must not be presented as Jev.

The completed automation includes a shuffled procedural-blind 288-item review
pack, six-item starter, blank CSV, local browser form and export validator.
It records zero annotations. The public key exists separately, so this is
procedural blinding rather than secrecy. Human exports require provenance and
adjudication; passing a file validator will not automatically open reserved scoring.

Next, review policy meanings and labels independently; version ambiguous or
incorrect cases before a new execution protocol. Use development to formulate,
not confirm, a mechanism-specific hypothesis. One promising branch compares
ordinary uncertainty scores with an explicit missing-fact/contradiction guard,
including the false-abstention cost on nondecisive deletion and a known-grammar
code upper reference. Another tests whether the failure survives an instruction-
tuned model and several fixed prompts under a matched budget. Avoid tuning a
null-subtraction coefficient against reserved answers. Record all candidate
methods and costs before releasing reviewed calibration, then run the untouched
test once under its own protocol. More source diversity and model paths are
needed before the result becomes an external benchmark or paper claim.

The public hook can be: **“Your decision model kept the answer after its evidence
disappeared.”** Pair that sentence with the negative deletion control and the
actual development counts. Do not advertise “Jev debunked” or “new calibration
algorithm.” The stronger question is which decision pipelines know when missing
evidence changes what can be concluded.
