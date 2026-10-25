# QA report — issue 14 (StatusBadge tokens)

User-visible status badge on the library card. Followed `update-smoke`. Added scenario 8 in `qa/smoke.md`.

## Scenario added

## 8. Status badge — after upload, the library card shows Не начата.

## Code tests

`scripts/check.sh` — pass (23 tests).

## Smoke

| # | Scenario | Result | Screenshot |
|---|---|---|---|
| 1 | Empty library | pass | `screenshots/issue-14/01-empty-library.png` |
| 2 | Upload EPUB | pass | `screenshots/issue-14/02-upload-epub.png` |
| 3 | Open reader | pass | `screenshots/issue-14/03-open-reader.png` |
| 4 | Delete | pass | `screenshots/issue-14/04-delete-empty.png` |
| 5 | Search Austen / zzz | pass | `screenshots/issue-14/05-search-austen.png`, `05-search-zzz.png` |
| 6 | Header stubs | pass | `screenshots/issue-14/06-header-authors.png`, `06-header-series.png`, `06-header-collection.png` |
| 7 | Cover fallback | pass | `screenshots/issue-14/07-cover-fallback.png` |
| 8 | Status badge | pass | `screenshots/issue-14/08-status-badge.png` |

No smoke failures.
