# Correct Code, Wrong Facts

**A verified executor can still act on an invented observation.** On this small
original-development diagnostic, the primary Kev-LoRA/native facts pipeline
improved final decisions from **31/72 to 44/72**, while filling **14/18 missing
target fields with a positive or negative value**. The executor passed all 96
possible four-state fact vectors of the three declared policies. It was executing
the extracted statuses correctly; those statuses were often wrong.

This is a post-hoc diagnostic on 12 familiar development parents, with six views
each. It is not a fresh-domain test, confirmation, significance claim or Jev
comparison. Only the 72 original texts were scored. There are no independent
human labels and no scores on the 144 provisional rewrite pairs or reserved splits.

![Decision and fact accuracy, with all call budgets](assets/fact-execution.png)

## Primary results, with matching schema assistance

Both direct decisions and field queries received the same full policy and all
target-field definitions. A field query chose TRUE, FALSE, MISSING or CONFLICT;
the code then enumerated compatible complete policy states. No model generated
reasoning or evidence quotes. Reference quotes are construction labels, while
predicted citations are explicitly null.

|Path|Direct, 1 call|Direct, 2-order average|Direct, 3-order average|Facts + code, 2/3 calls|Exact fact vectors|Missing fields turned into values|
|---|---:|---:|---:|---:|---:|---:|
|Base / native N0|39/72|28/72|35/72|24/72|0/72|0/18|
|Kev LoRA / native N1|31/72|31/72|31/72|44/72|33/72|14/18|
|Kev pointer K1|32/72|32/72|33/72|35/72|25/72|16/18|

The primary facts pipeline used the frozen canonical status order. Approvals
and reversal policies require two field queries; routes require three. Its
168 calls cost 63,467 native or 63,635 pointer input tokens. Direct single used
72 calls and 23,523/23,595 tokens; direct two/three used 144/216 calls. Extra calls
and longer schema prompts are charged rather than attributed to a cheaper model.
Every direct rotation, reverse facts order and two-order facts ensemble is in
[ALL_COUNTS.md](results/ALL_COUNTS.md), including family/view counts and regressions.

No path had a fully correct facts vector and a wrong executed decision. N1 had
11 correct actions with incorrect facts, and K1 had 10: decision accuracy alone
hides extraction defects. N1 still made 14/24 unsupported commitments on uncertain
texts; K1 made 20/24. Exact-grammar pure code solved 72/72 without model calls.
That code result is specific to the controlled grammar and should not be advertised
as natural-language competence.

## A concrete missing-fact failure

Input `joint_approval-1-decisive_missing` says:

```text
Request: allow action for request request-GZYYS.
Evidence:
Reviewer A approves request request-GZYYS.
Reviewer B rejects request other-SVNUU.
```

There is no reviewer B decision for the target request. The program reference is
review_a=TRUE, review_b=MISSING, so the requested decision is INSUFFICIENT. N1's
primary extractor returned review_a=TRUE, review_b=FALSE; the executor correctly
returned DENY **for that incorrect fact vector**. This observable output is
consistent with an object-binding failure or another extraction error; it does
not establish the model's internal cause.

## Why the Base result needs care

N0's canonical extraction was highly degenerate: 135/168 fields were classified
CONFLICT and 29 MISSING. Every executed result was INSUFFICIENT, yielding 24/72
correct simply because 24 labels were uncertain. On reversing option order, its
field accuracy moved from 16/168 to 49/168 and final decisions to 23/72. The
two-order ensemble reached only 23/72. This diagnoses a fragile frozen readout
on this four-status prompt; it does not show that all untrained small models
cannot extract facts. N0 is a Base model, not an instruction-tuned baseline.

N1's canonical/reverse/ensemble decision counts were 44/41/43; K1's were 35/42/40.
The highest observed order is not promoted to the primary result. New prompts,
label descriptions, instruction-tuned models and span-producing extraction would
all require a separate development study and an explicit resource budget.

## What ran and how to check it

Source freeze commit: `548e00f3e7322e2791541642f4371d60cec55ce1`, published before
scoring. Config SHA256: `a1d22fe660e255c2f2aa0bc309bd42550a51953bf3ce9eb65a3b2c9ed6c471ea`.
The run produced 1,656 scientific records, 552 additional pointer parity checks
with maximum probability delta 0, and six warmups. All 504 adapter tensors
(33,030,144 parameters) exactly matched the cached artifact. Runtime was
209.1 seconds on an RTX 5070 Ti; peak allocated GPU memory was 8,068 MiB. No
new training, download, API calls, paid jobs or output retries occurred.

The installed PEFT version ignored optional configuration keys from the newer
saved adapter configuration and warned about them. We preserved the historical
environment and verified every loaded tensor, rather than silently changing the
runtime. This audit establishes the loaded artifact, not behavior on other systems.

```bash
python research/fact-execution/data_tools.py verify
python research/fact-execution/fact_run.py build
python research/fact-execution/fact_analyze.py --verify
python research/fact-execution/publish_facts.py --verify
python -m unittest discover -s tests -v
```

These are offline checks, with no inference. Recompute all 1,944 derived decisions
and 1,512 fact claims from every saved score. Verification checks frozen source
against the execution Git commit as well as the current checkout. For a future
scored replication, use a separately versioned run rather than overwriting these
results. The runner deliberately rejects existing outputs.

Use [the offline replay](docs/explorer.html) to compare all paths/methods and see
every wrong fact. Use [the review pack](review/README.md) to prepare independent
semantic review; those provisional rewrites must not be treated as verified data.

## Research implication and next falsifiable step

The useful direction is now **evidence-aware fact extraction with an explicit
abstention contract**, evaluated with error attribution and total call cost.
Typed output and valid rule execution do not establish that a field observation
was present, relevant or correctly bound. This pilot isolates that failure;
it does not yet repair it or establish a novel neural-symbolic architecture.

After independent review, freeze a small language-transfer slice that preserves
the same facts and policies but changes phrasing. Test whether extraction quality
survives outside the exact sentence grammar, with program controls that explicitly
reject unsupported syntax. Only then compare bounded remedies such as
span-producing extraction or an instruction-tuned baseline. Keep an untouched,
reviewed confirmation set for any eventual paper claim. A result that fails this
transfer test is useful evidence and should change the research direction.
