Critical:
- apps/web/src/pages/ReaderPage.tsx:23 — no `any` — `saved` is typed as `any`
- apps/web/src/pages/ReaderPage.tsx:23 — progress per `bookId` — reads `localStorage.progress`, one global slot for all books
- apps/web/src/pages/ReaderPage.tsx:24 — no `console.log` — debug log in the resume effect
- apps/web/src/pages/ReaderPage.tsx:45 — progress per `bookId` — writes `localStorage.progress` without `bookId`

Should fix:
- none

Notes:
- Page fetches through `api.ts`; no EPUB parse and no SQL.
- Resume still applies server progress; the localStorage value is only logged.
