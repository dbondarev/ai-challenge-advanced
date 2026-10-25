# Day 5 full-spec issue pool

Still day 5 of the challenge (second loop after TZ + mockups). First loop: `pool.md` (#1–#18).

Tracker: GitLab `dbondarev/bookreader`, label `full-spec`.
Process: spec §9.1. Log: `run-4.md`.
Bugs created by review go to the **front** of this queue.

Status: `open` | `closed` | `failed`

## 1. Stage 1: schema_version migration and new book columns
- labels: `full-spec stage::1 type::feature profile::feature-implementer`
- status: closed
- gitlab: #19 https://git.modumuptools.com/dbondarev/bookreader/-/work_items/19
- mr: https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/1

Spec §4.3 and §4.1. Add schema_version. Extend books for published year, language, cover bytes/path, hasCover, reading status fields needed by §5.5. Do not drop EPUB files.

Done:
- [x] Migration runs on existing DB
- [x] Tests for migrate-from-empty and migrate-from-v1
- [x] scripts/check.sh green

## 2. Stage 1: parse publication year from dc:date
- labels: `full-spec stage::1 type::feature profile::feature-implementer`
- status: closed
- gitlab: #20 https://git.modumuptools.com/dbondarev/bookreader/-/work_items/20
- mr: https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/2

Spec §3: first four digits, number | null. Store on the book. Fixture with a date.

Done:
- [x] Year extracted in epub.ts
- [x] Returned on the book from the API
- [x] Test for a dated EPUB
- [x] scripts/check.sh green
Do not add authors/series tables in this issue.

## 3. Stage 1: parse language from dc:language
- labels: `full-spec stage::1 type::feature profile::feature-implementer`
- status: closed
- gitlab: #21 https://git.modumuptools.com/dbondarev/bookreader/-/work_items/21
- mr: https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/3

Primary subtag lowercase: ru-RU → ru. Missing → null.

Done:
- [x] Language extracted in epub.ts
- [x] Returned on the book
- [x] Test
- [x] scripts/check.sh green

## 4. Stage 1: cover from EPUB and GET /books/:id/cover
- labels: `full-spec stage::1 type::feature profile::feature-implementer`
- status: closed
- gitlab: #22 https://git.modumuptools.com/dbondarev/bookreader/-/work_items/22
- mr: https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/4

Spec §3 cover rules. jpeg/png/webp/gif. Missing cover → 404.

Done:
- [x] Cover bytes saved when present
- [x] GET /books/:id/cover returns the image or 404
- [x] Test both cases
- [x] scripts/check.sh green

## 5. Stage 1: automatic and manual reading status
- labels: `full-spec stage::1 type::feature profile::feature-implementer`
- status: closed
- gitlab: #23 https://git.modumuptools.com/dbondarev/bookreader/-/work_items/23
- mockup: `docs/design/screens/BookStates.png`
- mr: https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/5

Spec §5.5. unread / reading / done / dropped. Manual flags. PATCH /books/:id from tests only in this issue.

Done:
- [x] Status derived from progress unless manual
- [x] Tests for done at end, dropped hidden from continue-reading later
- [x] scripts/check.sh green

## 6. Stage 1: CLAUDE.md year language cover status
- labels: `full-spec stage::1 type::docs profile::feature-implementer`
- status: closed
- gitlab: #24 https://git.modumuptools.com/dbondarev/bookreader/-/work_items/24
- mr: https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/6

Spec §11 items that apply now (year, language, cover, status). Repeat hard parts in .cursorrules and .cursor/rules.

Done:
- [x] CLAUDE.md mentions the new fields
- [x] scripts/check.sh green

## 7. Stage 2: CSS tokens and fonts from spec 8.13
- labels: `full-spec stage::2 type::feature profile::feature-implementer`
- status: closed
- gitlab: #25 https://git.modumuptools.com/dbondarev/bookreader/-/work_items/25
- mockup: `docs/design/screens/Main.png`
- mr: https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/7

--bg #F4F4F1, --accent #2F4F8F, surface, text, radii. Onest + Literata via @fontsource locally.

Done:
- [x] Tokens in web CSS
- [x] Fonts load
- [x] scripts/check.sh green

## 8. Stage 2: AppHeader matches Main.png chrome
- labels: `full-spec stage::2 type::feature profile::feature-implementer`
- status: closed
- gitlab: #26 https://git.modumuptools.com/dbondarev/bookreader/-/work_items/26
- mockup: `docs/design/screens/Main.png`
- mr: https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/8

Spec §8.4. Logo → /. Sections Книги, Серии, Авторы with aria-current. Button Загрузить EPUB on all three. Search in header on collection: «Поиск по названию или автору».

Done:
- [x] Header layout matches Main.png chrome (not three plain text links only)
- [x] Screenshot qa/screenshots/issue-header.png at 1440px
- [x] Smoke updated
- [x] scripts/check.sh green

## 9. Stage 2: BookCover 2:3 with fallback card
- labels: `full-spec stage::2 type::feature profile::feature-implementer`
- status: closed
- gitlab: #27 https://git.modumuptools.com/dbondarev/bookreader/-/work_items/27
- mockup: `docs/design/screens/Main.png`
- mr: https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/9

Spec §8.2. img when hasCover. Else grey card #ECEBE5, blue bar, title, author caps.

Done:
- [x] BookCover component
- [x] Fallback looks like Main.png grey cards
- [x] scripts/check.sh green

## 10. Stage 2: StatusBadge YearLabel ProgressBar BookMenu
- labels: `full-spec stage::2 type::feature profile::feature-implementer`
- status: closed
- gitlab: #28 https://git.modumuptools.com/dbondarev/bookreader/-/work_items/28
- mockup: `docs/design/screens/BookStates.png`
- mr: https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/10

Spec §8.3 and BookStates.png. Status colors 8.13. YearLabel изд. YYYY. ProgressBar. BookMenu ⋯ with delete for now; other items can stub.

Done:
- [x] Four components exist
- [x] Screenshot vs BookStates.png
- [x] scripts/check.sh green

## 11. Stage 2: stub routes authors series suggestions
- labels: `full-spec stage::2 type::feature profile::feature-implementer`
- status: closed
- gitlab: #29 https://git.modumuptools.com/dbondarev/bookreader/-/work_items/29
- mockup: `docs/design/screens/Main.png`
- mr: https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/11

Routes /authors /series /suggestions with heading stubs so header links work. Russian labels from 8.4.

Done:
- [x] Stub pages render a heading
- [x] Header navigates
- [x] Smoke for header
- [x] scripts/check.sh green

## 12. Stage 3: GET /books filters sort query string
- labels: `full-spec stage::3 type::feature profile::feature-implementer`
- status: closed
- gitlab: #30 https://git.modumuptools.com/dbondarev/bookreader/-/work_items/30
- mr: https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/12

Spec §8.1 and §7. q, status, language, author, sort. In-memory after parse. No LIKE on JSON authors. No ilike/orWhere.

Done:
- [x] Query params documented in tests
- [x] scripts/check.sh green

## 13. Stage 3: GET /books/facets
- labels: `full-spec stage::3 type::feature profile::feature-implementer`
- status: closed
- gitlab: #31 https://git.modumuptools.com/dbondarev/bookreader/-/work_items/31
- mr: https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/13

Spec §8.5 filters left column. Counts for status, language, top authors.

Done:
- [x] Facets endpoint + tests
- [x] scripts/check.sh green

## 14. Stage 3: LibraryPage matches Main.png
- labels: `full-spec stage::3 type::feature profile::feature-implementer`
- status: closed
- gitlab: #32 https://git.modumuptools.com/dbondarev/bookreader/-/work_items/32
- mockup: `docs/design/screens/Main.png`
- mr: https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/14

Spec §8.5 ENTIRE collection screen. Sidebar filters, drag-and-drop upload + progress list, Continue reading, grid of covers, sort, grid/table toggle. Russian UI.

Closing this issue while LibraryPage is still a vertical ul of links + badge is a FAIL even if components exist.

Done:
- [x] Layout matches Main.png at 1440px
- [x] qa/screenshots/issue-library.png
- [x] update-smoke for collection flows
- [x] scripts/check.sh green

## 15. Stage 4: authors API
- labels: `full-spec stage::4 type::feature profile::feature-implementer`
- status: closed
- gitlab: #33 https://git.modumuptools.com/dbondarev/bookreader/-/work_items/33
- mr: https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/15

Spec §5.2 §7.3. Normalize authors from EPUB. GET /authors, GET /authors/:id.

Done:
- [x] Authors persisted
- [x] Tests
- [x] scripts/check.sh green

## 16. Stage 4: series API
- labels: `full-spec stage::4 type::feature profile::feature-implementer`
- status: closed
- gitlab: #34 https://git.modumuptools.com/dbondarev/bookreader/-/work_items/34
- mr: https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/16

Spec §5.4 §7.4. GET /series, GET /series/:id, series=none.

Done:
- [x] Series persisted from OPF when present
- [x] Tests
- [x] scripts/check.sh green

## 17. Stage 4: AuthorsPage matches Authors.png
- labels: `full-spec stage::4 type::feature profile::feature-implementer`
- status: closed
- gitlab: #35 https://git.modumuptools.com/dbondarev/bookreader/-/work_items/35
- mockup: `docs/design/screens/Authors.png`
- mr: https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/17

Spec §8.7. Letter index, cards with cover stacks, counts. Not a heading stub.

Done:
- [x] Layout matches Authors.png at 1440px
- [x] Screenshot
- [x] Smoke
- [x] scripts/check.sh green

## 18. Stage 4: AuthorPage matches Author.png
- labels: `full-spec stage::4 type::feature profile::feature-implementer`
- status: closed
- gitlab: #36 https://git.modumuptools.com/dbondarev/bookreader/-/work_items/36
- mockup: `docs/design/screens/Author.png`
- mr: https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/18

Spec §8.8. Books by series + outside series. Missing books dashed.

Done:
- [x] Layout matches Author.png
- [x] Screenshot
- [x] Smoke
- [x] scripts/check.sh green

## 19. Stage 4: SeriesPage matches Series.png
- labels: `full-spec stage::4 type::feature profile::feature-implementer`
- status: closed
- gitlab: #37 https://git.modumuptools.com/dbondarev/bookreader/-/work_items/37
- mockup: `docs/design/screens/Series.png`
- mr: https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/19

Spec §8.9. Series cards, progress, missing count chip.

Done:
- [x] Layout matches Series.png
- [x] Screenshot
- [x] Smoke
- [x] scripts/check.sh green

## 20. Stage 5: ReaderPage matches Reader.png
- labels: `full-spec stage::5 type::feature profile::feature-implementer`
- status: closed
- gitlab: #38 https://git.modumuptools.com/dbondarev/bookreader/-/work_items/38
- mockup: `docs/design/screens/Reader.png`
- mr: https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/20

Spec §8.11 without notes. TOC, chapter HTML, progress bar, next/prev. Desktop 1440px.

Done:
- [x] Layout matches Reader.png
- [x] Progress still per bookId
- [x] Screenshot + smoke
- [x] scripts/check.sh green

## 21. Stage 5: ReaderPhone layout ReaderPhone.png
- labels: `full-spec stage::5 type::feature profile::feature-implementer`
- status: closed
- gitlab: #39 https://git.modumuptools.com/dbondarev/bookreader/-/work_items/39
- mockup: `docs/design/screens/ReaderPhone.png`
- mr: https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/21

Spec §8.11 narrow < 900 and phone 390px. Bottom bar, sheets for TOC.

Done:
- [x] Screenshot at 390px matches ReaderPhone.png
- [x] Smoke
- [x] scripts/check.sh green

## 22. Stage 6: annotations API and reader notes panel
- labels: `full-spec stage::6 type::feature profile::feature-implementer`
- status: closed
- gitlab: #40 https://git.modumuptools.com/dbondarev/bookreader/-/work_items/40
- mockup: `docs/design/screens/Reader.png`
- mr: https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/22

Spec §4.4 §8.11 notes. CRUD, highlights, right panel.

Done:
- [x] API tests
- [x] Notes panel on reader
- [x] Smoke
- [x] scripts/check.sh green

## 23. Stage 7: EditBookDialog matches EditBook.png
- labels: `full-spec stage::7 type::feature profile::feature-implementer`
- status: closed
- gitlab: #41 https://git.modumuptools.com/dbondarev/bookreader/-/work_items/41
- mockup: `docs/design/screens/EditBook.png`
- mr: https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/23

Spec §8.6.

Done:
- [x] Dialog matches EditBook.png
- [x] PATCH from UI
- [x] Screenshot + smoke
- [x] scripts/check.sh green

## 24. Stage 7: merge authors matches AuthorsMerge and MergeAuthors
- labels: `full-spec stage::7 type::feature profile::feature-implementer`
- status: closed
- gitlab: #42 https://git.modumuptools.com/dbondarev/bookreader/-/work_items/42
- mockup: `docs/design/screens/AuthorsMerge.png`
- mr: https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/24

Spec §5.3 §8.7. AuthorsMerge.png + MergeAuthors.png.

Done:
- [x] Duplicate hint + merge dialog
- [x] Screenshots
- [x] Tests + smoke
- [x] scripts/check.sh green

## 25. Stage 7: EditSeriesDialog matches EditSeries.png
- labels: `full-spec stage::7 type::feature profile::feature-implementer`
- status: closed
- gitlab: #43 https://git.modumuptools.com/dbondarev/bookreader/-/work_items/43
- mockup: `docs/design/screens/EditSeries.png`
- mr: https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/25

Spec §8.10. Order, missing books, totals.

Done:
- [x] Dialog matches EditSeries.png
- [x] Screenshot + tests + smoke
- [x] scripts/check.sh green

## 26. Stage 8: enrich hosts and SuggestionsPage matches Suggestions.png
- labels: `full-spec stage::8 type::feature profile::feature-implementer`
- status: closed
- gitlab: #44 https://git.modumuptools.com/dbondarev/bookreader/-/work_items/44
- mockup: `docs/design/screens/Suggestions.png`
- mr: https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/26

Spec §6 §8.12 and §11 item 3. hosts.ts allowlist. Suggestions.png.

Done:
- [x] CLAUDE.md host allowlist
- [x] Page matches Suggestions.png
- [x] Offline message when sources fail
- [x] Screenshot + smoke
- [x] scripts/check.sh green

## 27. Final review LibraryPage and api.ts vs Main.png
- labels: `full-spec stage::3 type::review profile::review`
- status: closed
- gitlab: #45 https://git.modumuptools.com/dbondarev/bookreader/-/work_items/45
- mockup: `docs/design/screens/Main.png`

Review LibraryPage, AppHeader, api.ts against CLAUDE.md and Main.png. Comment only.

Done:
- [x] Reply in review shape
- [x] Files not edited
