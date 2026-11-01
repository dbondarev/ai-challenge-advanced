# День 6. QLoRA text-to-SQL на 1.5B

Тезис: после QLoRA маленькая instruct-модель чаще выдаёт **точный SQL**; на задачах вне SQL (ревью Bookreader, связный список) она **хуже базы**.

Полный лог 20 запросов: [`eval/20.md`](eval/20.md). Параметры запуска: [`params.md`](params.md). Адаптер: [`adapter/`](adapter/).

## Запуск

| | |
|---|---|
| База | `Qwen/Qwen2.5-1.5B-Instruct` |
| Датасет | `b-mc2/sql-create-context`, shuffle seed 42, 8k train / 1k val |
| Метод | QLoRA 4-bit NF4, LoRA r=16 alpha=32 |
| GPU | nv307001, RTX 3070 8 GB |
| VRAM peak | 2565 MiB |
| Время | 47.7 мин, 1000 шагов, train_loss 0.72 |
| Loss | 3.17 -> 0.59 (min 0.48) |

Обучение: `train.py` на хосте `nv307001` (не Ollama).

## In-domain (10 held-out)

Exact-match после нормализации пробелов/кавычек: **1/10 база, 6/10 тюнинг**.

Оба уже пишут SQL без «Sure, here is», если включён system prompt «one SQL statement only». Разница не в жанре, а в совпадении с gold.

### Пример лучше: in07 / in09 / in10

Тюнинг попадает в gold. База близко, но кавычки/формат не те.

### Пример хуже: in03

Вопрос: значение `length_feet` при фильтрах.

- База: `SELECT length_feet FROM ...` (смысл верный, обёрнут в markdown).
- Тюнинг: `SELECT COUNT(length_feet) FROM ...` — другая семантика.

## Stretch

Русский вопрос про отдел продаж (st01): оба дают `COUNT(*) ... department = Sales`. Тюнинг не развалился.

Нет колонки salary (st02): **оба выдумывают `AVG(salary)`**. Тюнинг пишет `FROM people` (колонки в схеме нет). Формат выучился, заземление — нет.

## Где тюнинг хуже (OOD)

System prompt SQL на эти 5 запросов **не вешали**. Модель не начала отвечать `SELECT` на «2+2» и хайку.

| id | База | Тюнинг |
|---|---|---|
| ood01 ревью ReaderPage | форма Critical / Should fix, хотя советы слабые | хвалит `any`, не видит global `localStorage.progress` |
| ood02 GET /books?q= | выдумывает жанры API | явно разрешает LIKE по JSON authors |
| ood03 2+2 | 4 | 4 |
| ood04 хайку | три строки про дождь | две строки про дождь |
| ood05 reverse linked list | разворот указателей in-place | копирует значения в list, O(n) память |

Для демо достаточно **in-domain exact-match 1 vs 6** и **ood01 + ood05**.

## Что показать

1. `params.md` + кусок `loss.csv` (старт ~3.0, финиш ~0.59).
2. `eval/20.md` таблица.
3. Пара in04/in05: база почти SQL, тюнинг = gold.
4. ood01: ревью деградировало.
