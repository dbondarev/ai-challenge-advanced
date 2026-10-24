import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { after, before, test } from "node:test";
import { buildApp } from "../src/app.js";
import { openDatabase } from "../src/db/client.js";
import { Library } from "../src/library.js";
import { makeEpub } from "./epub-fixture.js";

const root = fs.mkdtempSync(path.join(os.tmpdir(), "bookreader-http-"));
const store = openDatabase(root);
const library = new Library(store, path.join(root, "books"));
const app = await buildApp(library);

before(async () => {
  await app.ready();
});

after(async () => {
  await app.close();
  store.sqlite.close();
  fs.rmSync(root, { recursive: true, force: true });
});

async function postBook(title: string, author: string, body?: string): Promise<{ id: string }> {
  const epub = await makeEpub(title, author, body);
  const response = await app.inject({
    method: "POST",
    url: "/books",
    headers: {
      "content-type": "multipart/form-data; boundary=bound",
    },
    payload: Buffer.concat([
      Buffer.from(
        "--bound\r\nContent-Disposition: form-data; name=\"file\"; filename=\"book.epub\"\r\nContent-Type: application/epub+zip\r\n\r\n",
      ),
      epub,
      Buffer.from("\r\n--bound--\r\n"),
    ]),
  });
  assert.equal(response.statusCode, 201);
  return response.json() as { id: string };
}

test("GET /books/:id/chapters/:index returns the chapter HTML", async () => {
  const book = await postBook("Chapter Book", "Author", "Hello chapter");
  const response = await app.inject({ method: "GET", url: `/books/${book.id}/chapters/0` });
  assert.equal(response.statusCode, 200);
  const chapter = response.json() as { index: number; href: string; html: string };
  assert.equal(chapter.index, 0);
  assert.equal(chapter.href, "OEBPS/chapter1.xhtml");
  assert.equal(chapter.html.includes("Hello chapter"), true);
});

test("GET /books/:id and GET /books/:id/chapters/:index return 404 when missing", async () => {
  const missing = "00000000-0000-4000-8000-000000000000";
  const missingBook = await app.inject({ method: "GET", url: `/books/${missing}` });
  assert.equal(missingBook.statusCode, 404);
  assert.deepEqual(missingBook.json(), { error: "not found" });

  const missingChapterBook = await app.inject({
    method: "GET",
    url: `/books/${missing}/chapters/0`,
  });
  assert.equal(missingChapterBook.statusCode, 404);

  const book = await postBook("One Chapter", "Author");
  const missingIndex = await app.inject({
    method: "GET",
    url: `/books/${book.id}/chapters/9`,
  });
  assert.equal(missingIndex.statusCode, 404);
});

test("DELETE /books/:id removes the book, progress, and file", async () => {
  const book = await postBook("To Delete", "Author");
  await app.inject({
    method: "PUT",
    url: `/books/${book.id}/progress`,
    headers: { "content-type": "application/json" },
    payload: { spineIndex: 0, scrollRatio: 0.5 },
  });

  const removed = await app.inject({ method: "DELETE", url: `/books/${book.id}` });
  assert.equal(removed.statusCode, 204);

  const afterDelete = await app.inject({ method: "GET", url: `/books/${book.id}` });
  assert.equal(afterDelete.statusCode, 404);
  const progress = await app.inject({ method: "GET", url: `/books/${book.id}/progress` });
  assert.equal(progress.statusCode, 404);
  const chapter = await app.inject({ method: "GET", url: `/books/${book.id}/chapters/0` });
  assert.equal(chapter.statusCode, 404);

  const missingDelete = await app.inject({ method: "DELETE", url: `/books/${book.id}` });
  assert.equal(missingDelete.statusCode, 404);
});
