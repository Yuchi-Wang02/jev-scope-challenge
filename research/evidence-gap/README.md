# Missing Evidence Is Not Just Deleted Text

Status: candidate corpus and fixed development experiment; **not yet scored**.

Can a decision system distinguish deleting the fact that determines its answer
from deleting a fact that does not matter? Always abstaining cannot solve both.

New synthetic mechanisms: joint approvals, reversal exceptions, linked route
permissions, and a composed mechanism reserved for later test. Six views per
parent include decisive deletion, nondecisive deletion and conflicting records.
48 parents / 288 inputs; labels are rule-generated, not human-validated.

This release only permits **development inference**. Twelve calibration parents
and 24 test parents remain unscored pending independent labels/adjudication and
a new execution protocol. Public text is not secret or claimed globally unseen.

Read the [protocol](PROTOCOL.md), [corpus](data/cases.jsonl), [data card](data/README.md),
[truth solver audit](data/solver_audit.json), [source/novelty boundaries](related_work.md).
The model paths match the previous pinned Base/native, LoRA/native and pointer
diagnostics. Representation is fixed to original evidence/state + policy/question.
Raw output, null-subtraction ablation and two-order averaging are ordinary
baselines with explicit computation; no new algorithm is claimed.
