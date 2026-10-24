To add a search filter to the GET /books endpoint, you can modify the listBooks function in the api.ts file to include a query parameter for the search string. You can then use this search string to filter the books by title or author.

Here's how you can modify the listBooks function:

```typescript
export async function listBooks(search?: string): Promise<Book[]> {
  let url = "/books";
  if (search) {
    url += `?q=${encodeURIComponent(search)}`;
  }
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error("Failed to list books");
  }
  return (await response.json()) as Book[];
}
```

In this updated function, the search parameter is optional. If it's provided, the function appends a query string to the URL that includes the search string.

Next, you need to modify the server-side library.ts file to include the search filter. You can use the JavaScript Array.prototype.filter method to filter the books by title or author. Here's how you can modify the list method:

```typescript
list(): Book[] {
  return this.store.db
    .select()
    .from(books)
    .all()
    .filter((row) => {
      const title = row.title.toLowerCase();
      const authors = (JSON.parse(row.authors) as string[]).map(author => author.toLowerCase());
      const search = (this.search || '').toLowerCase();
      return title.includes(search) || authors.some(author => author.includes(search));
    })
    .map((row) => ({
      id: row.id,
      title: row.title,
      authors: JSON.parse(row.authors) as string[],
      createdAt: row.createdAt,
    }));
}
```

In this updated method, the filter function checks if the title or any author of a book includes the search string. The filter function is case-insensitive because it converts both the title and authors to lower case before checking for the search string.

Finally, you need to update the LibraryPage component in the web/src/pages/LibraryPage.tsx file to include a search field. Here's how you can modify the component:

```jsx
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

  // ...

  return (
    <main>
      <h1>Library</h1>
      <label htmlFor="library-file">Add EPUB</label>
      <input
        id="library-file"
        type="file"
        accept=".epub,applicationapplication/epub+zip