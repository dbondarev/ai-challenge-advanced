# День 5. Execution loop

Исходники цикла: [`source/`](source/) (агент, профили, ТЗ, макеты PNG, CI, smoke, CLAUDE.md).

Первый пул (18 задач, без MR): [`pool.md`](pool.md), лог [`run-1.md`](run-1.md) / [`run-3.md`](run-3.md). GitLab: [#1–#18](https://git.modumuptools.com/dbondarev/bookreader/-/issues?label_name=day-5).

Полный цикл по ТЗ + макетам (MR, pipeline, smoke, ревью): [`pool-full-spec.md`](pool-full-spec.md), лог [`run-4.md`](run-4.md). GitLab issues #19–#45, MR !1–!26.

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

1. Исходники: `source/execution-loop.md`, `source/spec-library-and-reader.md`, `source/design/screens/Main.png`.
2. Лог полного цикла: `run-4.md` (стоп на #19 — `#!/bin/zsh` в CI). Время по задачам — в `run-1.md`.
3. GitLab [MR !14](https://git.modumuptools.com/dbondarev/bookreader/-/merge_requests/14) и pipeline `check`.
4. Продукт: коллекция/читалка vs макеты в `source/design/screens/`.
5. Локальная 7B: `run-local.md` / `run-local-issue3.md`.
