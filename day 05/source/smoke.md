# Smoke scenarios

No sign-in. Create = upload EPUB. Fixture: `apps/api/test/fixtures/pride.epub`.

Base URL: `http://127.0.0.1:5173`

## 1. Empty library

Open `/`. The header shows Bookreader, Книги (current), Серии, Авторы, search labelled «Поиск по названию или автору», and Загрузить EPUB. The page has a left status sidebar, a drag-and-drop EPUB zone («Перетащите EPUB сюда»), and «Добавьте первую книгу». There is no leftover vertical list of text links. The page background is the cream token `#F4F4F1`.

## 2. Upload EPUB

Choose the fixture on Загрузить EPUB or the drop zone. After it lands, the cover grid shows Pride and Prejudice (Jane Austen) on a 2:3 BookCover.

## 3. Open reader

Click the book. Chapter text is visible. A «‹ Библиотека» control is visible, with TOC and next/prev chapter chrome.

## 4. Delete book

Go back to the library. Open ⋯ Меню книги, click Удалить…, confirm the dialog. The book is gone from the grid.

## 5. Header chrome

On `/`, Книги has aria-current. The search field has a visible label, not only a placeholder.

## 6. Card chrome

After upload, the card shows StatusBadge «Не начата» and a ⋯ BookMenu. If the file has only a publication year, YearLabel shows «изд. YYYY».

## 7. Header sections

Click Серии: heading «Серии», header still visible, Серии has aria-current. Click Авторы: heading «Авторы». Click Книги: back to the library.

## 8. Collection chrome

On `/` with a book, the layout has a status sidebar, an upload drop zone, a «Все книги» heading with a sort control and grid/table toggle. Hover a card to reveal ⋯. Switch to Таблица: a table with the book row is visible. Switch back to Сетка.

## 9. Authors index

After a book is in the library, open `/authors`. The page is not a stub heading: it has «Авторы», a letter index, search labelled «Поиск автора», sort «По фамилии, А–Я», and an author card (surname first, cover stack). Clicking the card opens `/authors/:id`.


## 10. Author detail

After a book is in the library, open `/authors` and click the author card. The page is not a stub heading: breadcrumbs «Авторы / …», initials, name, counts, По сериям / Все книги, and books (series and/or «Вне серий»). Unknown `/authors/00000000-0000-4000-8000-000000000000` shows «Автор не найден».


## 11. Series index

Open `/series`. The page is not a stub heading: «Серии», search labelled «Поиск серии или автора», chips, and «Книги вне серий». After a series EPUB is in the library, a series card with covers is visible.


## 12. Reader chrome

Open a book. Desktop reader matches Reader.png chrome without the notes column: top bar «Библиотека», TOC, title, progress bar, chapter HTML, footer prev/next. Progress is still per book.


## 13. Reader phone

Resize to 390px and open a book. Top bar is compact (back chevron, title, Aa). Bottom dock shows «Позиция в книге», a slider, and Оглавление. Opening Оглавление shows a sheet, not a leftover desktop sidebar of text links.


## 14. Reader notes

Open a book at 1440px. The right column is «Заметки». Select chapter text: toolbar «Выделить» / «Заметка» / «Копировать». Выделить keeps a highlight in the panel. The page is not a leftover list of links.


## 15. Edit book

On the library with a book, open ⋯ Меню книги → «Изменить данные…». The dialog is «Данные книги» with title, authors, series, years, language — not a leftover list. Cancel or Save closes it.


## 16. Merge authors

On `/authors`, if duplicate candidates exist, the block «Возможно, это один автор» is visible with «Объединить…». The merge dialog is «Объединить авторов», not a leftover list. Button «Объединить авторов» enters selection mode.


## 17. Edit series

Open `/series` with a series EPUB in the library. Open ⋯ Меню серии → «Изменить серию…». The dialog is «Серия» with name, total books, status segmented control, reading order, and «Книга, которой нет в библиотеке» — not a leftover list. Cancel or Save closes it.


## 18. Suggestions

Open `/suggestions`. The page is «Уточнения», not a leftover heading stub. Button «Уточнить всю библиотеку» runs enrich. If sources fail, «Базы недоступны, попробуйте позже» is visible. Empty copy is «Уточнений нет…» when there are no pending rows.
