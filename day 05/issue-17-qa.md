# QA report — issue 17 (q in memory, no LIKE)

API-only confirmation. Followed `qa-runner`. No new smoke scenario. `Library.list` already filters after `JSON.parse`, case-insensitive, no `LIKE` / `ilike` / `orWhere`. Spec §11.1 aliases not added.

## Code tests

`scripts/check.sh` — pass (23 tests).

## Smoke

Existing scenarios 1–9. No smoke.md change.

| # | Scenario | Result | Screenshot |
|---|---|---|---|
| 1 | Empty library | pass | `screenshots/issue-17/01-empty-library.png` |
| 2 | Upload EPUB | pass | `screenshots/issue-17/02-upload-epub.png` |
| 3 | Open reader | pass | `screenshots/issue-17/03-open-reader.png` |
| 4 | Delete | pass | `screenshots/issue-17/04-delete-empty.png` |
| 5 | Search Austen / zzz | pass | `screenshots/issue-17/05-search-austen.png`, `05-search-zzz.png` |
| 6 | Header stubs | pass | `screenshots/issue-17/06-header-authors.png`, `06-header-series.png`, `06-header-collection.png` |
| 7 | Cover fallback | pass | `screenshots/issue-17/07-cover-fallback.png` |
| 8 | Status badge | pass | `screenshots/issue-17/08-status-badge.png` |
| 9 | Year label | pass | `screenshots/issue-17/09-year-label.png` |

No smoke failures.
