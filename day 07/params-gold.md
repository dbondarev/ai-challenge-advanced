# gold launch parameters (rerun)

| | |
|---|---|
| Base model | `Qwen/Qwen2.5-1.5B-Instruct` |
| Train file | `data/train.jsonl` (671 after sql x3) |
| Valid | `/home/cursor/day07-rerun/data/valid.jsonl` (85) |
| Epochs | 5 |
| Best valid acc | 0.659 at epoch 5 |
| LoRA | r=16 alpha=32 |
| GPU | NVIDIA GeForce RTX 3070 |
| VRAM peak | 2569 MiB |
| Wall-clock | 1375 s (22.9 min) |
| Started (UTC) | 2026-10-29T22:28:28.003802+00:00 |
| train_loss | 0.7196210600790524 |
| Adapter | `adapter-gold` |
