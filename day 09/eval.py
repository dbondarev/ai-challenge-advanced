#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Score 1.5B before/after distillation; merge teacher 7B scores from eval/teacher.json."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from prompts import STUDENT_SYS

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT = ROOT / "eval"
ADAPTER = ROOT / "adapter"
STUDENT = "Qwen/Qwen2.5-1.5B-Instruct"
ENUM = re.compile(r"\b(no_change|rejection|not_ta|positive|mql|sql|meeting_held)\b")
MAX_NEW = 8


def gpu_mem_mib() -> int:
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
        return 0


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def normalize(text: str) -> str | None:
    m = ENUM.search(text.lower().strip().strip("`'\". "))
    return m.group(1) if m else None


def generate(model, tokenizer, system: str | None, user: str) -> str:
    msgs = [{"role": "user", "content": user}]
    if system:
        msgs.insert(0, {"role": "system", "content": system})
    prompt = tokenizer.apply_chat_template(
        msgs, tokenize=False, add_generation_prompt=True
    )
    device = next(model.parameters()).device
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    with torch.no_grad():
        gen = model.generate(
            input_ids=inputs["input_ids"],
            attention_mask=inputs.get("attention_mask"),
            max_new_tokens=MAX_NEW,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
    return tokenizer.decode(
        gen[0, inputs["input_ids"].shape[1] :], skip_special_tokens=True
    ).strip()


def run_split(model, tokenizer, name: str, rows: list[dict], system: str | None) -> dict:
    dest = OUT / name
    dest.mkdir(parents=True, exist_ok=True)
    hits = 0
    peak = gpu_mem_mib()
    preds = []
    t0 = time.time()
    for r in rows:
        raw = generate(model, tokenizer, system, r["user"])
        peak = max(peak, gpu_mem_mib())
        (dest / f"{r['id']}.txt").write_text(raw, encoding="utf-8")
        pred = normalize(raw)
        ok = bool(pred) and pred in r["gold_key"]
        hits += int(ok)
        preds.append(
            {
                "id": r["id"],
                "kind": r.get("kind"),
                "raw": raw,
                "pred": pred,
                "gold": r["gold_key"],
                "ok": ok,
            }
        )
        print(f"{name} {r['id']} pred={pred} ok={ok}", file=sys.stderr)
    wall = time.time() - t0
    n = len(rows)
    return {
        "n": n,
        "hits": hits,
        "accuracy": hits / n,
        "wall_s": wall,
        "ms_per_req": (wall / n) * 1000,
        "peak_vram_mib": peak,
        "preds": preds,
    }


def load_student():
    tok = AutoTokenizer.from_pretrained(STUDENT, trust_remote_code=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        STUDENT,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,
    )
    return model, tok


def main() -> None:
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    OUT.mkdir(parents=True, exist_ok=True)
    rows = load_jsonl(DATA / "eval.jsonl")
    report = {}

    teacher_path = OUT / "teacher.json"
    if teacher_path.exists():
        report["teacher"] = json.loads(teacher_path.read_text(encoding="utf-8"))

    print("loading student base", file=sys.stderr)
    model, tok = load_student()
    report["student_before"] = run_split(
        model, tok, "student_before", rows, STUDENT_SYS
    )
    del model
    torch.cuda.empty_cache()

    print("loading student distilled", file=sys.stderr)
    base, tok = load_student()
    model = PeftModel.from_pretrained(base, str(ADAPTER))
    report["student_after"] = run_split(model, tok, "student_after", rows, STUDENT_SYS)

    (OUT / "scores.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    def line(name, block):
        if not block:
            return None
        extra = ""
        if "ms_per_req" in block:
            extra = (
                f"{block['ms_per_req']:.0f} ms/req, "
                f"vram {block.get('peak_vram_mib', '?')} MiB"
            )
        return (
            f"| {name} | {block['hits']}/{block['n']} | "
            f"{block['accuracy']:.3f} | {extra} |"
        )

    lines = [
        "# Day 9 eval scores",
        "",
        "| Mode | Hits | Acc | Cost |",
        "|---|---|---|---|",
    ]
    for name, key in (
        ("1.5B + short system (before)", "student_before"),
        ("1.5B distilled + short system", "student_after"),
        ("7B 4-bit + long spec (teacher)", "teacher"),
    ):
        row = line(name, report.get(key))
        if row:
            lines.append(row)
    text = "\n".join(lines) + "\n"
    (OUT / "scores.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
