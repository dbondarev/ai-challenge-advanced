---
name: update-smoke
description: Updates Bookreader smoke scenarios after a new feature ships, then re-runs code tests and Playwright MCP smoke. Use when the user says they deployed a new feature and wants smoke updated and everything re-run.
---

# Update smoke after a feature

Read `CLAUDE.md` and `qa/smoke.md`.

1. Identify the new user-visible behavior (route, button, upload, delete).
2. Append or edit a numbered scenario in `qa/smoke.md`. Keep: no sign-in; create = EPUB upload; fixture path unchanged unless the feature needs another file.
3. Run `scripts/check.sh`.
4. Run all smoke scenarios through Playwright MCP with a screenshot per step.
5. Write a single report: what scenario you added, code tests, smoke results.

Do not invent login. Do not remove existing scenarios unless the UI removed that flow.
