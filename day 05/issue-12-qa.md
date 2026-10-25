# QA report — issue 12 (AppHeader stubs)

User-visible routes. Followed `update-smoke`. Added scenario 6 in `qa/smoke.md`.

## Scenario added

## 6. Header stubs — Коллекция / Авторы / Серии, stub headings.

## Code tests

`scripts/check.sh` — pass (23 tests).

## Smoke (Playwright MCP)

| # | Scenario | Result | Screenshot |
|---|---|---|---|
| 1 | Empty library | pass | `screenshots/issue-12/01-empty-library.png` |
| 2 | Upload EPUB | pass | `screenshots/issue-12/02-upload-epub.png` |
| 3 | Open reader | pass | `screenshots/issue-12/03-open-reader.png` |
| 4 | Delete | pass | `screenshots/issue-12/04-delete-book.png` |
| 5 | Search Austen / zzz | pass | `screenshots/issue-12/05-search-austen.png`, `05-search-zzz.png` |
| 6 | Header Авторы / Серии / Коллекция | pass | `screenshots/issue-12/06-authors-stub.png`, `06-series-stub.png`, `06-collection.png` |

No smoke failures.
