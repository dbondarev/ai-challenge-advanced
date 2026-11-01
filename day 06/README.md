# День 6. QLoRA text-to-SQL

Отчёт: [`demo.html`](demo.html). Тезис: после QLoRA 1.5B чаще выдаёт **точный SQL** (exact-match 1/10 → 6/10) и **хуже** на задачах вне SQL.

## Что в папке

| Файл | Зачем |
|---|---|
| [`demo.html`](demo.html) | Сводка: параметры запуска, 20 запросов, примеры |
| [`comparison.md`](comparison.md) | Тот же разбор текстом |
| [`params.md`](params.md) | Гиперпараметры, VRAM, время |
| [`eval/20.md`](eval/20.md) | Все 20 промптов base vs tuned |
| [`loss.csv`](loss.csv) | Loss / lr / VRAM по шагам |
| [`run-meta.json`](run-meta.json) | Стенд запуска |
| [`train.py`](train.py) | Обучение на nv307001 (transformers, не Ollama) |
| [`eval.py`](eval.py) | Прогон 20 промптов, temperature 0 |
| [`prompts.json`](prompts.json) | Stretch + OOD |
| [`prompts.resolved.json`](prompts.resolved.json) | In-domain gold с датасета |
| [`adapter/`](adapter/) | LoRA-веса |
| `eval/base/`, `eval/tuned/` | Сырые ответы |

Обучение не через Ollama дня 4.
