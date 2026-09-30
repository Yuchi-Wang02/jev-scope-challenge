# QA4PC: can the released facts execute the released rules?

**Completed structural audit, 2026-09-30. Zero model calls and zero new human
labels.** Of 437 development scenarios, 429 have complete formula inputs and all
429 reproduce the released final label. Eight cannot be fully executed because
one supplied tree references `Q1`, absent from its question inventory. We preserve
that omission rather than repair it or convert an absent variable to `maybe`.

This is a prerequisite for attributing model errors to fact interpretation versus
logical composition. It is not a new reasoning method, a model result, semantic
validation, or a reproduction of the authors' trained system.

## Source and scope

- Saeidi, Yazdani and Vlachos, [Cross-Policy Compliance Detection via Question
  Answering](https://aclanthology.org/2021.emnlp-main.678/), EMNLP 2021. The paper
  already decomposes policy compliance into condition questions and expression
  trees. This project credits that framework rather than claiming its invention.
- Public author-associated [Marzipan/QA4PC repository](https://huggingface.co/datasets/Marzipan/QA4PC),
  revision `2b1de7c5e588ec70afa1e753394ae25531e0d182`.
- Read three pinned files: shared dev/test trees, development entailment and
  development question-answer data. [report.json](report.json) records byte
  sizes, hashes, source URLs and overlap reference hashes.
- No test scenario or test label files were fetched. The shared tree file contains
  **all 193 dev/test policy graphs**, whose structure was inspected. Test policies
  must not be described as entirely untouched.
- Viewer `/splits` reported a file-format mismatch between training text and
  evaluation JSON. Reading the pinned JSON directly succeeded. The README names
  `dev_sc_qa4pc.json`; the actual question file is `dev_qa_qa4pc.json`.
- No root license file or explicit dataset license in the pinned README was
  found in the inspected repository inventory. This is a bounded observation,
  not a legal conclusion. Source bytes remain in ignored local storage; our
  published files contain original audit code and derived counts/IDs/hashes.
  No source text or complete label vector is redistributed by this audit.

## What the checks establish

|Check|Observed result|Meaning|
|---|---:|---|
|Shared graph inventory|193 unique tree IDs|60 occur in the development files.|
|Development scenarios|437, across 60 trees|Scenario key is `(tree_id, utterance_id)`.|
|Question records|1,600|`set_id` identifies individual QA rows, not scenario groups.|
|Final labels|206 no /124 maybe /107 yes|Released references, not our adjudication.|
|Question labels|739 no /506 maybe /355 yes|Repeated fact observations within scenarios/trees.|
|Join and exact-text checks|All pass|Policy/question/scenario text and per-tree question inventories align.|
|Formula variable availability|1 incomplete tree /8 scenarios|Separate from join success: the question table itself lacks `Q1`.|
|Complete composition|429/429 agree, across 59 trees|Standard three-valued execution using released fact labels.|
|Identical direct-input conflicts|0 among 437 distinct inputs|Only the exact policy/question/scenario contract is checked.|
|Prior 12-tree source screen overlap|0 tree IDs /0 utterance IDs|Does not establish population independence or absence of training exposure.|
|Previously inspected EXtrA overlap|4 trees /5 utterance IDs|35 QA4PC development scenarios lie on these four trees.|

Uppercase `AND`/`OR`/`NOT` are normalized to Python parser spellings. This changes
63 string representations, not logical operators or labels. Only names matching
`Q` plus digits, AND, OR, NOT and parentheses are accepted. The evaluator walks
a whitelisted syntax tree; it does not call `eval` or execute upstream code.
AND/OR/NOT use ordinary strong Kleene semantics, including `no AND maybe = no`
and `yes OR maybe = yes`. Tests enumerate every binary truth-table cell.

The incomplete tree is `94ce16365b9e777c4e2a3ec5c1443749bf8cf2f0`:
its expression requires `Q0 AND Q1`, while its dictionary contains only `Q0`.
All eight affected IDs remain in the report. We do not infer the intended repair
from the final labels. Even a short-circuitable missing-variable expression is
excluded from the **complete-input** composition check by design.

The paper describes checking and adjusting annotations for compositional
consistency. Consequently, 429/429 is an integrity check, not independent evidence
that all natural-language interpretations are correct. Using these fact labels
as model inputs would be explicit answer-derived assistance, not end-to-end
policy reasoning.

## Reproduce

From the repository root, with Python's standard library:

```powershell
python research/qa4pc-audit/audit.py fetch --source-dir .local/qa4pc-audit
python research/qa4pc-audit/audit.py verify --source-dir .local/qa4pc-audit
python -m unittest discover -s tests -p test_qa4pc_audit.py -v
```

`fetch` downloads only the three listed files if absent, checks exact lengths and
SHA-256, and leaves existing mismatched files as errors. `build` writes the derived
report; `verify` recomputes it without overwriting. A second independent download
directory also reproduced the report during this audit. LF/CRLF normalization
applies only to repository report/reference files, never to pinned source bytes.

The offline test suite exercises synthetic truth tables, precedence, unsafe
syntax rejection, duplicate/orphan joins, exact text, missing variables, label
disagreement and visible-input conflicts. CI can test this implementation without
downloading source data. **CI does not independently rerun the source-byte audit.**

## Decision and remaining gap

**Subsequent preparation:** the [next cohort](../qa4pc-stage-attribution/README.md)
now checks the pending training queue, excludes its three overlapping trees, and
selects 12 trees /24 scenarios. It still has zero model results. The decision
below records the transition at audit completion.

QA4PC can support a controlled **assisted decomposition diagnostic** on complete
development graphs. It cannot by itself establish a new method or validate the
original business-payment task. The incomplete graph stays a reported source
exception. EXtrA overlap must be accounted for before selecting another cohort;
the separate pending ShARC training review queue has not been compared here.

Next, [freeze a stage-attribution experiment](NEXT_EXPERIMENT_DESIGN.md) before any
model call. Give Jev and Qwen the same human-authored assistance in corresponding
arms and retain direct-with-graph as a control. Report cost increases alongside
any accuracy change. No input selection, prompts, model execution or result is
claimed by that design document.
