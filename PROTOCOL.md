# Frozen protocol: Cancel the Right Thing

**Version 0.1; 2026-09-29.** Series: *You Might Not Need Jev.*
User-authorized live comparison and public release. The protocol, code and data
are hashed in `manifest.json` before smoke or formal model calls. No method,
prompt or item selection follows observed formal predictions. This is a small
controlled behavioral probe, not a production benchmark or a method paper.

## Question and task

Can a frozen off-the-shelf Qwen3-4B handle the same cancellation scope decisions
as Jev? Classify the current effective instruction for the named target as
`CANCEL` or `KEEP`. The exact common contract and option descriptions are in
`core.py`. Only target and customer message reach either backend. Case IDs,
families, gold labels and variants are withheld from inference inputs.

The 48 original synthetic English inputs form 12 four-way cases:
four object-binding, four quoted-example versus actual-instruction, and four
superseded versus current-instruction cases. Each case contains the same
lowercased word multiset in all four texts. A/C are KEEP, B/D CANCEL. A/B and
C/D require a correct answer flip; A/C and B/D exchange complete clause order
and require a correct answer hold. All inputs unambiguously state an instruction.
This version excludes implicit intent, missing evidence, counting and arithmetic.

Labels are constructed from the explicit grammar and reviewed by AI. There is
**no independent human label audit**. User approval to run is not presented as
such an audit. Dataset status is preserved in every item and its data card.

## Backends and references

- Jev `jev-1.13.0`, original Choice distribution; exact served version required.
- Qwen/Qwen3-4B, revision `1cfa9a7208912126459214e8b04321603b3df60c`,
  BF16 on one GPU, eval/inference mode, TF32 off, `enable_thinking=False`.
  The native bare A/B next-token logits are conditionally normalized. Raw
  full-vocabulary A/B and leading-space A/B probabilities and candidate mass
  are retained. Leading-space probabilities are diagnostic, not a chosen
  alternative readout. No weights change, teacher, calibration or prompt search.
- Always KEEP; fixed word-boundary cancel/canceled/cancelled/end/terminate
  keyword rule; and a known-grammar parser. The parser accepts only message and
  target, resolves declared current/actual markers, and binds actions to their
  objects. Its rules are frozen before live calls. It is a grammar-specific
  code reference, not a general language benchmark competitor.

Each model sees both label mappings: A=CANCEL/B=KEEP and A=KEEP/B=CANCEL.
Jev Choice uses letters as keys and full semantics as descriptions. Qwen sees
the same state, contract and descriptions plus the letter-only output instruction.
One independent question per input. No prior case or answer in the context.

## Schedule and endpoints

1. Validate all word multisets, labels and invariants; test scoring and parser.
2. Freeze hashes of data, protocol, core, runner and analysis.
3. Dry-run; run three distinct engineering smoke inputs, one per family.
4. Formal round 0: 48 inputs x 2 mappings = 96 decisions per model.
5. Formal round 1: repeat all 96; a stability check, not more independent data.
6. Recompute offline, inspect the complete table, publish all outcomes.

Order within each round is randomized with seed 20260929+round, shared between
backends. Resume uses the full experiment fingerprint, case, mapping and round.
Successful jobs are not called again on resume. Terminal failures are retained;
they cannot be silently replaced by a later successful sample.

The main result is **complete case passes / 12 in round 0**: all four variants
under both mappings must be correct (8/8). Report each mapping's 4/4 score too.
Round 1 is reported separately. Auxiliary endpoints: per-decision correctness;
both-correct flip and hold pairs; wrong cancellation and missed cancellation;
mapping disagreement; wrong semantics under both mappings; repeat disagreement;
errors/missing jobs; binary Brier and NLL; raw probabilities and candidate mass.
Stable wrong pairs do not count as success. Errors/missing jobs stay in the
fixed denominator; no low-mass exclusion. Low mass <0.01 is flagged only.

Descriptive paired case bootstrap uses 10,000 resamples, seed 20260929. It is
**reweighting sensitivity within these 12 purposively constructed cases**, not
a real-world population confidence interval or equivalence test. The cases
share templates; do not treat 96 decisions or repeated rounds as independent.

Failure interpretation separates mapping/readout sensitivity from errors that
persist under both mappings. No universal claim about training necessity follows
from an open/closed model comparison with different unknown training histories.

## Cost and execution guardrails

Jev sequential calls, max two HTTP attempts per logical job, max 400 HTTP attempts
including smoke and across restarts. Cost stop threshold USD 1 based on observed
usage; it is not an invoice guarantee. Missing billed usage is unknown, not zero.
HTTP 401/403 and response/version-validation errors pause immediately. More than
5% formal jobs failing pauses the run. An instrument repair requires a documented
amendment; the existing freeze is never silently replaced.

Official price checked 2026-09-29: USD 0.042/million input tokens, output free:
[TypeSafe models](https://docs.typesafe.ai/models). Publish request/token totals
and usage-based estimated cost; account-level billed dollars are not inferred.
Qwen GPU time, model load and peak memory are reported separately. Existing GPU
ownership is not a zero-cost deployment claim.

Jev latency includes network and service; Qwen is local single-input execution,
CUDA synchronized, with startup/smoke separated. No architecture speed claim or
cost-normalized winner is inferred from this measurement.

## Public release and interpretation

README first example is S01, fixed before running. Publish all 48 inputs, exact
prompts/configuration, raw sanitized predictions, errors, recomputation script,
full case table, figure and offline result explorer. Model weights are excluded.
Independent project; no TypeSafe affiliation or endorsement. Code MIT; original
data CC BY 4.0; upstream model/component licenses remain their own.

Headline remains *Cancel the Right Thing: Jev vs a Frozen 4B*. A win subtitle
must be limited to this probe, supported by both mappings and repeated rounds.
If ranking reverses, disclose instability. If both pass, report that result;
do not modify the test until one model loses. New difficulty is a new version.

The ordinary paired/intervention test idea is prior work, including
[CheckList](https://aclanthology.org/2020.acl-main.442/). Native readout already has
open implementations such as [SemIf](https://github.com/TheoLeeCJ/SemIf-OpenJev).
This package claims a transparent small comparison, not invention of logits,
caching, label permutation or behavioral testing.

