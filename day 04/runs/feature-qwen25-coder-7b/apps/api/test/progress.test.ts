import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { after, before, test } from "node:test";
import { buildApp } from "../src/app.js";
import { openDatabase } from "../src/db/client.js";
import { Library } from "../src/library.js";
import { makeEpub } from "./epub-fixture.js";

const root = fs.mkdtempSync(path.join(os.tmpdir(), "bookreader-progress-"));
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

async function postBook(title: string, author: string): Promise<{ id: string }> {
  const epub = await makeEpub(title, author);
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

test("GET /books/:id/progress returns zeros when nothing is saved", async () => {
  const book = await postBook("Untitled Progress", "Author");
  const response = await app.inject({ method: "GET", url: `/books/${book.id}/progress` });
  assert.equal(response.statusCode, 200);
  const progress = response.json() as {
    bookId: string;
    spineIndex: number;
    scrollRatio: number;
    updatedAt: number;
  };
  assert.equal(progress.bookId, book.id);
  assert.equal(progress.spineIndex, 0);
  assert.equal(progress.scrollRatio, 0);
  assert.equal(progress.updatedAt, 0);
});

test("PUT /books/:id/progress stores progress per bookId", async () => {
  const first = await postBook("Book One", "Author One");
  const second = await postBook("Book Two", "Author Two");

  const savedFirst = await app.inject({
    method: "PUT",
    url: `/books/${first.id}/progress`,
    headers: { "content-type": "application/json" },
    payload: { spineIndex: 0, scrollRatio: 0.25 },
  });
  assert.equal(savedFirst.statusCode, 200);
  const firstBody = savedFirst.json() as {
    bookId: string;
    spineIndex: number;
    scrollRatio: number;
    updatedAt: number;
  };
  assert.equal(firstBody.bookId, first.id);
  assert.equal(firstBody.spineIndex, 0);
  assert.equal(firstBody.scrollRatio, 0.25);
  assert.equal(firstBody.updatedAt > 0, true);

  const savedSecond = await app.inject({
    method: "PUT",
    url: `/books/${second.id}/progress`,
    headers: { "content-type": "application/json" },
    payload: { spineIndex: 0, scrollRatio: 0.9 },
  });
  assert.equal(savedSecond.statusCode, 200);

  const loadedFirst = await app.inject({ method: "GET", url: `/books/${first.id}/progress` });
  const loadedSecond = await app.inject({ method: "GET", url: `/books/${second.id}/progress` });
  assert.equal(loadedFirst.statusCode, 200);
  assert.equal(loadedSecond.statusCode, 200);
  assert.equal((loadedFirst.json() as { scrollRatio: number }).scrollRatio, 0.25);
  assert.equal((loadedSecond.json() as { scrollRatio: number }).scrollRatio, 0.9);
  assert.equal((loadedFirst.json() as { bookId: string }).bookId, first.id);
  assert.equal((loadedSecond.json() as { bookId: string }).bookId, second.id);
});

test("GET and PUT /books/:id/progress return 404 for a missing book", async () => {
  const missing = "00000000-0000-4000-8000-000000000000";
  const getMissing = await app.inject({ method: "GET", url: `/books/${missing}/progress` });
  assert.equal(getMissing.statusCode, 404);
  const putMissing = await app.inject({
    method: "PUT",
    url: `/books/${missing}/progress`,
    headers: { "content-type": "application/json" },
    payload: { spineIndex: 0, scrollRatio: 0.1 },
  });
  assert.equal(putMissing.statusCode, 404);
});
