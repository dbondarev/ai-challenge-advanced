---
name: add-library-feature
description: Adds a Bookreader API method, query, page, or test using the project file shape. Use when editing the library list, reader, EPUB upload, or reading progress.
---

# Add a library feature

Read `CLAUDE.md` first. Change only what the task names.

## File shape

API: Fastify route delegates to `Library`. Tests use `node:test`, `assert`, and `app.inject`.

```ts
test("GET /books filters by author", async () => {
  const list = await app.inject({ method: "GET", url: "/books?q=Austen" });
  assert.equal(list.statusCode, 200);
});
```

Web: `LibraryPage` / `ReaderPage` call helpers in `api.ts`. A search field sends `q` to `GET /books`.

Do not edit `scripts/check.sh`. Do not parse EPUB in the page.
