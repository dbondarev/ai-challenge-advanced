# QA report — issue 13 (BookCover 2:3 fallback)

User-visible cover card. Followed `update-smoke`. Added scenario 7 in `qa/smoke.md`.

## Scenario added

## 7. Cover fallback — grey 2:3 card when the EPUB has no cover.

## Code tests

`scripts/check.sh` — pass (23 tests).

## Smoke

| # | Scenario | Result | Screenshot |
|---|---|---|---|
| 1 | Empty library | pass | `screenshots/issue-13/01-empty-library.png` |
| 2 | Upload EPUB | pass | `screenshots/issue-13/02-upload-epub.png` |
| 3 | Open reader | pass | `screenshots/issue-13/03-open-reader.png` |
| 4 | Delete | pass | `screenshots/issue-13/04-delete-book.png` |
| 5 | Search Austen / zzz | pass | `screenshots/issue-13/05-search-austen.png`, `05-search-zzz.png` |
| 6 | Header stubs | pass | `screenshots/issue-13/06-authors-stub.png`, `06-series-stub.png`, `06-collection.png` |
| 7 | Cover fallback | pass | `screenshots/issue-13/07-cover-fallback.png` |

No smoke failures.
