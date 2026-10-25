# QA report — issue 15 (YearLabel изд. YYYY)

User-visible year on the library card. Followed `update-smoke`. Added scenario 9 in `qa/smoke.md`. Dated fixture: `qa/fixtures/dated.epub` (pride.epub has no dc:date).

## Scenario added

## 9. Year label — upload dated.epub; the card shows изд. 2014.

## Code tests

`scripts/check.sh` — pass (23 tests).

## Smoke

| # | Scenario | Result | Screenshot |
|---|---|---|---|
| 1 | Empty library | pass | `screenshots/issue-15/01-empty-library.png` |
| 2 | Upload EPUB | pass | `screenshots/issue-15/02-upload-epub.png` |
| 3 | Open reader | pass | `screenshots/issue-15/03-open-reader.png` |
| 4 | Delete | pass | `screenshots/issue-15/04-delete-empty.png` |
| 5 | Search Austen / zzz | pass | `screenshots/issue-15/05-search-austen.png`, `05-search-zzz.png` |
| 6 | Header stubs | pass | `screenshots/issue-15/06-header-authors.png`, `06-header-series.png`, `06-header-collection.png` |
| 7 | Cover fallback | pass | `screenshots/issue-15/07-cover-fallback.png` |
| 8 | Status badge | pass | `screenshots/issue-15/08-status-badge.png` |
| 9 | Year label | pass | `screenshots/issue-15/09-year-label.png` |

No smoke failures.
