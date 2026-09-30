# Blinded review queue for the one-answer-flip study

**Status: selection frozen; 0 human reviews and 0 model forwards.** This is a
small *development* queue drawn from the public ShARC training split. It is
neither an independent test set nor a new ShARC benchmark. The original
[ShARC task and paper](https://aclanthology.org/D18-1233/) already study
Yes/No/Irrelevant decisions and when a follow-up question is needed.

The [pair inventory](SHARC_PAIR_AUDIT.md) found 3,037 provisional action-changing
contrasts. We freeze **30 pairs from 30 different `tree_id` groups**: eight
primary pairs and two ordered reserves for each of `No/Yes`, `ASK/No`, and
`ASK/Yes`. The three source-label strata are deliberately balanced for a
mechanism check, so the queue does not estimate natural ShARC frequencies.
Each candidate's rank is a SHA-256 digest of its pinned source identity and
`sharc-train-contrast-review-v0.1`; the script takes candidates in that order,
round-robin across strata, excluding every previously selected `tree_id`.
The [manifest](sharc_review_manifest.json) commits to the selection digest,
source archive digest, pack digests and counts without publishing source rows,
utterance IDs, pair IDs or the selected text.

The [official field guide](https://sharc-data.github.io/data.html) describes
`tree_id` as a unique snippet-and-question combination. In the exact pinned
train archive, however, each of the 628 `tree_id` groups contains one exact
snippet and **three distinct exact question strings**. Two of the three have
only `Irrelevant` labels in every group. The pair selector therefore requires
the exact snippet, question, scenario and follow-up question sequence to
match, with only one history answer changing from No to Yes. The original
paper describes negative-question generation. This structure is consistent
with that account, but does not establish how every variant was assigned.

## Human review before inference

The private export has **60 shuffled individual items**, not side-by-side
pairs. It shows only the original visible input fields: snippet, question,
scenario and history. It excludes source `answer`, `evidence`, source IDs,
provisional action stratum, primary/reserve role and pair links. This is
procedural blinding: a reviewer can still find the public source elsewhere.

For each item, choose `Yes`, `No`, `Irrelevant`, `ASK`, or `UNCLEAR` using only
the visible input, and write a short reason. `ASK` means a further question is
needed; this queue does **not** judge whether the source's particular
follow-up wording is best. Use `UNCLEAR` when the rule, question, scenario or
history does not justify a confident action. Obtain two independently saved
reviews of all 60 items, with reviewer identity and date on each copy of the
blank CSV. Compare them only after both are saved, then record adjudication
and reasons without treating source labels as automatic truth.
Exact string matching does not prove semantic validity: a fixed scenario may
contradict one flipped history answer, or a follow-up question may be
ambiguous. Mark such items `UNCLEAR` and explain the conflict rather than
forcing the source action.

After review, identify any primary pair whose action remains `UNCLEAR` after
adjudication or whose source input is malformed. Use its pre-ranked
same-stratum reserve **before model inference**. A clear human label that
disagrees with the source label is **not** a reason to discard the item; retain
it with the adjudicated label, even if the pair becomes a same-action control.
If more than two primary pairs are invalid in any stratum, or the available
reserves are also invalid, stop and version a new design instead of
hand-picking replacements. Preserve all reviews, exclusions and reasons.
Only after that process should a separate model protocol freeze prompts,
models, candidate mapping, direct/code baselines, total budgets, paired-action
metrics and analysis units. Public train examples may have appeared in model
pretraining, so even a clean result here is diagnostic, not a paper's final
generalization claim.

## Reproduce the preparation

The following commands fetch the pinned official archive, but call no model
and need no API key. `verify` checks the committed digest without writing
third-party text. `export` writes the text-containing, answer-hidden pack only
under the ignored `.local/` directory; never commit those generated files.

```bash
python research/external-validation/prepare_sharc_review.py verify
python research/external-validation/prepare_sharc_review.py export
python research/external-validation/prepare_sharc_review.py verify-export
python research/external-validation/prepare_sharc_review.py export-page
python research/external-validation/prepare_sharc_review.py verify-page
```

The private files are `.local/sharc-train-contrast-review-v0.1/review_items.json`
and `blank_review.csv`. The generated `review.html` is an offline, item-by-item
review interface with local drafts and CSV import/export. Its
[public template](review_template.html) contains no ShARC examples; the
text-filled page stays under ignored `.local/`. A reviewer can clear an
incomplete item before export; export includes every queue ID and leaves
unreviewed rows blank. The CSV starts blank; its presence, the machine
manifest and a passed verifier do **not** count as independent annotations.
The page opens without displaying any earlier draft. A reviewer must enter a
stable ID and select **Start / resume**; local drafts are keyed by both the
pack digest and that ID. **Switch reviewer** clears the displayed draft before
another ID is entered. This prevents accidental cross-reviewer display on a
shared page, not deliberate access or collaboration: reviewers should use
separate browser profiles and each fill a separate copy of the CSV. Older
drafts from the previous shared browser-storage key are not silently imported;
anyone who used that earlier page should export their CSV before replacing it.
The read-only checker
accepts partial exports, rejects foreign or duplicated IDs, incomplete rows,
invalid action names and malformed dates, but does not judge semantic truth or
reviewer independence:

```bash
python research/external-validation/prepare_sharc_review.py check-review \
  --review-csv .local/sharc-train-contrast-review-v0.1/blank_review.csv
```

When two **separate completed** reviewer CSVs exist, the
[reconciliation tool](review_reconcile.py) can compare them:

```bash
python research/external-validation/review_reconcile.py \
  --review-a .local/reviewer-a.csv --review-b .local/reviewer-b.csv
```

It refuses missing items, incomplete rows and the same declared reviewer ID
in both files. Only then does it reveal pair links in the private
`adjudication_queue.json`, alongside both reviewers' actions and reasons; it
also creates a blank `adjudication_blank.csv`. Neither output contains source
`answer`/`evidence`, provisional stratum or primary/reserve role. The tool
does not decide which reviewer is right, fill adjudicated actions, activate
reserves or open model inference. Distinct names in CSVs cannot prove that two
humans worked independently. **No reviewer CSV or adjudication output exists
yet.**

An adjudicator later saves a *copy* of `adjudication_blank.csv` with a final
action for both items, `VALID` or `INVALID` for the pair, a reason, identity
and date on all 30 rows. `VALID` requires two clear actions; persistent
`UNCLEAR` requires `INVALID`. The [finalizer](review_finalize.py) checks that
the saved pair queue matches both original reviewer files, validates every
adjudication row, and replaces invalid primaries with the first valid reserve
in the same frozen source stratum. It stops when reserves run out. Clear human
actions that disagree with the source remain eligible, including a pair
whose two adjudicated actions are the same.

```bash
python research/external-validation/review_finalize.py \
  --review-a .local/reviewer-a.csv --review-b .local/reviewer-b.csv \
  --adjudication .local/adjudicator.csv
```

This writes `reviewed_selection.json` privately and refuses to overwrite a
different prior result. It is an integrity check on declared reviews and
reserve order, not proof that the reviewers were independent or correct.
Even a complete reviewed selection leaves model inference closed until a
separate experiment protocol is frozen and approved. The finalizer has been
tested on synthetic fixtures only; no human adjudication has occurred.
