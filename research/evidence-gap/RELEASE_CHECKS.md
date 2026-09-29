# Automated release checks

The scientific run used the public pre-inference freeze at
`4809a5b2ea9aa8aef803f2875ad064998f60dd0b`. These are post-run integrity and UI
checks, not independent scientific replication or human label validation.

- Frozen config hash remains `e2df561595485cf9d328ec989852be9d476e24214e1e5e32fbc94acfb009948d`.
- Actual complete run: 756 scientific records, 252 extra parity forwards, six
  warmups. Zero reserved model records, paid API calls or training steps.
- All 1,008 saved plans re-encoded using the existing pinned tokenizer; no
  truncation or mismatch. This token check scored no reserved input.
- All 504 LoRA tensors loaded exactly; pointer ordinary-causal versus packed
  outputs had maximum probability delta zero across all 252 development inputs.
- Finite truth implementations agree on 1,120 partial/conflicting states.
  A known-grammar text-only post-run reference checks all 288 candidate labels;
  it does not certify natural-language meaning or human independence.
- 38 repository tests passed in Python 3.10.18, including corruption/foreign-
  split rejection, no-write verification and blind-pack field restrictions.
- Derived scores, exhaustive count table, replay payload and blank review files
  reproduce through read-only verification. Figure data is checked separately
  from rendering; plot PNG/SVG rendering is not byte-compared across platforms.
- Microsoft Edge via Playwright CLI: result replay inspected at 1280×900 and
  390×844; selectors update the saved records and nine-method table. Review page
  checked at 390×844, starter/all lists contain 6/288 items. No viewport overflow.
- A missing favicon caused a 404 during initial preview; inline icons fixed it.
  The final review-page console contained zero errors or warnings. Form guard,
  local save, download and JSON ingestion were exercised using an explicit
  `UI_TEST_FIXTURE_NOT_HUMAN`. Its browser draft was removed. That fixture exists
  only in ignored local QA output and is not a human annotation.
- Browser QA used a local HTTP preview. Direct `file://` operation was not
  separately tested here; no live model or remote submission was used.
- Credential-pattern scan found no matches in new study files and new tests.
  No credential or model weight is part of this release.

The review manifest still records **zero independent annotations**, and no
calibration/test execution switch was introduced. Future human exports need
provenance verification/adjudication and a new protocol before reserved inference.
