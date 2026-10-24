# День 4. Local Boost — настройка

GPU: nv307001, RTX 3070 8 GB, Ollama `http://100.82.92.14:11434` (NetBird).
IDE: Continue.dev v2.0.0 в Cursor. Нативный Override OpenAI Base URL не использовали: облако Cursor не видит NetBird, Tab всё равно облачный.

Конфиг: `bookreader/.continue/config.yaml` (копия здесь: `continue-config.yaml`). Правила дня 1 — `CLAUDE.md` в `chatOptions.baseSystemMessage` и в `.continue/rules/bookreader.md`.

После установки расширения перезагрузить окно Cursor. В панели Continue выбрать Qwen2.5 Coder 7B для чата; автокомплит — Qwen2.5 Coder 1.5B.

Прогоны: `run_local.py` → Ollama `/api/chat` с тем же system prompt. Изоляты в `runs/` (без `node_modules`). Продукт `bookreader/` не переписывался.
