# Day 6 launch parameters

| | |
|---|---|
| Base model | `Qwen/Qwen2.5-1.5B-Instruct` |
| Dataset | `b-mc2/sql-create-context` train split, shuffle seed 42 |
| Slice | first 8000 train, next 1000 val; eval in-domain uses rows 9000-9009 |
| Method | QLoRA 4-bit NF4, double quant, compute fp16 |
| LoRA | r=16, alpha=32, dropout=0.05, modules `q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj` |
| Max seq | 512 |
| Epochs | 1 |
| Batch | 1 x accum 8 (effective 8) |
| LR | 0.0002, cosine, warmup_steps=50 |
| Optimizer | paged_adamw_32bit |
| GPU | NVIDIA GeForce RTX 3070 |
| VRAM peak (nvidia-smi) | 2565 MiB |
| Wall-clock | 2864 s (47.7 min) |
| Started (UTC) | 2026-10-26T14:32:51.447341+00:00 |
| Train steps / loss | 2855.5333 runtime; train_loss=0.7246481810212135 |
| Loss CSV min / max | 0.47803 / 3.169441 |
| Adapter | `adapter/` |

Chat template: Qwen ChatML. System: `You write SQLite. Reply with one SQL statement only.`

## Notes

RTX 3070 rejected `fp16=True` (`_amp_foreach_non_finite_check_and_unscale_cuda` not implemented for BFloat16). Training used 4-bit NF4 weights and **no mixed-precision GradScaler** (`fp16=False`). LoRA compute stayed on GPU at 2565 MiB peak.
