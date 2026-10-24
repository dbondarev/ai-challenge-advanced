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

test("GET /books filters by author or title", async () => {
  const epub = await makeEpub("Moby-Dick", "Herman Melville");
  const created = await app.inject({
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
  assert.equal(created.statusCode, 201);
  const book = created.json() as { id: string; title: string };

  const byAuthor = await app.inject({ method: "GET", url: "/books?q=Melville" });
  assert.equal(byAuthor.statusCode, 200);
  const authorMatches = byAuthor.json() as { id: string; title: string }[];
  assert.equal(authorMatches.length, 1);
  assert.equal(authorMatches[0]?.id, book.id);

  const byTitle = await app.inject({ method: "GET", url: "/books?q=Moby" });
  assert.equal(byTitle.statusCode, 200);
  const titleMatches = byTitle.json() as { id: string; title: string }[];
  assert.equal(titleMatches.length, 1);
  assert.equal(titleMatches[0]?.id, book.id);

  const none = await app.inject({ method: "GET", url: "/books?q=Austen" });
  assert.equal(none.statusCode, 200);
  const unmatched = none.json() as { id: string }[];
  assert.equal(unmatched.map((item) => item.id).includes(book.id), false);
});
