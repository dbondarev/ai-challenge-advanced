# День 12. Indirect prompt injection

Отчёт: [`demo.html`](demo.html). Локальная Ollama `qwen2.5:7b` на nv307001. Прод Nexus не вызывался.

## Что в папке

| Файл | Зачем |
|---|---|
| [`demo.html`](demo.html) | Сводка: три вектора, ответы, что устояло |
| [`comparison.md`](comparison.md) | Сырой прогон против одного защитного слоя |
| [`cases.md`](cases.md) | Bing, Bard, Copilot и что из этого повторили |
| [`attack.py`](attack.py) | Ловушки, sanitizer, граница, проверка выхода |
| [`eval/`](eval/) | Ответы `raw.json`, `defended.json` и снимок `demo.png` |
