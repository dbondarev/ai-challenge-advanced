import path from "node:path";
import { fileURLToPath } from "node:url";
import { buildApp } from "./app.js";
import { openDatabase } from "./db/client.js";
import { Library } from "./library.js";

const root =
  process.env.BOOKREADER_DATA ??
  path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "data");
const store = openDatabase(root);
const library = new Library(store, path.join(root, "books"));
const app = await buildApp(library);
await app.listen({ port: 3333, host: "127.0.0.1" });
