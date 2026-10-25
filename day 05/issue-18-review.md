Critical:
- none

Should fix:
- apps/web/src/pages/LibraryPage.tsx:20-22 — list filters belong on GET /books, not only in the React list — after upload, `setBooks((current) => [...current, book])` appends locally and skips `listBooks(q)`, so a book that does not match the current `q` still appears until the next search change.

Notes:
- LibraryPage fetches through `api.ts` (`listBooks`, `uploadBook`, `deleteBook`). No EPUB parse, no `any`, no `console.log`, no raw SQL.
- Search has a visible `<label htmlFor="library-search">` and `listBooks(q)` sends `q` to `GET /books`.
- api.ts uses relative `/books` URLs, encodes `q`, and maps progress by `bookId` in the path. `as Book[]` is a type assertion, not `any`.
- StatusBadge is hardcoded `unread` (no status API yet). That is outside CLAUDE.md bans.
