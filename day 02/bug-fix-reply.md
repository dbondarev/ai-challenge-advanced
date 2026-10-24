Cause: `saveProgress` deleted the entire `progress` table before inserting the new row, so saving a second book’s place erased the first book’s position.

Fix: delete only the row for that `bookId` in `apps/api/src/library.ts`. Added regression test in `apps/api/test/library.test.ts`.

Verified: `zsh scripts/check.sh` — typecheck, 2 tests pass, lint (exit 0).

Files changed:
- `apps/api/src/library.ts`
- `apps/api/test/library.test.ts`
