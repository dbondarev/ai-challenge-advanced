# opus launch parameters (rerun)

| | |
|---|---|
| Base model | `Qwen/Qwen2.5-1.5B-Instruct` |
| Train file | `data/teacher_opus_train.jsonl` (671 after sql x3) |
| Valid | `/home/cursor/day07-rerun/data/valid.jsonl` (85) |
| Epochs | 5 |
| Best valid acc | 0.682 at epoch 4 |
| LoRA | r=16 alpha=32 |
| GPU | NVIDIA GeForce RTX 3070 |
| VRAM peak | 2569 MiB |
| Wall-clock | 1356 s (22.6 min) |
| Started (UTC) | 2026-10-29T22:51:28.251999+00:00 |
| train_loss | 0.7203182317316532 |
| Adapter | `adapter-opus` |
