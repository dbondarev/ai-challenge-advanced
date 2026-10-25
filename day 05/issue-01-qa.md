# QA report — issue 1 (README spec/design links)

Change: docs only in `bookreader/README.md`. No user-visible UI. Followed `qa-runner.md` (check.sh + existing smoke). `qa/smoke.md` not extended.

## Code tests

`scripts/check.sh` — pass (typecheck, 10 API tests, lint).

## Smoke (Playwright MCP, `http://127.0.0.1:5173`)

API: `BOOKREADER_DATA=/tmp/bookreader-smoke-keMR1l`, port 3333. Vite: 127.0.0.1:5173.

| # | Scenario | Result | Screenshot |
|---|---|---|---|
| 1 | Empty library — heading Library, no books | pass | `screenshots/issue-01/01-empty-library.png` |
| 2 | Upload pride.epub — Pride and Prejudice — Jane Austen | pass | `screenshots/issue-01/02-upload-epub.png` |
| 3 | Open reader — Chapter one, Back to Library | pass | `screenshots/issue-01/03-open-reader.png` |
| 4 | Delete — book gone | pass | `screenshots/issue-01/04-delete-book.png` |

Favicon.ico 404 only. No smoke failures.
