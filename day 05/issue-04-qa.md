# QA report Ч issue 4 (LibraryPage search field)

User-visible search field. Followed `update-smoke` skill. Added scenario 5 in `qa/smoke.md`.

## Scenario added

## 5. Search library Ч visible label, type Austen (hit), type zzz (empty).

## Code tests

`scripts/check.sh` Ч pass (typecheck, 11 API tests, lint).

## Smoke (Playwright MCP, `http://127.0.0.1:5173`)

| # | Scenario | Result | Screenshot |
|---|---|---|---|
| 1 | Empty library | pass | `screenshots/issue-04/01-empty-library.png` |
| 2 | Upload EPUB | pass | `screenshots/issue-04/02-upload-epub.png` |
| 3 | Open reader | pass | `screenshots/issue-04/03-open-reader.png` |
| 4 | Delete | pass | `screenshots/issue-04/04-delete-book.png` |
| 5 | Search Austen then zzz | pass | `screenshots/issue-04/05-search-austen.png`, `05-search-zzz.png` |

Visible label `ѕоиск`. `listBooks` passes `q`. No smoke failures.
