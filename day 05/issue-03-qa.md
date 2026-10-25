# QA report — issue 3 (GET /books?q=)

API-only in-memory filter. No LIKE / ilike / orWhere. Followed `qa-runner.md`. `qa/smoke.md` not extended.

## Code tests

`scripts/check.sh` — pass (typecheck, 11 API tests including `GET /books?q= filters by title or author in memory`, lint).

## Smoke (Playwright MCP, `http://127.0.0.1:5173`)

API: `BOOKREADER_DATA=/tmp/bookreader-smoke-SiduoC`, port 3333. Vite: 127.0.0.1:5173.

| # | Scenario | Result | Screenshot |
|---|---|---|---|
| 1 | Empty library | pass | `screenshots/issue-03/01-empty-library.png` |
| 2 | Upload pride.epub | pass | `screenshots/issue-03/02-upload-epub.png` |
| 3 | Open reader | pass | `screenshots/issue-03/03-open-reader.png` |
| 4 | Delete | pass | `screenshots/issue-03/04-delete-book.png` |

No smoke failures.
