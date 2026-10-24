# Smoke scenarios

No sign-in. Create = upload EPUB. Fixture: `apps/api/test/fixtures/pride.epub`.

Base URL: `http://127.0.0.1:5173`

## 1. Empty library

Open `/`. The heading is Library. The list has no books.

## 2. Upload EPUB

Choose the fixture on the Add EPUB control. The list shows Pride and Prejudice and Jane Austen.

## 3. Open reader

Click the book. Chapter text is visible. A Back to Library link is visible.

## 4. Delete book

Go back to the library. Click Delete. The book is gone from the list.
