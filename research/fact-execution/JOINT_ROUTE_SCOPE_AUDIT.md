# Joint routing is an ablation, not a new extraction architecture

This note checks the [frozen joint-routing pilot](JOINT_EXECUTION_PROTOCOL.md)
against close research precedents and an explicit representation failure. It
does not change the committed scientific prompts or introduce model scores.
The source check is bounded; it is not an exhaustive literature review.

|Primary source|What already exists|Implication for our claim|
|---|---|---|
|[FEVER, NAACL 2018](https://aclanthology.org/N18-1074/)|Claims labeled supported/refuted/not-enough-information with sentence-level evidence for supported/refuted cases.|Sentence evidence selection and an insufficient state are not new here.|
|[SciFact, EMNLP 2020](https://aclanthology.org/2020.emnlp-main.609/)|Scientific claims linked to support/refute evidence and rationales.|Evidence-backed polarity decisions and rationale checks precede this project.|
|[DocRED, ACL 2019](https://aclanthology.org/P19-1074/)|Document-level entities and relations can require combining several sentences.|Our one-line synthetic grammar does not test those dependencies.|
|[OneRel, AAAI 2022](https://ojs.aaai.org/index.php/AAAI/article/download/21379/21128)|Joint entity/relation triple classification addresses linked elements and overlapping triples.|Joint binding itself is prior work; our mutually exclusive label is a narrow prompt/interface choice, not a new extractor.|
|[RARR, ACL 2023](https://aclanthology.org/2023.acl-long.910/)|Finds attribution and revises unsupported generated content.|Attribution plus correction is prior work; our candidate does not generate or revise an answer.|

The historical [Kev and Laya attribution](../../THIRD_PARTY_NOTICES.md) is
separate: Kev source/checkpoint were used with attribution, while Laya was
inspected only. This pilot will score neither a new Jev run nor a Laya backend.

## A concrete limit of “one line, one owner”

Each of the 228 original synthetic source lines was generated from one
structured record with one field. The candidate therefore allows exactly one
request/field/value label per line. Consider a visible line that says both
“Reviewer A approves request A” and “Reviewer B approves request A.” Either
choice leaves the other field MISSING; there is no label that can report both.
The [software test](../../tests/test_joint_route_scope.py) demonstrates this
without a model call. This is a **representational failure**, not evidence
that the model misread the line. The current runner deliberately refuses that
altered text, so the limitation is not scored away or smuggled into the
frozen 72-input result.

For the current release, the honest claim is a costed and auditable ablation:
does mutual exclusivity reduce wrong-request/wrong-field selections on the
known one-record-per-line development grammar, and at what cost to determined
decisions? Even if its development gate passes, the architecture has not shown
that it handles multi-claim lines, paraphrases, cross-sentence facts or new
policies. A later protocol needs examples with those structures, independent
human review, a nonexclusive or span-level alternative, and matched resource
controls before making a broader software-component or paper claim.
