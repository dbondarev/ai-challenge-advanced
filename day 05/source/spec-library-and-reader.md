# ТЗ: коллекция, авторы, серии и читалка (v1)

Макеты: [`docs/design/`](../design/README.md). Правила кода и запреты: [`CLAUDE.md`](../../CLAUDE.md). ТЗ их не отменяет. Где ТЗ требует поменять правило, это вынесено в раздел 11, и правило меняется до начала соответствующего этапа.

## 1. Рамки

- Один локальный пользователь, без входа.
- Только EPUB. FB2 и MOBI не парсим. Фильтра по формату в интерфейсе нет.
- Веб-клиент + Node API. Нативные клиенты позже пойдут в тот же API. Поэтому фильтры, сортировки, группировки, статусы, склейка и дозаполнение живут в API, а не в React.
- Язык интерфейса — русский.
- Метаданные берутся из файла, правятся вручную и уточняются по внешним базам (Open Library, Wikidata). Ручная правка всегда важнее всего остального.

Не входит в v1: поиск по тексту книги (иконку лупы в читалке не показываем), разделение ранее склеенных авторов, книга в нескольких сериях сразу, синхронизация настроек читалки между устройствами.

## 2. Что есть сейчас

- `books`: `id, title, authors (JSON), file_path, spine (JSON), created_at`.
- `progress`: `book_id, spine_index, scroll_ratio, updated_at`.
- `epub.ts` достаёт из OPF только `title`, `creator`, spine.
- API: `GET/POST /books`, `GET/DELETE /books/:id`, `GET /books/:id/chapters/:index`, `GET/PUT /books/:id/progress`.
- Web: `LibraryPage` (список + загрузка одного файла + удаление), `ReaderPage` (одна глава, сохранение прокрутки).
- `GET /books` пока не фильтрует по `q`, хотя CLAUDE.md этого требует. Закрывается в этапе 3.

## 3. Метаданные из файла

Всё извлекается в `epub.ts` при загрузке. Любое поле может отсутствовать: книга без него всё равно добавляется.

| Поле | Источник в OPF | Правило |
|---|---|---|
| Название | `dc:title` | Пусто → `"Untitled"`. |
| Авторы | `dc:creator` | Плюс сортировочное имя: атрибут `opf:file-as` (EPUB2) или `<meta refines="#id" property="file-as">` (EPUB3). Нет — фамилия = последнее слово имени. |
| Год издания | `dc:date` | Первые 4 цифры, `number \| null`. Это год издания именно этого файла или бумажного издания, с которого он сделан. |
| Язык | `dc:language` | Основной подтег в нижнем регистре: `ru-RU` → `ru`. Нет → `null`. |
| Серия | EPUB3: `<meta property="belongs-to-collection" id="x">Имя</meta>` + `refines="#x"`: `collection-type = series` (если `collection-type` нет, тоже считаем серией) и `group-position`. EPUB2/Calibre: `<meta name="calibre:series" content="Имя">` + `calibre:series_index`. | Имя и позиция. Позиция дробная (бывает `1.5`). Если источников несколько, EPUB3 важнее Calibre. |
| Обложка | 1) manifest item с `properties="cover-image"`; 2) `<meta name="cover" content="<id>">` → item; 3) `<guide><reference type="cover">` → первый `<img>` в этом документе. | Файл кладётся в `data/covers/<bookId>.<ext>`. Только `image/jpeg`, `image/png`, `image/webp`, `image/gif`. |
| Оглавление | EPUB3 `nav[epub:type=toc]`, иначе NCX (`toc.ncx`). | `{ title, spineIndex, depth }[]`. Якорь в ссылке пока игнорируем. Нет оглавления — по пункту на документ spine с названием «Глава N». |
| Размеры глав | Длина текста каждого документа spine (символы без тегов). | `number[]`. Для процента по книге и оставшегося времени. |

Года написания или первого издания в EPUB обычно нет. Он появляется вручную или из внешних баз (раздел 6).

Сырые значения из файла сохраняются отдельно (`file_meta`). Так любое поле можно «вернуть к данным файла», и повторный разбор не затирает ручные правки.

Тесты (`apps/api/test/epub.test.ts`), по фикстуре на каждый случай: EPUB3 с серией и cover-image, EPUB2 с calibre:series и `meta name=cover`, книга без серии, обложки и даты, `file-as` у автора. Фикстуры собираем через `epub-fixture.ts`.

## 4. Хранилище

### 4.1 Модель

Авторы и серии становятся отдельными сущностями: иначе их нельзя склеивать, переименовывать и дозаполнять.

```
books
  id             TEXT PK
  title          TEXT NOT NULL
  language       TEXT NULL
  published_year INTEGER NULL         -- год издания (из файла или вручную)
  original_year  INTEGER NULL         -- год написания или первого издания
  original_kind  TEXT NULL            -- 'written' | 'first_published'
  file_path      TEXT NOT NULL
  cover_path     TEXT NULL
  spine          TEXT NOT NULL        -- JSON string[]
  toc            TEXT NOT NULL        -- JSON TocEntry[]
  spine_sizes    TEXT NOT NULL        -- JSON number[]
  file_meta      TEXT NOT NULL        -- JSON: сырые title/authors/fileAs/date/language/series/seriesPosition из OPF
  field_sources  TEXT NOT NULL        -- JSON: { title: 'file', originalYear: 'wikidata', ... }
  status_manual  TEXT NULL            -- 'done' | 'dropped' | NULL (= считать автоматически)
  finished_at    INTEGER NULL
  dropped_at     INTEGER NULL
  meta_version   INTEGER NOT NULL
  created_at     INTEGER NOT NULL

authors
  id             TEXT PK
  name           TEXT NOT NULL        -- как показываем: «Лев Толстой»
  sort_name      TEXT NOT NULL        -- как сортируем: «Толстой Лев»
  external_ids   TEXT NOT NULL        -- JSON: { wikidata?: 'Q7243', openlibrary?: 'OL26783A' }
  field_sources  TEXT NOT NULL
  created_at     INTEGER NOT NULL

author_aliases                        -- все написания, которые ведут к автору
  alias_key      TEXT PK              -- нормализованное имя (раздел 5)
  author_id      TEXT NOT NULL REFERENCES authors(id)
  alias          TEXT NOT NULL        -- как было написано

book_authors
  book_id        TEXT NOT NULL REFERENCES books(id)
  author_id      TEXT NOT NULL REFERENCES authors(id)
  position       INTEGER NOT NULL
  PRIMARY KEY (book_id, author_id)

series
  id             TEXT PK
  name           TEXT NOT NULL
  total_books    INTEGER NULL         -- сколько книг в серии всего; NULL = неизвестно
  completion     TEXT NOT NULL        -- 'completed' | 'ongoing' | 'unknown'
  external_ids   TEXT NOT NULL
  field_sources  TEXT NOT NULL
  created_at     INTEGER NOT NULL

series_books                          -- книги серии, которые есть в библиотеке
  book_id        TEXT PK REFERENCES books(id)   -- одна серия на книгу в v1
  series_id      TEXT NOT NULL REFERENCES series(id)
  position       REAL NOT NULL        -- порядок чтения

series_missing                        -- книги серии, которых в библиотеке нет
  id             TEXT PK
  series_id      TEXT NOT NULL REFERENCES series(id)
  title          TEXT NOT NULL
  position       REAL NULL
  year           INTEGER NULL
  source         TEXT NOT NULL        -- 'manual' | 'wikidata' | 'openlibrary'
  source_url     TEXT NULL
  created_at     INTEGER NOT NULL

progress                              -- без изменений
annotations                           -- раздел 4.4

suggestions                           -- предложения из внешних баз (раздел 6)
  id, entity ('book'|'author'|'series'), entity_id, field, value (JSON),
  source, source_url, confidence ('high'|'medium'), status ('pending'|'accepted'|'rejected'),
  created_at, decided_at

external_cache
  key TEXT PK, source TEXT, body TEXT, fetched_at INTEGER

meta
  key TEXT PK, value TEXT             -- schema_version и т.п.
```

`books.authors` (JSON) уходит: авторы теперь в `book_authors`. Порядок авторов книги — `position`.

### 4.2 Источники полей

У каждого редактируемого поля книги, автора и серии в `field_sources` записан источник: `file`, `manual`, `openlibrary`, `wikidata`.
- Повторный разбор файла (новая `meta_version`) обновляет только поля с источником `file`.
- Внешние базы автоматически пишут только в пустые поля (раздел 6.3).
- `manual` не перезаписывается ничем, кроме нового ручного значения или «Вернуть к данным файла».

### 4.3 Миграция

- Таблицы и колонки создаются в `db/client.ts` (единственное место для raw SQL): `CREATE TABLE IF NOT EXISTS`, `ALTER TABLE ... ADD COLUMN` с проверкой через `PRAGMA table_info`. `db/schema.ts` (Drizzle) обновляется синхронно.
- Перенос данных — в `Library.migrate()` через Drizzle при старте, идемпотентно, по `meta.schema_version`:
  1. Для каждой книги перечитать EPUB, заполнить новые поля, сохранить обложку.
  2. Разложить авторов из старого `books.authors` в `authors` / `author_aliases` / `book_authors`.
  3. Разложить серию из файла в `series` / `series_books`.
  4. Удалить колонку `authors`: пересоздать таблицу, это тоже делается в `client.ts`.
- Файл не найден или не парсится — книга остаётся с тем, что есть, сервер не падает, ошибка пишется в лог.

### 4.4 Аннотации

```
annotations
  id           TEXT PK
  book_id      TEXT NOT NULL REFERENCES books(id)
  kind         TEXT NOT NULL          -- 'highlight' | 'bookmark'
  spine_index  INTEGER NOT NULL
  start_offset INTEGER NULL           -- смещение в textContent главы
  end_offset   INTEGER NULL
  scroll_ratio REAL NULL              -- для закладок
  quote        TEXT NOT NULL DEFAULT ''
  note         TEXT NULL              -- есть note → это «заметка», иначе просто выделение
  created_at   INTEGER NOT NULL
  updated_at   INTEGER NOT NULL
```

### 4.5 Удаление книги

`DELETE /books/:id` удаляет строку, `book_authors`, `series_books`, прогресс, аннотации, предложения по книге, EPUB и обложку. Автор без книг удаляется вместе с алиасами. Серия, у которой не осталось ни книг, ни `series_missing`, удаляется. Нет книги → `BookNotFoundError` → 404.

## 5. Логика `Library`

### 5.1 Нормализация и сравнение строк

- Ключ имени: NFKC, trim, схлопнуть пробелы, нижний регистр, `ё → е`, убрать точки и запятые. «Толстой, Л. Н.» → `толстой л н`.
- Сравнение для сортировок: один `Intl.Collator(["ru", "en"], { sensitivity: "base", numeric: true })`. Кириллица раньше латиницы: А–Я — сначала кириллические ключи, потом латинские; Я–А — наоборот.
- Поиск `q` — подстрока без учёта регистра и `ё/е`, в памяти: по названию книги, именам авторов и всем их алиасам. Никаких `LIKE`.

### 5.2 Авторы при загрузке

Каждое имя из `dc:creator` нормализуется и ищется в `author_aliases`. Нашлось — книга привязывается к этому автору. Иначе создаётся новый автор, и его имя становится первым алиасом. Поэтому после склейки «Толстой Л. Н.» → «Лев Толстой» новые книги с любым из этих написаний сразу попадают к одному автору.

### 5.3 Склейка авторов

`mergeAuthors(targetId, sourceIds)`, в одной транзакции:
1. Привязки `book_authors` переводятся с источников на цель; дубли в одной книге схлопываются, сохраняется меньший `position`.
2. Все алиасы источников переводятся на цель.
3. `external_ids` объединяются; при конфликте остаётся значение цели.
4. Источники удаляются.

Слить автора с самим собой → `MergeConflictError` (409). Отмены нет, интерфейс просит подтверждение.

**Кандидаты в дубли** (`GET /authors/duplicates`). Группы авторов, где:
- совпадает фамилия (первое слово `sort_name`), а инициалы одного совпадают с началом имён другого («Толстой Л. Н.» ~ «Толстой Лев Николаевич» ~ «Лев Толстой»); или
- совпадает `external_ids.wikidata`; или
- ключ одного совпадает с алиасом из Wikidata (`altLabel` на ru/en) другого.

Отклонённую пару больше не предлагаем (хранится в `suggestions` со `status = rejected`, `field = 'duplicate'`).

### 5.4 Серии

**Серия при загрузке.** Если в файле есть серия, ищем существующую с тем же нормализованным именем среди серий, где уже есть книга хотя бы одного из авторов этой книги. Нашлась — книга добавляется туда, иначе создаётся новая серия. Если в `series_missing` этой серии есть запись с тем же нормализованным названием, запись удаляется, а книга занимает её позицию.

**Порядок чтения** — `position`. Изначально из файла или из Wikidata, дальше пользователь меняет его вручную, перетаскиванием. Книги без позиции идут в конце по году. Отсутствующие книги стоят в том же порядке, что и имеющиеся.

**Склейка серий** — как у авторов: книги и отсутствующие записи переходят в цель, дубли отсутствующих по названию схлопываются.

**Состояние серии:**
- `inLibrary` — сколько книг есть; `known` = `inLibrary` + число `series_missing`; `total` = `total_books ?? known`. Если `total_books` меньше `known`, показываем `known`.
- `finished` — все книги в библиотеке `done` или `dropped`, хотя бы одна `done`, и `known == total`, то есть недостающих нет.
- `caughtUp` — все книги в библиотеке `done` или `dropped`, но в серии есть ещё книги («Прочитано всё, что есть»).
- `active` — хотя бы одна `reading` или `done`, и не `finished` / `caughtUp`.
- `fresh` — все книги в библиотеке `new`.

**Следующая книга серии:** первая `reading`, иначе первая `new` по порядку, иначе `null`. Брошенные пропускаются.

### 5.5 Статус книги

`ReadingStatus = 'new' | 'reading' | 'done' | 'dropped'`:
- `status_manual = 'done'` → `done`; `status_manual = 'dropped'` → `dropped`;
- иначе есть прогресс и `percent > 0` → `reading`;
- иначе `new`.

Автоматическое «прочитано»: при сохранении прогресса на последнем документе spine с `scrollRatio ≥ 0.98` ставится `status_manual = 'done'` и `finished_at`, если книга не `dropped`.

Вручную (`PUT /books/:id/status`): `done` — отметить прочитанной (ставит `finished_at`); `dropped` — «передумал читать» (ставит `dropped_at`); `null` — вернуть автоматический статус (даты очищаются). Чтение брошенной книги статус не меняет.

### 5.6 Процент и время

- `percent = (сумма spineSizes[0..spineIndex-1] + spineSizes[spineIndex] × scrollRatio) / сумма spineSizes × 100`, до целого. Если `spineSizes` пуст — `spineIndex / spine.length`.
- Оставшееся время: непрочитанные символы / 1000 = минуты, округление до 10 мин. Меньше 10 минут — «меньше 10 мин».

### 5.7 Какой год показывать

- `displayYear = original_year ?? published_year`.
- В карточках: `original_year` без подписи («1836»). Если есть только `published_year` — «изд. 2014».
- В окне правки и в подсказке при наведении на год видны оба: «Написана: 1836 · Издание: 2014». Для `first_published` вместо «Написана» пишем «Впервые издана».
- Сортировка «по году» — по `displayYear`; книги без года в конце.

## 6. Уточнение по внешним базам

### 6.1 Источники

Модуль `apps/api/src/sources/`, по файлу на источник, общий клиент с белым списком хостов. Любой другой хост — ошибка. Точные запросы и поля проверяются на реальных ответах в начале этапа 8 и фиксируются тестами на сохранённых ответах (без сети в тестах).

| Источник | Хосты | Что берём |
|---|---|---|
| Wikidata | `query.wikidata.org` (SPARQL), `www.wikidata.org` | Произведение по названию + автору: `P577` (дата публикации → год первого издания), `P571` (дата создания → год написания), `P179` (часть серии) + `P1545` (порядковый номер), у серии — `P527` (состав: отсюда недостающие книги и `total_books`), `P582` / наличие последней части (признак завершённости). У автора — `rdfs:label` / `skos:altLabel` на ru и en (алиасы для склейки), Q-id. |
| Open Library | `openlibrary.org` | `search.json` по `title` + `author`: `first_publish_year` (год первого издания), ключ работы и автора. Серий там почти нет, для них не используем. |

Опционально, после проверки условий API: FantLab (`api.fantlab.ru`). Там есть циклы и годы написания для русскоязычной фантастики.

### 6.2 Сопоставление

- Кандидат ищется по нормализованному названию (без подзаголовка после `:` или `.`) и фамилии первого автора. Если у автора уже есть `external_ids.wikidata`, ищем только среди его произведений.
- `high` — название совпало точно и фамилия совпала. `medium` — название совпало после отбрасывания артиклей и пунктуации, или фамилия совпала только транслитерацией.
- Несколько кандидатов одинаковой уверенности — ничего не применяем, создаём `medium` с вариантами.
- Найденные Q-id и OL-ключи сохраняются в `external_ids`, дальше поиск идёт по ним.

### 6.3 Что применяется само, что предлагается

- `high` в пустое поле — применяется сразу, источник поля = база.
- `high` в поле с источником `file` (например, серия из файла с другим номером) — предложение.
- `medium` — всегда предложение.
- Поле с источником `manual` — никогда не трогаем и не предлагаем.
- Недостающие книги серии (`series_missing`) — предложением списком на серию, принимаются целиком или по одной.
- Кандидаты в дубли авторов — отдельный тип предложения, см. 5.3.

### 6.4 Когда запускается

- После загрузки книги — в фоне, не задерживая ответ `POST /books`.
- Кнопкой «Уточнить в базах» у книги, автора или серии.
- «Уточнить всю библиотеку» — фоновая задача по всем книгам с неполными данными (нет `original_year`, серии без `completion`, авторы без Q-id).
- Очередь в процессе API, не больше 1 запроса в секунду на источник, таймаут 10 с, без повторов. Ответы кэшируются в `external_cache` на 30 дней. Заголовок `User-Agent: Bookreader/<версия> (личная библиотека)`.
- Нет сети или источник не отвечает — задача завершается с ошибкой, интерфейс пишет «Базы недоступны, попробуйте позже». Остальное приложение работает.

## 7. API

Ошибки — классы: `BookNotFoundError`, `AuthorNotFoundError`, `SeriesNotFoundError`, `AnnotationNotFoundError`, `SuggestionNotFoundError`, `NotEpubError`, `MergeConflictError`. HTTP: not found → 404 `{ error: "not found" }`; `NotEpubError` → 400 `{ error: "not_epub" }`; файл больше 100 МБ → 413 `{ error: "too_large" }`; `MergeConflictError` → 409 `{ error: "merge_conflict" }`; невалидное тело → 400 `{ error: "invalid", field }`.

### 7.1 Типы (`packages/shared`)

```ts
export type ReadingStatus = "new" | "reading" | "done" | "dropped";
export type FieldSource = "file" | "manual" | "openlibrary" | "wikidata";

export type AuthorRef = { id: string; name: string };
export type BookSeries = { id: string; name: string; position: number | null };

export type BookYears = {
  original: number | null;
  originalKind: "written" | "first_published" | null;
  published: number | null;
  display: number | null;
};

export type Book = {
  id: string;
  title: string;
  authors: AuthorRef[];
  createdAt: number;
  years: BookYears;
  language: string | null;
  hasCover: boolean;
  series: BookSeries | null;
  status: ReadingStatus;
  statusIsManual: boolean;
  percent: number;
  lastOpenedAt: number | null;
  position: string | null;          // «Глава I · Сержант гвардии»
};

export type TocEntry = { title: string; spineIndex: number; depth: number };

export type BookDetail = Book & {
  spine: string[];
  toc: TocEntry[];
  remainingMinutes: number;
  fieldSources: Partial<Record<"title" | "authors" | "language" | "publishedYear" | "originalYear" | "series", FieldSource>>;
  fileMeta: { title: string; authors: string[]; year: number | null; language: string | null; series: string | null; seriesPosition: number | null };
};

export type ReadingProgress = { bookId: string; spineIndex: number; scrollRatio: number; updatedAt: number };

export type AuthorSummary = {
  id: string; name: string; sortName: string; letter: string; aliases: string[];
  bookCount: number; seriesCount: number; readingCount: number; doneCount: number;
  yearFrom: number | null; yearTo: number | null;
  coverBookIds: string[];           // до 3, приоритет — с обложкой
  externalIds: { wikidata?: string; openlibrary?: string };
};

export type MissingEntry = { id: string; title: string; position: number | null; year: number | null; source: FieldSource; sourceUrl: string | null };

export type SeriesState = "fresh" | "active" | "caughtUp" | "finished";

export type SeriesSummary = {
  id: string; name: string; authors: AuthorRef[];
  inLibrary: number; known: number; total: number;
  doneCount: number; droppedCount: number;
  completion: "completed" | "ongoing" | "unknown";
  state: SeriesState;
  yearFrom: number | null; yearTo: number | null;
  next: { bookId: string; title: string; action: "continue" | "start" } | null;
  entries: SeriesEntry[];           // книги и отсутствующие вперемешку, в порядке чтения
};

export type SeriesEntry =
  | { kind: "book"; position: number | null; book: Book }
  | { kind: "missing"; position: number | null; missing: MissingEntry };

export type AuthorDetail = { author: AuthorSummary; series: SeriesSummary[]; standalone: Book[] };

export type LibraryFacets = {
  total: number;
  statuses: Record<ReadingStatus, number>;
  languages: { code: string; count: number }[];
  authors: { id: string; name: string; count: number }[];
};

export type Annotation = {
  id: string; bookId: string; kind: "highlight" | "bookmark";
  spineIndex: number; startOffset: number | null; endOffset: number | null; scrollRatio: number | null;
  quote: string; note: string | null; createdAt: number; updatedAt: number;
};

export type Suggestion = {
  id: string; entity: "book" | "author" | "series"; entityId: string; entityTitle: string;
  field: string; current: unknown; value: unknown;
  source: FieldSource; sourceUrl: string | null; confidence: "high" | "medium";
};

export type EnrichJob = { id: string; state: "queued" | "running" | "done" | "failed"; processed: number; total: number; applied: number; suggested: number; error: string | null };
```

`Chapter` остаётся как есть.

### 7.2 Книги

| Метод и путь | Что делает |
|---|---|
| `GET /books` | `q`, `status` (`new\|reading\|done\|dropped`), `lang` (повторяемый), `author` (повторяемый), `series` (id или `none`), `sort` (`opened\|added\|title\|author\|year`, по умолчанию `opened`), `order` (`asc\|desc`). `opened` — по `lastOpenedAt` по убыванию, неоткрытые в конце по `createdAt`. → `Book[]`. |
| `GET /books/facets` | `LibraryFacets` по всей библиотеке. |
| `POST /books` | Загрузка. → 201 `Book`. Ошибки `not_epub`, `too_large`. Ставит фоновое уточнение. |
| `GET /books/:id` | `BookDetail`. |
| `PATCH /books/:id` | Ручная правка: `title`, `authors` (массив `{ id }` существующего или `{ name }` нового, порядок важен), `language`, `publishedYear`, `originalYear`, `originalKind`, `series` (`{ id } \| { name } \| null`), `seriesPosition`. Каждое переданное поле получает источник `manual`. `resetToFile: string[]` — вернуть перечисленные поля к `fileMeta` с источником `file`. → `BookDetail`. |
| `PUT /books/:id/status` | `{ status: "done" \| "dropped" \| null }` → `Book`. |
| `GET /books/:id/cover` | Байты обложки, `cache-control: max-age=31536000, immutable`. Нет → 404. |
| `GET /books/:id/resources/*` | Ресурсы архива (картинки и т.п.). Путь нормализуется, `..` и выход за корень → 404. |
| `GET /books/:id/chapters/:index` | HTML очищен на сервере: без `<script>`, `on*`-атрибутов, `javascript:`-ссылок, `<iframe>/<object>/<embed>`. Относительные `src`/`href` ресурсов переписаны на `/books/:id/resources/...`. |
| `GET/PUT /books/:id/progress` | Как сейчас; `PUT` может выставить автоматическое `done` (5.5). |
| `DELETE /books/:id` | 4.5. |

### 7.3 Авторы

| Метод и путь | Что делает |
|---|---|
| `GET /authors` | `q` (по имени и алиасам), `sort` (`az\|za\|books`) → `AuthorSummary[]`. |
| `GET /authors/duplicates` | Группы кандидатов в дубли: `{ authors: AuthorSummary[]; reason: "initials" \| "wikidata" \| "alias" }[]`. |
| `GET /authors/:id` | `AuthorDetail`. `sort` (`order\|title\|year`) — порядок внутри серий и в `standalone`. |
| `PATCH /authors/:id` | `name`, `sortName`. Старое имя остаётся алиасом. → `AuthorSummary`. |
| `POST /authors/:id/merge` | `{ sourceIds: string[] }` → `AuthorDetail` цели. |
| `POST /authors/duplicates/dismiss` | `{ authorIds: string[] }` — «это разные люди». |

### 7.4 Серии

| Метод и путь | Что делает |
|---|---|
| `GET /series` | `q` (название серии и авторы), `state` (`fresh\|active\|caughtUp\|finished`), `sort` (`title\|author\|progress\|year`). `progress` — по `doneCount / total` по убыванию, `year` — по году первой книги. → `{ series: SeriesSummary[]; standaloneCount: number }`. |
| `GET /series/:id` | `SeriesSummary`. |
| `PATCH /series/:id` | `name`, `totalBooks` (число или `null`), `completion`. → `SeriesSummary`. |
| `PUT /series/:id/order` | `{ entries: { kind: "book" \| "missing"; id: string }[] }` — полный список в новом порядке. Позиции перезаписываются: 1, 2, 3… → `SeriesSummary`. |
| `POST /series/:id/missing` | `{ title, position?, year? }` → 201 `MissingEntry`. |
| `PATCH /series/:id/missing/:missingId` | Правка записи. |
| `DELETE /series/:id/missing/:missingId` | 204. |
| `POST /series/:id/merge` | `{ sourceIds: string[] }` → `SeriesSummary` цели. |

### 7.5 Аннотации

`GET /books/:id/annotations` (по `spineIndex`, затем `startOffset`), `POST /books/:id/annotations` → 201, `PATCH /annotations/:id` (`note`), `DELETE /annotations/:id` → 204.

### 7.6 Уточнение

| Метод и путь | Что делает |
|---|---|
| `POST /enrich` | `{ scope: "book" \| "author" \| "series" \| "library"; id?: string }` → 202 `EnrichJob`. Одновременно одна задача `library`; повторный запрос возвращает текущую. |
| `GET /enrich/jobs/:id` | `EnrichJob`. |
| `GET /suggestions` | `status=pending` по умолчанию; `entity`, `entityId` → `Suggestion[]`. |
| `POST /suggestions/accept` | `{ ids: string[] }` — применить; источник поля = база. → `{ applied: number }`. |
| `POST /suggestions/reject` | `{ ids: string[] }`. Отклонённое больше не предлагается для того же поля и значения. |

Тесты — `node:test` + `app.inject`: каждый эндпоинт, каждый фильтр и сортировка, 404 на каждый `:id`, склейка (книги, алиасы, загрузка после склейки), порядок серии с отсутствующими книгами, автозамена отсутствующей записи при загрузке, состояния серии, ручные статусы, защита `manual` от перезаписи, очистка HTML, `..` в ресурсах, каскадное удаление. Источники тестируются на сохранённых ответах, сеть в тестах не трогаем.

## 8. Веб-клиент

### 8.1 Общее

- Роуты: `/` → `LibraryPage`, `/series` → `SeriesPage`, `/authors` → `AuthorsPage`, `/authors/:id` → `AuthorPage`, `/books/:id` → `ReaderPage`, `/suggestions` → `SuggestionsPage`.
- Все запросы — через `apps/web/src/api.ts`, по функции на эндпоинт.
- Фильтры, поиск, сортировка и вид хранятся в query-строке (`?status=reading&sort=title`), чтобы работали «назад» и ссылки. Поиск — с задержкой 250 мс.
- Шрифты Literata (текст книг, заголовки) и Onest (интерфейс) — локально через `@fontsource`.
- Цвета и размеры — CSS-переменные в одном файле токенов (8.12).
- Иконки-кнопки от 44 px, у полей видимый `<label>`, у иконок `aria-label`. Всё работает от 360 px.
- Компоненты по одному на файл: `AppHeader`, `BookCover`, `BookCard`, `BookTable`, `BookMenu`, `StatusBadge`, `ProgressBar`, `YearLabel`, `UploadPanel`, `SortSelect`, `AuthorCard`, `SeriesCard`, `SeriesEntryCard`, `EditBookDialog`, `MergeAuthorsDialog`, `EditSeriesDialog`, `SuggestionList`, `TocPanel`, `NotesPanel`, `ReaderSettings`, `SelectionToolbar`.

### 8.2 `BookCover`

- `hasCover` → `<img src="/books/:id/cover" alt="Обложка: {title}">`, `object-fit: cover`, 2:3, `loading="lazy"`, радиус 4 px, тень как на макете.
- Нет обложки или `onError` → запасная карточка: фон `#ECEBE5`, рамка `#D9D8D0`, синяя черта 24×2 px, название Literata 600, автор капителью 11 px.
- Бейдж «№ N» в левом верхнем углу — только там, где показана серия. Дробная позиция печатается как есть: «№ 1.5».
- Размеры: сетка — ячейка от 164 px; «Продолжить чтение» 64×96; таблица 28×42; серии от 120 px; стопка у автора 46×69.

### 8.3 `StatusBadge`, `YearLabel`, `BookMenu`

- Статусы: «Не начата», «Читаю», «Прочитана», «Брошена» (цвета в 8.12). У ручного статуса нет отдельной пометки.
- `YearLabel` — правило 5.7, с `title` вида «Написана: 1836 · Издание: 2014».
- `BookMenu` («⋯» на карточке, в строке таблицы, в шапке читалки; на карточке появляется при наведении и фокусе, на сенсорных экранах виден всегда):
  - «Отметить прочитанной» / «Снять отметку „Прочитана“»;
  - «Бросить читать» / «Вернуть в чтение»;
  - «Изменить данные…» → `EditBookDialog`;
  - «Уточнить в базах»;
  - «Удалить…».

### 8.4 `AppHeader`

Логотип → `/`. Разделы «Книги», «Серии», «Авторы», активный с `aria-current="page"`. Кнопка «Загрузить EPUB» на всех трёх разделах (`multiple`, `accept=".epub,application/epub+zip"`). Если есть ожидающие предложения — точка-индикатор и ссылка «Уточнения (N)» → `/suggestions`. На коллекции в шапке ещё поиск с подписью «Поиск по названию или автору».

### 8.5 Коллекция (`/`) — `screens/Main.png`

1. **Загрузка.** Зона drag-and-drop + список загрузок. Несколько файлов, одновременно не больше 2. Статусы строки:
   - «Загрузка · N%» с полосой (`XMLHttpRequest.upload.onprogress`; `uploadBook` в `api.ts` переходит на XHR);
   - «Читаем название и автора…» — байты ушли, ответа нет;
   - «Добавлена в библиотеку» — 201, книга появляется в списке без перезагрузки;
   - ошибки: `not_epub` → «Не EPUB-файл. Пока поддерживается только EPUB»; `too_large` → «Файл больше 100 МБ»; сеть → «Не удалось загрузить» + «Повторить».
   Отмена — крестик. «Очистить завершённые» убирает «Добавлена» и ошибки. Без загрузок остаётся только зона.
2. **Продолжить чтение.** До 3 книг `reading` по `lastOpenedAt`: обложка, название, автор, `position`, процент. Скрыт при поиске, фильтре статуса и когда читаемых нет.
3. **Фильтры слева** (`GET /books/facets`):
   - Статус: «Все книги», «Читаю», «Не начата», «Прочитана», «Брошена» со счётчиками; «Брошена» скрыта при нуле.
   - Язык: чекбоксы по языкам библиотеки; блок скрыт, если язык один.
   - Автор: топ-4 + «Все авторы (N)» → `/authors`.
4. **Список.** Заголовок по фильтру и число книг. Сортировка: «Недавно открытые», «По названию, А–Я», «По автору, А–Я», «По году». Переключатель «Сетка / Таблица».
   - Сетка: обложка, название, «автор · год», бейдж статуса, у `reading` полоса и процент, `BookMenu`.
   - Таблица: миниатюра + название + автор, год, статус, прогресс, дата добавления, `BookMenu`.
   - Удаление — диалог «Удалить „{title}“? Заметки и прогресс тоже удалятся».
   - Пусто по фильтрам: «Ничего не нашлось» + «Сбросить фильтры». Пустая библиотека: зона загрузки и «Добавьте первую книгу».

### 8.6 `EditBookDialog` (нет на макетах)

Модальное окно, поля:
- Название;
- Авторы — чипы с автодополнением по существующим авторам (поиск по алиасам), можно создать нового, порядок перетаскиванием;
- Серия — автодополнение по существующим или новая, «Без серии»;
- Номер в серии — число, допускает дробь;
- Год написания / первого издания — число + переключатель «написания / первого издания»;
- Год издания;
- Язык.

У каждого поля мелкая подпись источника: «из файла», «вручную», «Wikidata ↗», «Open Library ↗» (ссылка на запись). Если значение отличается от файла — «Вернуть из файла». Внизу «Уточнить в базах»: найденное показывается прямо в окне как предложения у полей («Wikidata: 1836 · Принять»). Сохранение отправляет только изменённые поля.

### 8.7 Авторы (`/authors`) — `screens/Authors.png`

- Заголовок, «N авторов · M книг», поиск «Поиск автора» (по алиасам тоже), сортировка «По фамилии, А–Я» / «Я–А» / «По числу книг».
- Алфавитный указатель: полный русский алфавит + латинские буквы, что есть в библиотеке; пустые серые и некликабельные.
- А–Я и Я–А — группы по букве; «По числу книг» — одна сетка, указатель скрыт.
- Карточка: стопка до 3 обложек, «**Фамилия** Имя», «N книг · K серий», годы, бейджи «Читаю N» / «Прочитано N».
- **Возможные дубли** (нет на макетах): если `GET /authors/duplicates` не пуст, над списком блок «Возможно, это один автор» — группы карточек с кнопками «Объединить…» (открывает `MergeAuthorsDialog` с этой группой) и «Это разные люди».
- **Режим объединения** (нет на макетах): кнопка «Объединить авторов» включает чекбоксы на карточках; при выборе от 2 — панель «Объединить выбранных (N)».
- `MergeAuthorsDialog`: список выбранных с числом книг, выбор главного (его имя остаётся основным), предпросмотр «Будет: Лев Толстой — 7 книг, 2 серии; остальные написания станут вариантами имени», подтверждение. После — переход на страницу главного автора.
- Склонения — общая утилита `plural(n, "книга", "книги", "книг")`.

### 8.8 Автор (`/authors/:id`) — `screens/Author.png`

- Крошки «Авторы / Фамилия Имя».
- Шапка: круг с инициалами, имя, «N книг · K серий · YYYY–YYYY», полоса «Прочитано / Читаю / Брошено / Не начато» с легендой (сегмент «Брошено» только если есть), «Продолжить «{title}»», если есть `reading`. Под именем мелко «Также: Толстой Л. Н., L. Tolstoy», если есть алиасы. Меню автора: «Изменить имя…», «Объединить с…», «Уточнить в базах».
- «По сериям / Все книги» и сортировка «По порядку в серии / По названию, А–Я / По году». В режиме «Все книги» «По порядку» = по году.
- По сериям: секция на серию (по названию А–Я) — заголовок, «Серия · 3 из 5 в библиотеке · годы», метка завершённости («Серия завершена» / «Продолжается»; при `unknown` ничего), полоса «Прочитано X из total»; затем «Вне серий». Внутри — сетка `SeriesEntryCard`: книги и отсутствующие вперемешку по порядку.
- Отсутствующая книга (нет на макетах): пунктирная рамка `#C9C8C0` на прозрачном фоне, «№ N», название, год, подпись «Нет в библиотеке». Меню: «Убрать из серии», «Изменить». Порядок «По названию» и «По году» тоже включает отсутствующие.
- У заголовка серии меню: «Изменить серию…» → `EditSeriesDialog`, «Уточнить в базах».
- Неизвестный `id` → «Автор не найден» со ссылкой на `/authors`. Если `id` был склеен — 404 тоже; редиректы в v1 не делаем.

### 8.9 Серии (`/series`) — `screens/Series.png`

- Заголовок, «N серий · M книг», поиск «Поиск серии или автора», сортировка «По названию, А–Я / По автору, А–Я / По прогрессу / По году первой книги».
- Чипы: «Все», «В процессе», «Не начаты», «Прочитано всё, что есть», «Прочитаны», со счётчиками; пустые скрыты.
- Карточка серии:
  - слева: название, автор(ы) ссылкой, «3 из 5 в библиотеке · годы», метка «Серия завершена» / «Продолжается»;
  - состояние: «В процессе», «Не начата», «Прочитано всё, что есть — не хватает N», «Серия прочитана»;
  - «X из total», полоса;
  - кнопка «Продолжить «…»» / «Начать «…»» из `next`;
  - если `total > known`: «Ещё N книг серии неизвестны» и ссылка «Уточнить в базах»;
  - справа: `SeriesEntryCard` по порядку, под каждой книгой полоса прогресса и «год · статус»;
  - меню «⋯»: «Изменить серию…», «Объединить с…», «Уточнить в базах».
- Внизу «Книги вне серий — N книг» → `/?series=none`.

### 8.10 `EditSeriesDialog` (нет на макетах)

- Название.
- Всего книг в серии: число или «Неизвестно».
- Статус: «Завершена» / «Продолжается» / «Неизвестно».
- Порядок чтения: вертикальный список всех записей (книги и отсутствующие), перетаскивание ручкой и кнопки ↑/↓ для клавиатуры; позиции пересчитываются при сохранении (`PUT /series/:id/order`).
- «Добавить книгу, которой нет в библиотеке»: название, год, место в списке.
- Предложения из баз по этой серии: недостающие книги, общее число, завершённость — каждое с «Принять» / «Отклонить».
- «Объединить с другой серией…» — выбор серии, предпросмотр, подтверждение.

### 8.11 Читалка (`/books/:id`) — `screens/Reader.png`, `screens/ReaderPhone.png`

**Каркас.** Верхняя панель: «‹ Библиотека» (возврат на предыдущую страницу списка, иначе `/`), кнопка оглавления, по центру название и «автор · год · текущая глава», справа закладка, «Aa», заметки, `BookMenu`. Под панелью полоса прогресса (`role="progressbar"`). Нижняя панель: «Предыдущая глава», «Глава N из M · Прочитано X% · Осталось ≈ …», «{следующая глава} ›»; на краях неактивны.

**Брошенная книга.** Над текстом тонкая плашка «Вы бросили эту книгу · Вернуть в чтение».

**Оглавление** (слева, 260 px). Пункты из `toc`, отступ по `depth`, своей нумерации не добавляем. Текущий пункт подсвечен и показывает процент главы. Клик открывает главу с начала. Скрывается кнопкой, состояние помнится.

**Текст.** Колонка до 660 px. Очищенный HTML с сервера. CSS книги не подключаем; стили на `article`: шрифт, размер, межстрочный 1.65, абзацный отступ 1.5em, картинки `max-width: 100%`.

**Прогресс.** `PUT /books/:id/progress` с задержкой 1 с и при `visibilitychange` / `pagehide`. При открытии — восстановление главы и `scrollRatio`. Под текстом главы кнопка «Следующая глава». Прогресс всегда по `bookId`.

**Настройки «Aa».** Размер 15–26 px (шаг 1, по умолчанию 19), шрифт Literata / Onest, тема «Светлая» / «Сепия» / «Тёмная». Применяются сразу. Хранятся в `localStorage` под `reader.settings` — это настройки устройства, а не прогресс.

**Выделения и заметки.**
- Выделение текста → плавающая панель «Выделить», «Заметка», «Копировать».
- «Выделить» создаёт highlight. «Заметка» создаёт highlight и открывает поле «Заметка к выделенному» внизу правой панели; «Сохранить» пишет `note`, «Отмена» удаляет пустую.
- Позиция — смещения в `textContent` главы. Выделения рисуются `<mark>`, у заметок надстрочный номер; клик по номеру прокручивает панель к карточке.
- Если `quote` не совпал с вырезанным фрагментом — в тексте не рисуем, карточку в панели показываем.

**Правая панель** (300 px). Вкладки «Заметки N» / «Закладки N». Карточка заметки: номер, «Глава · дата», цитата, текст, меню «⋯» (изменить, удалить); клик ведёт к месту. Закладка: «Глава · начало абзаца · дата». Флажок в шапке ставит или снимает закладку на текущей позиции.

**Конец книги.** На последней главе под текстом «Отметить прочитанной»; если `done` — «Прочитана · Снять отметку».

**Узкий экран** (< 900 px). Оглавление и заметки — выдвижные листы. Нижняя панель как на `ReaderPhone.png`: ползунок позиции по книге, «Оглавление», «Заметки», «Закладка». Панели прячутся тапом по тексту.

### 8.12 Уточнения (`/suggestions`) — нет на макетах

- Сверху «Уточнить всю библиотеку» и состояние задачи («Проверено 12 из 40 · применено 9 · ждут решения 5»).
- Список предложений, сгруппированный по книге, автору или серии: обложка или инициалы, название, строки «Поле: сейчас → предлагается · источник ↗». У каждой строки «Принять» / «Отклонить», у группы «Принять всё».
- Отдельная группа «Недостающие книги серий» и «Возможные дубли авторов» (ведёт на 8.7).
- Пусто: «Уточнений нет. Новые появятся после загрузки книг или проверки библиотеки».

### 8.13 Токены

| Токен | Значение |
|---|---|
| Фон приложения | `#F4F4F1` |
| Поверхность | `#FFFFFF`, линия `#E3E2DC`, разделитель `#EEEDE8`, рамка полей `#D4D3CC`, пунктир отсутствующих книг `#C9C8C0` |
| Текст / вторичный | `#17181C` / `#5E6068` |
| Акцент | `#2F4F8F`, наведение `#1F3766`, мягкий `#E6ECF7` |
| Статусы | Читаю `#2F4F8F` на `#E6ECF7`; Прочитана `#2B6E4F` на `#E3F0E8`; Не начата `#4B4D55` на `#ECECE7`; Брошена `#7A4E12` на `#F5EBDA`; ошибка `#A8281E` на `#F8E3E0` |
| Радиусы | поля и кнопки 8, карточки 12, крупные блоки 16, обложки 4, бейджи 999 |
| Шрифты | Onest 400/500/600 — интерфейс 14 px; Literata 400/600 и курсив — заголовки (22/24/34/36 px) и текст книг |

Темы читалки (`bg / panel / line / ink / muted / accent / mark / selection`):

- Светлая: `#FBFAF7 / #FFFFFF / #E6E3DB / #1C1B19 / #5F5D57 / #2F4F8F / #F3E29A / #CFDCF5`
- Сепия: `#F3EAD8 / #EEE3CC / #D9CBAE / #3A2E21 / #665641 / #7C4A1F / #E6C77C / #DDC9A2`
- Тёмная: `#16171A / #1D1E22 / #2E3036 / #DAD7CF / #9A978F / #8FB0EE / #5C4C1C / #2F4468` (текст на акцентной кнопке `#0F1420`)

## 9. Этапы

Этап закрыт, только когда экран(ы) этапа совпадают с макетами из раздела 10, а не когда собраны отдельные компоненты в старом списке.

Один GitLab issue = один шаг ниже. После **каждого** issue обязателен процесс 9.1.

1. **Модель и метаданные файла.** Раздел 3, таблицы и миграция (4), удаление (4.5), обложка, статусы с ручными отметками (5.5), процент (5.6), годы (5.7), `PATCH /books/:id` пока только из тестов. Правки CLAUDE.md из раздела 11, пункты 1–2.
2. **Каркас интерфейса.** Шрифты, токены, `AppHeader` как на `Main.png` (логотип, Книги / Серии / Авторы, поиск в шапке, «Загрузить EPUB»), `BookCover`, `StatusBadge`, `YearLabel`, `ProgressBar`, `BookMenu`, роуты и заглушки страниц. Макет шапки: `screens/Main.png`.
3. **Коллекция.** Фильтры и сортировки `GET /books`, `GET /books/facets`, `LibraryPage` **целиком** по 8.5 и `screens/Main.png` (сайдбар, drag-and-drop, «Продолжить чтение», сетка и таблица). Недостаточно вставить обложку в старый `<ul>`.
4. **Авторы и серии — просмотр.** API авторов и серий; `AuthorsPage` = `screens/Authors.png`; `AuthorPage` = `screens/Author.png`; `SeriesPage` = `screens/Series.png`; отсутствующие книги и завершённость.
5. **Читалка.** Очистка HTML, ресурсы, `toc`, оставшееся время; `ReaderPage` = `screens/Reader.png`; узкий экран = `screens/ReaderPhone.png`. Без заметок на этом этапе.
6. **Заметки и закладки.** `annotations`, CRUD, выделения, панель — как правая колонка на `Reader.png`.
7. **Ручное редактирование.** `EditBookDialog` = `screens/EditBook.png`; склейка авторов = `AuthorsMerge.png` + `MergeAuthors.png`; `EditSeriesDialog` = `screens/EditSeries.png`; порядок, отсутствующие книги, склейка серий.
8. **Внешние базы.** Раздел 6, `/enrich`, `/suggestions`; `SuggestionsPage` = `screens/Suggestions.png`. Перед этапом — правка CLAUDE.md из раздела 11, пункт 3.

### 9.1 Процесс после каждого issue

Агент не переходит к следующему issue, пока не сделано всё ниже. Лог — `ai-challenge-advanced/day 05/run-4.md` (и зеркало в комментарии GitLab issue).

1. **Код.** Только этот issue. Не закрывать этап целиком одной правкой.
2. **Тесты.** Новые или расширенные `node:test` на новое поведение. `scripts/check.sh` зелёный.
3. **Макет (если UI).** Сверить страницу с PNG из раздела 10 при 1440 px (читалка на телефоне — 390 px). Скриншот в `qa/screenshots/issue-{iid}.png`. Если это всё ещё список ссылок вместо сетки/сайдбара с макета — issue не закрыт.
4. **Smoke.** UI-изменение → скилл `update-smoke` (дописать сценарий и прогнать все). Иначе `qa-runner` (check.sh + существующий smoke).
5. **GitLab.** Ветка `issue/{iid}-{slug}`, коммит, push, merge request в `main`, дождаться pipeline (`.gitlab-ci.yml` = `scripts/check.sh`). Красный pipeline — не мержить.
6. **Ревью и баги.** Профиль `review` по изменённым файлам + поиск расхождений с ТЗ и макетом. Critical / явный баг → новые GitLab issues `type::bug` в **голову очереди** (их берут раньше следующих фич). Should-fix — тоже в очередь, мерж фичи можно делать.
7. **Закрытие.** Issue закрывают после зелёного pipeline. Баги из п.6 живут отдельными issues.

## 10. Макеты к разделам

PNG в `docs/design/screens/`. Приёмка UI — совпадение раскладки с макетом, не наличие отдельных компонентов.

| Раздел | Макет |
|---|---|
| 8.4 шапка, 8.5 коллекция целиком (сайдбар, загрузка, «Продолжить чтение», сетка, фильтр «Брошена») | `screens/Main.png` |
| 8.3 статусы, «Брошена», `BookMenu`, `YearLabel`; 8.11 плашка брошенной книги и конец книги | `screens/BookStates.png` |
| 8.7 список авторов, указатель букв | `screens/Authors.png` |
| 8.7 дубли и режим объединения | `screens/AuthorsMerge.png` |
| 8.7 `MergeAuthorsDialog` | `screens/MergeAuthors.png` |
| 8.8 страница автора, отсутствующие книги, «Серия завершена», «Прочитано всё, что есть» | `screens/Author.png` |
| 8.9 список серий, «Ещё N книг неизвестны», чип «Прочитано всё, что есть» | `screens/Series.png` |
| 8.11 читалка desktop | `screens/Reader.png` |
| 8.11 читалка ≤ 640 px | `screens/ReaderPhone.png` |
| 8.6 `EditBookDialog` | `screens/EditBook.png` |
| 8.10 `EditSeriesDialog` | `screens/EditSeries.png` |
| 8.12 Уточнения | `screens/Suggestions.png` |

Иконки в меню на макете — текстовые значки-заглушки. В коде используем один набор SVG-иконок.

## 11. Что поменять в правилах проекта

Менять одновременно в `CLAUDE.md`, `.cursorrules`, `.github/copilot-instructions.md`, `.cursor/rules/`.

1. Строку «`q` matches title or any author after `JSON.parse` … Do not `LIKE` the authors JSON column» заменить на: «`q` matches title, author names and author aliases, compared case-insensitively in memory. No `LIKE`.» (колонки `authors` больше нет).
2. В «Shared types» добавить `Author*`, `Series*`, `Annotation`, `Suggestion`; в «Layout» — `apps/api/src/sources/`, новые страницы. Ошибки — новые классы из раздела 7.
3. Запрет «`fetch` to unknown hosts from the API» уточнить: «API may `fetch` only hosts listed in `apps/api/src/sources/hosts.ts` (Wikidata, Open Library). Any other host is banned.»

## 12. Приёмка (сводно)

- Коллекция, авторы, серии, читалка и диалоги на 1440 px (читалка телефон — 390 px) совпадают с PNG из раздела 10: шапка, колонки, сетка. Список ссылок с бейджем вместо `Main.png` — не сдача этапа 3.
- Загрузка EPUB3 с серией и обложкой показывает обложку, год и серию везде, где есть эта книга.
- Книга без обложки везде рисуется запасной карточкой, без битых картинок.
- Если есть только год издания, он подписан «изд. YYYY»; после уточнения появляется год написания без подписи, а в подсказке видны оба.
- Ручная правка поля не перезаписывается ни повторным разбором файла, ни базами. «Вернуть из файла» восстанавливает значение файла.
- После склейки «Толстой Л. Н.» с «Лев Толстой» все книги у одного автора, поиск «толстой л» находит его, а новая загрузка с любым написанием попадает к нему же.
- Порядок серии, изменённый перетаскиванием, сохраняется и одинаков на странице автора и серий.
- Отсутствующая книга серии видна пунктиром. После загрузки этой книги пунктир исчезает, книга встаёт на ту же позицию.
- Серия, где прочитаны все имеющиеся книги, но не хватает одной, — «Прочитано всё, что есть — не хватает 1», а не «Серия прочитана».
- Дочитанная до конца книга становится «Прочитана». «Бросить читать» убирает её из «Продолжить чтение» и из «следующей книги» серии. «Вернуть автоматический статус» возвращает «Читаю» или «Не начата» по прогрессу.
- Перезагрузка читалки возвращает на то же место; у разных книг свои позиции.
- Заметка видна в панели после перезагрузки и подсвечена в тексте.
- Удаление последней книги автора убирает автора; страница такого автора отдаёт 404.
- При выключенной сети приложение работает, уточнение пишет «Базы недоступны».
