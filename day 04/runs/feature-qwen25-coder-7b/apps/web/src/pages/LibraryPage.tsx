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
