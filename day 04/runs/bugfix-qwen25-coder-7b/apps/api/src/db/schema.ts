import { integer, real, sqliteTable, text } from "drizzle-orm/sqlite-core";

export const books = sqliteTable("books", {
  id: text("id").primaryKey(),
  title: text("title").notNull(),
  authors: text("authors").notNull(),
  filePath: text("file_path").notNull(),
  spine: text("spine").notNull(),
  createdAt: integer("created_at").notNull(),
});

export const progress = sqliteTable("progress", {
  bookId: text("book_id")
    .primaryKey()
    .references(() => books.id),
  spineIndex: integer("spine_index").notNull(),
  scrollRatio: real("scroll_ratio").notNull(),
  updatedAt: integer("updated_at").notNull(),
});
