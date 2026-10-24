import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { Book } from "@bookreader/shared";
import { listBooks, uploadBook } from "../api.js";

export function LibraryPage() {
  const [books, setBooks] = useState<Book[]>([]);

  useEffect(() => {
    void listBooks().then(setBooks);
  }, []);

  async function onFile(file: File | undefined) {
    if (!file) {
      return;
    }
    const book = await uploadBook(file);
    setBooks((current) => [...current, book]);
  }

  return (
    <main>
      <h1>Library</h1>
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
