#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Score base and adapters on eval.jsonl and eval2.jsonl, per class and kind."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT = ROOT / "eval"
MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
ENUM = re.compile(r"\b(no_change|rejection|not_ta|positive|mql|sql|meeting_held)\b")
MAX_NEW = 8
LABELS = [
    "no_change",
    "rejection",
    "not_ta",
    "positive",
    "mql",
    "sql",
    "meeting_held",
]


def normalize(text: str) -> str | None:
    m = ENUM.search(text.lower().strip().strip("`'\". "))
    return m.group(1) if m else None


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def generate(model, tokenizer, row: dict, with_system: bool) -> str:
    msgs = [{"role": "user", "content": row["user"]}]
    if with_system:
        msgs.insert(0, {"role": "system", "content": row["system"]})
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
    )


def breakdown(preds: list[dict]) -> dict:
    by_lab_n: dict[str, int] = Counter()
    by_lab_ok: dict[str, int] = Counter()
    by_kind_n: dict[str, int] = Counter()
    by_kind_ok: dict[str, int] = Counter()
    for p in preds:
        lab = p["gold"][0] if p["gold"] else "?"
        kind = p.get("kind") or "?"
        by_lab_n[lab] += 1
        by_kind_n[kind] += 1
        if p["ok"]:
            by_lab_ok[lab] += 1
            by_kind_ok[kind] += 1
    return {
        "by_label": {
            k: {"hits": by_lab_ok[k], "n": n, "acc": by_lab_ok[k] / n}
            for k, n in sorted(by_lab_n.items())
        },
        "by_kind": {
            k: {"hits": by_kind_ok[k], "n": n, "acc": by_kind_ok[k] / n}
            for k, n in sorted(by_kind_n.items())
        },
    }


def run_split(name: str, model, tokenizer, rows: list[dict], with_system: bool) -> dict:
    dest = OUT / name
    dest.mkdir(parents=True, exist_ok=True)
    hits = 0
    preds = []
    for r in rows:
        raw = generate(model, tokenizer, r, with_system)
        (dest / f"{r['id']}.txt").write_text(raw, encoding="utf-8")
        pred = normalize(raw)
        gold = r["gold_key"]
        ok = bool(pred) and pred in gold
        hits += int(ok)
        preds.append(
            {
                "id": r["id"],
                "kind": r.get("kind"),
                "raw": raw,
                "pred": pred,
                "gold": gold,
                "ok": ok,
            }
        )
        print(f"{name} {r['id']} pred={pred} gold={gold} ok={ok}", file=sys.stderr)
    n = len(rows)
    out = {
        "accuracy": hits / n if n else 0,
        "hits": hits,
        "n": n,
        "preds": preds,
    }
    out.update(breakdown(preds))
    return out


def load_base():
    return AutoModelForCausalLM.from_pretrained(
        MODEL,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,
    )


def md_block(title: str, block: dict) -> list[str]:
    lines = [
        f"### {title}",
        "",
        f"Hits **{block['hits']}/{block['n']}** = {block['accuracy']:.3f}",
        "",
        "| class | hits | n | acc |",
        "|---|---|---|---|",
    ]
    for k, v in block["by_label"].items():
        note = " (untrainable)" if k == "meeting_held" else ""
        lines.append(f"| `{k}`{note} | {v['hits']} | {v['n']} | {v['acc']:.3f} |")
    lines += ["", "| kind | hits | n | acc |", "|---|---|---|---|"]
    for k, v in block["by_kind"].items():
        lines.append(f"| `{k}` | {v['hits']} | {v['n']} | {v['acc']:.3f} |")
    lines.append("")
    return lines


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold-adapter", default=str(ROOT / "adapter-gold"))
    parser.add_argument("--opus-adapter", default=str(ROOT / "adapter-opus"))
    parser.add_argument("--skip-base", action="store_true")
    args = parser.parse_args()
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    OUT.mkdir(parents=True, exist_ok=True)

    sets = {
        "eval": load_jsonl(DATA / "eval.jsonl"),
        "eval2": load_jsonl(DATA / "eval2.jsonl"),
    }
    tokenizer = AutoTokenizer.from_pretrained(MODEL, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    report: dict = {}
    if not args.skip_base:
        print("loading base", file=sys.stderr)
        model = load_base()
        for sname, rows in sets.items():
            report[f"base_no_system_{sname}"] = run_split(
                f"base_no_system_{sname}", model, tokenizer, rows, False
            )
            report[f"base_with_system_{sname}"] = run_split(
                f"base_with_system_{sname}", model, tokenizer, rows, True
            )
        del model
        torch.cuda.empty_cache()

    for tag, path in (("gold", Path(args.gold_adapter)), ("opus", Path(args.opus_adapter))):
        if not path.exists():
            print(f"skip missing adapter {path}", file=sys.stderr)
            continue
        print(f"loading {tag} {path}", file=sys.stderr)
        base = load_base()
        model = PeftModel.from_pretrained(base, str(path))
        for sname, rows in sets.items():
            report[f"{tag}_with_system_{sname}"] = run_split(
                f"{tag}_with_system_{sname}", model, tokenizer, rows, True
            )
        del model, base
        torch.cuda.empty_cache()

    opus_scores = DATA / "teacher_opus_scores.json"
    if opus_scores.exists():
        report["teacher_opus"] = json.loads(opus_scores.read_text(encoding="utf-8"))

    (OUT / "scores-rerun.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    lines = ["# Day 7/9 rerun scores", ""]
    order = []
    for sname in ("eval", "eval2"):
        lines.append(f"## {sname}")
        lines.append("")
        for key in (
            f"base_no_system_{sname}",
            f"base_with_system_{sname}",
            f"gold_with_system_{sname}",
            f"opus_with_system_{sname}",
        ):
            if key in report:
                lines.extend(md_block(key, report[key]))
        lines.append("")
    (OUT / "scores-rerun.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
