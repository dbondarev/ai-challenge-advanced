To implement the `private filePath(id: string): string` method in the `Library` class, we need to ensure that the method correctly retrieves the file path of a book from the database and throws a `BookNotFoundError` if the book is not found. Here's the updated `Library` class with the `filePath` method:

### apps/api/src/library.ts
```typescript
import { eq, sql } from "drizzle-orm";
import { books } from "./db/schema";
import { BookNotFoundError } from "./errors.js";
import { BookStore } from "./store.js";

export class Library {
  private store: BookStore;

  constructor(store: BookStore) {
    this.store = store;
  }

  public async list(): Promise<Book[]> {
    const rows = this.store.db.select().from(books).getAll();
    return rows.map((row) => ({
      id: row.id,
      title: row.title,
      authors: row.authors,
      filePath: row.filePath,
    }));
  }

  public async addEpub(epub: Uint8Array): Promise<Book> {
    const id = this.store.addEpub(epub);
    const row = this.store.db.select().from(books).where(eq(books.id, id)).get();
    return {
      id: row.id,
      title: row.title,
      authors: row.authors,
      filePath: row.filePath,
    };
  }

  public async get(id: string): Promise<BookDetail> {
    const row = this.store.db.select().from(books).where(eq(books.id, id)).get();
    if (!row) {
      throw new BookNotFoundError();
    }
    return {
      id: row.id,
      title: row.title,
      authors: row.authors,
      filePath: row.filePath,
      chapters: await this.chapterList(id),
    };
  }

  public async chapter(id: string, index: number): Promise<Chapter> {
    const row = this.store.db.select().from(books).where(eq(books.id, id)).get();
    if (!row) {
      throw new BookNotFoundError();
    }
    const spine = await this.store.db.select().from(chapters).where(eq(chapters.bookId, id)).getAll();
    const chapter = spine[index];
    if (!chapter) {
      throw new ChapterNotFoundError();
    }
    return {
      id: chapter.id,
      title: chapter.title,
      content: await this.store.db.select().from(chapterContent).where(eq(chapterContent.chapterId, chapter.id)).get(),
    };
  }

  public async progressFor(id: string): Promise<ReadingProgress> {
    const row = this.store.db.select().from(books).where(eq(books.id, id)).get();
    if (!row) {
      throw new BookNotFoundError();
    }
    const progress = await this.store.db.select().from(progress).where(eq(progress.bookId, id)).get();
    return {
      spineIndex: progress.spineIndex ?? 0,
      scrollRatio: progress.scrollRatio ?? 0,
    };
  }

  public async saveProgress(id: string, spineIndex: number, scrollRatio: number): Promise<ReadingProgress> {
    const row = this.store.db.select().from(books).where(eq(books.id, id)).get();
    if (!row) {
      throw new BookNotFoundError();
    }
    await this.store.db.insert(progress).values({ bookId: id, spineIndex, scrollRatio }).onConflictDoUpdate();
    return await this.progressFor(id);
  }

  public async remove(id: string): Promise<void> {
    const row = this.store.db.select().from(books).where(eq(books.id, id)).get();
    if (!row) {
      throw new BookNotFoundError();
    }
    await this.store.db.delete(books).where(eq(books.id, id));
    await this.store.removeEpub(id);
  }

  private async chapterList(id: string): Promise<Chapter[]> {
    const spine = await this.store.db.select().from(chapters).where(eq(chapters.bookId, id)).getAll();
    return spine.map((chapter) => ({
      id: chapter.id,
      title: chapter.title,
    }));
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

### Explanation
1. **Method Definition**: The `filePath` method is defined as a private method within the `Library` class.
2. **Database Query**: The method queries the database to find the book with the given `id`.
3. **Error Handling**: If the book is not found, it throws a `BookNotFoundError`.
4. **Return Path**: If the book is found, it returns the `filePath` associated with the book.

This method ensures that the file path of a book can be retrieved safely and correctly, throwing an error if the book does not exist in the database.