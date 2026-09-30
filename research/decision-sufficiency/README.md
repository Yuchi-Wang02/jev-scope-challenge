# Unknown order. Known answer?

**Executable specification lab: zero model calls, zero independent human reviews.**

Can a refund-destination restriction be determined before identifying exactly which order a user means? Sometimes, under a predicate-only contract. That still does not authorize a refund. This lab makes the distinction executable without changing the old experiments.

[Interactive examples](https://yuchi-wang02.github.io/jev-scope-challenge/decision_sufficiency.html) · [Contract and projection argument](CONTRACT.md) · [Prior work and reuse](RELATED_WORK.md)

## What ran

- 20 authored specification examples plus 5 malformed/inconsistent input examples.
- Independent complete-database enumeration agreed with the projection on 730 finite contracts; 180 inconsistent contracts were rejected.
- 192 of those constructed contracts distinguish predicate-only and identity-required outputs. This is a software test count, not empirical accuracy or a prevalence estimate.
- Brute-force scope: two ordinary original methods, at most two visible and two omitted records, product/exact-ID selection, gift-card, ordinary, absent and unresolved destinations.
- No Jev request, local model inference, model download, new human annotation, or live refund operation.

## Inspect the contrast

|Example|Predicate only|Unique target required|Why|
|---|---|---|---|
|s01: One known order, original method|VALID_DESTINATION|VALID_DESTINATION|Both interfaces have enough information.|
|s02: One known order, another ordinary method|INVALID_DESTINATION|INVALID_DESTINATION|An ordinary method in the profile is not enough.|
|s03: Two orders, same original method|VALID_DESTINATION|NOT_ESTABLISHED|The predicate is invariant; identity is not established.|
|s04: Two orders, destination invalid for both|INVALID_DESTINATION|NOT_ESTABLISHED|Certain falsity also need not identify the order.|
|s05: Two orders, opposite answers|NOT_ESTABLISHED|NOT_ESTABLISHED|One consistent target accepts; another rejects.|
|s06: Two orders, existing gift-card exception|VALID_DESTINATION|NOT_ESTABLISHED|The stated exception holds for either target, but does not authorize execution.|
|s07: One visible match, unknown completeness|NOT_ESTABLISHED|NOT_ESTABLISHED|The missing candidate can reverse the predicate.|
|s08: Unknown completeness, gift-card exception|VALID_DESTINATION|NOT_ESTABLISHED|A visible match guarantees existence; the exception covers every possible target.|
|s09: Omitted candidates share the same original method|VALID_DESTINATION|NOT_ESTABLISHED|The supplied domain is a synthetic contract assertion, not an inferred fact.|
|s10: Omitted candidates cannot use this destination|INVALID_DESTINATION|NOT_ESTABLISHED|No consistent target has card_C as its original method.|
|s11: Unique identity, unresolved original payment|NOT_ESTABLISHED|NOT_ESTABLISHED|Knowing which order does not resolve its payment predicate.|
|s12: Unique identity, gift card bypasses missing original|VALID_DESTINATION|VALID_DESTINATION|The exception suffices for this component despite an unresolved original method.|
|s13: No matching order in a complete query|NOT_ESTABLISHED|NOT_ESTABLISHED|No target is not a vacuously valid refund destination.|
|s14: No visible match, existence unknown, gift card|NOT_ESTABLISHED|NOT_ESTABLISHED|A world with no matching target prevents a determined component answer.|
|s15: Existence guaranteed, unseen identity, gift card|VALID_DESTINATION|NOT_ESTABLISHED|Existence and the exception suffice for the predicate, not an order ID.|
|s16: Visible exact ID with a loose completeness bound|VALID_DESTINATION|VALID_DESTINATION|The unique-ID constraint excludes an additional matching order; possible is an upper bound.|
|s17: Destination not identified|NOT_ESTABLISHED|NOT_ESTABLISHED|A missing destination is not a known invalid destination.|
|s18: Named but nonexistent gift card|INVALID_DESTINATION|INVALID_DESTINATION|Names do not create the existing-gift-card exception; the method universe is complete.|
|s19: An unrelated record changes neither interface|VALID_DESTINATION|VALID_DESTINATION|The contract and selection remain scoped to mug.|
|s20: Exact unseen ID, existence and payment guaranteed|VALID_DESTINATION|VALID_DESTINATION|The synthetic contract guarantees this exact ID exists with one original method.|

## Reproduce

From the repository root, using Python 3.10 or newer; only the standard library is needed:

```powershell
python research/decision-sufficiency/build.py --verify
python research/decision-sufficiency/semantics.py research/decision-sufficiency/example_contract.json
python -m unittest discover -s tests -p test_decision_sufficiency.py -v
```

The CLI accepts one contract JSON object and returns both interpretations, the possible outcomes and concrete projected witnesses. An invalid contract exits with code 2 and does not invent a decision label. Use `build.py` without `--verify` to regenerate the checked artifacts.

## Stage decision

This branch has value as a task-definition and software-control example. Possible-world consensus, certain answers and query-scoped completeness have direct prior literature; they are not our inventions. The finite schema already has a complete program solution. Do not launch a new model leaderboard on these examples or present the audit as benchmark evidence.

A next study requires a concrete user need for the predicate-only interface, independently reviewed language and an available capable ordinary-model comparator. If the actual operation always needs unique identity, keep this as documentation and continue the existing coverage-review path. Model experiments on the earlier 72 inputs remain closed. The current review package is [here](../candidate-completeness/review/README.md).

All objects are artificial; domains and coverage assertions are provided by construction. They are not a deployed retrieval contract, real customer data, tau benchmark examples, or human-validated labels. The schema does not model split payments or full return policy. A machine-checked contract cannot certify its supplied facts.
