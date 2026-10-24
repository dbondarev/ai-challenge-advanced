import type { Book, BookDetail, Chapter, ReadingProgress } from "@bookreader/shared";

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

export async function deleteBook(id: string): Promise<void> {
  const response = await fetch(`/books/${id}`, { method: "DELETE" });
  if (!response.ok) {
    throw new Error("Failed to delete book");
  }
}

export async function uploadBook(file: File): Promise<Book> {
  const body = new FormData();
  body.append("file", file);
  const response = await fetch("/books", { method: "POST", body });
  if (!response.ok) {
    throw new Error("Failed to upload book");
  }
  return (await response.json()) as Book;
}

export async function getBook(id: string): Promise<BookDetail> {
  const response = await fetch(`/books/${id}`);
  if (!response.ok) {
    throw new Error("Failed to load book");
  }
  return (await response.json()) as BookDetail;
}

export async function getChapter(id: string, index: number): Promise<Chapter> {
  const response = await fetch(`/books/${id}/chapters/${index}`);
  if (!response.ok) {
    throw new Error("Failed to load chapter");
  }
  return (await response.json()) as Chapter;
}

export async function getProgress(id: string): Promise<ReadingProgress> {
  const response = await fetch(`/books/${id}/progress`);
  if (!response.ok) {
    throw new Error("Failed to load progress");
  }
  return (await response.json()) as ReadingProgress;
}

export async function saveProgress(
  id: string,
  spineIndex: number,
  scrollRatio: number,
): Promise<ReadingProgress> {
  const response = await fetch(`/books/${id}/progress`, {
    method: "PUT",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ spineIndex, scrollRatio }),
  });
  if (!response.ok) {
    throw new Error("Failed to save progress");
  }
  return (await response.json()) as ReadingProgress;
}
