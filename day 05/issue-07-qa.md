# QA report — issue 7 (language from dc:language)

API/parse only. Followed `qa-runner.md`. `qa/smoke.md` not extended.

## Code tests

`scripts/check.sh` — pass (18 tests, including `ru-RU` ? `ru`).

## Smoke

| # | Scenario | Result | Screenshot |
|---|---|---|---|
| 1 | Empty library | pass | `screenshots/issue-07/01-empty-library.png` |
| 2 | Upload EPUB | pass | `screenshots/issue-07/02-upload-epub.png` |
| 3 | Open reader | pass | `screenshots/issue-07/03-open-reader.png` |
| 4 | Delete | pass | `screenshots/issue-07/04-delete-book.png` |
| 5 | Search Austen / zzz | pass | `screenshots/issue-07/05-search-austen.png`, `05-search-zzz.png` |

No smoke failures.
