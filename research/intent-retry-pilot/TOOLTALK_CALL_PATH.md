# ToolTalk SendMessage caller-path audit

Checked: 2026-10-05. Pinned upstream: `microsoft/ToolTalk@e05f4ce6132c80ed33392b81535b077d56ab28fd` (MIT). **Static source inspection only:** no installation, import of upstream modules, vectorizer execution, inference, or benchmark rerun was performed for this audit.

## Finding

The inspected standard evaluation path **does check the tool name, but does not add a generic exact-parameter or recipient-equality check before/after `SendMessage.check_api_call_correctness`**. The API base class has a generic parameter comparator, but `SendMessage` overrides it; the dispatcher calls the override directly. Therefore the recipient self-comparison in the custom checker is not repaired by the inspected caller path.

This establishes a missing check in a reachable source path. It does not quantify affected published predictions, historical benchmark scores, or behavior of uninspected forks/configurations.

## Source chain and checks

| Stage | What the pinned source actually does | Reference |
|---|---|---|
| Evaluation entry point | `main` constructs `ToolExecutor`; after prediction, the evaluation branch calls `tool_executor.evaluate_predictions(conversation)`. The optional validation branch only asserts that `match` and `bad_action` fields exist. | [`evaluate_openai.py`, lines 152–202](https://github.com/microsoft/ToolTalk/blob/e05f4ce6132c80ed33392b81535b077d56ab28fd/src/tooltalk/evaluation/evaluate_openai.py#L152-L202) |
| API registration | `ALL_APIS` includes the imported `SendMessage` class. `ToolExecutor` builds a name-to-class dictionary from that list. | [`apis/__init__.py`, lines 36–40, 80–82](https://github.com/microsoft/ToolTalk/blob/e05f4ce6132c80ed33392b81535b077d56ab28fd/src/tooltalk/apis/__init__.py#L36-L82); [`tool_executor.py`, line 45](https://github.com/microsoft/ToolTalk/blob/e05f4ce6132c80ed33392b81535b077d56ab28fd/src/tooltalk/evaluation/tool_executor.py#L45) |
| Pair selection | `evaluate_predictions` collects predictions and reference calls, then invokes `compare_api_calls` for candidate pairs. It uses the returned boolean to mark a match and remove that reference call from further matching. There is no separate field-equality filter in this loop. | [`tool_executor.py`, lines 154–182](https://github.com/microsoft/ToolTalk/blob/e05f4ce6132c80ed33392b81535b077d56ab28fd/src/tooltalk/evaluation/tool_executor.py#L154-L182) |
| Dispatcher | `compare_api_calls` rejects differing `api_name` values, then returns `self.apis[api_name].check_api_call_correctness(prediction, ground_truth)`. | [`tool_executor.py`, lines 121–127](https://github.com/microsoft/ToolTalk/blob/e05f4ce6132c80ed33392b81535b077d56ab28fd/src/tooltalk/evaluation/tool_executor.py#L121-L127) |
| SendMessage override | It compares exception values and session tokens, self-compares the predicted recipient, and rejects message semantic similarity below `0.8`. It does not compare the predicted recipient to the reference recipient and intentionally does not require response-message-ID equality. No `super`/base-comparator call occurs. | [`message.py`, lines 198–216](https://github.com/microsoft/ToolTalk/blob/e05f4ce6132c80ed33392b81535b077d56ab28fd/src/tooltalk/apis/message.py#L198-L216) |
| Post-comparison scoring | Match state, action status and successful execution determine `bad_action` and the counters. The success calculation uses recall and bad-action rate; it does not independently inspect recipients. | [`tool_executor.py`, lines 189–232](https://github.com/microsoft/ToolTalk/blob/e05f4ce6132c80ed33392b81535b077d56ab28fd/src/tooltalk/evaluation/tool_executor.py#L189-L232) |

## Why the base comparator does not fix this

[`API.check_api_call_correctness`, lines 44–69](https://github.com/microsoft/ToolTalk/blob/e05f4ce6132c80ed33392b81535b077d56ab28fd/src/tooltalk/apis/api.py#L44-L69) checks response/exception equality and each reference parameter. It would compare a recipient if this method were invoked for the pair. However, `SendMessage` defines a same-named static method, and the dispatcher resolves that override. Python does not automatically run a base method before an override.

The runtime call wrapper is a different method: [`API.__call__`, lines 75–102](https://github.com/microsoft/ToolTalk/blob/e05f4ce6132c80ed33392b81535b077d56ab28fd/src/tooltalk/apis/api.py#L75-L102). It invokes `self.call(**kwargs)` and packages success or exceptions; it has no ground-truth argument and cannot enforce recipient agreement with a reference.

## Does execution reject a mismatched recipient instead?

The inspected execution route [`execute_tool`, lines 82–119](https://github.com/microsoft/ToolTalk/blob/e05f4ce6132c80ed33392b81535b077d56ab28fd/src/tooltalk/evaluation/tool_executor.py#L82-L119) checks whether the API is registered, supplies an authenticated session token when needed, and calls the tool. It does not receive the reference call or compare recipients.

[`SendMessage.call`, lines 182–196](https://github.com/microsoft/ToolTalk/blob/e05f4ce6132c80ed33392b81535b077d56ab28fd/src/tooltalk/apis/message.py#L182-L196) validates the session, accepts recipient strings without matching them to the reference, rejects an empty message, and returns a generated message ID. It does not append an outgoing effect to a persistent sent-message ledger in this method.

Consequently, for ordinary string recipients, a pair with the same tool, equal exceptions and session tokens, and a message comparison that passes can be marked as matching even when the recipients differ. This is a **conditional source-level consequence**. We did not execute the semantic comparator here: [`semantic_str_compare`, lines 43–58](https://github.com/microsoft/ToolTalk/blob/e05f4ce6132c80ed33392b81535b077d56ab28fd/src/tooltalk/apis/utils.py#L43-L58) uses an initialized text vectorizer and cosine similarity. Dependency errors or other runtime conditions are outside this static audit.

## Limits and appropriate claim

Supported: the pinned standard dispatcher reaches the recipient-defective override without applying the generic exact-parameter comparator; neither the inspected execution wrapper nor optional validation restores reference-recipient equality.

Unsupported: a measured false-positive rate, an altered published model ranking, a claim that all ToolTalk tools share this defect, or a full-runtime reproduction. Those require separate evidence. An isolated unit demonstration, if reported elsewhere, should stay labeled isolated unless the actual dependency-backed evaluation path is run.

The downstream [`calculate_error_types.py`, lines 37–59](https://github.com/microsoft/ToolTalk/blob/e05f4ce6132c80ed33392b81535b077d56ab28fd/src/tooltalk/evaluation/calculate_error_types.py#L37-L59) consumes previously written success/match/bad-action flags; it does not provide a second recipient validator. No upstream patch, issue, PR, or message was sent as part of this audit.

Fixed-version source bytes and SHA-256 entries are in the ignored `.local/intent-natural-screen/manifest.json`. No existing research files were changed by this audit.
