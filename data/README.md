# Data card

48 original synthetic English customer messages, arranged in 12 controlled
four-way cases. Each case has two CANCEL and two KEEP labels. All four texts
share the same lowercased English word multiset, preserving multiplicity.
They swap object binding or instruction roles and reverse clause display order.

Fields: `id`, `parent_id`, `family`, `variant`, `target`, `customer_message`,
`gold`, `review_status`, `human_reviewed`, `split`. Only the last two message
input fields are sent to a model. A/C gold KEEP; B/D gold CANCEL. Variant names
and gold are deliberately omitted from inference.

Created by Yuchi Wang with AI-assisted drafting and rule/AI review, September
2026. **No independent human label audit.** All `human_reviewed` values are false.
No real customer information. This intentionally artificial grammar is not a
random sample of customer service language; the known-grammar parser can solve
it without model inference. It measures behavior on the controlled inputs only.

`smoke.jsonl` contains three separate instrument checks excluded from all scores.
Original data licensed CC BY 4.0:
https://creativecommons.org/licenses/by/4.0/

