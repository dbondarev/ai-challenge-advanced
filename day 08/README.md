# День 8. Границы файнтюнинга

Отчёт: [`demo.html`](demo.html). Тезис: тюн чинит **формат и тон**; **факты** дешевле в промпте (12/12 vs 9/12). Переобучение с шага 410.

## Что в папке

| Файл | Зачем |
|---|---|
| [`demo.html`](demo.html) | Сводка: факты, OOD, лосс, три типа задач |
| [`comparison.md`](comparison.md) | Тот же разбор текстом |
| [`eval/scores.md`](eval/scores.md) | Hits по format / facts / style / OOD |
| [`eval/loss.md`](eval/loss.md) | Train vs valid |
| [`params.md`](params.md) | Запуск, 10 эпох, best 410 |
| [`eval/enum-rescore.md`](eval/enum-rescore.md) | Enum на новом gold без ретрейна |
| [`adapter/`](adapter/) | Best valid |
| [`adapter-last/`](adapter-last/) | Конец 10 эпохи |
| `data/` | Смесь и probes (в gitignore) |

Адаптер дня 7 не меняли. На reply-status в сервисе — он, не эта смесь.
