# Can one prefill replace a generated decision?

Current status: **complete, 56/56 prefills retained.** Eight interface checks
passed before 48 task prefills on the same 24 public ShARC inputs and two option
mappings. Source agreement is **13/24 and 10/24**, with **3/12 and 2/12** fully
matching pairs. One exact maximum tie is invalid. Total input: 14,448 tokens;
zero generated tokens; 10.672 session seconds. No API requests or downloads.

[Results and costs](RESULTS.md) · [Stage interpretation](INTERPRETATION.md) ·
[Interactive replay](https://yuchi-wang02.github.io/jev-scope-challenge/source_label_screen.html)

This control asks how decisions and compute change when a model selects among
four next-token letters instead of generating semantic JSON. The prompt,
verbalizer and readout change together. It is an outcome-aware follow-up to the
[completed source-label screen](../source-label-screen/RESULTS.md), not a new
algorithm or an independent test set. All prior outputs and source labels stay
unchanged. Source agreement is not independently verified correctness.

- [Frozen protocol and stop rules](PROTOCOL.md)
- [Exact prompts, token IDs and job order](plan.json)
- [Code and parent-evidence hashes](freeze.json)
- [Earlier tokenizer feasibility inspection](FEASIBILITY.md)
- [Source evidence concerns](../source-label-screen/SOURCE_REVIEW.md)

The first eight copy-letter checks must all pass. A failure stops this diagnostic
without prompt repair. The entire stage permits at most 56 physical prefills,
50,000 input tokens and 300 session seconds. No generated tokens, retries,
warmups or repeated jobs are planned. Record candidate-conditional probabilities
and full-vocabulary candidate mass separately; neither is calibrated confidence.

```powershell
python research/finite-choice-readout/finite_readout.py verify --model-dir PATH_TO_PINNED_LOCAL_MODEL
python research/finite-choice-readout/finite_readout.py run --model-dir PATH_TO_PINNED_LOCAL_MODEL
python research/finite-choice-readout/analyze_finite.py capture
python research/finite-choice-readout/analyze_finite.py verify
```

Execution requires the published clean freeze and the exact pinned runtime and
local files. The journal prevents silently rerunning an unknown outcome. Offline
analysis imports no model weights and makes no API calls.

The derivative input plan retains [ShARC attribution and CC BY-SA 3.0 terms](../source-label-screen/ATTRIBUTION.md).
Original implementation code is MIT; no upstream implementation is forked.
