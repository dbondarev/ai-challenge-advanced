# День 10. Как включить тюн в проде (текст, без патча Nexus)

Этот день **не** меняет прод, флаги проектов и репозиторий Nexus. Ниже — как это сделали бы.

## Артефакт (не в git)

Хост nv307001, `100.82.92.14`, Ollama уже с дня 4 на `:11434`.

| Что | Где |
|---|---|
| Модель для воркера | Ollama tag **`nexus-reply-status`** (`Q4_K_M`, 941 MB) |
| GGUF | `/home/cursor/day10-serve/qwen25-1.5b-reply-status-q4_k_m.gguf` |
| Merged fp16 (запас) | `/home/cursor/day10-serve/merged-fp16` |
| Adapter | `/home/cursor/day07-rerun/adapter-gold` |
| Modelfile | `/home/cursor/day10-serve/Modelfile` (`PARAMETER temperature 0`) |

Проверка с любой машины в NetBird:

```
curl -sS http://100.82.92.14:11434/v1/models
# OpenAI SDK: base_url=http://100.82.92.14:11434/v1, model=nexus-reply-status, api_key=ollama
```

Пересоздать тег (если GGUF на месте):

```
ollama create nexus-reply-status -f /home/cursor/day10-serve/Modelfile
```

## Preflight (не выкатывать, пока не зелёное)

1. [`day 07/comparison.md`](../day%2007/comparison.md): eval **≥ 79%** (54/68), eval2 **≥ 65%** (97/149) — уже есть на gold-адаптере.
2. Этот shadow: agreement с luna на свежем окне. Сейчас **62% (207/334)**. Для среза статуса в проде держать порог **≥ 80%** vs luna **и** ручную выборку расхождений (хотя бы 30: `not_ta`/`rejection`/`mql`/`no_change`). 62% порог не проходит.
3. Bench: Q4_K_M грузится, VRAM < 2 GB, p95 не деградирует очередь `nexus.outreach.reply_status_label`.
4. Честная схема: 1.5B = одно слово enum. **Не** подставлять её вместо luna на весь v2 JSON (next_step, referral, facts). Либо гибрид, либо сначала дистилляция схемы.

Пока preflight красный — только shadow (как этот день) или отдельный лог предсказаний рядом с продом.

## Переключение без переката всего Nexus

Сейчас провайдер читается **один раз при старте процесса**: `settings = Settings()` в `apps/api/app/config.py`, `reply_status_provider()` смотрит `settings.reply_status_llm_provider` (`openai` | `gemini`). Воркер: контейнер `nexus-outreach-reply-status-label-worker` (`deploy/docker-compose.yml`), API при этом не пересобирают.

Два уровня «без recast всего сервиса»:

### A. Как есть сегодня — рестарт только label-worker

Поменять env у воркера (GitLab / compose), **не** трогая api/frontend:

```
REPLY_STATUS_LLM_PROVIDER=openai   # пока единственные рабочие значения: openai | gemini
OPENAI_REPLY_STATUS_MODEL=gpt-5.6-luna
```

Рестарт: контейнер `outreach-reply-status-label-worker`. Остальной Nexus живой. Откат — вернуть те же две переменные и снова рестарт воркера.

`local` **ещё нет в коде**. Чтобы A заработало на Ollama, нужен маленький патч (не в этом дне):

- `reply_status_provider()`: допустимо `openai | gemini | local`.
- `local`: `OpenAI(base_url="http://100.82.92.14:11434/v1", api_key="ollama")`, модель `nexus-reply-status`, **без** `json_schema` — одно слово, затем тот же coerce статуса, что после luna (или гибрид: статус локально, JSON по-прежнему luna).
- Env воркера, например:

```
REPLY_STATUS_LLM_PROVIDER=local
OPENAI_REPLY_STATUS_MODEL=nexus-reply-status
REPLY_STATUS_LOCAL_BASE_URL=http://100.82.92.14:11434/v1
```

Рестарт снова только label-worker. API не выкатывать.

### B. Как просили в задании — читать провайдер на каждый job

`Settings()` кэширует env. Чтобы переключать **без** рестарта воркера: в `process_reply_status_label` / `reply_status_provider()` читать файл env или поле `project_outreach_settings` на каждый job (`os.getenv` заново, не модульный singleton). Значения те же: `openai` | `gemini` | `local`. Это тоже патч Nexus, не сегодня.

Пока B нет — путь A (рестарт одного воркера) уже не перекатывает API.

## Откат

1. Env воркера: `REPLY_STATUS_LLM_PROVIDER=openai`, `OPENAI_REPLY_STATUS_MODEL=gpt-5.6-luna`. Рестарт label-worker.
2. Если уже записали плохие авто-метки: существующий `--reclassify` из `nexus/docs/60-as-built/outreach/REPLY_STATUS_AUTO_LABEL.md`:

```
python -m app.scripts.backfill_reply_status_labels --all-enabled --since-days 7 --reclassify
```

`--reclassify` снимает неподтверждённые `suggested_by` `openai`/`gemini` в окне и пересчитывает. После появления `local` в тот же список suggested_by нужно добавить `local`, иначе откат меток его не почистит — это часть будущего патча.

Ollama/GGUF на nv307001 можно оставить: на воркер не влияет, пока provider не `local`.

## Что сознательно не делали в дне 10

- Запись в прод и смена `reply_status_auto_label_enabled`.
- Патч `outreach_reply_status_llm.py` / compose / GitLab.
- Мерж в репозиторий Nexus.
- Подмена всего v2 JSON на 1.5B.
