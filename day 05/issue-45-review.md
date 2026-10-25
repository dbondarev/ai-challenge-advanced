# #45 review — LibraryPage, AppHeader, api.ts vs Main.png

```
Critical:
- none

Should fix:
- apps/web/src/AppHeader.tsx:20 — listSuggestions() has no catch; a down API rejects unhandled on every page.
- apps/web/src/pages/LibraryPage.tsx:91 — facets reload only when books.length changes, so metadata-only edits can leave sidebar counts stale until a book is added/removed.
- apps/web/src/pages/LibraryPage.tsx:99 — continue-reading uses GET /books?status=reading&sort=opened (good) but does not hide on language/author query filters, only q and status (spec 8.5 item 2).
- CLAUDE.md still documents `q` as JSON.parse authors; listBooks already sends q to GET /books (aliases live on the API).

Notes:
- LibraryPage is the Main.png collection: sidebar, dropzone+upload list, continue row, cover grid/table toggle — not a leftover ul of links.
- Filters/search/sort live in the query string; listBooks/getFacets go through api.ts. No EPUB parse, any, console.log, or raw SQL in these files.
- AppHeader: logo → /, Книги/Серии/Авторы with aria-current via NavLink, labelled search, Загрузить EPUB multiple accept=.epub. Pending «Уточнения (N)» when suggestions exist.
- Progress is book.percent from the API (per bookId).
```
