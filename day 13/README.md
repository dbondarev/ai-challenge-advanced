# День 13. LLM gateway

Отчёт: [`demo.html`](demo.html). Прокси на stdlib перед локальной Ollama `qwen2.5:7b`. OpenAI и Anthropic не вызываются.

```
python3 gateway.py
```

`POST /v1/chat/completions`. Секрет во входе — `400`, в модель ничего не уходит. Заголовок `X-Guard-Mode: redact` маскирует и пропускает. Лимит — 30 запросов в минуту с одного IP.

## Что в папке

| Файл | Зачем |
|---|---|
| [`demo.html`](demo.html) | Сводка тестов и боевого вызова |
| [`comparison.md`](comparison.md) | 13 кейсов: что поймали и что пропустили |
| [`gateway.py`](gateway.py) | HTTP-прокси, лимит, стоимость |
| [`guards.py`](guards.py) | Сканер входа и выхода |
| [`test_guards.py`](test_guards.py) | 13 тестов на сокете, апстрим — заглушка |
| [`live_check.py`](live_check.py) | Один чистый вызов на nv |
| [`logs/audit.jsonl`](logs/audit.jsonl) | Аудит без сырых секретов |
| [`eval/live.json`](eval/live.json) | Ответ `pong` и стоимость |
| [`eval/demo.png`](eval/demo.png) | Снимок отчёта |
