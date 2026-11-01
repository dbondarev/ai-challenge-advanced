# День 9. Дистилляция opus → 1.5B

Отчёт: [`demo.html`](demo.html). Тезис: сильная модель размечает, 1.5B учится. Eval **52/68 (76.5%)** при учителе 85% и gold-SFT дня 7 79%. Онлайн учитель не нужен.

Run1 (7B, фильтр 232, +1 пример) — [`comparison-run1.md`](comparison-run1.md), не смешивать с rerun.

## Что в папке

| Файл | Зачем |
|---|---|
| [`demo.html`](demo.html) | Процесс, данные, качество vs экономия |
| [`comparison.md`](comparison.md) | Rerun текстом |
| [`params-opus.md`](params-opus.md) | Запуск ученика |
| [`adapter/`](adapter/) | LoRA opus, эпоха 4 |
| [`data/distill.jsonl`](data/distill.jsonl) | Run1, 232 строки |
| Метки учителя | `../day 07/data/teacher_opus_train.jsonl` |
