# ShARC review-package publication amendment

2026-09-30. Scope: distribution only; no selection, label, or inference change.

The earlier source audit did not find a license file inside the pinned official
archive. That observation remains correct. It missed the explicit **CC BY-SA 3.0**
notice on the [official data page](https://sharc-data.github.io/data.html),
verified on the date above. This corrects our source inventory; it does not claim
the authors changed their license today. The [license terms](https://creativecommons.org/licenses/by-sa/3.0/)
require attribution and share-alike distribution of adaptations.

We now distribute a separately built [review package](public-review/review_package.zip),
with the original authors, source links, license, and transformation notice inside
the archive and the review page. This supersedes the publication restriction in
the historical [review protocol](SHARC_REVIEW_PROTOCOL.md) **only for this named
package**. Private exports, original manifests, selectors and protocols remain
unchanged. The repository's general MIT license does not replace the package's
CC BY-SA 3.0 license.

The package contains exactly the same 60 visible items and opaque item IDs as
the frozen private pack. It removes no additional input text and adds no answer
hint. It includes no source answer/evidence, source IDs, pair links, source-action
strata, primary/reserve roles, model output or completed annotation. ShARC is
public, so blinding is procedural rather than guaranteed. Reviewers receive only
the ZIP and should not read the study analysis before saving their initial review.

The old manifest's `source_rows_committed: 0` and related fields describe its
freeze-time state. The new publication manifest explicitly records 60 public
visible inputs and 60 opaque review IDs, with zero public source IDs or labels.
Do not read the two manifests as conflicting current counts.

The requirement for two independent human reviews, adjudication, frozen reserve
order and a separate model protocol is unchanged. A complete ZIP, license check,
or CI success supplies no human labels and opens no model run. The existing
payment reviewers have not reviewed these ShARC items.

Build from the preserved private pack after the original export, then verify
offline from the public ZIP (no private files needed for verification):

```bash
python research/external-validation/publish_review.py build
python research/external-validation/publish_review.py verify
```

Byte digests tie the embedded pack and blank CSV back to the original freeze.
ZIP entry names, field allowlists, blank status, attribution, generated page and
archive bytes are checked; additional external-data files remain rejected by
the repository publication check. These checks establish technical consistency,
not legal certification or semantic validity.

Publication QA: the full local suite passed 204 tests. The package's five focused
checks cover frozen-text drift, forbidden fields, filled CSV rejection, offline
verification and deterministic rebuilding. Browser inspection verified blank
startup, reviewer activation and navigation. A clearly named `UI_TEST_NOT_A_REVIEW`
export was saved and checked as one test row plus 59 blanks; it is not a human
submission. The browser download-event listener timed out despite the file being
written. A subsequent clear-draft interaction also lost browser control, so its
completion is not claimed. A fresh page opened blank; UI test data are excluded
from the ZIP, manifests and review counts. Automated checks do not establish
reviewer independence or completeness of cross-browser behavior.
