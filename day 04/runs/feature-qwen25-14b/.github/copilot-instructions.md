# Bookreader

Web + Node API EPUB library. Full rules: `CLAUDE.md`.

- Mutations go through `Library`. Missing ids throw `BookNotFoundError`.
- Pages use `api.ts`. No EPUB unzip and no SQLite in React.
- Progress is per `bookId` (`spineIndex`, `scrollRatio`).
- No `any`, no `console.log`, no raw SQL in features.
- List filters belong on `GET /books`. Match title or parsed authors, case-insensitive. Do not LIKE the authors JSON column.
- The library search field has a visible label.
- Do not edit `scripts/check.sh`.
- No sign-in in v1. fb2/mobi later. Native clients later use this API.
- Run `scripts/check.sh` after a change.
