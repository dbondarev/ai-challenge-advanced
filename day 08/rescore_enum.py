#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Optional day 8: rescore enum adapter on updated eval.jsonl / eval2.jsonl. No retrain."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

ROOT = Path(__file__).resolve().parent
D7 = ROOT.parent / "day 07" / "data"
# remote layout: DAY7_DATA env
DATA = Path(os.environ.get("DAY7_DATA", str(D7)))
ADAPTER = Path(os.environ.get("DAY8_ADAPTER", str(ROOT / "adapter")))
OUT = ROOT / "eval"
MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
ENUM = re.compile(r"\b(no_change|rejection|not_ta|positive|mql|sql|meeting_held)\b")


def normalize(text: str) -> str | None:
    m = ENUM.search(text.lower().strip().strip("`'\". "))
    return m.group(1) if m else None


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def generate(model, tokenizer, row: dict) -> str:
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
    return tokenizer.decode(
        gen[0, inputs["input_ids"].shape[1] :], skip_special_tokens=True
    )


def score(model, tokenizer, rows: list[dict], name: str) -> dict:
    hits = 0
    preds = []
    dest = OUT / f"day8_{name}"
    dest.mkdir(parents=True, exist_ok=True)
    for r in rows:
        raw = generate(model, tokenizer, r)
        (dest / f"{r['id']}.txt").write_text(raw, encoding="utf-8")
        pred = normalize(raw)
        ok = bool(pred) and pred in r["gold_key"]
        hits += int(ok)
        preds.append({"id": r["id"], "pred": pred, "gold": r["gold_key"], "ok": ok})
        print(f"day8 {name} {r['id']} pred={pred} ok={ok}", file=sys.stderr)
    n = len(rows)
    return {"hits": hits, "n": n, "accuracy": hits / n, "preds": preds}


def main() -> None:
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    if not ADAPTER.exists():
        raise SystemExit(f"no adapter at {ADAPTER}")
    tok = AutoTokenizer.from_pretrained(MODEL, trust_remote_code=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    base = AutoModelForCausalLM.from_pretrained(
        MODEL, torch_dtype=torch.float16, device_map="auto", trust_remote_code=True
    )
    model = PeftModel.from_pretrained(base, str(ADAPTER))
    report = {
        "eval": score(model, tok, load_jsonl(DATA / "eval.jsonl"), "eval"),
        "eval2": score(model, tok, load_jsonl(DATA / "eval2.jsonl"), "eval2"),
        "note": "no retrain; mixed day8 adapter on new gold",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "enum-rescore.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    lines = [
        "# Day 8 enum rescore (no retrain)",
        "",
        f"| eval | {report['eval']['hits']}/{report['eval']['n']} | {report['eval']['accuracy']:.3f} |",
        f"| eval2 | {report['eval2']['hits']}/{report['eval2']['n']} | {report['eval2']['accuracy']:.3f} |",
        "",
        "Day 8 was not retrained. This is the mixed adapter on the corrected gold.",
    ]
    (OUT / "enum-rescore.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
