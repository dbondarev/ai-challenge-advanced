### apps/api/src/library.ts
```
import fs from "node:fs/promises";
import path from "node:path";
import { randomUUID } from "node:crypto";
import { eq, ilike } from "drizzle-orm";
import type { Book, BookDetail, Chapter, ReadingProgress } from "@bookreader/shared";
import type { DatabaseClient } from "./db/client.js";
import { books, progress } from "./db/schema.js";
import { parseEpub, readChapter } from "./epub.js";

export class BookNotFoundError extends Error {
  constructor() {
    super("Book not found");
    this.name = "BookNotFoundError";
  }
}

export class Library {
  constructor(
    private readonly store: DatabaseClient,
    private readonly filesRoot: string,
  ) {}

  async addEpub(bytes: Buffer): Promise<Book> {
    const parsed = await parseEpub(bytes);
    const id = randomUUID();
    const filePath = path.join(this.filesRoot, `${id}.epub`);
    await fs.mkdir(this.filesRoot, { recursive: true });
    await fs.writeFile(filePath, bytes);
    const createdAt = Date.now();
    this.store.db.insert(books).values({
      id,
      title: parsed.title,
      authors: JSON.stringify(parsed.authors),
      filePath,
      spine: JSON.stringify(parsed.spine),
      createdAt,
    }).run();
    return { id, title: parsed.title, authors: parsed.authors, createdAt };
  }

  list(q?: string): Book[] {
    const query = this.store.db.select().from(books);
    if (q) {
      query.where(ilike(books.title, `%${q}%`)).orWhere(ilike(books.authors, `%${q}%`));
    }
    return query.all().map((row) => ({
      id: row.id,
      title: row.title,
      authors: JSON.parse(row.authors) as string[],
      createdAt: row.createdAt,
    }));
  }

  get(id: string): BookDetail {
    const row = this.store.db.select().from(books).where(eq(books.id, id)).get();
    if (!row) {
      throw new BookNotFoundError();
    }
    return {
      id: row.id,
      title: row.title,
      authors: JSON.parse(row.authors) as string[],
      createdAt: row.createdAt,
      spine: JSON.parse(row.spine) as string[],
    };
  }

  async chapter(id: string, index: number): Promise<Chapter> {
    const book = this.get(id);
    const href = book.spine[index];
    if (!href) {
      throw new BookNotFoundError();
    }
    const bytes = await fs.readFile(this.filePath(id));
    const html = await readChapter(bytes, href);
    return { index, href, html };
  }

  progressFor(id: string): ReadingProgress {
    this.get(id);
    const row = this.store.db.select().from(progress).where(eq(progress.bookId, id)).get();
    return {
      bookId: id,
      spineIndex: row?.spineIndex ?? 0,
      scrollRatio: row?.scrollRatio ?? 0,
      updatedAt: row?.updatedAt ?? 0,
    };
  }

  saveProgress(id: string, spineIndex: number, scrollRatio: number): ReadingProgress {
    this.get(id);
    const updatedAt = Date.now();
    this.store.db
      .insert(progress)
      .values({ bookId: id, spineIndex, scrollRatio, updatedAt })
      .onConflictDoUpdate({
        target: progress.bookId,
        set: { spineIndex, scrollRatio, updatedAt },
      })
      .run();
    return { bookId: id, spineIndex, scrollRatio, updatedAt };
  }

  async remove(id: string): Promise<void> {
    const row = this.store.db.select().from(books).where(eq(books.id, id)).get();
    if (!row) {
      throw new BookNotFoundError();
    }
    this.store.db.delete(progress).where(eq(progress.bookId, id)).run();
    this.store.db.delete(books).where(eq(books.id, id)).run();
    await fs.unlink(row.filePath).catch(() => undefined);
  }

  private filePath(id: string): string {
    const row = this.store.db.select().from(books).where(eq(books.id, id)).get();
    if (!row) {
      throw new BookNotFoundError();
    }
    return row.filePath;
  }
}

```

### apps/web/src/pages/LibraryPage.tsx
```
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { Book } from "@bookreader/shared";
import { deleteBook, listBooks, uploadBook } from "../api.js";

export function LibraryPage() {
  const [books, setBooks] = useState<Book[]>([]);
  const [search, setSearch] = useState("");

  useEffect(() => {
    void listBooks(search).then(setBooks);
  }, [search]);

  async function onFile(file: File | undefined) {
    if (!file) {
      return;
    }
    const book = await uploadBook(file);
    setBooks((current) => [...current, book]);
  }

  async function onDelete(id: string) {
    await deleteBook(id);
    setBooks((current) => current.filter((book) => book.id !== id));
  }

  return (
    <main>
      <h1>Library</h1>
      <label htmlFor="library-search">Search</label>
      <input
        id="library-search"
        type="text"
        value={search}
        onChange={(event) => setSearch(event.target.value)}
      />
      <label htmlFor="library-file">Add EPUB</label>
      <input
        id="library-file"
        type="file"
        accept=".epub,application/epub+zip"
        onChange={(event) => void onFile(event.target.files?.[0])}
      />
      <ul>
        {books.map((book) => (
          <li key={book.id}>
            <Link to={`/books/${book.id}`}>
              {book.title}
              {book.authors.length > 0 ? ` — ${book.authors.join(", ")}` : ""}
            </Link>
            <button type="button" onClick={() => void onDelete(book.id)}>
              Delete
            </button>
          </li>
        ))}
      </ul>
    </main>
  );
}

```

### apps/api/test/library.test.ts
```
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

```