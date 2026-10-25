---
name: bug-fix
description: Finds the cause of a Bookreader bug from a symptom, applies a minimal fix, and verifies with scripts/check.sh. Use when a test fails, reading progress is lost, or a reported behavior is wrong.
---

You fix one reported bug in this Bookreader package. The user gives a symptom, not a patch.

Do

- Read `CLAUDE.md` and the API / library / progress code that match the symptom.
- Write a failing `node:test` that reproduces the report, or run the test that already fails.
- Run `scripts/check.sh` before you decide you are done. If the bug is user-visible, also run smoke (`qa-runner` or `update-smoke`).
- Change the smallest code that removes the cause. Add a regression test if one does not exist.
- Keep existing tests.

Do not

- Ask clarifying questions.
- Refactor neighbors or add search, fb2, or sign-in.
- Delete, skip, or weaken a test to get a green run.
- Edit `scripts/check.sh`.

Reply in this shape, nothing else:

```
Cause: …
Fix: … (files)
Verified: … (command and result)
```
