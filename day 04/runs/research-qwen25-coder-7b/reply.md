Files:
- `apps/api/src/app.ts` - Defines the Fastify routes for the API, including endpoints for listing, adding, retrieving, updating, and deleting books, as well as saving reading progress.
- `apps/api/src/library.ts` - Contains the `Library` class, which handles the business logic for interacting with the database and file system, including adding, retrieving, and deleting books, as well as saving reading progress.
- `apps/api/src/server.ts` - Sets up the Fastify server and connects it to the database.
- `packages/shared/src/index.ts` - Defines the types used throughout the project, including `Book`, `BookDetail`, `ReadingProgress`, and `Chapter`.

Answer:
Authorization is not set up in this project. All endpoints are accessible without any authentication or authorization checks. The boundary with the library is defined by the `Library` class, which handles the business logic for interacting with the database and file system. The `Library` class is used by the Fastify routes defined in `app.ts` to perform operations on the books and reading progress.

Absent:
- Authentication or authorization checks in the API routes.