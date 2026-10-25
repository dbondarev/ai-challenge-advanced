# QA report — issue 8 (cover + GET /books/:id/cover)

API-only. UI fallback later (issue 13). Followed `qa-runner.md`. `qa/smoke.md` not extended.

## Code tests

`scripts/check.sh` — pass (22 tests). Cover 200 when present, 404 when missing.

## Smoke

| # | Scenario | Result | Screenshot |
|---|---|---|---|
| 1 | Empty library | pass | `screenshots/issue-08/01-empty-library.png` |
| 2 | Upload EPUB | pass | `screenshots/issue-08/02-upload-epub.png` |
| 3 | Open reader | pass | `screenshots/issue-08/03-open-reader.png` |
| 4 | Delete | pass | `screenshots/issue-08/04-delete-book.png` |
| 5 | Search Austen / zzz | pass | `screenshots/issue-08/05-search-austen.png`, `05-search-zzz.png` |

No smoke failures.
