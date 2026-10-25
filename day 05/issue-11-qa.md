# QA report — issue 11 (CSS tokens 8.13)

CSS only, no new click path. Followed `qa-runner.md`. `qa/smoke.md` not extended.

## Code tests

`scripts/check.sh` — pass (23 tests).

## Smoke

| # | Scenario | Result | Screenshot |
|---|---|---|---|
| 1 | Empty library | pass | `screenshots/issue-11/01-empty-library.png` |
| 2 | Upload EPUB | pass | `screenshots/issue-11/02-upload-epub.png` |
| 3 | Open reader | pass | `screenshots/issue-11/03-open-reader.png` |
| 4 | Delete | pass | `screenshots/issue-11/04-delete-book.png` |
| 5 | Search Austen / zzz | pass | `screenshots/issue-11/05-search-austen.png`, `05-search-zzz.png` |

Tokens `--bg`, `--accent`, `--surface`, `--text` on body/library. No smoke failures.
