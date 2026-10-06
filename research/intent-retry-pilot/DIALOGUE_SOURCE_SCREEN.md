# Bounded screen of existing multi-turn dialogue sources

Checked: 2026-10-05. Status: **source inspection, no model evaluation**. This screen does not upgrade the pilot's synthetic inputs to natural-user evidence.

## Decision

Two established sources provide useful complete conversational workflows, but the inspected material does **not yet supply a directly reusable, same-payload retry-versus-new-operation contrast**. The closest ToolTalk dialogue requests another notification after a meeting change; its message payload changes. A second dialogue repairs a failed login by using the changed password. Both are ordinary, meaningful continuations, but neither measures the current pilot's central ambiguity without adaptation.

This is a bounded screening result, not a claim that these datasets, other releases, or the wider literature lack such cases. Do not run a new model batch merely by relabeling these conversations as `RESUME_EXISTING`/`START_ADDITIONAL`: their original tasks have more actions and different truth conditions.

## Sources, provenance, license, and inspected scope

| Source | Pinned revision and scope | Origin of dialogue | License evidence |
|---|---|---|---|
| BFCL / Gorilla | `6ea57973c7a6097fd7c5915698c54c17c5b1b6c8`; 200 `BFCL_v4_multi_turn_base` records, 734 user turns, paired reference trajectories; selected function schemas and implementations | Curated simulated workflows with human-labeled trajectories. The multi-turn construction uses task graphs, persona-based phrasing, and human checking. It is **not** the separately described crowd-sourced single-turn Live collection. The inspected construction account does not establish an individual utterance's exact authorship/tool-assistance provenance. | [Repository Apache-2.0 license](https://github.com/ShishirPatil/gorilla/blob/6ea57973c7a6097fd7c5915698c54c17c5b1b6c8/LICENSE); [BFCL release/license statement](https://github.com/ShishirPatil/gorilla/blob/6ea57973c7a6097fd7c5915698c54c17c5b1b6c8/berkeley-function-call-leaderboard/README.md#license) |
| ToolTalk | `e05f4ce6132c80ed33392b81535b077d56ab28fd`; all 50 hard conversations in `data/tooltalk`, 194 user turns; selected API implementations | GPT-4 proposed scenarios, then authors selected scenarios and manually wrote full conversations. These are human-authored benchmark dialogues with model-assisted scenario development, **not captured production conversations**. | [Repository MIT license, Microsoft copyright](https://github.com/microsoft/ToolTalk/blob/e05f4ce6132c80ed33392b81535b077d56ab28fd/LICENSE) |

Construction sources: [BFCL multi-turn authors' account, Data Curation](https://gorilla.cs.berkeley.edu/blogs/13_bfcl_v3_multi_turn.html), [ToolTalk paper, conversation construction](https://arxiv.org/abs/2311.10775). This report distinguishes simulated but independently published material from observed real-world demand.

Selection used the source conversations/reference calls, never model failures or a leaderboard score. The bounded screen searched all user turns in these two splits for `again`, `another`, `repeat`, `retry`, `duplicate`, and selected same-message phrases; compared cross-turn reference calls; then read complete promising dialogues and relevant schemas/code. The search produced two ToolTalk keyword-hit turns and nine BFCL keyword-hit turns. Repeated action names were also checked to avoid relying only on keywords. This is a retrieval screen, not exhaustive semantic annotation of every turn.

ToolTalk has no exact repeated cross-turn request after JSON key normalization in these 50 records. BFCL has one repeated call after AST/keyword-order normalization: `cd(folder='temp')` in `multi_turn_base_0`, discussed below. The normalization does not prove semantic equivalence or non-equivalence: positional/keyword aliases, defaults, and context-dependent relative paths need tool-aware interpretation.

## Four complete case pointers and their fit

All case summaries below are paraphrases. The linked full source preserves the original wording and trace. No actual account credential is needed to study these examples; fixture credential strings are not reproduced here.

### 1. Meeting changed; notify the same people again

- Source: ToolTalk `Calendar-Messages-Weather-SendMessage-1`, conversation ID `068dbfba-0b2b-42b2-835e-f068a3e545ca`; all four dialogue entries, especially user entry 2.
- Full [pinned conversation](https://github.com/microsoft/ToolTalk/blob/e05f4ce6132c80ed33392b81535b077d56ab28fd/data/tooltalk/Calendar-Messages-Weather-SendMessage-1.json).
- Sequence: user requests a September 14 meeting, 14:00–16:00, with three named participants and reminder messages. The reference creates the event and sends three reminders. The user reports a participant's conflict and asks to move the event two hours earlier and notify the team again. The reference modifies the existing event to 12:00–14:00 and sends three updated messages.
- Visible evidence: the earlier successful event/message responses, existing event ID, recipients, and later user instruction are available. This is not a lost receipt or timeout scenario.
- Tools: `ModifyEvent(session_token, event_id, new_start_time, new_end_time)` and `SendMessage(session_token, receiver, message)`. [Calendar implementation](https://github.com/microsoft/ToolTalk/blob/e05f4ce6132c80ed33392b81535b077d56ab28fd/src/tooltalk/apis/calendar.py), [message implementation](https://github.com/microsoft/ToolTalk/blob/e05f4ce6132c80ed33392b81535b077d56ab28fd/src/tooltalk/apis/message.py#L159-L216).
- Original truth: preserve the existing meeting identity, revise times, send updated notifications. New sends are required, but their contents differ from the initial sends. A whole-payload hash already distinguishes the messages. It is therefore **not evidence of a same-payload deduplication failure**.
- Reuse boundary: keeping it intact would test update-versus-create and notification propagation, a broader/different task. Replacing the second request with an identical-message repeat, or injecting response loss, creates a new authored derivative with new labels.
- Annotation caution: the recorded created event name is unrelated to the meeting request, and corresponding message IDs repeat between the two assistant entries. Neither is a reason to infer real duplicate delivery. The source runtime/checker limitations below make those response IDs unsuitable as an effect ledger.

### 2. Password change; a failed old-password check; login with current credentials

- Source: ToolTalk `AccountTools-Email-Reminder-ChangePassword-1`, conversation ID `acf76d08-c7a5-4b5d-97f1-01f6eb13046e`; complete entries 0–16, decisive entries 12–15.
- Full [pinned conversation](https://github.com/microsoft/ToolTalk/blob/e05f4ce6132c80ed33392b81535b077d56ab28fd/data/tooltalk/AccountTools-Email-Reminder-ChangePassword-1.json).
- Sequence: user changes a leaked password, updates contact details, and verifies the account. The user explicitly requests logout and an old-password login to check that it no longer works. That login returns a known authentication failure. The user subsequently asks to log back in; the reference uses the new password successfully.
- State/schema: a successful `ChangePassword` updates the account record; `UserLogin(username, password)` checks the stored password and returns a session token on success. [Pinned account implementation](https://github.com/microsoft/ToolTalk/blob/e05f4ce6132c80ed33392b81535b077d56ab28fd/src/tooltalk/apis/account.py#L477-L519).
- Original truth: use current credentials after the deliberate failed test. The reference directly supports evaluating credential-state tracking and recovery from a known failure. Both visible feedback and payload change; there is no uncertain successful write or extra identical side effect.
- Reuse boundary: labeling this simply `RESUME_EXISTING` erases the reason the first failure was requested and loses the required parameter update. It would not fairly instantiate the current three-label contract.

### 3. Place a trade; inspect it; cancel the same pending order

- Source: BFCL `multi_turn_base_124`, three user turns, JSONL line 125 in both [questions/state](https://github.com/ShishirPatil/gorilla/blob/6ea57973c7a6097fd7c5915698c54c17c5b1b6c8/berkeley-function-call-leaderboard/bfcl_eval/data/BFCL_v4_multi_turn_base.json#L125) and [reference calls](https://github.com/ShishirPatil/gorilla/blob/6ea57973c7a6097fd7c5915698c54c17c5b1b6c8/berkeley-function-call-leaderboard/bfcl_eval/data/possible_answer/BFCL_v4_multi_turn_base.json#L125).
- Sequence: buy 100 AAPL shares at current price; retrieve details of the latest order; cancel that still-pending order after a change of mind. The initial configuration includes a completed older AAPL order and a new-order counter of `12446`.
- Reference trace: `get_stock_info(AAPL)`; `place_order(Buy, AAPL, 227.16, 100)`; `get_order_details(12446)`; `cancel_order(12446)`.
- [Tool schema](https://github.com/ShishirPatil/gorilla/blob/6ea57973c7a6097fd7c5915698c54c17c5b1b6c8/berkeley-function-call-leaderboard/bfcl_eval/data/multi_turn_func_doc/trading_bot.json), [state transitions](https://github.com/ShishirPatil/gorilla/blob/6ea57973c7a6097fd7c5915698c54c17c5b1b6c8/berkeley-function-call-leaderboard/bfcl_eval/eval_checker/multi_turn_eval/func_source_code/trading_bot.py#L275-L387): placement allocates an order ID; cancellation updates that order and rejects a completed order.
- Original truth: bind the later read/cancellation to the newly created order, not the older completed one. This is a useful native entity/reference control, but cancellation is outside the pilot's resume/additional/clarify action set. Adding a second identical purchase or a timeout would change the task.
- Visibility boundary: BFCL's initial backend configuration is evaluator state, not a free oracle view to feed the model. A derivative should preserve the tool observations the agent could obtain, rather than expose all hidden state directly.

### 4. Identical relative-path call, legitimately repeated in a different working directory

- Source: BFCL `multi_turn_base_0`, four user turns; [questions/state](https://github.com/ShishirPatil/gorilla/blob/6ea57973c7a6097fd7c5915698c54c17c5b1b6c8/berkeley-function-call-leaderboard/bfcl_eval/data/BFCL_v4_multi_turn_base.json#L1), [reference calls](https://github.com/ShishirPatil/gorilla/blob/6ea57973c7a6097fd7c5915698c54c17c5b1b6c8/berkeley-function-call-leaderboard/bfcl_eval/data/possible_answer/BFCL_v4_multi_turn_base.json#L1).
- Sequence: move a report into a new `document/temp` directory; inspect a section; sort its contents; bring in a previous report and compare the two files. The reference enters `temp`, later returns to its parent to move the previous report, then enters `temp` again.
- Why retrieved: the two `cd(folder='temp')` calls are textually/structurally identical, separated by `cd(folder='..')` and other work.
- Original truth: the second directory change is required in the updated execution state. This demonstrates why global argument-only caching is invalid for a stateful relative-path tool. It does **not** establish a user-intent retry ambiguity or an irreversible duplicate effect. A correct tool-specific baseline already knows that `cd` depends on current directory and should not deduplicate it globally.
- Reuse boundary: this is a useful negative control for a proposed universal deduplicator, but it should not be promoted to a flagship payment/message reliability example.

## Why ToolTalk's existing executor is not our effect oracle

Static inspection of [the pinned `SendMessage` code](https://github.com/microsoft/ToolTalk/blob/e05f4ce6132c80ed33392b81535b077d56ab28fd/src/tooltalk/apis/message.py#L182-L216) found two concrete constraints:

1. `call` validates the session and nonempty message, then generates a response ID. It does not append a sent message to a persistent outbox in this method. Response IDs alone therefore do not measure delivered effects.
2. The correctness function's recipient check compares the predicted recipient to itself. It does not actually compare that field against the reference recipient. This is a local static-code finding, not a re-evaluation of the published benchmark scores.

If we reuse the conversation, an independently verified effect ledger and recipient comparison are required, with an explicit adaptation record. Do not silently patch upstream behavior and present results as the unchanged ToolTalk benchmark. No upstream issue, PR, or message was sent in this screen.

## Next useful action

The source screen offers two honest choices:

- **Keep the current narrow research question:** seek a source that actually records a same-payload repeat with a reason for an additional effect, plus an uncertain-completion recovery context. These two screened sources have not supplied that pair. A targeted incident or opt-in interaction collection would be more informative than another synthetic paraphrase batch.
- **Investigate a different, source-grounded question:** evaluate maintaining object identity while applying revisions and propagating their consequences, starting with the meeting and trade workflows. This is already an established multi-turn tool-use problem, so first reproduce the native task and compare strong baselines. It cannot be advertised as a newly discovered semantic-idempotency gap.

A derivative must preserve original source IDs, version, license/notice, full prior dialogue, original reference trace, and every modification. Added failure states, altered requests, and new operation labels are ours and require fresh review. Neither existing human annotation nor an upstream license validates those new labels.

## Local audit trail

The ignored cache `.local/intent-natural-screen/` contains pinned repository metadata/tree inventories, fetched source files, `manifest.json` (URL, revision, byte count, SHA-256), and `screen_stats.json`. It is not part of a public dataset release. At completion this cache held roughly 1 MB of source/data plus the small paper text and metadata, with no model weights or upstream installation. No inference, model-output selection, fork, commit, push, or publication was performed for this screen.
