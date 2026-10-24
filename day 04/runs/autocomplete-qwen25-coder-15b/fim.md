# FIM autocomplete qwen2.5-coder:1.5b (1374 ms)

## Prefix

```ts
  list(q?: string): Book[] {
    const rows = this.store.db
      .select()
      .from(books)
      .all()
      .map((row) => ({
        id: row.id,
        title: row.title,
        authors: JSON.parse(row.authors) as string[],
        createdAt: row.createdAt,
      }));
    if (!q) {
      return rows;
    }
    const needle = q.toLowerCase();
    return rows.filter(

```

## Suffix

```ts

    );
  }

```

## Completion

```ts
      (row) =>
        row.title.toLowerCase().includes(needle) ||
        row.authors.some((author) => author.toLowerCase().includes(needle))
```
