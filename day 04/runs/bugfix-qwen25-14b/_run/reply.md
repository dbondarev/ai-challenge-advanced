Your implementation for saving and retrieving reading progress for books in the API is well-structured and follows good practices. However, there are a few areas where improvements can be made for better readability, maintainability, and robustness. Here are some suggestions:

### 1. **Refactor the `progressFor` Method**
The `progressFor` method can be simplified by using a single query to fetch the progress and book details. This reduces the number of database calls and improves performance.

```typescript
progressFor(id: string): ReadingProgress {
  const row = this.store.db
    .select({
      bookId: books.id,
      spineIndex: progress.spineIndex,
      scrollRatio: progress.scrollRatio,
      updatedAt: progress.updatedAt,
    })
    .from(progress)
    .innerJoin(books, eq(books.id, progress.bookId))
    .where(eq(books.id, id))
    .get();

  if (!row) {
    return {
      bookId: id,
      spineIndex: 0,
      scrollRatio: 0,
      updatedAt: 0,
    };
  }

  return row;
}
```

### 2. **Improve Error Handling in `saveProgress`**
The `saveProgress` method can be improved by handling the case where the book does not exist before attempting to save progress. This avoids unnecessary database operations and improves performance.

```typescript
saveProgress(id: string, spineIndex: number, scrollRatio: number): ReadingProgress {
  const book = this.get(id);
  if (!book) {
    throw new BookNotFoundError();
  }

  const updatedAt = Date.now();
  this.store.db.delete(progress).where(eq(progress.bookId, id)).run();
  this.store.db.insert(progress).values({ bookId: id, spineIndex, scrollRatio, updatedAt }).run();
  return { bookId: id, spineIndex, scrollRatio, updatedAt };
}
```

### 3. **Refactor the `remove` Method**
The `remove` method can be simplified by using a single transaction to delete the book and its progress. This ensures that the operation is atomic and reduces the risk of data inconsistencies.

```typescript
async remove(id: string): Promise<void> {
  const row = this.store.db.select().from(books).where(eq(books.id, id)).get();
  if (!row) {
    throw new BookNotFoundError();
  }

  await this.store.db.transaction(async (tx) => {
    tx.delete(progress).where(eq(progress.bookId, id)).run();
    tx.delete(books).where(eq(books.id, id)).run();
  });

  await fs.unlink(row.filePath).catch(() => undefined);
}
```

### 4. **Improve Test Coverage**
Ensure that your tests cover edge cases and handle unexpected scenarios. For example, you can add tests to check what happens when a book is deleted before its progress is saved.

### 5. **Improve API Documentation**
Add comments and documentation to your API methods to make it easier for other developers to understand the purpose and usage of each endpoint.

### 6. **Refactor the `Library` Class**
Consider breaking down the `Library` class into smaller, more focused classes or modules. This can improve readability and maintainability.

### 7. **Improve Error Handling in the API**
Ensure that your API endpoints handle errors gracefully and return appropriate HTTP status codes and error messages.

### 8. **Improve Test Fixture Setup**
Ensure that your test fixture setup is robust and handles cleanup properly to avoid leaving temporary files behind.

### 9. **Improve Code Readability**
Use consistent naming conventions and improve code readability by breaking down complex methods into smaller, more manageable functions.

### 10. **Improve Database Schema**
Consider adding indexes to the database schema to improve query performance, especially for frequently accessed columns like `bookId`.

By implementing these improvements, your code will be more robust, maintainable, and efficient.