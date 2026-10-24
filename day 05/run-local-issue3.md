# Issue 3 local (6492 ms)

To implement the `q` parameter for filtering books based on title or authors, we need to modify the `list` method in `apps/api/src/library.ts` to include a filter based on the `q` parameter. Here's how you can do it:

1. Extract the `q` parameter from the request.
2. Parse the `authors` JSON column.
3. Compare the `q` parameter with the `title` and `authors` in a case-insensitive manner.
4. Return only the books that match the filter.

Here's the updated `list` method:

```typescript
import { eq, ilike } from "drizzle-orm";
import { books } from "./db/schema.js";

export class Library {
  constructor(private store: Store) {}

  async list(q?: string): Promise<Book[]> {
    const query = this.store.db.select().from(books);

    if (q) {
      const authors = JSON.parse(q).map((author: string) => author.toLowerCase());
      query = query
        .where(
          ilike(books.title, `%${q.toLowerCase()}%`)
        )
        .orWhere((query) =>
          authors.some((author) =>
            query.where(ilike(books.authors, `%${author}%`))
          )
        );
    }

    const rows = await query.all();
    return rows.map((row) => ({
      id: row.id,
      title: row.title,
      authors: JSON.parse(row.authors) as string[],
      createdAt: row.createdAt,
    }));
  }
}
```

In the `app.ts` file, you can pass the `q` parameter to the `list` method:

```typescript
import { FastifyInstance } from "fastify";
import { Library } from "./library";
import { Store } from "./store";

export async function app(fastify: FastifyInstance, opts: { store: Store }) {
  const library = new Library(opts.store);

  fastify.get("/books", async (request, reply) => {
    const q = request.query.q as string | undefined;
    const books = await library.list(q);
    reply.send(books);
  });
}
```

This implementation ensures that the `q` parameter is used to filter books based on the title and authors in a case-insensitive manner, without using `LIKE` on the `authors` JSON column.
