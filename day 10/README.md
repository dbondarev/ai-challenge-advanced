# День 10. Тюн в сервисе (shadow)

Отчёт: [`demo.html`](demo.html). Gold дня 7 стоит на nv307001 как `nexus-reply-status` (Ollama `/v1`) **параллельно для тестов**. Luna пишет прод-метки. Shadow: база 24% → QLoRA **62%** vs luna на 334 входящих за ~2 дня.

## Что в папке

| Файл | Зачем |
|---|---|
| [`demo.html`](demo.html) | Сводка: сервинг, bench, shadow |
| [`shadow.md`](shadow.md) | Классы, проекты, расхождения |
| [`comparison.md`](comparison.md) | eval / eval2 / shadow |
| [`bench.md`](bench.md) | VRAM, мс/запрос, GGUF |
| [`rollout.md`](rollout.md) | Как включить local и откатить |
| [`eval/shadow.json`](eval/shadow.json) | Агрегаты без PII |
