# Candidate data card

Original synthetic finite-policy English corpus, CC BY 4.0. 48 parents / 288
six-view inputs. No external source document, personal record or benchmark score
is reused. This is new policy-mechanism construction, not a real-document dataset.

Development: 12 parents / 72 inputs; reserved calibration: 12 / 72; reserved test:
24 / 144. Parent groups do not cross splits. The composed mechanism is exclusively
reserved test. Presentation styles and random entity identities are grouped.
All three labels have 96 inputs overall and 24 each in development.

Fields: id/parent/family/variant/split/style are bookkeeping; target/sites/records
are construction facts; state/instruction are the only main model text; gold
and legal_worlds are derived truth metadata. None of gold/world count/split/view
name/construction facts are appended to model input. Null input is computed only
from the request line, with unchanged instruction, not gold or deleted-key oracle.

`solver_audit.json` cross-checks two implementations over 1120 partial/conflicting
structured states. The known-grammar same-text parser roundtrip is also checked.
This certifies specified finite rules and generated text consistency. Natural
language validity and human policy interpretation still require independent review.

Current human annotations: zero. Any objections/corrections must be versioned,
retaining original inputs and development model failures; do not change labels
to improve a model score. Reserved inputs may be tokenized but not scored here.
