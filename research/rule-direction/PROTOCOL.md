# One "Only". Different Decision.

Prospective diagnostic, v1. Status at freeze: zero model calls. This is an
AI-authored synthetic diagnostic of rule direction, not a new logic algorithm,
independently reviewed benchmark, or confirmation of the QA4PC audit.

## Question and semantics

With facts and question fixed, do Jev and a named local Qwen configuration
distinguish `Q if P`, `Q only if P`, and `Q if and only if P`? All are fictional
constraints. Query Q under classical propositional implication. Enumerate all
four Boolean assignments to P and Q; keep those satisfying the rule and observed
P. Return yes if Q is true in all surviving worlds, no if false in all, and maybe
otherwise. Missing P is unknown. The contract is always satisfiable in this grid.

|Visible P|Q if P|Q only if P|Q iff P|
|---|---|---|---|
|True|yes|maybe|yes|
|False|maybe|no|no|
|Unstated|maybe|maybe|maybe|

The key direction switches are sufficient-to-necessary with P true (yes to
maybe) and P false (maybe to no). Unknown P supplies answer-preserving controls.
Equivalence supplies determined controls. Contraposition is valid under this
stated classical-constraint contract; this is not a Horn forward-chaining task.

## Fixed materials and scope

Twelve authored business vocabulary families, three rule patterns and three fact
states give 108 inputs. Each family shares its facts and question across rule
variants; only the rule connector changes. There are 24 yes,24 no,60 maybe
references. Always-maybe is therefore 60/108 and must be reported.

These twelve families are lexical replications of three shared logical patterns,
not twelve independently sampled real-world policies. No population prevalence,
significance or general model-ranking claim. Zero human reviews. Synthetic
templates intentionally remove the source-reference uncertainty; they do not
establish that these wordings represent real operations or explain prior errors.
No QA4PC, ShARC, payment or reserved queue text is reused. The old cohorts stay closed.

The grammar baseline receives visible policy/question/scenario only, recognizes
the authored vocabulary and connectors, and uses a closed-form decision table.
An independent exhaustive enumerator supplies possible-world witnesses and the
references. Their agreement checks software semantics, not independent human
validation. Full generated text and references are public under the repository
MIT license; the text is original synthetic material, not derived source prose.

## Execution and bounds

- Jev pinned `jev-1.13.0`, native three-choice API; actual served model, choice,
  raw probabilities, usage, latency and error records retained.
- Qwen3.5-4B at revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, existing local
  weights, BF16/SDPA, Transformers5.3.0/PyTorch2.8.0+cu128/PEFT0.18.1. Semantic
  labels, greedy nonthinking generation,32 new tokens maximum, natural EOS.
- Two display mappings: yes/no/maybe and maybe/no/yes. They are repeated measures,
  not full permutation coverage; no remains central. No position-invariance claim.
- Three independent badge smoke cases cover yes/no/maybe in both mappings:
  six calls per backend. Then108 inputs x2 mappings per backend.
- Total444 logical decisions:222 HTTP attempts and222 local generations, no
  retries, no adaptive follow-up or prompt search. Actual local physical forwards
  are separately logged; generation may use multiple forwards per decision.
- Whole-stage plan bound:2,000,000 API request bytes plus per-call allowance
  (a planning proxy, not tokens),300,000 actual Jev input tokens,200,000 local
  input tokens,7,104 local generated tokens and900 local session seconds.
  No model download or cloud deployment. Hosted internal work is unknown;
  call counts and token counts are not claims of matched hidden compute.
- Existing durable journal and audited adapters are reused unchanged and pinned
  in the freeze. Only unstarted jobs resume. Unresolved starts, protocol/schema,
  version or execution errors stop that backend; preserve failures. Semantic
  smoke errors and invalid generated answers are observations, not launch gates.
- Publish a clean code/data freeze and verify it before calls. Run the two
  backends without inspecting intermediate scores; only operational status is
  monitored. Freeze does not imply novelty or reference validity.

## Analysis fixed before outputs

Report both mappings, by relation and fact state, invalids, full-family9/9
correctness, both critical direction-pair correctness, unknown-fact invariance,
mapping disagreements, false commitments on maybe and unnecessary deferral on
yes/no. Keep invalids in accuracy denominators and separate from maybe.
Identify the specific biconditional-like signature: necessary+positive =>yes or
sufficient+negative =>no. Report how many lexical families have this signature
in both mappings; it is an error signature, not a proven internal mechanism.

No updated labels or removal after seeing results. On a data/program flaw,
preserve the run and name a separate amendment before any rerun.

Stop after this grid in all cases. If both models solve all main cells, close
this narrow candidate as a passed boundary. If one or more families fail, report
the full matrix. A replicated candidate signal requires the same critical
signature on at least3/12 vocabulary families in both mappings; fewer families
remain isolated observations. Even crossing this exploratory screen does not
authorize claiming a new phenomenon or a dedicated-model advantage.
Before a larger next study, require stronger ordinary-model comparison and new
independently reviewed material. Do not add harder cases until a failure appears.

## Prior work and reuse

[RuleTaker](https://www.ijcai.org/Proceedings/2020/537) studies reasoning over
natural-language facts and rules. [ProofWriter](https://aclanthology.org/2021.findings-acl.317/)
adds generated implications/proofs and three-way answering; those tasks already
motivate separating unknown from false. [FOLIO](https://aclanthology.org/2024.emnlp-main.1229/)
is a direct precedent for formal-logic-grounded natural-language entailment.
Our two-proposition constraint diagnostic is much narrower. Necessary/sufficient
conditions, truth-table enumeration and controlled connective substitutions are
not inventions here. No upstream repo was forked, no upstream dataset copied,
and no author code was executed. The run infrastructure reuses our own previous
adapters, generation configuration, tokenizer checks and journal unchanged.
