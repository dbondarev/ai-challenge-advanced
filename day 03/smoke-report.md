# Smoke report

Base URL: http://localhost:5173
Fixture: bookreader/apps/api/test/fixtures/pride.epub
Playwright MCP. One screenshot per step in screenshots/.

## 1. Empty library — pass

Opened /. Heading Library. List had no items.
Screenshot: screenshots/01-empty-library.png

## 2. Upload EPUB — pass

Add EPUB + pride.epub. List showed Pride and Prejudice and Jane Austen. Delete was visible.
Screenshot: screenshots/02-upload-epub.png

## 3. Open reader — pass

Clicked the book. Heading Pride and Prejudice. Article showed Chapter one. Back to Library link present.
Screenshot: screenshots/03-open-reader.png

## 4. Delete book — pass

Back to library. Clicked Delete. Pride and Prejudice gone. List empty.
Screenshot: screenshots/04-delete-book.png

## Failures

None. A leftover console error from the first navigation happened while the API was still starting (Vite proxy ECONNREFUSED). Later steps used a live API.

## Where it would break

If upload failed, stop at scenario 2 (file input / POST /books). If the reader stayed blank, stop at scenario 3 (GET chapter). If Delete left the row, stop at scenario 4 (DELETE /books/:id or LibraryPage onDelete).
