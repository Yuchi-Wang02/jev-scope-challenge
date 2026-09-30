# Can one prefill replace a generated decision?

Current status: **56 jobs frozen; no model outputs yet.** Eight independent
interface checks precede 48 task prefills on the same 24 public ShARC inputs and
two option mappings. Planned input: 14,448 tokens. The ordinary model is the
existing pinned Qwen3.5-4B; no API requests or downloads are needed.

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
