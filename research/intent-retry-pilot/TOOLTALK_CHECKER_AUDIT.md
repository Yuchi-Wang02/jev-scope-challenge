# ToolTalk receiver-check regression: isolated reproduction

**At the inspected revision, `SendMessage.check_api_call_correctness` cannot reject an incorrect receiver through its receiver check.** It compares `predict_params['receiver']` with itself. With an ordinary string that condition is false regardless of the reference receiver.

Source: [Microsoft ToolTalk, pinned `message.py` line 210](https://github.com/microsoft/ToolTalk/blob/e05f4ce6132c80ed33392b81535b077d56ab28fd/src/tooltalk/apis/message.py#L210), commit `e05f4ce6132c80ed33392b81535b077d56ab28fd`. Source file SHA-256: `8cad12aec95c6befd7aefe0f938918d42a3b2d642eaedd8e142a3993db8118b8`.

## What was executed

The [reproducer](tooltalk_checker_repro.py) parses the pinned source with Python AST and extracts this one method without editing its body. It removes only the staticmethod decorator to call the method in isolation. It supplies a controlled numeric `semantic_str_compare` dependency. Neither the upstream package nor an embedding model is loaded, and no message is sent.

These are **software regression tests, not mock model evaluations**. Passing message similarity is the explicit premise of the counterexample; the upstream similarity model itself was not run. The source helper computes embedding cosine similarity, so independently assessing that helper remains outside this test.

| Test | Controlled similarity | Original checker accepts | One-line repair accepts |
|---|---:|---|---|
| Correct recipient, same session | 1.0 | Yes | Yes |
| Different recipient, identical text, same session | 1.0 | **Yes** | **No** |
| Wrong session | 1.0 | No | No |
| Dissimilar message | 0.0 | No | No |
| Different recipient, similarity at accepted boundary | 0.8 | **Yes** | **No** |

All five expectations were checked by running the extracted method and a copy with only the receiver comparison repaired. [Machine result](results/tooltalk_checker_repro.json).

## Reuse consequence

Do not reuse this checker as evidence of recipient correctness. The same source's `SendMessage.call` returns a generated message identifier without persisting a sent-message record; it is not an effect ledger for duplicate-send research. Its source dialogues may still be useful when separately audited and attributed. Those are distinct decisions.

This inspection establishes a local checker defect. It does **not** establish how frequently models chose wrong receivers, how much any published score would change, whether another evaluation layer catches the error, or whether an existing issue/patch already describes it. No upstream issue or PR was posted.

## Attribution and patch

The unchanged source file is retained as [audit_sources/tooltalk_message.py](audit_sources/tooltalk_message.py), with the upstream [MIT license](audit_sources/TOOLTALK_LICENSE). Copyright Microsoft Corporation. Its only use here is the isolated reproduction; our independent operation-scope simulator does not import this source.

[tooltalk_receiver_fix.patch](tooltalk_receiver_fix.patch) is a proposed one-line correction. It has not been applied to an upstream checkout, committed, pushed, or validated by the full ToolTalk test suite. A proper upstream change should add a regression test in its own test structure and check the other evaluation layers before making score-impact claims.

Reproduce locally, without inference:

```bash
python research/intent-retry-pilot/tooltalk_checker_repro.py
```
