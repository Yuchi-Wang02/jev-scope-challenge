# Publication checks

Completed locally before the final result upload:

- Original freeze, 384 formal / 6 smoke records, raw evidence and 195-attempt
  ledger match. Original frozen runner/analyzer/protocol are preserved.
- New resume code's cache-only, ledger cap/orphan and malformed-evidence tests.
- New study: 24 parent groups, all four interventions, grouped split, no gold
  insertion, 864 raw v0.2 records and exact N0/N1 input equivalence.
- Every new input re-encoded with the pinned cached tokenizer, without inference.
- Both explorers checked in a real Edge browser with Playwright CLI: selectors
  and saved records, desktop and 390px mobile, zero page errors, no horizontal
  overflow. HTTP preview tested; a direct file URL was blocked by the automation
  browser, so that browser did not establish file-protocol behavior.
- Scientific figure rendered and visually inspected. Denominators and limitations
  appear on the figure, the README and the research note.
- Credential-pattern scan on intended public files; no weight/cache files tracked.

Final publication requires a fresh public clone, offline checks, matching remote
tree and green final-commit CI. These checks establish delivery and consistency,
not independent human labels, production reliability or paper novelty.
