#!/usr/bin/env python3
"""Baseline for day 07: Qwen2.5-1.5B-Instruct on eval.jsonl, temperature 0, without and with system.

Run on nv307001 in ~/day06-qlora/.venv:  python baseline.py eval.jsonl > baseline.json
"""
import json
import re
import sys

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
ENUM = re.compile(r"\b(no_change|rejection|not_ta|positive|mql|sql|meeting_held)\b")


def normalize(text: str) -> str | None:
    m = ENUM.search(text.lower().strip().strip("`'\". "))
    return m.group(1) if m else None


def main() -> None:
    rows = [json.loads(line) for line in open(sys.argv[1], encoding="utf-8")]
    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float16, device_map="auto")
    out = {}
    for mode in ("no_system", "with_system"):
        hits, preds = 0, []
        for r in rows:
            msgs = [{"role": "user", "content": r["user"]}]
            if mode == "with_system":
                msgs.insert(0, {"role": "system", "content": r["system"]})
            prompt = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
            inputs = tok(prompt, return_tensors="pt").to(model.device)
            gen = model.generate(
                input_ids=inputs["input_ids"],
                attention_mask=inputs.get("attention_mask"),
                max_new_tokens=8,
                do_sample=False,
                pad_token_id=tok.eos_token_id,
            )
            text = tok.decode(gen[0, inputs["input_ids"].shape[1]:], skip_special_tokens=True)
            pred = normalize(text)
            ok = pred in r["gold_key"]
            hits += ok
            preds.append({"id": r["id"], "raw": text, "pred": pred, "gold": r["gold_key"], "ok": ok})
        out[mode] = {"accuracy": hits / len(rows), "n": len(rows), "preds": preds}
        print(f"{mode}: {hits}/{len(rows)} = {hits / len(rows):.3f}", file=sys.stderr)
    json.dump(out, sys.stdout, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
