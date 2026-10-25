# QA report — issue 6 (publication year from dc:date)

API/parse only. Year is not shown in the library UI yet. Followed `qa-runner.md`. `qa/smoke.md` not extended.

## Code tests

`scripts/check.sh` — pass (15 tests, including dated EPUB year 2014).

## Smoke

| # | Scenario | Result | Screenshot |
|---|---|---|---|
| 1 | Empty library | pass | `screenshots/issue-06/01-empty-library.png` |
| 2 | Upload EPUB | pass | `screenshots/issue-06/02-upload-epub.png` |
| 3 | Open reader | pass | `screenshots/issue-06/03-open-reader.png` |
| 4 | Delete | pass | `screenshots/issue-06/04-delete-book.png` |
| 5 | Search Austen / zzz | pass | `screenshots/issue-06/05-search-austen.png`, `05-search-zzz.png` |

No smoke failures. No authors/series tables added.
