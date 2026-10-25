# Run 3 — Day 5 execution loop (both QA levels)

Tracker: `pool.md` (GitLab MCP 401 invalid_token; skip GitLab close). Product restored to pre-day-5. No commits.

`qa/smoke.md` was extended on issue 4 (search scenario 5) and issue 12 (header scenario 6).

| # | Issue | Profile | Result | Smoke ran | Notes |
|---|---|---|---|---|---|
| 1 | README spec/design links | feature-implementer | closed | yes (existing) | `issue-01-qa.md` |
| 2 | schema_version research | research | closed | n/a | `issue-02-research.md` |
| 3 | GET /books?q= | bug-fix | closed | yes (existing) | in-memory, no LIKE; `issue-03-qa.md` |
| 4 | LibraryPage search label | bug-fix | closed | yes (update-smoke) | visible Поиск; scenario 5; `issue-04-qa.md` |
| 5 | test q matches author | feature-implementer | closed | yes (existing) | two books; `issue-05-qa.md` |
| 6 | year from dc:date | feature-implementer | closed | yes (existing) | publishedYear; `issue-06-qa.md` |
| 7 | language from dc:language | feature-implementer | closed | yes (existing) | ru-RU to ru; `issue-07-qa.md` |
| 8 | cover + GET cover | feature-implementer | closed | yes (existing) | 200/404; `issue-08-qa.md` |
| 9 | fixture without date/cover | feature-implementer | closed | yes (existing) | POST 201; `issue-09-qa.md` |
| 10 | CLAUDE.md year/language/cover | feature-implementer | closed | yes (existing) | also .cursorrules; `issue-10-qa.md` |
| 11 | CSS tokens 8.13 | feature-implementer | closed | yes (existing) | styles.css; `issue-11-qa.md` |
| 12 | AppHeader stubs | feature-implementer | closed | yes (update-smoke) | header stubs; scenario 6; `issue-12-qa.md` |
| 13 | BookCover 2:3 fallback | feature-implementer | closed | yes (update-smoke) | scenario 7; `issue-13-qa.md` |
| 14 | StatusBadge tokens | feature-implementer | closed | yes (update-smoke) | unread badge; scenario 8; `issue-14-qa.md` |
| 15 | YearLabel | feature-implementer | closed | yes (update-smoke) | year 2014; scenario 9; `issue-15-qa.md` |
| 16 | Russian UI + smoke.md | bug-fix | closed | yes (update-smoke) | Russian copy; smoke 1-4,6; `issue-16-qa.md` |
| 17 | q in memory, no LIKE | feature-implementer | closed | yes (existing) | confirmed JSON.parse + in-memory; `issue-17-qa.md` |
| 18 | review LibraryPage + api.ts | review | closed | n/a | comment only; `issue-18-review.md` |

Streak: **18 / 18**. First failure: none.

Broke on: none.

Smoke reports live under `ai-challenge-advanced/day 05/issue-*-qa.md` and `issue-18-review.md`.

`qa/smoke.md` extended: yes (scenarios 5-9).
