# День 14. Security step

Отчёт: [`demo.html`](demo.html). Короткий цикл для Node: генерация, `node --test`, LLM review (fail-closed), `static_findings`, локальный коммит. Все вызовы модели идут через прокси дня 13 на `qwen2.5-coder:7b`. Bookreader не менялся.

```
python3 loop.py
```

## Что в папке

| Файл | Зачем |
|---|---|
| [`demo.html`](demo.html) | Три задачи: security, gateway, пропуск |
| [`comparison.md`](comparison.md) | Разбор кода и вердиктов |
| [`loop.py`](loop.py) | Цикл, review, static gate |
| [`sandbox/`](sandbox/) | Отдельный git; коммит только токена |
| [`logs/audit.jsonl`](logs/audit.jsonl) | 12 allowed, 1 blocked |
| [`eval/tasks.json`](eval/tasks.json) | Сырой прогон |
| [`eval/demo.png`](eval/demo.png) | Снимок отчёта |
