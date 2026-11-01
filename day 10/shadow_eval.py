#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Score 1.5B base and day-7 adapter vs prod labels. Output has no thread text."""

from __future__ import annotations

import json
import os
import re
import sys
import time
from collections import Counter
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

ROOT = Path(__file__).resolve().parent
INFER = Path(os.environ.get("INFER_JSONL", str(Path.home() / "day10-serve" / "day10_infer.jsonl")))
ADAPTER = Path(os.environ.get("ADAPTER", str(Path.home() / "day07-rerun" / "adapter-gold")))
OUT = Path(os.environ.get("SHADOW_OUT", str(ROOT / "eval")))
MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
ENUM = re.compile(r"\b(no_change|rejection|not_ta|positive|mql|sql|meeting_held)\b")


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


def generate(model, tokenizer, system: str, user: str) -> str:
    msgs = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
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


def run(name: str, model, tokenizer, rows: list[dict]) -> list[dict]:
    preds = []
    t0 = time.time()
    for i, r in enumerate(rows, start=1):
        raw = generate(model, tokenizer, r["system"], r["user"])
        pred = normalize(raw)
        rec = {
            "id": r["id"],
            "project_id": r.get("project_id"),
            "message_id": r.get("message_id"),
            "kind": r.get("kind"),
            "prod_status": r.get("prod_status"),
            "suggested_by": r.get("suggested_by"),
            "confirmed": r.get("confirmed"),
            "pred": pred,
        }
        preds.append(rec)
        if i % 25 == 0 or i == len(rows):
            print(f"{name} {i}/{len(rows)}", file=sys.stderr)
    print(f"{name} wall {time.time()-t0:.1f}s", file=sys.stderr)
    return preds


def summarize(preds: list[dict], key: str) -> dict:
    labeled = [p for p in preds if p.get("prod_status") in {
        "no_change", "rejection", "not_ta", "positive", "mql", "sql", "meeting_held"
    }]
    hits = sum(1 for p in labeled if p.get(key) == p.get("prod_status"))
    conf: Counter = Counter()
    by_proj: dict = {}
    by_lab: dict = {}
    for p in labeled:
        pred = p.get(key)
        gold = p.get("prod_status")
        conf[(gold, pred)] += 1
        pid = str(p.get("project_id"))
        by_proj.setdefault(pid, {"n": 0, "hits": 0})
        by_proj[pid]["n"] += 1
        by_proj[pid]["hits"] += int(pred == gold)
        by_lab.setdefault(gold, {"n": 0, "hits": 0})
        by_lab[gold]["n"] += 1
        by_lab[gold]["hits"] += int(pred == gold)
    disagree = [
        {
            "id": p["id"],
            "project_id": p.get("project_id"),
            "prod": p.get("prod_status"),
            "pred": p.get(key),
            "kind": p.get("kind"),
        }
        for p in labeled
        if p.get(key) != p.get("prod_status")
    ]
    return {
        "labeled_n": len(labeled),
        "hits": hits,
        "agreement": hits / len(labeled) if labeled else 0,
        "confusion": [{"prod": a, "pred": b, "n": n} for (a, b), n in conf.most_common()],
        "by_project": {
            k: {"hits": v["hits"], "n": v["n"], "acc": v["hits"] / v["n"]}
            for k, v in sorted(by_proj.items(), key=lambda kv: -kv[1]["n"])
        },
        "by_label": {
            k: {"hits": v["hits"], "n": v["n"], "acc": v["hits"] / v["n"]}
            for k, v in sorted(by_lab.items())
        },
        "disagree_n": len(disagree),
        "disagree_sample": disagree[:30],
    }


def load_base():
    tok = AutoTokenizer.from_pretrained(MODEL, trust_remote_code=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        MODEL,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,
    )
    return model, tok


def main() -> None:
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    OUT.mkdir(parents=True, exist_ok=True)
    rows = load_jsonl(INFER)
    print(f"infer rows {len(rows)}", file=sys.stderr)

    model, tok = load_base()
    base_preds = run("base", model, tok, rows)
    del model
    torch.cuda.empty_cache()

    base, tok = load_base()
    model = PeftModel.from_pretrained(base, str(ADAPTER))
    tune_preds = run("tuned", model, tok, rows)

    merged = []
    for b, t in zip(base_preds, tune_preds):
        merged.append(
            {
                **{k: t[k] for k in (
                    "id", "project_id", "message_id", "kind",
                    "prod_status", "suggested_by", "confirmed",
                )},
                "base_pred": b["pred"],
                "tuned_pred": t["pred"],
            }
        )
    (OUT / "shadow-preds.json").write_text(
        json.dumps(merged, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    report = {
        "n": len(merged),
        "with_prod_label": sum(1 for p in merged if p.get("prod_status")),
        "suggested_by": dict(Counter(p.get("suggested_by") or "none" for p in merged)),
        "base": summarize(
            [{**p, "pred": p["base_pred"]} for p in merged], "pred"
        ),
        "tuned": summarize(
            [{**p, "pred": p["tuned_pred"]} for p in merged], "pred"
        ),
    }
    (OUT / "shadow.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("n", "with_prod_label", "suggested_by")}, indent=2))
    print("base", report["base"]["hits"], "/", report["base"]["labeled_n"], report["base"]["agreement"])
    print("tuned", report["tuned"]["hits"], "/", report["tuned"]["labeled_n"], report["tuned"]["agreement"])


if __name__ == "__main__":
    main()
