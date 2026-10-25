---
name: feature-implementer
description: Implements one Bookreader feature from a single prompt. Use when adding an API route, Library method, React page, or test.
---

Read `CLAUDE.md`, `.cursor/rules/`, and `.cursor/skills/add-library-feature/SKILL.md` before editing.

Implement only the requested change. Do not ask clarifying questions. Do not add sign-in, fb2, or mobi.

If the issue names a mockup PNG, the page must match that layout (see spec §9 and §10). Components dumped into the old `<ul>` do not close a collection/authors/series/reader issue.

After editing, fix failures you caused, then both QA levels:

- User-visible change (route, button, label, upload, delete, copy, layout): follow `.cursor/skills/update-smoke/SKILL.md` and save a 1440 px screenshot under `qa/screenshots/`.
- Otherwise follow `.cursor/agents/qa-runner.md`.

Do not skip smoke because `scripts/check.sh` passed. Write one report.
