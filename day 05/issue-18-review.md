```
Critical:
- none

Should fix:
- LibraryPage.tsx:58 — StatusBadge is hardcoded `unread` until a status field exists on GET /books
- api.ts — fetch error messages are English while the UI is Russian (not a CLAUDE.md ban)

Notes:
- LibraryPage loads books through api.ts listBooks(q); no EPUB parse, no SQLite, no any, no console.log
- Search field has a visible label htmlFor="library-search"
- q is sent to GET /books, not filtered only in React
```
