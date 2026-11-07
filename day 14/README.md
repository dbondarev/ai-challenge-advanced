# День 14. Security step

Отчёт: [`demo.html`](demo.html). Короткий цикл для Node: генерация, `node --test`, security review, локальный коммит. Все вызовы модели идут через прокси дня 13 на `qwen2.5-coder:7b`. Bookreader не менялся.

```
python3 loop.py
```

## Что в папке

| Файл | Зачем |
|---|---|
| [`demo.html`](demo.html) | Три задачи: security, gateway, пропуск |
| [`comparison.md`](comparison.md) | Разбор кода и вердиктов |
| [`loop.py`](loop.py) | Цикл и security-промпт под Node |
| [`sandbox/`](sandbox/) | Отдельный git, два коммита |
| [`logs/audit.jsonl`](logs/audit.jsonl) | 9 allowed, 1 blocked |
| [`eval/tasks.json`](eval/tasks.json) | Сырой прогон |
| [`eval/demo.png`](eval/demo.png) | Снимок отчёта |
