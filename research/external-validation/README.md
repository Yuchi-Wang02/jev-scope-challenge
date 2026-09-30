# External rule-data candidate: ShARC, before any model evaluation

The current Jev/Kev series repeatedly probes a public synthetic development
corpus. A later paper needs a different source of language and labels. This is
a **candidate-source audit**, not a new score, benchmark release or permission
to run the frozen [514-forward development pilot](../fact-execution/JOINT_EXECUTION_PROTOCOL.md).

|Source|Why it matters|Why it is not a drop-in confirmation set|
|---|---|---|
|[ShARC, official project](https://sharc-data.github.io/)|Short natural-language rules, scenarios and conversation histories can change whether to answer or ask a follow-up. The [original paper](https://aclanthology.org/D18-1233/) frames this as conversational rule reading.|Its answer space includes follow-up **question text**, not just yes/no/insufficient. Public splits and prior research also limit a novelty or hidden-test claim.|
|[ContractNLI, official project](https://stanfordnlp.github.io/contract-nli/)|Entailment, contradiction and not-mentioned labels plus evidence spans directly test decision/evidence binding.|It uses long legal contracts, 17 repeated hypotheses and separate dataset download terms; truncation or retrieved-span help would change the task and require matched controls.|
|[ConditionalQA, official project](https://haitian-sun.github.io/conditionalqa/)|Complex questions have answers that depend on conditions.|Its free-text answer and condition output are farther from our typed action interface; the official site lists CC BY-SA 4.0 and a test set without answers.|

## Read-only ShARC source audit

The [inspector](inspect_sharc.py) reads the official 6,810,878-byte archive in
memory and pins SHA-256
`72dca3f4f3ba73b1d796b40e952a80d53cd2011ef90b2168b8bcaa818f5edd1e`.
It parses **train and dev only** and does not store third-party examples. A
preliminary archive inventory displayed the first public test row's answer;
no test distribution or model score was computed. The test is therefore not
presented as untouched or hidden. The [saved summary](sharc_source_summary.json)
reports:

|Split|Rows|Distinct `tree_id` groups|Yes|No|Irrelevant|Other answer text|Rows with history|
|---|---:|---:|---:|---:|---:|---:|---:|
|Train|21,890|628|6,773|7,057|1,256|6,804|15,006|
|Dev|2,270|69|804|766|138|562|1,509|

Train and dev have **zero overlapping `tree_id` values** in this pinned
archive. `tree_id` is a conservative grouping unit, but can include multiple
visible questions; the [pair audit](SHARC_PAIR_AUDIT.md) therefore also checks
exact question text. The dev rule snippet is a median 38 words, so source
length is more compatible with a bounded decision readout than a full legal
contract.
These counts describe dataset structure; no Jev, Kev or Qwen prediction exists.

The official ShARC archive contains no license file. On 2026-09-30 we corrected
the earlier incomplete inventory: the [official data page](https://sharc-data.github.io/data.html)
explicitly states **CC BY-SA 3.0**, also listed by the
[UCLNLP Hugging Face dataset card](https://huggingface.co/datasets/UCLNLP/sharc/blob/main/README.md).
The [publication amendment](PUBLICATION_AMENDMENT.md) now permits one attributed,
licensed review package with 60 visible training inputs. The original archive
is not vendored, and frozen source/selection summaries remain unchanged.
The Hugging Face Dataset
Viewer API refused this dataset because its loader uses arbitrary Python code,
so the inspector reads the official archive directly and pins its bytes.

## A viable next task, with an explicit limit

ShARC is the strongest near-term external **rule-action** candidate. A future
four-way interface would need `YES`, `NO`, `IRRELEVANT`, and `ASK`; treating
follow-up questions as ordinary `INSUFFICIENT` would discard the action the
dataset actually requests. A first comparison could score only the **choice to
ask**, with question-text quality evaluated separately. It must feed models
only `snippet`, `question`, `scenario` and `history`, never `answer`, `evidence`,
`tree_id` or source metadata. A fixed tree-level sample, human review of the
action mapping, matched prompts/tools/budgets and a separate frozen protocol
are required before any inference. These are proposed steps, not completed
results. Existing ShARC methods and scores remain prior work; this project
does not claim the task or dataset as its own contribution.

The separate [one-answer-flip audit](SHARC_PAIR_AUDIT.md) now confirms that
the pinned **training** split contains exact visible-input contrasts suitable
for later human review. It publishes aggregate counts and selection logic
only, with no third-party row text or model score.

A [blinded review queue](SHARC_REVIEW_PROTOCOL.md) is frozen at 30 pairs
from 30 `tree_id` groups. Its original private export is preserved. A separately
licensed [downloadable review package](public-review/README.md) now presents the
same 60 shuffled items, with blank CSV, offline page, cover note and attribution.
This changes distribution only. Review reconciliation and frozen reserve
selection have software checks, but **zero completed human reviews or model
outputs** have been added. See the [task card](TASK_CARD.md) for the current
comparison question, prior-work boundary, missing controls and next gates.

The [nearest-work update](NEAREST_WORK_UPDATE.md) adds closer 2024/2025 precedents
and specifies which contribution claims and baseline shortcuts they rule out.
It changes the planned comparison obligations, not the frozen queue or labels.

To recompute the structural summary from the pinned source (network required,
no model or API credential):

```bash
python research/external-validation/inspect_sharc.py verify
```
