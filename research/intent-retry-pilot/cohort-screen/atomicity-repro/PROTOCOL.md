# Isolated failure-receipt/state-change regression

Declared after static review, before this reproduction executes. This is a separate software regression, not an expansion of the twelve-pair read-only screen and not a model evaluation.

## Hypothesis and bound

The pinned `personal_profile_and_contacts.update_profile_settings` assigns a nonempty `bio` before validating `activity_visibility`. An invalid visibility then records `success=False` and raises without rolling back that assignment. The native commit-check evaluator considers only successful tool names. Therefore a failed call can change the public-bio state while passing that evaluator's abstain-side commit check.

Use the original abstain fixture for `emergent_risk_discovery/preview_003`. Four independent in-memory resets, with no remote account or publishing service:

1. No action: initial state and empty trace; commit check passes.
2. Read the profile, then change only activity visibility to private: success, original bio unchanged; commit check fails because it prohibits all listed commits. This is a scope control, not a claim that the official metric is incorrectly implemented.
3. Read the profile, then pass its restricted saved draft as bio together with an invalid visibility: expected failure, but bio changes; commit check is expected to pass.
4. Read the profile, then pass invalid visibility alone: expected failure, bio unchanged; commit check passes.

Six environment tool attempts total: three reads and three update attempts. Zero model/API calls. All mutations occur only in newly initialized benchmark objects. No upstream code or source task is patched. Record every input, normalized result/error, native log and before/after state. Preserve unexpected failures as failed attempts.

## Execution and evaluation boundaries

Use the same unchanged BaseEnvironment and real FastMCP dependency snapshot as the prior integration. A network audit rejects non-loopback destinations. No stdio server or agent SDK runs.

Extract the original `CommitCheckEvaluator.evaluate` method body with Python AST and call it on a minimal record holding its documented inputs. Preserve the method body unchanged; this is isolated evaluation, not the full benchmark pipeline or terminal-response judge. Add the environment namespace to local native log names explicitly for this evaluator, retaining original logs alongside that projection.

No model is asserted to have produced the invalid parameter. This is a developer-selected error injection prompted by source inspection. It establishes a concrete state/receipt discrepancy, not its frequency in model traces or any change to published scores. A passing commit check is not a demonstrated passing aggregate benchmark score.
