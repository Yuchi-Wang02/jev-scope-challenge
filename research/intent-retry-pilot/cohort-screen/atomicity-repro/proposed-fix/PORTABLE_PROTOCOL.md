# Portable staged-source replay protocol

Declared before the staged environment run. This is a portability replay of the existing author-proposed fix, not a new task, model evaluation, upstream release, or independent scientific replication.

## Frozen change

`portable_regress.py` is a straightforward copy of the frozen `regress.py`, with its complete textual difference in `portable-runner.diff`. It removes only the three exact ignored bytecode paths from the original 29-entry local preservation inventory, requires the other 26 entries, and checks its own additional freeze. It reports those exclusions and both freeze hashes. Case definitions, derivative environment, real runtime dispatch, dependency checks, source checks, native error assertions, state assertions, result records and isolated commit evaluator are unchanged. There is no dynamic monkeypatch.

The old runner, 14-file freeze, source manifest and all previous results remain unchanged. `portable-preservation.json` inventories the 62 pre-existing files present before this task, excluding only the README that will receive the new outcome. Verify that inventory after the staged run.

## Clean source tree and bounds

Create a fresh directory inside ignored `.local/agentabstain-portable-replay/`, preserving repository-relative paths. Copy only the union of:

- integration freeze and its declared files; integration source manifest entries;
- original reproduction's 26 non-bytecode preservation entries, original freeze/source files and their entries;
- proposed-fix original freeze and its declared files;
- portable protocol, runner, textual diff, preservation inventory, portable freeze and source-only preflight script.

Record every copied path, size and actual SHA-256 before execution. No path containing `__pycache__` or ending in `.pyc`/`.pyo` may be copied or present in the staged tree. The repository is currently uncommitted; this is a clean staged tree of reviewable files, **not a remote Git clone**. Original history is copied only where its frozen source checks require it.

Run the existing source-only preflight in that tree. Then run `portable_regress.py` once with Python UTF-8 mode and `-B`, using the already installed integration virtual environment outside staging. This is **not a fresh dependency installation**. Actual versions must match all 68 entries of the existing dependency lock; no installation or download is permitted.

Use the same five `cases.json` resets: no action, privacy only, invalid visibility with bio, invalid visibility without bio, and benign valid bio plus visibility. Bound: **8 real local environment calls, 6 expected successes, 2 expected validation errors, zero model/API calls**. Same unchanged BaseEnvironment and actual FastMCP; no agent SDK/server transport. Only local simulated state is modified. Retain an unexpected failure in its own output directory; at most a necessary program repair and new attempt may follow.

## Verification and collection

After execution, verify every copied input hash again, scan the whole staged tree for bytecode/cache artifacts, and verify the 62 original-file preservation hashes. Copy the complete new preflight and run results into fresh `portability-checks/staged-001` and `results/portable-staged-001` directories in proposed-fix. Record source and copied-result hashes so the public records are demonstrably the staged outputs. Do not overwrite any existing directory.

Record the staging path, the absolute reused Python executable, invocation, return code, input inventory and pre/post cache scans in a separate portability verification record. Existing local proposed-fix attempts used 12 calls; with one successful new eight-call replay the proposed-fix subtotal becomes 20. Original unpatched reproduction and earlier integration calls remain separate historical units, not additional calls in this replay.

Success supports replay from a bytecode-free source tree on this Windows host with the existing locked runtime. It does not prove fresh installation, cross-platform portability, a remote checkout/release, generalized atomicity, or model performance. Keep those limits in the README.
