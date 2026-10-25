# QA report — issue 5 (test q matches author)

Test-only. Followed `qa-runner.md`. `qa/smoke.md` not changed this issue.

## Code tests

`scripts/check.sh` — pass (typecheck, 12 API tests including `GET /books?q= matches author of one of two books`, lint).

## Smoke (Playwright MCP)

| # | Scenario | Result | Screenshot |
|---|---|---|---|
| 1 | Empty library | pass | `screenshots/issue-05/01-empty-library.png` |
| 2 | Upload EPUB | pass | `screenshots/issue-05/02-upload-epub.png` |
| 3 | Open reader | pass | `screenshots/issue-05/03-open-reader.png` |
| 4 | Delete | pass | `screenshots/issue-05/04-delete-book.png` |
| 5 | Search Austen / zzz | pass | `screenshots/issue-05/05-search-austen.png`, `05-search-zzz.png` |

No smoke failures.
