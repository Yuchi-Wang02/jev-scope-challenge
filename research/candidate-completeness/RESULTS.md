# One visible match: caution can also be wrong

**Exploratory result; 12 parent scenarios, 72 constructed inputs, zero independent human reviews of this new set.**

Jev recognized missing relevant candidates for product-name requests, but sometimes deferred even when an exact order ID already selected a visible target. Every Jev main error was an unnecessary NOT_ESTABLISHED on the explicit-ID / relevant-omission condition. This is not the originally proposed foreign-order payment substitution.

|Method / mapping|Correct /72|Complete parents /12|False commitments /12 unknown|Unnecessary deferrals /60 determined|
|---|---:|---:|---:|---:|
|Jev 1.13.0, 0|63|3|0|9|
|Jev 1.13.0, 1|67|7|0|5|
|Qwen3-4B native, thinking off, 0|34|0|12|0|
|Qwen3-4B native, thinking off, 1|30|0|12|0|
|Code: scope_aware|72|12|0|0|
|Code: ignore_scope|60|0|12|0|
|Code: keyword_all|36|0|0|36|
|Code: keyword_product|60|0|0|12|

Constants VALID / INVALID / NOT_ESTABLISHED score 30/30/12 out of 72, with zero complete parents each. The known-grammar solver sees the same visible state and scores 72/72; it is an essential limit on model-necessity claims.

The prespecified Jev screen fails in both mappings. Strict correctness across all six inputs and both mappings is 3/12 parents for Jev and 0/12 for Qwen. These are repeated measurements of 12 parents, not 144 independent examples.

## Where the decisions differ

|Request / coverage|Jev map 0 /12|Jev map 1 /12|Qwen map 0 /12|Qwen map 1 /12|
|---|---:|---:|---:|---:|
|explicit / complete|12|12|6|6|
|explicit / relevant_omission|3|7|10|6|
|explicit / irrelevant_omission|12|12|6|6|
|product / complete|12|12|6|6|
|product / relevant_omission|12|12|0|0|
|product / irrelevant_omission|12|12|6|6|

Required product-answer changes are correct in 12/12 pairs per Jev mapping, as are product irrelevant-omission controls. Explicit-ID relevant-omission stability succeeds in 3/12 and 7/12 pairs; explicit-ID irrelevant omissions remain 12/12. Correctness requires both pair members to match their references.

Jev changes its semantic answer across option orders on 4/72 inputs. Five explicit-ID cases defer under both orders; four more defer only under mapping 0. This is a failure of this instrument/configuration, not a demonstrated internal mechanism or a universal scope deficit.

Qwen is not merely choosing the first letter: it predicts VALID on 68/72 inputs in mapping 0 and 72/72 in mapping 1. Its native readout has 12/12 false commitments in each mapping. No thinking or free-form generation was allowed in this arm. A weak native readout is not an estimate of the checkpoint's reasoning ceiling.

## Interface and accounting

Jev smoke: 6/6; Qwen smoke: 2/6. All valid semantic errors were retained under the predeclared gate. No malformed response, retry, warmup forward or follow-up prompt search occurred.

Jev: 150 HTTP attempts, 226,329 reported input tokens (221,964 main), estimated $0.009505818. The frozen plan reserved 522,016 conservative byte-based units, below 1,000,000; these are not exact billed tokens. Returned model: jev-1.13.0. Prices are usage estimates, not invoices.

Qwen: 150 local prefills, 181,360 prompt tokens (178,656 main). Existing pinned instruction weights; BF16, SDPA, RTX 5070 Ti, Transformers 4.55.4 / torch 2.8.0+cu128, no training/downloads. Peak allocated memory 8805.4 MiB. Candidate mass minimum 0.5495, median 0.9983; zero low-mass (<0.01) main records. The full-vocabulary top token is A/B/C in 142/144 main records. Conditional probabilities are not calibrated confidence.

Median main measured latency: hosted Jev 0.149s; local Qwen 0.293s. They use different serving environments and tokenizers; this is not a deployment speed/cost ranking. Runtime load times and exact prompt IDs are separately retained.

## Evidence chain and limits

- Jev inputs/code/protocol were published at `680fb6f` before calls. Local prompts/readout were published at `c327d59`, after the six Jev smoke responses but before either main grid and before all new local outputs.
- Data selection is deterministic from pinned public simulated tau retail records; 12 users are disjoint from the earlier payment pilot. Coverage statements and omitted-world witnesses are constructed premises, not actual source retrieval failures.
- The unique-target requirement is explicit. An order ID uniquely selects the visible order; unseen same-product orders do not make that ID ambiguous. The omission sentence describes product-name requests, not explicit-ID requests.
- One wording family, simple templates, program-derived labels and no new independent review. The two earlier reviewers reviewed a different dataset. Later review cannot make these inspected data independent confirmation.
- Qwen and Jev do not share a backbone, serialization or inference interface. Inputs/rubrics and options correspond, but this comparison does not isolate dedicated training. No new Kev or Laya model was executed.
- No general novelty, model replacement, tau-bench agent score or paper-ready causal explanation is established. Established context-sufficiency and abstention work is discussed in [RELATED_WORK.md](RELATED_WORK.md).

## Decision and reproduction

Stop the frozen Jev/native grids here. The next justified control is one separately frozen fixed-budget Qwen reasoning arm on the same material, disclosed as outcome-aware exploration. Independent semantic review is needed before stronger reference claims. New-material confirmation and natural-language transfer are later gates, not completed work.

Run `python research/candidate-completeness/analyze.py --verify` and `python research/candidate-completeness/publish.py --verify` without API credentials or model weights. These verify recorded results, not model honesty or scientific validity. See [PROTOCOL.md](PROTOCOL.md), [LOCAL_PROTOCOL.md](LOCAL_PROTOCOL.md), [machine-readable summary](results/summary.json), [review-only package](review/README.md) and [replay](../../docs/candidate_coverage.html).
