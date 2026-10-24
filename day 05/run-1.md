# Run 1 — cloud (Cursor)

Tracker: `pool.md` (GitLab MCP 401 invalid_token after mcp_auth; issues not created on git.modumuptools.com).
Profile file: `bookreader/.cursor/agents/execution-loop.md`. No commits.

check.sh after code: 15 tests, green.

| # | Issue | Profile | Result | Time | Notes |
|---|---|---|---|---|---|
| 1 | README spec/design links | feature | pass | ~1 min | README |
| 2 | schema_version research | research | pass | ~2 min | `issue-02-research.md` |
| 3 | GET /books?q= | bug-fix | pass | ~3 min | in-memory filter, no LIKE |
| 4 | LibraryPage search label | bug-fix | pass | ~2 min | htmlFor=library-search |
| 5 | test q matches author | feature | pass | ~2 min | library.test.ts |
| 6 | year from dc:date | feature | pass | ~4 min | publishedYear |
| 7 | language from dc:language | feature | pass | ~2 min | ru-RU → ru |
| 8 | cover + GET cover | feature | pass | ~5 min | 200/404 |
| 9 | upload without date/cover | test | pass | ~1 min | http.test |
| 10 | CLAUDE.md year/language/cover | docs | pass | ~1 min | |
| 11 | CSS tokens 8.13 | refactor | pass | ~2 min | styles.css |
| 12 | AppHeader stubs | feature | pass | ~2 min | /authors /series |
| 13 | BookCover fallback | feature | pass | ~2 min | |
| 14 | StatusBadge | feature | pass | ~2 min | hardcoded unread |
| 15 | YearLabel изд. YYYY | feature | pass | ~1 min | |
| 16 | Russian UI + smoke.md | bug-fix | pass | ~2 min | |
| 17 | q in memory, no LIKE | refactor | pass | ~1 min | already true; rules + ilike ban |
| 18 | review LibraryPage + api.ts | review | pass | ~2 min | `issue-18-review.md` |

Streak: **18 / 18**. First-try (this loop, no user prompt between issues): **100%**.
Broke on: none.
Average: ~2 min/issue (wall ~35 min including check.sh).
