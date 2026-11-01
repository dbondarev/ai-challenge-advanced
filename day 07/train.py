#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Day 7/9 QLoRA: sql oversample, save each epoch, keep best valid accuracy."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import torch
from datasets import Dataset
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
MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
SEED = 42
MAX_LEN = 512
EPOCHS = 5
BATCH = 1
GRAD_ACCUM = 8
LR = 2e-4
LORA_R = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.05
WARMUP_STEPS = 20
SQL_REPEAT = 3
TARGET = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
ENUM = re.compile(r"\b(no_change|rejection|not_ta|positive|mql|sql|meeting_held)\b")


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


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def oversample_sql(rows: list[dict], repeat: int) -> list[dict]:
    extra = []
    for r in rows:
        if r.get("assistant") == "sql":
            extra.extend([r] * (repeat - 1))
    return rows + extra


def format_row(tokenizer, row: dict) -> str:
    messages = [
        {"role": "system", "content": row["system"]},
        {"role": "user", "content": row["user"]},
        {"role": "assistant", "content": row["assistant"]},
    ]
    return tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=False
    )


def normalize(text: str) -> str | None:
    m = ENUM.search(text.lower().strip().strip("`'\". "))
    return m.group(1) if m else None


def generate_label(model, tokenizer, row: dict) -> str | None:
    msgs = [
        {"role": "system", "content": row["system"]},
        {"role": "user", "content": row["user"]},
    ]
    prompt = tokenizer.apply_chat_template(
        msgs, tokenize=False, add_generation_prompt=True
    )
    device = next(model.parameters()).device
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    with torch.no_grad():
        gen = model.generate(
            input_ids=inputs["input_ids"],
            attention_mask=inputs.get("attention_mask"),
            max_new_tokens=8,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
    raw = tokenizer.decode(
        gen[0, inputs["input_ids"].shape[1] :], skip_special_tokens=True
    )
    return normalize(raw)


class LossCsvCallback(TrainerCallback):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.peak_mib = gpu_mem_mib() or 0
        self.path.write_text("step,loss,learning_rate,vram_mib\n", encoding="utf-8")

    def on_log(self, args, state, control, logs=None, **kwargs):
        if not logs or "loss" not in logs:
            return
        used = gpu_mem_mib() or 0
        self.peak_mib = max(self.peak_mib, used)
        with self.path.open("a", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(
                [
                    state.global_step,
                    f"{logs['loss']:.6f}",
                    f"{logs.get('learning_rate', '')}",
                    used,
                ]
            )


class ValidAccCallback(TrainerCallback):
    def __init__(self, tokenizer, rows: list[dict], adapter_dir: Path, csv_path: Path) -> None:
        self.tokenizer = tokenizer
        self.rows = rows
        self.adapter_dir = adapter_dir
        self.csv_path = csv_path
        self.best = -1.0
        self.best_epoch = None
        csv_path.write_text("epoch,step,hits,n,valid_acc,vram_mib\n", encoding="utf-8")

    def on_epoch_end(self, args, state, control, model=None, **kwargs):
        if model is None:
            return
        was_training = model.training
        model.eval()
        hits = 0
        for row in self.rows:
            pred = generate_label(model, self.tokenizer, row)
            gold = row.get("gold_key") or [row["assistant"]]
            if pred in gold:
                hits += 1
        n = len(self.rows)
        acc = hits / n if n else 0.0
        used = gpu_mem_mib() or 0
        with self.csv_path.open("a", encoding="utf-8") as fh:
            csv.writer(fh).writerow(
                [int(state.epoch), state.global_step, hits, n, f"{acc:.4f}", used]
            )
        print(
            f"valid acc epoch={state.epoch:.0f} step={state.global_step} "
            f"{hits}/{n}={acc:.3f} best={self.best:.3f}",
            flush=True,
        )
        if acc >= self.best:
            self.best = acc
            self.best_epoch = int(state.epoch)
            self.adapter_dir.mkdir(parents=True, exist_ok=True)
            model.save_pretrained(self.adapter_dir)
            print(f"saved best adapter acc={acc:.3f} -> {self.adapter_dir}", flush=True)
        if was_training:
            model.train()


def to_text_dataset(rows: list[dict], tokenizer) -> Dataset:
    texts = [format_row(tokenizer, r) for r in rows]
    return Dataset.from_dict({"text": texts})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", default=str(DATA / "train.jsonl"))
    parser.add_argument("--valid", default=str(DATA / "valid.jsonl"))
    parser.add_argument("--adapter", default=str(ROOT / "adapter"))
    parser.add_argument("--sql-repeat", type=int, default=SQL_REPEAT)
    parser.add_argument("--epochs", type=int, default=EPOCHS)
    parser.add_argument("--tag", default="day7")
    args = parser.parse_args()

    if not torch.cuda.is_available():
        raise SystemExit("CUDA required for QLoRA on this script")
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

    adapter_dir = Path(args.adapter)
    adapter_dir.mkdir(parents=True, exist_ok=True)
    loss_csv = ROOT / f"loss-{args.tag}.csv"
    valid_csv = ROOT / f"valid-acc-{args.tag}.csv"
    params_path = ROOT / f"params-{args.tag}.md"
    meta_path = ROOT / f"run-meta-{args.tag}.json"
    ckpt_dir = ROOT / f"checkpoints-{args.tag}"

    started = time.time()
    started_iso = datetime.now(timezone.utc).isoformat()

    tokenizer = AutoTokenizer.from_pretrained(MODEL, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    train_rows = oversample_sql(load_jsonl(Path(args.train)), args.sql_repeat)
    valid_rows = load_jsonl(Path(args.valid))
    train_ds = to_text_dataset(train_rows, tokenizer)
    val_ds = to_text_dataset(valid_rows, tokenizer)

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

    loss_cb = LossCsvCallback(loss_csv)
    valid_cb = ValidAccCallback(tokenizer, valid_rows, adapter_dir, valid_csv)
    common = dict(
        output_dir=str(ckpt_dir),
        per_device_train_batch_size=BATCH,
        per_device_eval_batch_size=BATCH,
        gradient_accumulation_steps=GRAD_ACCUM,
        learning_rate=LR,
        num_train_epochs=args.epochs,
        logging_steps=1,
        eval_strategy="no",
        save_strategy="epoch",
        save_total_limit=6,
        fp16=False,
        bf16=False,
        gradient_checkpointing=True,
        lr_scheduler_type="cosine",
        warmup_steps=WARMUP_STEPS,
        report_to="none",
        optim="paged_adamw_32bit",
        seed=SEED,
        max_grad_norm=1.0,
    )
    try:
        targs = SFTConfig(
            **common,
            max_length=MAX_LEN,
            dataset_text_field="text",
            packing=False,
        )
    except TypeError:
        try:
            targs = SFTConfig(**common)
        except TypeError:
            common.pop("eval_strategy", None)
            targs = SFTConfig(**common, evaluation_strategy="no")

    trainer_kwargs = dict(
        model=model,
        args=targs,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        peft_config=peft_config,
        callbacks=[loss_cb, valid_cb],
    )
    try:
        trainer = SFTTrainer(**trainer_kwargs, processing_class=tokenizer)
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
    tokenizer.save_pretrained(adapter_dir)

    elapsed = time.time() - started
    peak = loss_cb.peak_mib
    metrics = train_result.metrics if train_result else {}
    params = f"""# {args.tag} launch parameters (rerun)

| | |
|---|---|
| Base model | `{MODEL}` |
| Train file | `{args.train}` ({len(train_rows)} after sql x{args.sql_repeat}) |
| Valid | `{args.valid}` ({len(valid_rows)}) |
| Epochs | {args.epochs} |
| Best valid acc | {valid_cb.best:.3f} at epoch {valid_cb.best_epoch} |
| LoRA | r={LORA_R} alpha={LORA_ALPHA} |
| GPU | {gpu_name()} |
| VRAM peak | {peak} MiB |
| Wall-clock | {elapsed:.0f} s ({elapsed / 60:.1f} min) |
| Started (UTC) | {started_iso} |
| train_loss | {metrics.get("train_loss")} |
| Adapter | `{adapter_dir}` |
"""
    params_path.write_text(params, encoding="utf-8")
    meta_path.write_text(
        json.dumps(
            {
                "tag": args.tag,
                "train": args.train,
                "train_n": len(train_rows),
                "val_n": len(valid_rows),
                "epochs": args.epochs,
                "best_valid_acc": valid_cb.best,
                "best_epoch": valid_cb.best_epoch,
                "elapsed_s": elapsed,
                "peak_vram_mib": peak,
                "train_loss": metrics.get("train_loss"),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(params)


if __name__ == "__main__":
    main()
