# День 10. Железо: merge, 4-bit, GGUF

Прод не трогали. Кандидат — gold-адаптер дня 7 (`~/day07-rerun/adapter-gold` на nv307001, 79% eval / 65% eval2), не смесь дня 8 и не opus дня 9.

Веса **не** в git. Артефакты только на nv307001 (`100.82.92.14`).

## Что получилось

| Артефакт | Путь на nv307001 | Диск |
|---|---|---|
| QLoRA adapter (gold) | `~/day07-rerun/adapter-gold` | 46 MB |
| Merged fp16 (`merge_and_unload`) | `~/day10-serve/merged-fp16` | 2955 MB |
| GGUF F16 | `~/day10-serve/qwen25-1.5b-reply-status-f16.gguf` | 2.9 GB |
| GGUF Q4_K_M | `~/day10-serve/qwen25-1.5b-reply-status-q4_k_m.gguf` | 941 MB |
| Ollama tag | `nexus-reply-status:latest` на `:11434` | слой ≈ 941 MB |

Merge in-memory: 0.04 с. Запись merged на диск: 3.7 с.

GGUF: `convert_hf_to_gguf.py` из llama.cpp на хосте (venv дня 6), квант `Q4_K_M` через `ghcr.io/ggml-org/llama.cpp:full`, затем `ollama create nexus-reply-status`. Ollama 0.34.2 сам safetensors→GGUF уже не конвертирует — нужен llama.cpp.

OpenAI-совместимый endpoint уже есть: `http://100.82.92.14:11434/v1` (слушает `*:11434`, рядом с моделями дня 4). Модель `nexus-reply-status`. Отдельный тонкий сервер на PEFT не понадобился.

## Latency на eval.jsonl (68), nv307001 RTX 3070 8 GB

Temperature 0, max_new_tokens 8, короткий system дня 7. Сырые цифры: [`eval/bench68.json`](eval/bench68.json). На 20 строках те же порядки ([`eval/bench.json`](eval/bench.json)).

| Режим | Загрузка, с | Peak VRAM | мс/запрос | Диск |
|---|---:|---:|---:|---:|
| 1.5B база fp16 | 1.0 | 3229 MiB | 88 | HF cache |
| PEFT adapter на fp16 базе | 1.4 | 3339 MiB | 156 | 46 MB |
| Merged fp16 | 1.9 | 3229 MiB | 91 | 2955 MB |
| 4-bit NF4 + adapter (как train) | 1.9 | 3301 MiB | 205 | 46 MB |
| **Ollama Q4_K_M `nexus-reply-status`** | **1.8** (холодный 1-й запрос) | **1265 MiB** | **66** | **941 MB** |

Вывод для сервиса: в проде держать **Ollama Q4_K_M**. Merged fp16 быстрее PEFT, но жрёт ~3.2 GB. NF4+adapter на этой карте **медленнее** fp16 (оверхед generate), VRAM почти не экономит, потому что 1.5B и так влезает. Q4_K_M: меньше диск и VRAM, быстрее запрос.

На shadow (374 inbound) PEFT дал ~142 мс/запрос (53 с на tuned) — согласуется с 156 мс на eval.

Скрипты: [`merge_bench.py`](merge_bench.py), [`bench_68.py`](bench_68.py). Modelfile: [`Modelfile`](Modelfile).
