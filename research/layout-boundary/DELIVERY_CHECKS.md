# Delivery checks

Local checks completed before result upload:

- 24 unit/fault-injection checks passed in Python 3.10.18. Corrupted sharing,
  causal logits and duplicate grids are rejected; verification preserves evidence.
- Offline verification covers 2592 logical records, 2016 scientific forwards,
  576 shared native records, 864 old anchors and 864 parity checks.
- The pinned cached tokenizer re-encodes all 864 plans and checks all saved inputs.
- Original/new figures were rendered and visually inspected; all-split figure
  displays the one-decision pooled gap and development/calibration reversals.
- Real Edge / Playwright CLI: all-pilot default totals, old-test score selector,
  parent/view/order selectors, three layout cards, desktop 1280 and mobile 390px.
  Zero page console errors/warnings; document width stays within viewport.
  This checked localhost HTTP; direct file-protocol behavior was not measured.
- Public inputs/code/docs checked for credential patterns; model/cache weights
  stay outside Git. Blank review sheets do not count as human annotation.

Final public delivery additionally requires a matching remote tree, an updated
public clone with offline verification, and green CI for the final commit.
These establish delivery and evidence consistency, not paper novelty, independent
labels or production reliability. Existing Python 3.13 strict prior-summary
recomputation is unsupported; use the documented Python 3.10 environment.
