import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { after, before, test } from "node:test";
import { buildApp } from "../src/app.js";
import { openDatabase } from "../src/db/client.js";
import { Library } from "../src/library.js";
import { makeEpub } from "./epub-fixture.js";

const root = fs.mkdtempSync(path.join(os.tmpdir(), "bookreader-"));
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

test("POST /books extracts title and author and lists the book", async () => {
  const epub = await makeEpub("Pride and Prejudice", "Jane Austen");
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
  const created = response.json() as { id: string; title: string; authors: string[] };
  assert.equal(created.title, "Pride and Prejudice");
  assert.deepEqual(created.authors, ["Jane Austen"]);

  const list = await app.inject({ method: "GET", url: "/books" });
  assert.equal(list.statusCode, 200);
  const books = list.json() as { id: string }[];
  assert.equal(books.map((book) => book.id).includes(created.id), true);
});

async function postBook(title: string, author: string) {
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

test("PUT /books/:id/progress keeps a separate place for each book", async () => {
  const first = await postBook("First Book", "Author A");
  const second = await postBook("Second Book", "Author B");

  const saveFirst = await app.inject({
    method: "PUT",
    url: `/books/${first.id}/progress`,
    payload: { spineIndex: 0, scrollRatio: 0.4 },
  });
  assert.equal(saveFirst.statusCode, 200);

  const saveSecond = await app.inject({
    method: "PUT",
    url: `/books/${second.id}/progress`,
    payload: { spineIndex: 0, scrollRatio: 0.8 },
  });
  assert.equal(saveSecond.statusCode, 200);

  const firstProgress = await app.inject({
    method: "GET",
    url: `/books/${first.id}/progress`,
  });
  assert.equal(firstProgress.statusCode, 200);
  const firstBody = firstProgress.json() as {
    bookId: string;
    spineIndex: number;
    scrollRatio: number;
  };
  assert.equal(firstBody.bookId, first.id);
  assert.equal(firstBody.spineIndex, 0);
  assert.equal(firstBody.scrollRatio, 0.4);

  const secondProgress = await app.inject({
    method: "GET",
    url: `/books/${second.id}/progress`,
  });
  assert.equal(secondProgress.statusCode, 200);
  const secondBody = secondProgress.json() as {
    bookId: string;
    spineIndex: number;
    scrollRatio: number;
  };
  assert.equal(secondBody.bookId, second.id);
  assert.equal(secondBody.spineIndex, 0);
  assert.equal(secondBody.scrollRatio, 0.8);
});
