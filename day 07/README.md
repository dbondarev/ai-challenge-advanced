# День 7. Свой датасет, reply-status

Отчёт: [`demo.html`](demo.html). Тезис: на согласованном gold 1.5B с промптом даёт **46%** на eval / **16%** на eval2; QLoRA — **79%** и **65%**.

Сначала eval с эталоном и два прогона базы (без system и с system). Потом train/valid из Nexus, формат дня 6, без утечки eval в train.

## Что в папке

| Файл | Зачем |
|---|---|
| [`demo.html`](demo.html) | Сводка: датасет, baseline, тюн |
| [`comparison.md`](comparison.md) | Rerun текстом |
| [`data/task.md`](data/task.md) | Задача, enum, метрика |
| [`data/stats.md`](data/stats.md) | Сплиты, leak, разметка |
| [`data/RERUN.md`](data/RERUN.md) | Что изменилось после run1 |
| [`eval/scores-rerun.md`](eval/scores-rerun.md) | Таблицы hits |
| [`params-gold.md`](params-gold.md) | Запуск rerun |
| [`train.py`](train.py) / [`eval.py`](eval.py) | Обучение и скоринг |
| [`data/train.jsonl`](data/train.jsonl) | 623 примера |
| [`adapter/`](adapter/) | LoRA gold, эпоха 5 |

Run1 (старый gold, 69%) — [`comparison-run1.md`](comparison-run1.md), не смешивать с rerun.
