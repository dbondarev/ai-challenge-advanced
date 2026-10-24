import fs from "node:fs/promises";
import path from "node:path";
import { randomUUID } from "node:crypto";
import { eq, like, or } from "drizzle-orm";
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
    const query = q?.trim() ?? "";
    const rows = query
      ? this.store.db
          .select()
          .from(books)
          .where(or(like(books.title, `%${query}%`), like(books.authors, `%${query}%`)))
          .all()
      : this.store.db.select().from(books).all();
    return rows.map((row) => ({
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

  private filePath(id: string): string {
    const row = this.store.db.select().from(books).where(eq(books.id, id)).get();
    if (!row) {
      throw new BookNotFoundError();
    }
    return row.filePath;
  }
}
