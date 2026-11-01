# Baseline

Run 2026-10-29 on nv307001, `Qwen/Qwen2.5-1.5B-Instruct`, temperature 0, `max_new_tokens=8`.
Script: `python data/baseline.py data/eval.jsonl > data/baseline.json`.

| Mode | Accuracy |
|---|---|
| no system | 0/68 = 0.000 |
| with system | 34/68 = 0.500 |

Without `system` the base model never emits a label: it writes email-style drafts (`Subject: ...`). With the task `system` it always answers in the enum, but often confuses `mql` with `sql`.

Five `with_system` errors from `baseline.json`:

| id | gold | pred | raw |
|---|---|---|---|
| ev-001 | mql | sql | `sql` |
| ev-003 | not_ta, mql | sql | `sql` |
| ev-007 | mql | sql | `sql` |
| ev-009 | mql | sql | `sql` |
| ev-012 | mql | meeting_held | `meeting_held` |

Reference point (not this model): on the same 68 replies, the prod labeler gpt-5.6-luna with the full v2 prompt agreed with the manual gold about as well as the old prompt (see the Nexus eval, 2026-10-28).
