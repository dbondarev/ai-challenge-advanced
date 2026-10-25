# Bookreader

Personal EPUB library. Web + Node API now. Native iOS, iPad, and Windows later use the same API. Sync is the server: books and reading progress live there.

v1 has no sign-in. One local user. fb2 and mobi are future formats. Do not parse them yet.

## Global vs local

Global, already set outside this repo: reply language, git safety, no secrets, no commits unless asked.

Local: stack, folders, names, and the bans below. Source of truth is this file. `.cursorrules`, `.github/copilot-instructions.md`, and `.cursor/rules/` repeat the hard parts.

## Stack

- npm workspaces: `apps/api`, `apps/web`, `packages/shared`
- API: Fastify, Drizzle, SQLite. EPUB files in `data/books/`
- Web: React, Vite, React Router. `LibraryPage` and `ReaderPage`
- Shared types: `Book`, `BookDetail`, `ReadingProgress`, `Chapter`, `ReadingStatus`, `Author*`, `Series*`, `Annotation`, `Suggestion`
- Book fields now: `publishedYear`, `language`, `hasCover`, `status`, `statusIsManual`
- Progress is per book: `bookId + spineIndex + scrollRatio`
- Delete: `DELETE /books/:id` removes the row, progress, EPUB file, and cover file. Missing id throws `BookNotFoundError`.
- Data directory: `BOOKREADER_DATA` or `apps/api/data`. Covers in `data/covers/`.
- Verify with `scripts/check.sh` (`tsc`, API tests, ESLint)

## Layout

```
packages/shared/src/     Book, ReadingProgress
apps/api/src/library.ts  mutations
apps/api/src/epub.ts     OPF parse only
apps/api/src/app.ts      HTTP
apps/api/src/sources/    Wikidata and Open Library (hosts.ts allowlist)
apps/web/src/pages/      LibraryPage, ReaderPage, SuggestionsPage
apps/api/test/           node:test
```

One exported component or class per file. Pages end in `Page`. API errors are classes (`BookNotFoundError`).

## Patterns

- Views fetch through `apps/web/src/api.ts`. They do not unzip EPUB or open SQLite.
- Library mutations go through `Library`. Missing ids throw `BookNotFoundError`.
- List filters belong on `GET /books`, not only in the React list.
- `q` matches title or any author after `JSON.parse`. Compare case-insensitively in memory. Do not `LIKE` the authors JSON column.
- The search field on `LibraryPage` has a visible `<label>`, not only a placeholder.
- Progress is keyed by `bookId`. Never one global row or `localStorage` key for all books.
- Year from `dc:date`: first four digits, `number | null`.
- Language from `dc:language`: primary subtag lowercase (`ru-RU` → `ru`). Missing → `null`.
- Cover: only jpeg/png/webp/gif. Saved under `data/covers/<bookId>.<ext>`. `GET /books/:id/cover` returns the image or 404.
- Status is `new | reading | done | dropped`. Derived from progress unless `status_manual`. Last spine item at `scrollRatio >= 0.98` → `done` unless dropped. `PATCH /books/:id` `{ status }` from tests only.
- Feature code uses Drizzle. Do not add raw SQL in routes or pages. Schema bootstrap in `db/client.ts` is the exception.
- A feature does not edit `scripts/check.sh`.

## Good code

Types (`packages/shared/src/index.ts`):

```ts
export type ReadingProgress = {
  bookId: string;
  spineIndex: number;
  scrollRatio: number;
  updatedAt: number;
};
```

Throw on a missing book (`library.ts`):

```ts
const row = this.store.db.select().from(books).where(eq(books.id, id)).get();
if (!row) {
  throw new BookNotFoundError();
}
```

Library card shows title and authors (`LibraryPage.tsx`):

```tsx
<Link to={`/books/${book.id}`}>
  {book.title}
  {book.authors.length > 0 ? ` — ${book.authors.join(", ")}` : ""}
</Link>
```

Upload stays in the API helper (`api.ts`):

```ts
export async function uploadBook(file: File): Promise<Book> {
  const body = new FormData();
  body.append("file", file);
  const response = await fetch("/books", { method: "POST", body });
  return (await response.json()) as Book;
}
```

Tests use `node:test` and Fastify `inject` (`library.test.ts`):

```ts
test("POST /books extracts title and author and lists the book", async () => {
  const response = await app.inject({ method: "POST", url: "/books", ... });
  assert.equal(response.statusCode, 201);
});
```

## Banned

- `any` and `console.log` in `apps/` and `packages/`.
- Raw SQL in `Library`, routes, or React.
- Parsing EPUB inside a page. That stays in `epub.ts`.
- One progress slot for every book (`localStorage.progress`, a table without `bookId`).
- Microsoft 365, MSAL, or `fetch` to unknown hosts from the API. API may `fetch` only hosts listed in `apps/api/src/sources/hosts.ts` (Wikidata, Open Library). Any other host is banned.

## File shape

Imports, then the type or function, then export. No narration comments.

```ts
import { eq } from "drizzle-orm";
import { books } from "./db/schema.js";

export function get(id: string): BookDetail {
  const row = ...
  return { id: row.id, title: row.title, authors: ..., createdAt: row.createdAt, spine: ... };
}
```
