# День 7. QLoRA на своём датасете (Nexus reply-status)

Тезис: 1.5B без system **не попадает в enum вообще**. С тем же system prompt, что в train, base даёт **50%**; после QLoRA на 623 своих примерах — **69%**. Главный выигрыш: email в ответе это `mql`, не `sql`.

Датасет: [`data/`](data/) (task / stats / eval.jsonl). Параметры: [`params.md`](params.md). Baseline до тюнинга: [`data/baseline.md`](data/baseline.md). Таблица 68: [`eval/68.md`](eval/68.md). Адаптер: [`adapter/`](adapter/).

## nv307001

SSH `nv307001` (100.82.92.14) жив. RTX 3070 8 GB idle 13 MiB, CUDA True, venv дня 6 (`torch 2.6.0+cu124`). Ходить руками не нужно было.

## Датасет

| Split | N | Откуда |
|---|---|---|
| train | 623 | 12 проектов Nexus, не 98; v2 + judge + human |
| valid | 85 | то же |
| eval | 68 | проект 98, ручной gold |

Задача: одно слово `no_change|rejection|not_ta|positive|mql|sql|meeting_held` по последнему `IN (last)`. Метрика: `normalize(pred) in gold_key`.

`meeting_held` в train = 0. `sql` редко (24 train).

## Eval-first (до тюнинга)

`Qwen/Qwen2.5-1.5B-Instruct`, temperature 0, 8 новых токенов.

| Режим | Hits | Accuracy |
|---|---|---|
| без system | 0/68 | 0.000 |
| с system из `task.md` | 34/68 | 0.500 |
| QLoRA + system | 47/68 | **0.691** |

Без system модель пишет черновик письма (`Subject: Exclusive Sneakers...`). С system оба режима отвечают одним словом из enum.

## Запуск

| | |
|---|---|
| База | `Qwen/Qwen2.5-1.5B-Instruct` |
| Метод | QLoRA 4-bit NF4, LoRA r=16 alpha=32, 3 эпохи, 234 шага |
| GPU | nv307001, RTX 3070 |
| VRAM peak | 2569 MiB |
| Время | 12.0 мин, train_loss 1.07 |
| Loss | 4.02 ? 0.30 |

Тот же venv, что день 6. `fp16=False` (иначе AMP на 3070 падает, как в дне 6).

## Где тюнинг лучше

Prompt-only часто ставит `sql` на любой контакт. Тюнинг выучил правило «свой email ? mql».

**ev-001** gold `mql` (INES прислала свой email):

- без system: `Subject: Exclusive Sneakers Collection - Join`
- prompt: `sql`
- tuned: `mql`

По kind: `contact_shared` 20/47 ? **37/47**. По классу `mql` 13/32 ? **25/32**.

22 ошибки prompt-only исправлены, 9 регрессий, 12 так и не взяты.

## Где хуже / не выучилось

- `multi_turn` 4/4 ? 1/4: входящий питч проспекта (`ev-010`, `ev-011`) gold `no_change`, tuned ставит `mql`.
- `sql` 0/3 ? 1/3: мало train, путает с `mql` / `no_change`.
- `positive` 0/2 в обоих режимах.
- `meeting_held` в train нет — класс модель не видела.

## Что показать

1. `nvidia-smi` на nv307001: GPU свободен, потом VRAM ~2.5 GB.
2. `data/baseline.md`: 0% vs 50% до тюнинга.
3. ev-001: письмо / `sql` / `mql`.
4. `eval/scores.md`: 34/68 ? 47/68.
5. Оговорка: `meeting_held` не выучить, 9 регрессий на `no_change`.
