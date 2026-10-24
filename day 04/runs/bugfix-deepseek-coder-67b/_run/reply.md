The issue seems to be with the `saveProgress` method in the `Library` class. The method is overwriting the progress for the book every time it is called, instead of updating it. This is causing the first book to open at the start every time a second book is opened.

The `saveProgress` method in the `Library` class is defined as follows:

```typescript
saveProgress(id: string, spineIndex: number, scrollRatio: number): ReadingProgress {
  this.get(id);
  const updatedAt = Date.now();
  this.store.db.delete(progress).run();
  this.store.db.insert(progress).values({ bookId: id, spineIndex, scrollRatio, updatedAt }).run();
  return { bookId: id, spineIndex, scrollRatio, updatedAt };
}
```

The problem is that the `delete(progress).run()` line is deleting all progress records for the book every time the method is called, regardless of the `bookId`. This means that every time you save progress for a book, all previous progress for that book is deleted.

To fix this, you should modify the `saveProgress` method to only delete the progress record for the specific book. You can do this by changing the `delete(progress).run()` line to `delete(progress).where(eq(progress.bookId, id)).run()`. This will ensure that only the progress record for the specific book is deleted.

Here is the corrected `saveProgress` method:

```typescript
saveProgress(id: string, spineIndex: number, scrollRatio: number): ReadingProgress {
  this.get(id);
  const updatedAt = Date.now();
  this.store.db.delete(progress).where(eq(progress.bookId, id)).run();
  this.store.db.insert(progress).values({ bookId: id, spineIndex, scrollRatio, updatedAt }).run();
  return { bookId: id, spineIndex, scrollRatio, updatedAt };
}
```

With this change, the `saveProgress` method will now correctly update the progress record for the specific book without deleting all previous progress records for that book.
