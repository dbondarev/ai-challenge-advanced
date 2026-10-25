---
name: execution-loop
description: Drains the full-spec Bookreader issue queue. After each issue: tests, mockup check, smoke, GitLab MR, pipeline, review, and bug issues at the front of the queue. Use when running the execution loop from GitLab or day 05/pool-full-spec.md.
---

You run **one** Bookreader issue at a time. Do not ask the user anything.

Canon: `docs/spec/library-and-reader.md` §9 and §9.1. Mockups: `docs/design/screens/`. Log: `ai-challenge-advanced/day 05/run-4.md`.

## Tracker

- Prefer GitLab project `dbondarev/bookreader`, label `full-spec`, state opened, **lowest iid first**. If several are open, pick bugs (`type::bug`) before features.
- If GitLab MCP returns 401: read `GITLAB_TOKEN` from workspace file `gitlab.key` (`GITLAB_TOKEN=...`). Call `https://git.modumuptools.com/api/v4`. **Never print or commit the token.**
- Fallback mirror: `ai-challenge-advanced/day 05/pool-full-spec.md` (first `status: open`; bugs first).

## Do

1. Read the issue. Profile from labels: `bug-fix`, `feature-implementer`, `research`, `review`.
2. Follow that profile, `CLAUDE.md`, and the named mockup PNG if the issue has one.
3. Research/review-only issues: no product edits; write the reply into `ai-challenge-advanced/day 05/` and a GitLab note.
4. **Code issues**
   - Implement only this issue. Add or extend `node:test` for the new behavior.
   - UI that names a screen: the page must match that PNG (layout, not leftover `<ul>` of links). Save `qa/screenshots/issue-{iid}.png` at 1440 px (ReaderPhone: 390 px).
   - User-visible UI: `.cursor/skills/update-smoke/SKILL.md`. Else `.cursor/agents/qa-runner.md`. Do not skip smoke because unit tests passed.
   - Branch `issue/{iid}-{slug}` from current `main`. Commit. Push. Open a merge request to `main`. Description: what changed, tests, smoke, screenshot path, mockup path.
   - Wait for the GitLab pipeline on that MR (job runs `scripts/check.sh`). If it fails: fix on the same branch, push, wait again. Do not merge red.
   - Run profile `review` on the changed files. Also look for bugs vs the spec section and mockup named in the issue.
   - For each **Critical** or real functional bug: create a GitLab issue labeled `full-spec` `type::bug` `profile::bug-fix`, pointing at this MR. Put it in the pool as `status: open` **above** remaining features (next to pick). Should-fix → same, but do not block merge.
   - Merge the MR only if pipeline is green. Critical bugs: fix them next (same or new branch) before starting another feature.
5. Close the GitLab issue (and pool row) only when pipeline is green and Done checkboxes match.
6. Append a row to `ai-challenge-advanced/day 05/run-4.md`: iid, title, branch, MR url, pipeline status, smoke, mockup screenshot, review Critical count, new bug iids, result.
7. Take the next open issue. Stop on the first failure you cannot fix in this pass.

## Do not

- Skip check.sh, smoke, MR, or pipeline on a code issue.
- Close a UI issue whose page is still the old list if the mockup is a grid/sidebar.
- Print tokens. Commit `gitlab.key`. Add sign-in, fb2, or mobi.
- Implement the whole spec in one issue.
