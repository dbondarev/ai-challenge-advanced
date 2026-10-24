import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { Book } from "@bookreader/shared";
import { listBooks, uploadBook } from "../api.js";

export function LibraryPage() {
  const [books, setBooks] = useState<Book[]>([]);
  const [query, setQuery] = useState("");

  useEffect(() => {
    void listBooks(query).then(setBooks);
  }, [query]);

  async function onFile(file: File | undefined) {
    if (!file) {
      return;
    }
    await uploadBook(file);
    setBooks(await listBooks(query));
  }

  return (
    <main>
      <h1>Library</h1>
      <input
        type="search"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="Search author or title"
      />
      <input
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
          </li>
        ))}
      </ul>
    </main>
  );
}
