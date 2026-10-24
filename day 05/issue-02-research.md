```
Files:
- bookreader/docs/spec/library-and-reader.md — spec 4.3: CREATE/ALTER in db/client.ts, migrate() by meta.schema_version
- bookreader/apps/api/src/db/client.ts — today only CREATE TABLE books + progress; no meta table, no ALTER, no schema_version
- bookreader/apps/api/src/db/schema.ts — Drizzle shape; must stay in sync with client.ts SQL
- bookreader/apps/api/src/library.ts — mutations; spec wants Library.migrate() here via Drizzle at startup
- bookreader/apps/api/src/server.ts — opens DB and Library; the place to call migrate() once

Links:
- server.ts ? openDatabase (client.ts) ? Library
- spec 4.3 ? client.ts (DDL) + Library.migrate() (data)
- books.authors JSON today ? authors / author_aliases / book_authors after version bump

Answer:
schema_version should live in a `meta` table (key/value) created in `db/client.ts` next to the other CREATE TABLE statements. `openDatabase` runs idempotent DDL: CREATE IF NOT EXISTS plus ALTER ADD COLUMN guarded by PRAGMA table_info. After that, `Library.migrate()` reads meta.schema_version and applies numbered steps with Drizzle: reparse EPUBs into new columns, split authors JSON into author tables, then rebuild books without the authors column. Each step bumps schema_version. Missing files must not crash the server.

Absent:
- meta table
- schema_version
- Library.migrate()
- authors / series tables
```
