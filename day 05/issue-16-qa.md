# QA report — issue 16 (Russian library UI + smoke.md)

User-visible Russian strings. Followed `update-smoke`. Updated scenarios 1–4 and 6 in `qa/smoke.md` (Коллекция, Добавить EPUB, Удалить, Назад в коллекцию). No new scenario number.

## Scenario added

Existing scenarios 1–4 and 6 rewritten to match Russian library copy. Scenarios 5 and 7–9 unchanged.

## Code tests

`scripts/check.sh` — pass (23 tests).

## Smoke

| # | Scenario | Result | Screenshot |
|---|---|---|---|
| 1 | Empty library (heading Коллекция) | pass | `screenshots/issue-16/01-empty-library.png` |
| 2 | Upload EPUB (Добавить EPUB) | pass | `screenshots/issue-16/02-upload-epub.png` |
| 3 | Open reader (Назад в коллекцию) | pass | `screenshots/issue-16/03-open-reader.png` |
| 4 | Delete (Удалить) | pass | `screenshots/issue-16/04-delete-empty.png` |
| 5 | Search Austen / zzz | pass | `screenshots/issue-16/05-search-austen.png`, `05-search-zzz.png` |
| 6 | Header stubs | pass | `screenshots/issue-16/06-header-authors.png`, `06-header-series.png`, `06-header-collection.png` |
| 7 | Cover fallback | pass | `screenshots/issue-16/07-cover-fallback.png` |
| 8 | Status badge | pass | `screenshots/issue-16/08-status-badge.png` |
| 9 | Year label | pass | `screenshots/issue-16/09-year-label.png` |

No smoke failures.
