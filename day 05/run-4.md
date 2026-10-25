# Run 4 — Day 5 full-spec loop

Tracker: GitLab label `full-spec` / `pool-full-spec.md`.
This is still **day 5** (execution loop), not a separate challenge day.
Product starts from pre-day-5 library (list + upload + delete + reader).

| iid | title | branch | MR | pipeline | smoke | mockup shot | review Critical | new bugs | result |
|---|---|---|---|---|---|---|---|---|---|
| 19 | Stage 1: schema_version migration and new book columns | `issue/19-schema-version-migration` | https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/1 | **success** 2410 (job 5498); 2409 failed on `#!/bin/zsh` | pass (empty, upload, reader, delete) | none (schema-only); smoke `bookreader/qa/screenshots/issue-19-*.png` | 0 | none | **merged** — !1 into main `8fb9a9d`; check.sh shebang → bash |
| 20 | Stage 1: parse publication year from dc:date | `issue/20-parse-publication-year` | https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/2 | **success** 2412 (job 5500) | pass (empty, upload, reader, delete) | none (API-only); smoke `bookreader/qa/screenshots/issue-20-*.png` | 0 | none | **merged** — !2 into main `6d3a047` |
| 21 | Stage 1: parse language from dc:language | `issue/21-parse-language` | https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/3 | **success** 2414 (job 5502) | pass (empty, upload, reader, delete) | none (API-only); smoke `bookreader/qa/screenshots/issue-21-*.png` | 0 | none | **merged** — !3 into main `3e43bdc` |
| 22 | Stage 1: cover from EPUB and GET /books/:id/cover | `issue/22-epub-cover` | https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/4 | **success** 2416 (job 5504) | pass (empty, upload, reader, delete) | none (API-only); smoke `bookreader/qa/screenshots/issue-22-*.png` | 0 | none | **merged** — !4 into main `b1f7468` |
| 23 | Stage 1: automatic and manual reading status | `issue/23-reading-status` | https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/5 | **success** 2418 (job 5506) | pass (empty, upload, reader, delete) | BookStates.png named; API-only this issue; smoke `bookreader/qa/screenshots/issue-23-*.png` | 0 | none | **merged** — !5 into main `3db4685` |
| 24 | Stage 1: CLAUDE.md year language cover status | `issue/24-claude-year-language-cover-status` | https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/6 | **success** 2420 (job 5508) | pass (empty, upload, reader, delete) | none (docs); smoke `bookreader/qa/screenshots/issue-24-*.png` | 0 | none | **merged** — !6 into main `3d44da8` |
| 25 | Stage 2: CSS tokens and fonts from spec 8.13 | `issue/25-css-tokens-fonts` | https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/7 | **success** 2422 (job 5510) | pass (empty+cream bg, upload, reader, delete) | tokens only; `bookreader/qa/screenshots/issue-25.png` | 0 | none | **merged** — !7 into main `89845a2` |
| 26 | Stage 2: AppHeader matches Main.png chrome | `issue/26-app-header` | https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/8 | **success** 2424 (job 5512) | pass (empty+header, upload via Загрузить EPUB, reader, delete, aria-current+label) | Main.png chrome; `bookreader/qa/screenshots/issue-header.png` + `issue-26.png` | 0 | none | **merged** — !8 into main `a4f0852` |
| 27 | Stage 2: BookCover 2:3 with fallback card | `issue/27-book-cover` | https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/9 | **success** 2426 (job 5514) | pass (empty, upload fallback card, reader, delete) | Main.png grey cards; `bookreader/qa/screenshots/issue-27.png` | 0 | none | **merged** — !9 into main `f4c87a1` |
| 28 | Stage 2: StatusBadge YearLabel ProgressBar BookMenu | `issue/28-status-components` | https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/10 | **success** 2428 (job 5516) | pass (empty, upload Не начата+⋯, reader, delete via Удалить…) | BookStates.png; `bookreader/qa/screenshots/issue-28.png` + `issue-28-menu.png` | 0 | none | **merged** — !10 into main `49f26ec` |
| 29 | Stage 2: stub routes authors series suggestions | `issue/29-stub-routes` | https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/11 | **success** 2430 (job 5518) | pass (Серии/Авторы/Уточнения headings, Книги back, upload, reader, delete) | header on stubs; `bookreader/qa/screenshots/issue-29.png` | 0 | none | **merged** — !11 into main `296c037` |

| 30 | Stage 3: GET /books filters sort query string | `issue/30-books-filters` | https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/12 | **success** 2432 (job 5520) | pass (empty, upload, reader, delete) | none (API) | 0 | none | **merged** — !12 into main `b1d0074` |

| 31 | Stage 3: GET /books/facets | `issue/31-books-facets` | https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/13 | **success** 2434 (job 5522) | pass (library still loads) | none (API) | 0 | none | **merged** — !13 into main `3866068` |

| 32 | Stage 3: LibraryPage matches Main.png | `issue/32-library-page` | https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/14 | **success** 2436 (job 5524) | pass (empty+sidebar+dropzone, upload, grid card, reader, delete dialog, table toggle, header sections) | Main.png; `bookreader/qa/screenshots/issue-library.png` + `issue-32.png` | 0 | none | **merged** — !14 into main `478e295` |

| 33 | Stage 4: authors API | `issue/33-authors-api` | https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/15 | **success** 2438 (job 5526) | pass (empty, upload, reader, delete; author facet after persist) | none (API); `bookreader/qa/screenshots/issue-33.png` | 0 | none | **merged** — !15 into main `8e4542a` |

| 34 | Stage 4: series API | `issue/34-series-api` | https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/16 | **success** 2440 (job 5528) | pass (empty, upload, grid) | none (API); `bookreader/qa/screenshots/issue-34.png` | 0 | none | **merged** — !16 into main `f5810bd` |

| 35 | Stage 4: AuthorsPage matches Authors.png | `issue/35-authors-page` | https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/17 | **success** 2442 (job 5530) | pass (authors index letter A + Austen Jane 1 книга, card → stub, reader, delete, series) | Authors.png; `bookreader/qa/screenshots/issue-35.png` | 0 | none | **merged** — !17 into main `ef897f9` |

| 36 | Stage 4: AuthorPage matches Author.png | `issue/36-author-page` | https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/18 | **success** 2444 (job 5532) | pass (Jane Austen hero + Вне серий, 404 «Автор не найден», reader, delete, series) | Author.png; `bookreader/qa/screenshots/issue-36.png` | 0 | none | **merged** — !18 into main `daca0d8` |

| 37 | Stage 4: SeriesPage matches Series.png | `issue/37-series-page` | https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/19 | **success** 2446 (job 5534) | pass (Dark Tower card + №1 Gunslinger, standalone footer, reader, delete) | Series.png; `bookreader/qa/screenshots/issue-37.png` | 0 | none | **merged** — !19 into main `5aa0614` |

| 38 | Stage 5: ReaderPage matches Reader.png | `issue/38-reader-page` | https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/20 | **success** 2448 (job 5536) | pass (TOC + «‹ Библиотека», chapter HTML, footer, back, delete) | Reader.png; `bookreader/qa/screenshots/issue-38.png` | 0 | none | **merged** — !20 into main `489dcd7` |

| 39 | Stage 5: ReaderPhone layout ReaderPhone.png | `issue/39-reader-phone` | https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/21 | **success** 2450 (job 5538) | pass (390px dock + TOC sheet, delete) | ReaderPhone.png; `bookreader/qa/screenshots/issue-39.png` | 0 | none | **merged** — !21 into main `8470918` |

| 40 | Stage 6: annotations API and reader notes panel | `issue/40-annotations` | https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/22 | **success** 2452 (job 5540) | pass (notes column + highlight «Chapter one», authors/series, delete) | Reader.png; `bookreader/qa/screenshots/issue-40.png` | 0 | none | **merged** — !22 into main `ea23ce3` |

| 41 | Stage 7: EditBookDialog matches EditBook.png | `issue/41-edit-book` | https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/23 | **success** 2454 (job 5542) | pass (⋯ → Данные книги, save title Pride, delete) | EditBook.png; `bookreader/qa/screenshots/issue-41.png` | 0 | none | **merged** — !23 into main |

| 42 | Stage 7: merge authors matches AuthorsMerge and MergeAuthors | `issue/42-merge-authors` | https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/24 | **success** 2456 (job 5544) | pass (Austen duplicates → merge to Jane Austen 2 books) | AuthorsMerge.png; `bookreader/qa/screenshots/issue-42.png` | 0 | none | **merged** — !24 into main `415fa14` |

| 43 | Stage 7: EditSeriesDialog matches EditSeries.png | `issue/43-edit-series` | https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/25 | **success** 2458 (job 5546) | pass (⋯ → Изменить серию…, add missing, save) | EditSeries.png; `bookreader/qa/screenshots/issue-43.png` | 0 | none | **merged** — !25 into main `f4cc54a` |

| 44 | Stage 8: enrich hosts and SuggestionsPage matches Suggestions | `issue/44-suggestions` | https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/26 | **success** 2460 (job 5548) | pass (`/suggestions` layout + enrich-all + empty copy) | Suggestions.png; `bookreader/qa/screenshots/issue-44.png` | 0 | none | **merged** — !26 into main `0aef2e2` |

| 45 | Final review LibraryPage and api.ts vs Main.png | n/a (review-only) | n/a | n/a | n/a | Main.png; comment `day 05/issue-45-review.md` | 0 | none | **closed** — GitLab note; no product edits |

Queue empty.
