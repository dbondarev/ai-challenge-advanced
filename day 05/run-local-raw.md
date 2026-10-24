# Local qwen2.5-coder:7b

## Issue 1 (4513 ms)

# Bookreader

Personal EPUB library and a simple reader.

## Documentation

- [Library and Reader](docs/spec/library-and-reader.md)
- [Design](docs/design/README.md)
```

### END

## Issue 3 (25662 ms)

### apps/api/src/library.ts
```
import fs from "node:fs/promises";
import path from "node:path";
import { randomUUID } from "node:crypto";
import { eq } from "drizzle-orm";
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
    let coverPath: string | null = null;
    await fs.mkdir(this.filesRoot, { recursive: true });
    await fs.writeFile(filePath, bytes);
    if (parsed.cover) {
      const coversRoot = path.join(path.dirname(this.filesRoot), "covers");
      await fs.mkdir(coversRoot, { recursive: true });
      coverPath = path.join(coversRoot, `${id}.${parsed.cover.ext}`);
      await fs.writeFile(coverPath, parsed.cover.bytes);
    }
    const createdAt = Date.now();
    this.store.db.insert(books).values({
      id,
      title: parsed.title,
      authors: JSON.stringify(parsed.authors),
      filePath,
      coverPath,
      spine: JSON.stringify(parsed.spine),
      publishedYear: parsed.publishedYear,
      language: parsed.language,
      createdAt,
    }).run();
    return this.toBook({
      id,
      title: parsed.title,
      authors: JSON.stringify(parsed.authors),
      coverPath,
      publishedYear: parsed.publishedYear,
      language: parsed.language,
      createdAt,
    });
  }

  list(q?: string): Book[] {
    const rows = this.store.db
      .select()
      .from(books)
      .all()
      .map((row) => this.toBook(row));
    if (!q) {
      return rows;
    }
    const needle = q.toLowerCase();
    return rows.filter(
      (book) =>
        book.title.toLowerCase().includes(needle) ||
        book.authors.some((author) => author.toLowerCase().includes(needle)),
    );
  }

  get(id: string): BookDetail {
    const row = this.store.db.select().from(books).where(eq(books.id, id)).get();
    if (!row) {
      throw new BookNotFoundError();
    }
    return {
      ...this.toBook(row),
      spine: JSON.parse(row.spine) as string[],
    };
  }

  private toBook(row: { [key: string]: any }): Book {
    return {
      id: row.id,
      title: row.title,
      authors: JSON.parse(row.authors) as string[],
      coverPath: row.coverPath,
      publishedYear: row.publishedYear,
      language: row.language,
      createdAt: row.createdAt,
    };
  }
}
```

### apps/api/src/app.ts
```
import cors from "@fastify/cors";
import multipart from "@fastify/multipart";
import Fastify, { type FastifyInstance } from "fastify";
import { BookNotFoundError, Library } from "./library.js";

export async function buildApp(library: Library): Promise<FastifyInstance> {
  const app = Fastify();
  await app.register(cors);
  await app.register(multipart);

  app.get("/books", async (request, reply) => {
    const q = request.query.q as string | undefined;
    const books = await library.list(q);
    return reply.code(200).send(books);
  });

  app.post("/books", async (request, reply) => {
    const file = await request.file();
    if (!file) {
      return reply.code(400).send({ error: "file required" });
    }
    const bytes = await file.toBuffer();
    const book = await library.addEpub(bytes);
    return reply.code(201).send(book);
  });

  app.get("/books/:id/cover", async (request, reply) => {
    const { id } = request.params as { id: string };
    const coverPath = path.join(library.filesRoot, "covers", `${id}.jpg`);
    try {
      await fs.access(coverPath);
      reply.code(200).type("image/jpeg").send(await fs.readFile(coverPath));
    } catch {
      reply.code(404).send({ error: "Cover not found" });
    }
  });

  app.delete("/books/:id", async (request, reply) => {
    const { id } = request.params as { id: string };
    try {
      const book = await library.get(id);
      await fs.unlink(book.filePath);
      if (book.coverPath) {
        await fs.unlink(book.coverPath);
      }
      await library.store.db.delete(books).where(eq(books.id, id)).run();
      await library.store.db.delete(progress).where(eq(progress.bookId, id)).run();
      reply.code(204).send();
    } catch (error) {
      if (error instanceof BookNotFoundError) {
        reply.code(404).send({ error: "Book not found" });
      } else {
        reply.code(500).send({ error: "Internal server error" });
      }
    }
  });

  return app;
}
```

### apps/web/src/api.ts
```
import { type Book, type BookDetail, type Chapter, type ReadingProgress } from "@bookreader/shared";
import { buildApp } from "../apps/api/src/app.js";

export async function listBooks(q?: string): Promise<Book[]> {
  const app = await buildApp();
  const response = await app.inject({ method: "GET", url: "/books", query: { q } });
  if (response.statusCode !== 200) {
    throw new Error(`Failed to list books: ${response.statusCode} ${response.statusMessage}`);
  }
  return response.json() as Book[];
}

export async function addBook(file: File): Promise<Book> {
  const app = await buildApp();
  const formData = new FormData();
  formData.append("file", file);
  const response = await app.inject({ method: "POST", url: "/books", body: formData });
  if (response.statusCode !== 201) {
    throw new Error(`Failed to add book: ${response.statusCode} ${response.statusMessage}`);
  }
  return response.json() as Book;
}

export async function getBookCover(id: string): Promise<Blob | null> {
  const app = await buildApp();
  const response = await app.inject({ method: "GET", url: `/books/${id}/cover` });
  if (response.statusCode === 404) {
    return null;
  }
  if (response.statusCode !== 200) {
    throw new Error(`Failed to get book cover: ${response.statusCode} ${response.statusMessage}`);
  }
  return response.body;
}

export async function deleteBook(id: string): Promise<void> {
  const app = await buildApp();
  const response = await app.inject({ method: "DELETE", url: `/books/${id}` });
  if (response.statusCode !== 204) {
    throw new Error(`Failed to delete book: ${response.statusCode} ${response.statusMessage}`);
  }
}
```

### apps/web/src/pages/LibraryPage.tsx
```
import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listBooks, deleteBook } from "../api.ts";
import { Book } from "@bookreader/shared";
import { AppHeader } from "../components/AppHeader";
import { StatusBadge } from "../components/StatusBadge";
import { YearLabel } from "../components/YearLabel";

export const LibraryPage: React.FC = () => {
  const [books, setBooks] = useState<Book[]>([]);

  useEffect(() => {
    const fetchBooks = async () => {
      try {
        const fetchedBooks = await listBooks();
        setBooks(fetchedBooks);
      } catch (error) {
        console.error("Failed to fetch books:", error);
      }
    };

    fetchBooks();
  }, []);

  const handleDelete = async (id: string) => {
    try {
      await deleteBook(id);
      setBooks(books.filter((book) => book.id !== id));
    } catch (error) {
      console.error("Failed to delete book:", error);
    }
  };

  return (
    <div>
      <AppHeader />
      <h1>Library</h1>
      <ul>
        {books.map((book) => (
          <li key={book.id}>
            <Link to={`/books/${book.id}`}>
              {book.title}
              {book.authors.length > 0 ? ` — ${book.authors.join(", ")}` : ""}
            </Link>
            <StatusBadge status={book.status} />
            <YearLabel year={book.publishedYear} />
            <button onClick={() => handleDelete(book.id)}>Delete</button>
          </li>
        ))}
      </ul>
    </div>
  );
};
```

### apps/web/src/pages/ReaderPage.tsx
```
import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getBookCover, getBookDetail } from "../api.ts";
import { Book, Chapter } from "@bookreader/shared";
import
