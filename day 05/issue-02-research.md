```
Files:
- bookreader/docs/spec/library-and-reader.md — spec 4.3: DDL in db/client.ts; data move in Library.migrate() by meta.schema_version
- bookreader/apps/api/src/db/client.ts — today only CREATE TABLE books + progress; no meta table, no ALTER, no schema_version
- bookreader/apps/api/src/db/schema.ts — Drizzle books.authors JSON + progress; must stay in sync with client.ts SQL
- bookreader/apps/api/src/library.ts — mutations only; no migrate()
- bookreader/apps/api/src/server.ts — openDatabase then new Library; the call site for migrate() once at start
- bookreader/CLAUDE.md — schema bootstrap in db/client.ts is the raw-SQL exception; features use Drizzle

Links:
- server.ts ? openDatabase (client.ts DDL) ? Library ? Library.migrate() (Drizzle data)
- spec 4.3 ? client.ts (CREATE/ALTER + drop authors column via recreate) + Library.migrate() (reparse EPUB, split authors/series)
- books.authors JSON today ? authors / author_aliases / book_authors after a version bump

Answer:
Keep a `meta` table (key TEXT PK, value TEXT) created in `db/client.ts` next to the other CREATE TABLE IF NOT EXISTS statements. `openDatabase` stays the only raw-SQL place: CREATE IF NOT EXISTS, then ALTER TABLE ... ADD COLUMN only when PRAGMA table_info shows the column is missing. Update `db/schema.ts` in the same change.

After the DB is open, `server.ts` constructs `Library` and calls `Library.migrate()` once. `migrate()` reads `meta.schema_version` (treat missing as 0) and runs numbered, idempotent Drizzle steps:
1. Re-read each EPUB, fill new book columns, save cover; missing/unreadable files keep the row and do not crash the server.
2. Split `books.authors` JSON into `authors` / `author_aliases` / `book_authors`.
3. Split series from the file into `series` / `series_books`.
4. Drop `books.authors` by recreating the table in `client.ts` (SQLite cannot DROP COLUMN here per spec), then bump schema_version.

Do not run LIKE/ilike on the authors JSON column; author tables come later, after this migration. Do not add sign-in, fb2, or mobi.

Absent:
- meta table
- schema_version
- Library.migrate()
- authors / author_aliases / book_authors / series / series_books / field_sources tables
```
