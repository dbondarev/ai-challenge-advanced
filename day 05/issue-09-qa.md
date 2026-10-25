# QA report — issue 9 (minimal EPUB still uploads)

Test-only. Followed `qa-runner.md`. `qa/smoke.md` not extended.

## Code tests

`scripts/check.sh` — pass (23 tests, including POST 201 without date/cover/series).

## Smoke

| # | Scenario | Result | Screenshot |
|---|---|---|---|
| 1 | Empty library | pass | `screenshots/issue-09/01-empty-library.png` |
| 2 | Upload EPUB | pass | `screenshots/issue-09/02-upload-epub.png` |
| 3 | Open reader | pass | `screenshots/issue-09/03-open-reader.png` |
| 4 | Delete | pass | `screenshots/issue-09/04-delete-book.png` |
| 5 | Search Austen / zzz | pass | `screenshots/issue-09/05-search-austen.png`, `05-search-zzz.png` |

No smoke failures.
