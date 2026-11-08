# День 11. Prompt injection

Отчёт: [`demo.html`](demo.html). Цель — локальная Ollama `nexus-reply-status` на nv307001. Прод Nexus не вызывался. System v1 — строка классификатора из дня 7.

## Что в папке

| Файл | Зачем |
|---|---|
| [`demo.html`](demo.html) | Сводка: параметры, атаки, ответы v1/v2 |
| [`comparison.md`](comparison.md) | Что пробило формат и что стало с меткой |
| [`collection.md`](collection.md) | 5 публичных инъекций и как их глушить |
| [`prompt-v1.md`](prompt-v1.md) | System дня 7 |
| [`prompt-v2.md`](prompt-v2.md) | Усиленный system |
| [`attack.py`](attack.py) | Прогон `python3 attack.py v1` или `v2`; пост-фильтр enum |
| [`eval/`](eval/) | Сырые ответы и снимок отчёта `demo.png` |
