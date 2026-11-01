#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run Qwen2.5-7B-Instruct 4-bit as teacher: eval 68 + label train, then filter."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from prompts import STUDENT_SYS, TEACHER_SYS

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT = ROOT / "eval"
TEACHER = "Qwen/Qwen2.5-7B-Instruct"
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


def one_word(raw: str, pred: str | None) -> bool:
    if not pred:
        return False
    t = raw.strip().strip("`'\". ")
    t = t.splitlines()[0].strip() if t else ""
    return t.lower().rstrip(".") == pred


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
            max_new_tokens=MAX_NEW,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
    return tokenizer.decode(
        gen[0, inputs["input_ids"].shape[1] :], skip_special_tokens=True
    ).strip()


def load_teacher():
    tok = AutoTokenizer.from_pretrained(TEACHER, trust_remote_code=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )
    model = AutoModelForCausalLM.from_pretrained(
        TEACHER,
        quantization_config=bnb,
        device_map="auto",
        torch_dtype=torch.float16,
        trust_remote_code=True,
    )
    model.eval()
    return model, tok


def run_split(model, tokenizer, rows: list[dict], tag: str) -> dict:
    dest = OUT / tag
    dest.mkdir(parents=True, exist_ok=True)
    hits = 0
    times = []
    peak = gpu_mem_mib()
    preds = []
    t0 = time.time()
    for i, r in enumerate(rows, start=1):
        started = time.time()
        raw = generate(model, tokenizer, TEACHER_SYS, r["user"])
        elapsed = time.time() - started
        times.append(elapsed)
        peak = max(peak, gpu_mem_mib())
        (dest / f"{r['id']}.txt").write_text(raw, encoding="utf-8")
        pred = normalize(raw)
        gold = r.get("gold_key") or [r.get("assistant")]
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
                "ms": round(elapsed * 1000, 1),
            }
        )
        print(
            f"{tag} {i}/{len(rows)} {r['id']} pred={pred} ok={ok} {elapsed*1000:.0f}ms",
            file=sys.stderr,
        )
    wall = time.time() - t0
    n = len(rows)
    return {
        "model": TEACHER,
        "n": n,
        "hits": hits,
        "accuracy": hits / n if n else 0,
        "wall_s": wall,
        "ms_per_req": (wall / n) * 1000 if n else 0,
        "peak_vram_mib": peak,
        "preds": preds,
    }


def filter_train(rows: list[dict], labeled: list[dict]) -> None:
    by_id = {p["id"]: p for p in labeled}
    kept = []
    dropped = []
    conf = Counter()
    for r in rows:
        p = by_id[r["id"]]
        pred = p["pred"]
        gold = r.get("gold_key") or [r["assistant"]]
        reason = None
        if not pred:
            reason = "no_enum"
        elif not one_word(p["raw"], pred):
            reason = "not_one_word"
        elif pred not in gold:
            reason = "disagree_gold"
            conf[(r["assistant"], pred)] += 1
        if reason:
            dropped.append(
                {
                    "id": r["id"],
                    "reason": reason,
                    "gold": gold,
                    "pred": pred,
                    "raw": p["raw"],
                }
            )
            continue
        kept.append(
            {
                "id": r["id"],
                "split": "train",
                "kind": r.get("kind"),
                "system": STUDENT_SYS,
                "user": r["user"],
                "assistant": pred,
                "gold_key": [pred],
                "teacher_raw": p["raw"],
                "source_gold": r["assistant"],
            }
        )
    with (DATA / "distill.jsonl").open("w", encoding="utf-8") as fh:
        for row in kept:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    (DATA / "teacher_train.json").write_text(
        json.dumps(labeled, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    lines = [
        f"# Dropped teacher labels",
        "",
        f"Train inputs: {len(rows)}",
        f"Kept: {len(kept)}",
        f"Dropped: {len(dropped)}",
        "",
        "## Reasons",
        "",
    ]
    rc = Counter(d["reason"] for d in dropped)
    for k, v in rc.most_common():
        lines.append(f"- `{k}`: {v}")
    lines += ["", "## Teacher vs gold (dropped disagreements)", ""]
    for (g, pr), n in conf.most_common(20):
        lines.append(f"- gold `{g}` -> teacher `{pr}`: {n}")
    lines += ["", "## Sample (up to 10)", ""]
    for d in dropped[:10]:
        raw = (d["raw"] or "").replace("\n", " ")[:160]
        lines.append(
            f"- `{d['id']}` reason={d['reason']} gold={d['gold']} pred={d['pred']} raw={raw!r}"
        )
    (DATA / "dropped.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        f"distill kept {len(kept)}/{len(rows)} dropped {len(dropped)}",
        file=sys.stderr,
    )


def main() -> None:
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    OUT.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)
    eval_rows = load_jsonl(DATA / "eval.jsonl")
    train_rows = load_jsonl(DATA / "train_inputs.jsonl")
    print("loading teacher 7B 4-bit", file=sys.stderr)
    model, tok = load_teacher()
    print(f"vram after load {gpu_mem_mib()} MiB", file=sys.stderr)

    teacher_eval = run_split(model, tok, eval_rows, "teacher")
    (OUT / "teacher.json").write_text(
        json.dumps(teacher_eval, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    print(
        f"teacher eval {teacher_eval['hits']}/{teacher_eval['n']} "
        f"acc={teacher_eval['accuracy']:.3f} "
        f"{teacher_eval['ms_per_req']:.0f} ms/req "
        f"vram={teacher_eval['peak_vram_mib']} MiB",
        file=sys.stderr,
    )

    train_pack = run_split(model, tok, train_rows, "teacher_train")
    filter_train(train_rows, train_pack["preds"])
    (OUT / "teacher_train_meta.json").write_text(
        json.dumps(
            {
                "n": train_pack["n"],
                "wall_s": train_pack["wall_s"],
                "ms_per_req": train_pack["ms_per_req"],
                "peak_vram_mib": train_pack["peak_vram_mib"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
