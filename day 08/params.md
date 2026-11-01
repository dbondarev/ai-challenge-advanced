# Day 8 launch parameters

| | |
|---|---|
| Base model | `Qwen/Qwen2.5-1.5B-Instruct` |
| Dataset | `data/train.jsonl` (815 mixed), `data/valid.jsonl` (85 enum only) |
| Method | QLoRA 4-bit NF4, double quant, compute fp16 |
| LoRA | r=16, alpha=32, dropout=0.05 |
| Max seq | 512 |
| Epochs | 10 |
| Batch | 1 x accum 8 (effective 8) |
| LR | 0.0002, cosine, warmup_steps=40 |
| Eval | every 10 steps; save every 20 |
| GPU | NVIDIA GeForce RTX 3070 |
| VRAM peak (nvidia-smi) | 2567 MiB |
| Wall-clock | 3851 s (64.2 min) |
| Started (UTC) | 2026-10-29T16:47:18.101265+00:00 |
| train_loss | 0.4188228182458118 |
| Train loss min / max | 0.0485 / 4.179489 |
| Valid loss min / max | 0.583392 / 3.405285 |
| Best valid | step 410, eval_loss=0.583392 |
| Adapter | `adapter/` = best valid step 410 eval_loss=0.583392 from checkpoint-400 |
| Last | `adapter-last/` |
