Files:
- CLAUDE.md — v1 has no sign-in; one local user; Microsoft 365/MSAL banned
- .cursor/rules/architecture.mdc — No auth in v1; server owns books and progress
- apps/api/src/app.ts — HTTP routes; no auth plugin; calls Library
- apps/api/src/library.ts — mutations; no user/identity
- apps/api/src/db/schema.ts — books + progress keyed by bookId; no users table
- packages/shared/src/index.ts — no User type
- apps/web/src/api.ts — fetch to /books with no tokens

Links:
- LibraryPage / ReaderPage ? api.ts ? app.ts ? Library ? SQLite and EPUB files
- ReadingProgress ? bookId only (not a user id)

Answer:
Authorization is not set up. v1 is a single local user. Routes accept every request with no login, session, or token. The boundary is the HTTP layer: `buildApp` calls `Library`; Library owns books and progress and does not know who the caller is. Progress is per bookId. Native clients later use this same API.

Absent:
- Auth (sign-in, sessions, tokens, user ids)
- Microsoft 365 / MSAL
- Native iOS/iPad/Windows apps
- fb2/mobi parsers
