# Same facts. Different answer interface.

Current status: **all 648 jobs completed and independently recounted**.
[Results, costs and limits](RESULTS.md) · [Next decision](NEXT_DECISION.md).
Semantic-label generation improves mapping consistency but does not improve
mean source agreement over generated letters. This cohort is now closed.

Historical status at execution freeze: **prepared, zero model calls**. This is the next
bounded study after the [completed stage-attribution comparison](../qa4pc-stage-attribution/CONTINUATION_RESULTS.md).
Subsequent execution must add a separate result/status entry here and preserve
the prospective protocol and original preparation artifacts.

Question: how much does the ordinary/dedicated-model comparison depend on the
output interface? On 12 disjoint QA4PC policy trees /24 scenarios, compare native
Jev with Qwen finite letters, generated letters, and generated semantic labels.
All six label permutations are evaluated. The generated-letter bridge has the
exact same input tokens as the finite-letter route.

- [Design and decision rules](DESIGN.md)
- [Execution protocol](PROTOCOL.md), [freeze](freeze.json), [648-job manifest](plan_manifest.json)
- [Source selection](cohort.json) and [selection code](cohort.py)
- [Prior-method check and novelty limits](RELATED_WORK.md)
- [No-weight generation configuration audit](generation_audit.json)

The planned ledger is 162 HTTP attempts, 162 local prefills and 324 local
generations, including smoke. Local inputs total 115,668 tokens; generated output
cap 10,368. These are plans, not actual usage or completed results. Semantic smoke
mistakes and malformed generated answers remain observations; structural errors
halt the corresponding backend. No automatic retries or output-dependent search.

The current new sample contains no=13/maybe=6/yes=5 source labels. Zero new human
labels have been collected. Upstream QA4PC consistency is not semantic truth.
Policies may have appeared in model training; project ID disjointness does not
establish contamination freedom. Twelve trees are the statistical clusters.

Provenance: original source is [QA4PC](https://huggingface.co/datasets/Marzipan/QA4PC/tree/2b1de7c5e588ec70afa1e753394ae25531e0d182),
with unresolved explicit dataset redistribution terms. Source prose stays local;
public artifacts expose IDs/hashes and derived outputs. No third-party repository
was forked for this stage. Selection, API/logit observations and configuration
audits adapt this project's prior original code; the durable journal is reused
unchanged. Related option-sensitivity/calibration methods are credited above.

Pre-execution self-audit: an uncommitted local freeze draft was replaced before
any call to pin an explicit implementation file list, permitting later analysis
files without changing the execution contract. The old draft remains in the
local preparation cache. No model observation motivated this bookkeeping change.

Remaining before a scientific conclusion: complete the frozen grid, independently
recompute actions/counts/costs, report invalids and all six mappings, then close
this cohort. Human semantic validation and stronger/cost-matched comparators
remain separate gaps. Neither voting nor option sensitivity is claimed as new.
