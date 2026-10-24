# Run local — qwen2.5-coder:7b on nv307001

Same pool texts. Continue/Ollama, CLAUDE.md as system, temperature 0.2, num_ctx 8192. No GitLab tools.

| # | Issue | Result | Time | Why |
|---|---|---|---|---|
| 1 | README links | pass (docs) | 4.5 s | Added spec/design links |
| 3 | GET /books?q= | **fail** | 6.5 s | `ilike` + `orWhere` + `JSON.parse(q)` — not in-memory author filter. Would not typecheck |

Streak: **1** (docs only). Broke on first code bug (#3). First-try code: **0%**.
Raw: `run-local-issue3.md`, `run-local-raw.md`.
