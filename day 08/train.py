#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""QLoRA SFT day 8: day 7 enum mix + planted facts + style, with valid loss."""

from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import torch
from datasets import load_dataset
from peft import LoraConfig, prepare_model_for_kbit_training
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainerCallback,
)

try:
    from trl import SFTConfig, SFTTrainer
except ImportError:
    from transformers import TrainingArguments as SFTConfig
    from trl import SFTTrainer

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
ADAPTER_DIR = ROOT / "adapter"
ADAPTER_LAST = ROOT / "adapter-last"
CKPT_DIR = ROOT / "checkpoints"
LOSS_CSV = ROOT / "loss.csv"
PARAMS = ROOT / "params.md"
META = ROOT / "run-meta.json"

MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
SEED = 42
MAX_LEN = 512
EPOCHS = 10
BATCH = 1
GRAD_ACCUM = 8
LR = 2e-4
LORA_R = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.05
WARMUP_STEPS = 40
EVAL_STEPS = 10
SAVE_STEPS = 20
TARGET = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]


def gpu_mem_mib() -> int | None:
    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=memory.used",
                "--format=csv,noheader,nounits",
            ],
            text=True,
        )
        return int(out.strip().splitlines()[0])
    except Exception:
        return None


def gpu_name() -> str:
    if torch.cuda.is_available():
        return torch.cuda.get_device_name(0)
    return "cpu"


def format_row(tokenizer, row: dict) -> str:
    messages = [
        {"role": "system", "content": row["system"]},
        {"role": "user", "content": row["user"]},
        {"role": "assistant", "content": row["assistant"]},
    ]
    return tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=False
    )


class LossCsvCallback(TrainerCallback):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.peak_mib = gpu_mem_mib() or 0
        self.path.write_text(
            "step,train_loss,eval_loss,learning_rate,vram_mib\n", encoding="utf-8"
        )

    def on_log(self, args, state, control, logs=None, **kwargs):
        if not logs:
            return
        if "loss" not in logs and "eval_loss" not in logs:
            return
        used = gpu_mem_mib() or 0
        self.peak_mib = max(self.peak_mib, used)
        with self.path.open("a", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(
                [
                    state.global_step,
                    f"{logs['loss']:.6f}" if "loss" in logs else "",
                    f"{logs['eval_loss']:.6f}" if "eval_loss" in logs else "",
                    f"{logs.get('learning_rate', '')}",
                    used,
                ]
            )


def pick_best_checkpoint() -> tuple[int | None, float | None, Path | None]:
    rows = []
    if LOSS_CSV.exists():
        with LOSS_CSV.open(encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if row.get("eval_loss"):
                    try:
                        rows.append((int(row["step"]), float(row["eval_loss"])))
                    except ValueError:
                        pass
    if not rows:
        return None, None, None
    step, loss = min(rows, key=lambda x: x[1])
    ckpts = []
    if CKPT_DIR.exists():
        for p in CKPT_DIR.iterdir():
            if p.is_dir() and p.name.startswith("checkpoint-"):
                try:
                    ckpts.append((int(p.name.split("-")[1]), p))
                except ValueError:
                    pass
    ckpts.sort()
    chosen = None
    for s, p in ckpts:
        if s <= step:
            chosen = p
        else:
            break
    if chosen is None and ckpts:
        chosen = min(ckpts, key=lambda x: abs(x[0] - step))[1]
    return step, loss, chosen


def copy_adapter(src: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)
    for name in (
        "adapter_config.json",
        "adapter_model.safetensors",
        "README.md",
        "tokenizer.json",
        "tokenizer_config.json",
        "chat_template.jinja",
        "special_tokens_map.json",
    ):
        p = src / name
        if p.exists():
            shutil.copy2(p, dest / name)


def main() -> None:
    if not torch.cuda.is_available():
        raise SystemExit("CUDA required for QLoRA on this script")
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True

    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    ADAPTER_DIR.mkdir(parents=True, exist_ok=True)
    ADAPTER_LAST.mkdir(parents=True, exist_ok=True)
    CKPT_DIR.mkdir(parents=True, exist_ok=True)

    started = time.time()
    started_iso = datetime.now(timezone.utc).isoformat()

    tokenizer = AutoTokenizer.from_pretrained(MODEL, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    train_raw = load_dataset("json", data_files=str(DATA / "train.jsonl"), split="train")
    val_raw = load_dataset("json", data_files=str(DATA / "valid.jsonl"), split="train")

    def add_text(batch):
        n = len(batch["id"])
        rows = [
            {
                "system": batch["system"][i],
                "user": batch["user"][i],
                "assistant": batch["assistant"][i],
            }
            for i in range(n)
        ]
        return {"text": [format_row(tokenizer, r) for r in rows]}

    train_ds = train_raw.map(add_text, batched=True, remove_columns=train_raw.column_names)
    val_ds = val_raw.map(add_text, batched=True, remove_columns=val_raw.column_names)

    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )
    model = AutoModelForCausalLM.from_pretrained(
        MODEL,
        quantization_config=bnb,
        device_map="auto",
        torch_dtype=torch.float16,
        trust_remote_code=True,
    )
    model.config.use_cache = False
    model.config.dtype = torch.float16
    model = prepare_model_for_kbit_training(model)

    peft_config = LoraConfig(
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        target_modules=TARGET,
        bias="none",
        task_type="CAUSAL_LM",
    )

    loss_cb = LossCsvCallback(LOSS_CSV)
    common = dict(
        output_dir=str(CKPT_DIR),
        per_device_train_batch_size=BATCH,
        per_device_eval_batch_size=BATCH,
        gradient_accumulation_steps=GRAD_ACCUM,
        learning_rate=LR,
        num_train_epochs=EPOCHS,
        logging_steps=1,
        fp16=False,
        bf16=False,
        gradient_checkpointing=True,
        lr_scheduler_type="cosine",
        warmup_steps=WARMUP_STEPS,
        report_to="none",
        optim="paged_adamw_32bit",
        seed=SEED,
        max_grad_norm=1.0,
        load_best_model_at_end=False,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
    )

    def make_args(**extra):
        merged = dict(common)
        merged.update(extra)
        try:
            return SFTConfig(
                **merged,
                max_length=MAX_LEN,
                dataset_text_field="text",
                packing=False,
            )
        except TypeError:
            try:
                return SFTConfig(**merged)
            except TypeError as exc:
                raise exc

    try:
        args = make_args(
            eval_strategy="steps",
            eval_steps=EVAL_STEPS,
            save_strategy="steps",
            save_steps=SAVE_STEPS,
        )
    except TypeError:
        args = make_args(
            evaluation_strategy="steps",
            eval_steps=EVAL_STEPS,
            save_strategy="steps",
            save_steps=SAVE_STEPS,
        )

    trainer_kwargs = dict(
        model=model,
        args=args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        peft_config=peft_config,
        callbacks=[loss_cb],
    )
    try:
        trainer = SFTTrainer(
            **trainer_kwargs,
            processing_class=tokenizer,
        )
    except TypeError:
        try:
            trainer = SFTTrainer(
                **trainer_kwargs,
                tokenizer=tokenizer,
                dataset_text_field="text",
                max_seq_length=MAX_LEN,
            )
        except TypeError:
            trainer = SFTTrainer(**trainer_kwargs, tokenizer=tokenizer)

    train_result = trainer.train()
    trainer.model.save_pretrained(ADAPTER_LAST)
    tokenizer.save_pretrained(ADAPTER_LAST)

    best_step, best_eval, best_ckpt = pick_best_checkpoint()
    if best_ckpt is not None:
        copy_adapter(best_ckpt, ADAPTER_DIR)
        tokenizer.save_pretrained(ADAPTER_DIR)
        adapter_note = f"best valid step {best_step} eval_loss={best_eval} from {best_ckpt.name}"
    else:
        copy_adapter(ADAPTER_LAST, ADAPTER_DIR)
        adapter_note = "no eval_loss logged; adapter/ is last"

    elapsed = time.time() - started
    peak = loss_cb.peak_mib
    metrics = train_result.metrics if train_result else {}
    final_loss = metrics.get("train_loss")

    train_losses = []
    eval_losses = []
    if LOSS_CSV.exists():
        with LOSS_CSV.open(encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if row.get("train_loss"):
                    try:
                        train_losses.append(float(row["train_loss"]))
                    except ValueError:
                        pass
                if row.get("eval_loss"):
                    try:
                        eval_losses.append(float(row["eval_loss"]))
                    except ValueError:
                        pass

    params = f"""# Day 8 launch parameters

| | |
|---|---|
| Base model | `{MODEL}` |
| Dataset | `data/train.jsonl` ({len(train_raw)} mixed), `data/valid.jsonl` ({len(val_raw)} enum only) |
| Method | QLoRA 4-bit NF4, double quant, compute fp16 |
| LoRA | r={LORA_R}, alpha={LORA_ALPHA}, dropout={LORA_DROPOUT} |
| Max seq | {MAX_LEN} |
| Epochs | {EPOCHS} |
| Batch | {BATCH} x accum {GRAD_ACCUM} (effective {BATCH * GRAD_ACCUM}) |
| LR | {LR}, cosine, warmup_steps={WARMUP_STEPS} |
| Eval | every {EVAL_STEPS} steps; save every {SAVE_STEPS} |
| GPU | {gpu_name()} |
| VRAM peak (nvidia-smi) | {peak} MiB |
| Wall-clock | {elapsed:.0f} s ({elapsed / 60:.1f} min) |
| Started (UTC) | {started_iso} |
| train_loss | {final_loss} |
| Train loss min / max | {min(train_losses) if train_losses else "n/a"} / {max(train_losses) if train_losses else "n/a"} |
| Valid loss min / max | {min(eval_losses) if eval_losses else "n/a"} / {max(eval_losses) if eval_losses else "n/a"} |
| Best valid | step {best_step}, eval_loss={best_eval} |
| Adapter | `adapter/` = {adapter_note} |
| Last | `adapter-last/` |
"""
    PARAMS.write_text(params, encoding="utf-8")
    META.write_text(
        json.dumps(
            {
                "model": MODEL,
                "train_n": len(train_raw),
                "val_n": len(val_raw),
                "seed": SEED,
                "epochs": EPOCHS,
                "elapsed_s": elapsed,
                "peak_vram_mib": peak,
                "gpu": gpu_name(),
                "train_loss": final_loss,
                "best_valid_step": best_step,
                "best_valid_loss": best_eval,
                "best_ckpt": str(best_ckpt) if best_ckpt else None,
                "metrics": {
                    k: (float(v) if isinstance(v, (int, float)) else str(v))
                    for k, v in metrics.items()
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(params)


if __name__ == "__main__":
    main()
