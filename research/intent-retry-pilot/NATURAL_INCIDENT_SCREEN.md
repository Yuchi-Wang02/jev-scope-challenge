# Bounded screen of public duplicate-execution incidents

**Decision: these four nominated reports do not establish a natural-language retry-versus-additional-intent problem.** They provide evidence that duplicate execution is reported in agent products, but the available mechanisms are scheduling, message delivery, permission resumption, or unresolved application behavior. None supplies a complete conversation in which a legitimate second operation must be distinguished from recovery of the first.

Screen date: **2026-10-05 America/New_York** (retrieval continued at **2026-10-06 00:15 UTC**). This is a source inspection, not a reproduction, prevalence estimate, or model evaluation. No upstream code was executed; no model was called; no issue author was contacted; no repository was forked.

## Scope and method

The four issues were nominated before inspection from the existing ACRFence reference leads. This is a convenience sample, not an exhaustive search. All four issue bodies, all **11 issue comments**, and their GitHub API event records were read. One directly linked predecessor discussion and its five comments were inspected for OpenHands context; it is not counted as a fifth independent incident. A linked LangGraph pull request and its three-file diff were also read.

The classification asks whether the available record requires inferring a new logical operation from user dialogue. Repeated execution alone is insufficient: transport duplication and interrupted-node replay can occur with the intended operation already known. Reporter statements, maintainer acknowledgment, merged code, and our reproduction are separate evidence levels.

## NI-01 — LangGraph interrupt scheduling

[Issue #6208](https://github.com/langchain-ai/langgraph/issues/6208), GitHub issue ID `3458360766`. Opened **2025-09-26 16:50:57 UTC**; updated **2026-10-01 03:30:48 UTC**; API state **open** at retrieval.

A collaborator describes unnecessary node re-execution while interrupts remain unresolved. The issue proposes tracking interrupt identities. Its sole [comment](https://github.com/langchain-ai/langgraph/issues/6208#issuecomment-5924159070), dated 2026-10-01, promotes an external checker; it is not a maintainer validation or a reproduced incident.

**Classification:** deterministic scheduler/resume bookkeeping. The report does not contain a natural user dialogue, competing operation intents, or a verified duplicate external effect. Its open status alone does not prove that the described implementation remains unfixed.

**Context and reproducibility:** source-level reproduction material exists in [PR #6158](https://github.com/langchain-ai/langgraph/pull/6158), merged **2025-10-06 20:11:53 UTC**, commit `6cc889981854b12acb1dad406adf5d517e8a22f2`. The diff adds interrupt tracking, skips blocked tasks, and tests synchronous/asynchronous selective resume. Tests also intentionally re-execute nodes under some resume patterns; node invocation count is not equivalent to duplicate side-effect count. We inspected the code but did not run the tests. The PR says it addresses this issue, despite the issue still being open.

## NI-02 — Claude Code approval followed by a redundant call

[Issue #13897](https://github.com/anthropics/claude-code/issues/13897), GitHub issue ID `3726173595`. Opened **2025-12-13 16:58:40 UTC**; closed **2026-02-14 00:09:46 UTC**; last updated **2026-02-21 14:15:02 UTC**. API state **closed / not_planned**.

The reporter describes a held SDKMAN installation call executing after approval, followed by another call and approval prompt. The second invocation reportedly finds the software installed. Listed environment: Linux, a custom MCP server, and `claude-sonnet-4-5-20250929`. Possible harm from non-idempotent operations is hypothetical in this report; no payment loss is shown.

All three comments are housekeeping automation. The [closure comment](https://github.com/anthropics/claude-code/issues/13897#issuecomment-3900202754) cites inactivity, **not a verified fix**. No human maintainer diagnosis is present.

**Classification:** reported permission/resume coordination problem, with a redundant model invocation alleged. It could motivate testing whether an agent waits for a pending call, but does not demonstrate confusion between a retry and a genuinely new user request.

**Context and reproducibility:** procedural steps and environment are available; full conversation, event ordering log, CLI version, and runnable custom server fixture are absent. Not reproduced here.

## NI-03 — OpenHands duplicate message dispatch

[Issue #9595](https://github.com/OpenHands/OpenHands/issues/9595), GitHub issue ID `3210032897`. The former `All-Hands-AI` URL redirects to `OpenHands`. Opened **2025-07-07 19:24:19 UTC**; closed **2025-08-05 12:29:22 UTC**; updated **2025-08-05 12:44:57 UTC**. API state **closed / completed**.

The reporter describes duplicate messages and apparent concurrent agents after a branch-push UI action, followed by duplicate commits. A [collaborator reply](https://github.com/OpenHands/OpenHands/issues/9595#issuecomment-3046493893) identifies it with a cloud incident and mentions a planned change. The reporter's interpretation of concurrent execution is not our reconstruction.

**Classification:** message delivery/lifecycle duplication. The visible record contains one intended message delivered twice, not authorization for two distinct operations.

**Context and reproducibility:** two screenshot attachments and a hosted conversation identifier are referenced, but there is no public full transcript, exact hosted version, model, or minimal executable fixture. Attachment pixels were not inspected. We did not access the private conversation or verify commits. Closed/completed status does not itself prove a fix in current deployments.

The directly linked [cloud discussion #148](https://github.com/OpenHands/OpenHands-Cloud/issues/148), ID `3319854285`, is supporting context. A [2025-05-13 contributor reply](https://github.com/OpenHands/OpenHands-Cloud/issues/148#issuecomment-3185745419) associates recurrence with server load and a refactor. A [2025-08-13 reply](https://github.com/OpenHands/OpenHands-Cloud/issues/148#issuecomment-3185855666) suggests closure. Neither supplies a dialogue-identity example or independent reproduction.

## NI-04 — CrewAI repeated kickoff and email task

[Issue #1978](https://github.com/crewAIInc/crewAI/issues/1978), GitHub issue ID `2812268456`. Opened **2025-01-27 07:26:59 UTC**; closed **2025-03-06 12:17:34 UTC**; updated **2026-07-24 21:06:01 UTC**. API state **closed / not_planned**.

The reporter attributes repeated email work to repeated crew kickoff, using CrewAI `0.98.0`, tools `0.32.0`, and a customized fork; they say upstream also exhibits it. A member requests code and then [execution logs](https://github.com/crewAIInc/crewAI/issues/1978#issuecomment-2621726512) to distinguish task repetition from wider agent repetition. No diagnostic log follows. The [closure](https://github.com/crewAIInc/crewAI/issues/1978#issuecomment-2703686597) is automatic inactivity housekeeping. A later third-party idempotency-tool promotion is not maintainer confirmation.

**Classification:** reported application/framework repetition; root cause unresolved. The source does not establish semantic operation-identity inference as the cause.

**Context and reproducibility:** linked [application source](https://github.com/Vardaan-Grover/agent_army/tree/195627a0a7c5b5a34994d43926ee3b0ca929e516) is available (tree inspected, application not executed or fully audited). No exact failing dialogue, outgoing-message ledger, or execution trace is provided. We cannot confirm actual duplicate email delivery from this record.

## Reuse and provenance boundary

This report contains short paraphrases, metadata, links, and our classifications. It incorporates no issue transcript, screenshot, application code, or benchmark sample. No issue-thread-specific dataset redistribution permission was established during this screen. Before republishing complete discussions, screenshots, or derived transcript data, review the relevant terms and provenance; public visibility alone is not the evidence of permission recorded here. The CrewAI reporter's application repository returned `license: null` in GitHub metadata, so no code-reuse license was established for that application. A separate framework fork reports MIT metadata; this does not resolve the application's status.

Live metadata endpoints used were `https://api.github.com/repos/{owner}/{repo}/issues/{number}`, its `/comments?per_page=100` and `/events?per_page=100` endpoints, the LangGraph `/pulls/6158` and `/pulls/6158/files?per_page=100` endpoints, and the reporter application tree/commit endpoints. Numeric issue/comment identifiers above allow precise relocation even if repository names change. All primary-thread comments fit on a single API page. Dates and status describe the retrieval snapshot and may change.

## Consequence for this pilot

**Do not convert these four reports into natural operation-identity benchmark items.** That would add unseen dialogue and intended-operation labels authored by us, while borrowing credibility from unrelated public failures. They may motivate separate deterministic scheduling and approval-resumption tests, with explicitly authored fixtures and properly scoped claims.

This bounded sample provides **zero complete natural retry-versus-additional-intent pairs**, and zero locally reproduced incidents. It does not prove that such pairs never occur. It does mean these nominated citations cannot supply the ecological-validity evidence currently missing from this pilot.

Further investment in the semantic candidate should require a complete source unit containing the initial request, prior operation status, subsequent user utterance, and evidence for the intended number of logical operations. A useful comparison must include a legitimate-repeat case as well as a duplicate-prevention case. In the meantime, preserve the clear-case Jev pass result and avoid constructing progressively trickier assent phrases merely to obtain an error.
