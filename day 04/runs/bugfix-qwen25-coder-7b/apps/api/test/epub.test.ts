import assert from "node:assert/strict";
import { test } from "node:test";
import { parseEpub, readChapter } from "../src/epub.js";
import { makeEpub } from "./epub-fixture.js";

test("parseEpub extracts title, author, and spine from OPF", async () => {
  const bytes = await makeEpub("Pride and Prejudice", "Jane Austen");
  const parsed = await parseEpub(bytes);
  assert.equal(parsed.title, "Pride and Prejudice");
  assert.deepEqual(parsed.authors, ["Jane Austen"]);
  assert.deepEqual(parsed.spine, ["OEBPS/chapter1.xhtml"]);
});

test("readChapter returns the chapter HTML for a spine href", async () => {
  const bytes = await makeEpub("Moby-Dick", "Herman Melville", "Call me Ishmael.");
  const html = await readChapter(bytes, "OEBPS/chapter1.xhtml");
  assert.equal(html.includes("Call me Ishmael."), true);
});

test("readChapter throws when the href is not in the EPUB", async () => {
  const bytes = await makeEpub("Emma", "Jane Austen");
  await assert.rejects(() => readChapter(bytes, "OEBPS/missing.xhtml"), /Missing chapter/);
});
