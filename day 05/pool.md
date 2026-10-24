# Day 5 issue pool

Tracker: GitLab `dbondarev/bookreader`, label `day-5`. Issues #1–#18 exist and are closed. This file is the mirror.

Status: `open` | `closed` | `failed`
GitLab iid: filled if create_issue succeeds.

No commits. Spec: `bookreader/docs/spec/library-and-reader.md`. Design: `bookreader/docs/design/README.md`.

## 1. README links to spec and mockups
- labels: `day-5` `type::docs` `profile::feature-implementer`
- status: closed
- gitlab: #1 https://git.modumuptools.com/dbondarev/bookreader/-/work_items/1

Add links in `bookreader/README.md` to `docs/spec/library-and-reader.md` and `docs/design/README.md`.

Done:
- [ ] README names the spec and the design folder
- [ ] `scripts/check.sh` still green

Do not implement API or UI in this issue.

## 2. Research schema_version migration
- labels: `day-5` `type::research` `profile::research`
- status: closed
- gitlab: #2 https://git.modumuptools.com/dbondarev/bookreader/-/work_items/2

How should `schema_version` migration work in this repo given spec 4.3 and the current `db/client.ts`?

Done:
- [ ] Reply in research shape (Files / Links / Answer / Absent)
- [ ] No product files edited

## 3. GET /books ignores q
- labels: `day-5` `type::bug` `profile::bug-fix`
- status: closed
- gitlab: #3 https://git.modumuptools.com/dbondarev/bookreader/-/work_items/3

Spec §2 and CLAUDE.md: `q` on `GET /books` matches title or any author after JSON.parse, case-insensitive, in memory. No LIKE on the authors JSON column.

Done:
- [ ] `GET /books?q=` filters
- [ ] No `LIKE` / `ilike` / `orWhere` on authors JSON
- [ ] `scripts/check.sh` green

## 4. LibraryPage missing search field
- labels: `day-5` `type::bug` `profile::bug-fix`
- status: closed
- gitlab: #4 https://git.modumuptools.com/dbondarev/bookreader/-/work_items/4

Visible `<label>` on the search field, not only a placeholder. Query goes to `GET /books` via `api.ts`.

Done:
- [ ] Search input with visible label
- [ ] `listBooks` passes `q`
- [ ] `scripts/check.sh` green

## 5. Test q matches author not only title
- labels: `day-5` `type::test` `profile::feature-implementer`
- status: closed
- gitlab: #5 https://git.modumuptools.com/dbondarev/bookreader/-/work_items/5

Done:
- [ ] `node:test` + Fastify inject: two books, `q` hits author of one
- [ ] Existing tests kept
- [ ] `scripts/check.sh` green

## 6. Parse publication year from dc:date
- labels: `day-5` `type::feature` `profile::feature-implementer`
- status: closed
- gitlab: #6 https://git.modumuptools.com/dbondarev/bookreader/-/work_items/6

Spec §3: first four digits, `number | null`. Store on the book. Fixture with a date.

Done:
- [ ] Year extracted in `epub.ts`
- [ ] Returned on the book from the API
- [ ] Test for a dated EPUB
- [ ] `scripts/check.sh` green

Do not add authors/series tables.

## 7. Parse language from dc:language
- labels: `day-5` `type::feature` `profile::feature-implementer`
- status: closed
- gitlab: #7 https://git.modumuptools.com/dbondarev/bookreader/-/work_items/7

Primary subtag lowercase: `ru-RU` → `ru`. Missing → null.

Done:
- [ ] Language extracted in `epub.ts`
- [ ] Returned on the book
- [ ] Test
- [ ] `scripts/check.sh` green

## 8. Cover from EPUB and GET /books/:id/cover
- labels: `day-5` `type::feature` `profile::feature-implementer`
- status: closed
- gitlab: #8 https://git.modumuptools.com/dbondarev/bookreader/-/work_items/8

Spec §3 cover rules. jpeg/png/webp/gif. Missing cover → 404, UI uses fallback later.

Done:
- [ ] Cover bytes saved when present
- [ ] `GET /books/:id/cover` returns the image or 404
- [ ] Test both cases
- [ ] `scripts/check.sh` green

## 9. Fixture EPUB without date, cover, or series still uploads
- labels: `day-5` `type::test` `profile::feature-implementer`
- status: closed
- gitlab: #9 https://git.modumuptools.com/dbondarev/bookreader/-/work_items/9

Done:
- [ ] Test uses a minimal EPUB (current `makeEpub` is enough)
- [ ] POST /books is 201
- [ ] `scripts/check.sh` green

## 10. Document year, language, cover in CLAUDE.md
- labels: `day-5` `type::docs` `profile::feature-implementer`
- status: closed
- gitlab: #10 https://git.modumuptools.com/dbondarev/bookreader/-/work_items/10

Spec §11 item 2, only these fields. Repeat hard parts in `.cursorrules` if they exist.

Done:
- [ ] CLAUDE.md mentions year, language, cover
- [ ] `scripts/check.sh` green

## 11. CSS tokens from spec 8.13
- labels: `day-5` `type::refactor` `profile::feature-implementer`
- status: closed
- gitlab: #11 https://git.modumuptools.com/dbondarev/bookreader/-/work_items/11

`--bg #F4F4F1`, `--accent #2F4F8F`, surface, text. Apply to `body` / library.

Done:
- [ ] Tokens exist in web CSS
- [ ] Library uses them
- [ ] `scripts/check.sh` green

## 12. AppHeader with collection / authors / series stubs
- labels: `day-5` `type::feature` `profile::feature-implementer`
- status: closed
- gitlab: #12 https://git.modumuptools.com/dbondarev/bookreader/-/work_items/12

Routes `/`, `/authors`, `/series`. Stub pages for the last two. Russian labels.

Done:
- [ ] Header links work
- [ ] Stub pages render a heading
- [ ] `scripts/check.sh` green

## 13. BookCover 2:3 with fallback card
- labels: `day-5` `type::feature` `profile::feature-implementer`
- status: closed
- gitlab: #13 https://git.modumuptools.com/dbondarev/bookreader/-/work_items/13

Design README: grey card when no cover. `object-fit: cover`, radius 4px.

Done:
- [ ] `BookCover` component
- [ ] Used on LibraryPage
- [ ] `scripts/check.sh` green

## 14. StatusBadge tokens
- labels: `day-5` `type::feature` `profile::feature-implementer`
- status: closed
- gitlab: #14 https://git.modumuptools.com/dbondarev/bookreader/-/work_items/14

Макет `docs/design/screens/BookStates.png`. Читаю / Прочитана / Не начата / Брошена.

Done:
- [ ] `StatusBadge` exists
- [ ] Colors match spec 8.13 status tokens
- [ ] Shown on a library card (Не начата is enough if no status API yet)
- [ ] `scripts/check.sh` green

## 15. YearLabel изд. YYYY
- labels: `day-5` `type::feature` `profile::feature-implementer`
- status: closed
- gitlab: #15 https://git.modumuptools.com/dbondarev/bookreader/-/work_items/15

Spec 5.7 / 8.3. Only publication year → «изд. YYYY».

Done:
- [ ] `YearLabel` component
- [ ] Library card shows it when year is present
- [ ] `scripts/check.sh` green

## 16. Library UI in Russian and smoke.md
- labels: `day-5` `type::bug` `profile::bug-fix`
- status: closed
- gitlab: #16 https://git.modumuptools.com/dbondarev/bookreader/-/work_items/16

Spec §1: UI language is Russian. Heading Коллекция, Delete Удалить, Add EPUB. Update `qa/smoke.md`.

Done:
- [ ] Visible library strings are Russian
- [ ] smoke.md matches
- [ ] `scripts/check.sh` green

## 17. q matches title and authors in memory
- labels: `day-5` `type::refactor` `profile::feature-implementer`
- status: closed
- gitlab: #17 https://git.modumuptools.com/dbondarev/bookreader/-/work_items/17

Authors column is still JSON. Filter after parse, case-insensitive, no LIKE. Spec §11.1 without aliases.

Done:
- [ ] Filter is in-memory on parsed authors
- [ ] No SQL LIKE
- [ ] `scripts/check.sh` green

## 18. Review LibraryPage and api.ts
- labels: `day-5` `type::review` `profile::review`
- status: closed
- gitlab: #18 https://git.modumuptools.com/dbondarev/bookreader/-/work_items/18

Review those two files against CLAUDE.md. Comment only.

Done:
- [ ] Reply in review shape
- [ ] Files not edited
