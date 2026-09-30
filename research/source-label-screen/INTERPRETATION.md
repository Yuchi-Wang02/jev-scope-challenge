# What this completed pilot changes

2026-09-30. Post-run interpretation of the [complete results](RESULTS.md).
The source references remain unchanged; no new model calls accompany this note.

## Three findings, three different boundaries

1. **Jev matches more of these source labels.** Native choice scores 18/24 in
   each mapping, with 8/12 pairs fully matching. Qwen3.5-4B direct generation
   scores 11/24 and 12/24, with 3/12 fully matching pairs. A last-history-answer
   copying control scores 14/24 and 4/12 pairs. These are selected public-source
   diagnostic results, not independently established correctness or a complete
   natural-language-rule baseline comparison.
2. **The thinking arm mostly fails to deliver a final answer within its cap.**
   Of 48 thinking generations, 37 reach 2,048 tokens. All 37 saved extractions
   have empty final text, no extraction boundary error and no closing `</think>`
   in their decoded output. The pinned-tokenizer audit reproduced the extraction.
   The failure occurs before a final response, not because the scorer silently
   rejected a completed final JSON. The other 11 outputs match the source, but
   selecting only those completed outputs would change the evaluated population.
   Keep the full 5/24 and 6/24 condition scores; do not claim a reasoning ceiling.
3. **Source agreement is an imperfect target for the original research question.**
   The [all-pair audit](SOURCE_REVIEW.md) was written before reading these scores.
   In the title-only child-seat pair, Jev returns ASK / Irrelevant against source
   Yes / Yes. For the loan-approval Yes reference, Jev returns ASK. The source
   audit had already identified insufficient rule content and a necessary-versus-
   sufficient-condition concern, respectively. These observations motivate
   adjudication; they do not automatically establish Jev's alternative as correct.

Jev's native actions are identical across both mappings. The displayed-argmax
view differs on one item across mappings; both argmax aggregates remain 18/24.
Qwen direct changes two valid actions across mappings. Thinking is valid in both
mappings for only two inputs; its apparent zero action changes on that subset
does not demonstrate stability on all 24 inputs.

## Execution and presentation audit

- Planned: 48 API requests and 96 local generations, no repeated jobs, a one-hour
  local generation-session limit, complete source and input provenance.
- Actual: all planned jobs returned. Qwen used 28,256 input /92,559 output tokens
  and 2,983.875 session seconds, with no recorded budget overrun. Direct and
  thinking output totals are 537 and 92,022 respectively.
- Gap: the original strict API readout stopped twice across separately frozen
  phases. Native-choice completion is an adaptive engineering repair, not the
  uninterrupted original experiment. Both failure ledgers remain published.
- Validation: raw-token re-decoding and saved-text/arithmetic replay agree. The
  source row audit confirms all 24 original records. None of those checks replaces
  human semantic judgment. This source slice still has zero project human reviews.
- Public presentation: [interactive replay](../../docs/source_label_screen.html)
  includes every pair, all five controls, both API readouts, both local modes and
  the source-evidence caveat. The hook is a question about changed decisions;
  it does not advertise a proven model failure rate or a new reasoning algorithm.

## Next action and stop rule

Close this frozen grid. Do not rerun it at larger caps, search prompts against
these labels, or spend API calls trying to turn the title-only example into a
more dramatic failure. The full cohort is now inspected development material.

The next useful engineering question is whether a finite-choice readout on the
same existing ordinary model can provide cheaper, valid decisions without long
generation. That route would be a separately frozen, outcome-aware diagnostic,
with explicit tokenization and option-mapping controls, not a repair of these
scores or a newly invented method. First inspect the local one-token interface
and define the hypothesis, computation budget and unavoidable prompt differences;
this note does not claim that comparison has run.

For the paper trajectory, source-grounded decisions still need independently
reviewed rules, treatment of sufficiency and ambiguity, and new confirmation
material. The existing training-review queue stays unscored. A stronger ordinary
model, common assistance accounting and an intervention that beats established
controls remain necessary before arguing about model replacement. A successful
GitHub artifact is progress in reproducibility and communication, not that paper
result itself.
