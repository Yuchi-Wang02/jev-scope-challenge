# Four-action interfaces: live integration evidence

Technical label-copy smoke, not research task accuracy. Four AI-authored records
explicitly supply a selected label and a distractor. There are **zero source
dataset items and zero human reviews**. No ShARC, payment, or calibration grid
was rerun. These checks cannot rank Jev against Qwen or establish rule reasoning.

The [protocol](PROTOCOL.md), [call list](plan.json) and code were committed at
`6f26707137776940a23f022aa39a73b2afc78751` before execution. Both backends ran once, with no retry,
new model download, prompt repair or extra seed. All traces and start/finish
accounting are retained in [Jev results](results/jev/run.json),
[Jev events](results/jev/events.jsonl), [Qwen results](results/qwen/run.json) and
[Qwen events](results/qwen/events.jsonl).

|Interface check|Finished|Copied label matches|Input tokens|Output work|
|---|---:|---:|---:|---:|
|Jev 1.13.0, two four-option mappings|8/8|8|3236|360 returned output tokens|
|Qwen3.5-4B, direct/thinking|8/8|8|764|2195 generated tokens|

Statuses: Jev **completed**, Qwen **completed**. Known Jev input
price estimate: **$0.000135912**, using the checked official
$0.042/M input-token rate, not an invoice. Attempts missing usage:
0. Jev summed request latency 1.330s.
Qwen load 3.557s; generation-stage wall
70.113s. These tiny prompts do not establish throughput
or cost on the research workload. Qwen ran locally; electricity cost is unmeasured.

Qwen direct wrappers: `{'bare_json': 4}`; thinking wrappers:
`{'bare_json': 3, 'fenced_json': 1}`. The wrapper-tolerant contract was declared
before these outputs. Strict JSON compliance remains separate from copied-label
correctness. No historical result is rescored.

The [token audit](token_audit.json) re-rendered all local prompts, retokenized inputs,
decoded saved output IDs, and recomputed EOS/thinking boundaries and final parses,
using the pinned tokenizer without model forwards. The offline analyzer checks
the freeze, exact scheduled calls, event records, mappings, settings and work sums.
The pre-existing credential helper was checked out with CRLF; its recorded raw
byte hash is compared against that line-ending form of the frozen Git blob.
No semantic source difference is accepted. Credentials and HTTP headers are absent
from public records. These integrity checks do not authenticate a human reviewer.

## Stage audit and next decision

The original question was whether both backends could deliver an auditable
four-action result under the proposed interface. This narrow integration now has
real invocation evidence. Copying a supplied label cannot establish that the
model will infer it correctly from ambiguous natural-language rules.

The [external task card](../external-validation/TASK_CARD.md) still requires
independent human review and adjudication, then a separately frozen task protocol
with matched evidence, explicit baselines, prompts, budgets and paired analysis.
No ShARC performance result is claimed. This smoke is closed; do not expand it
into another generic calibration search. The useful next evidence is reviewed
natural-language task material and the matched, frozen comparison on it.

Offline verification (no model or API):

```bash
python research/action-backends/plan.py
python research/action-backends/analyze.py --verify
```
