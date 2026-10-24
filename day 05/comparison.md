# День 5. Execution loop

Пул: 18 задач из ТЗ [`docs/spec/library-and-reader.md`](../../bookreader/docs/spec/library-and-reader.md) и макетов. Очередь: [`pool.md`](pool.md). GitLab: [#1–#18](https://git.modumuptools.com/dbondarev/bookreader/-/issues?label_name=day-5) (закрыты после лупа). Cursor MCP OAuth по-прежнему не использовали — issues созданы через API.

Коммитов нет.

## Метрики

| | Облако run 1 | Облако run 2 | Локально 7B |
|---|---|---|---|
| Подряд без паузы | **18 / 18** | нечего гонять | **1** (docs), стоп на #3 |
| % с первого раза | 100% | — | 0% на коде |
| Среднее время | ~2 мин | — | 5–7 с на ответ, код не собирается |
| Где сломался | не сломался | — | `ilike` / `orWhere` на SQLite |

## Облако vs локальная

Облако (этот агент + `execution-loop.md`) дошло до конца пула: поиск, год/язык/обложка, каркас UI по макетам, русские строки, review. `scripts/check.sh` зелёный (15 тестов).

Локальная `qwen2.5-coder:7b` закрывает короткие docs и падает на первом баге API так же, как в дне 4: игнорирует «in memory, no LIKE».

Правила после лупа: явный запрет `ilike` и `orWhere`. На облако в run 1 это не понадобилось; на локальную — недостаточно без повторного прогона с уже зелёным эталоном.

## Для демо

1. GitLab [day-5 issues](https://git.modumuptools.com/dbondarev/bookreader/-/issues?label_name=day-5) и `pool.md`.
2. `bookreader/` — Коллекция, поиск, обложка, бейдж, изд. YYYY, шапка Авторы/Серии.
3. `run-local-issue3.md` — как 7B чинит `q`.
