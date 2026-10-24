import fs from "node:fs";
import path from "node:path";
import Database from "better-sqlite3";
import { drizzle } from "drizzle-orm/better-sqlite3";
import * as schema from "./schema.js";

export type DatabaseClient = ReturnType<typeof openDatabase>;

export function openDatabase(root: string): {
  db: ReturnType<typeof drizzle<typeof schema>>;
  sqlite: Database.Database;
} {
  fs.mkdirSync(root, { recursive: true });
  const sqlite = new Database(path.join(root, "library.sqlite"));
  sqlite.exec(`
    CREATE TABLE IF NOT EXISTS books (
      id TEXT PRIMARY KEY,
      title TEXT NOT NULL,
      authors TEXT NOT NULL,
      file_path TEXT NOT NULL,
      spine TEXT NOT NULL,
      created_at INTEGER NOT NULL
    );
    CREATE TABLE IF NOT EXISTS progress (
      book_id TEXT PRIMARY KEY REFERENCES books(id),
      spine_index INTEGER NOT NULL,
      scroll_ratio REAL NOT NULL,
      updated_at INTEGER NOT NULL
    );
  `);
  return { db: drizzle(sqlite, { schema }), sqlite };
}
