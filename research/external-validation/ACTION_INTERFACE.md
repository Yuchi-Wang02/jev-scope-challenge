# Proposed next-run final-action contract

2026-09-30; implementation and synthetic software checks only. No model outputs
have been scored with this contract. It is not a frozen inference protocol.

The [parser](action_interface.py) accepts the following **final-channel** payload:

```json
{"action": "ASK"}
```

The value must be exactly `Yes`, `No`, `Irrelevant`, or `ASK`. Surrounding whitespace
is allowed. One complete lowercase `json` Markdown fence, with an opening and
closing line, is also allowed. The output records bare versus fenced JSON and a
separate strict-format flag. Extra keys, duplicate keys (even identical ones),
extra prose, multiple objects, arrays, case-normalized labels, missing braces,
unclosed fences and unknown labels are rejected without repair or another call.
The parser does not search reasoning text for a convenient answer.

Termination is a separate requirement: the backend adapter must supply
`natural_eos` based on saved provider metadata or output token IDs. Length stops,
errors and unknown reasons are rejected even if the visible text happens to
contain a complete object. The parser cannot authenticate this metadata. A later
adapter must be tested against the pinned model's final-channel boundaries and
termination behavior before an end-to-end run. No Jev adapter is implemented by
this module; its helper only validates a four-action option permutation.

This change was motivated by the [completed calibration](../generation-calibration/README.md),
where harmless fences accounted for 13 rejected thinking finals. That historical
experiment retains its stricter parser, results and qualification decision. This
module does not import its outputs or rescore any previous research grid.

The six software tests exercise every action, allowed wrappers, conflicting
answers, duplicate keys, extra fields, invalid values, incomplete output,
unverified completion and malformed option mappings. These are hand-constructed
parser fixtures, not an AI evaluation dataset or a model capability result.

```bash
python -m unittest discover -s tests -p test_rule_action_interface.py -v
```

Next integration requires completed human review, a separate frozen model
protocol, backend-specific completion/final-channel extraction, declared prompts
and budgets, and explicit cost accounting. The existing user authorization
covers bounded runs once those scientific and technical prerequisites are met;
this document adds no repeated approval requirement.
