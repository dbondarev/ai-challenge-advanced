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

test("GET /books filters by search string", async () => {
  const epub1 = await makeEpub("Pride and Prejudice", "Jane Austen");
  const epub2 = await makeEpub("To Kill a Mockingbird", "Harper Lee");
  await app.inject({
    method: "POST",
    url: "/books",
    headers: {
      "content-type": "multipart/form-data; boundary=bound",
    },
    payload: Buffer.concat([
      Buffer.from(
        "--bound\r\nContent-Disposition: form-data; name=\"file\"; filename=\"book1.epub\"\r\nContent-Type: application/epub+zip\r\n\r\n",
      ),
      epub1,
      Buffer.from("\r\n--bound--\r\n"),
    ]),
  });
  await app.inject({
    method: "POST",
    url: "/books",
    headers: {
      "content-type": "multipart/form-data; boundary=bound",
    },
    payload: Buffer.concat([
      Buffer.from(
        "--bound\r\nContent-Disposition: form-data; name=\"file\"; filename=\"book2.epub\"\r\nContent-Type: application/epub+zip\r\n\r\n",
      ),
      epub2,
      Buffer.from("\r\n--bound--\r\n"),
    ]),
  });

  const list1 = await app.inject({ method: "GET", url: "/books?q=Austen" });
  assert.equal(list1.statusCode, 200);
  const books1 = list1.json() as { id: string }[];
  assert.equal(books1.map((book) => book.id).includes(created.id), true);

  const list2 = await app.inject({ method: "GET", url: "/books?q=Mockingbird" });
  assert.equal(list2.statusCode, 200);
  const books2 = list2.json() as { id: string }[];
  assert.equal(books2.map((book) => book.id).includes(epub2.id), true);
});
