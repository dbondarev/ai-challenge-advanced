#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compare base Qwen2.5-1.5B-Instruct vs QLoRA adapter on 20 prompts."""

from __future__ import annotations

import json
import re
from pathlib import Path

import torch
from datasets import load_dataset
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

ROOT = Path(__file__).resolve().parent
ADAPTER = ROOT / "adapter"
OUT_BASE = ROOT / "eval" / "base"
OUT_TUNED = ROOT / "eval" / "tuned"
TABLE = ROOT / "eval" / "20.md"
PROMPTS_PATH = ROOT / "prompts.json"

MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
DATASET = "b-mc2/sql-create-context"
SEED = 42
SKIP = 9000
SYSTEM = "You write SQLite. Reply with one SQL statement only."
SQL_START = re.compile(
    r"^\s*(select|insert|update|delete|with|create|drop|alter|pragma)\b",
    re.I,
)


def load_in_domain() -> list[dict]:
    raw = load_dataset(DATASET, split="train").shuffle(seed=SEED)
    rows = raw.select(range(SKIP, SKIP + 10))
    out = []
    for i, row in enumerate(rows, start=1):
        out.append(
            {
                "id": f"in{i:02d}",
                "group": "in-domain",
                "question": row["question"],
                "context": row["context"],
                "gold": row["answer"],
                "user": f"Schema:\n{row['context']}\n\nQuestion:\n{row['question']}",
                "use_sql_system": True,
            }
        )
    return out


def all_prompts() -> list[dict]:
    extra = json.loads(PROMPTS_PATH.read_text(encoding="utf-8"))
    return load_in_domain() + extra


def generate(model, tokenizer, prompt: dict) -> str:
    messages = []
    if prompt.get("use_sql_system"):
        messages.append({"role": "system", "content": SYSTEM})
    messages.append({"role": "user", "content": prompt["user"]})
    text = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    inputs = tokenizer(text, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(
            input_ids=inputs["input_ids"],
            attention_mask=inputs.get("attention_mask"),
            max_new_tokens=256,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
    new_tokens = out[0, inputs["input_ids"].shape[1] :]
    return tokenizer.decode(new_tokens, skip_special_tokens=True).strip()


def strip_fence(text: str) -> str:
    t = text.strip()
    t = re.sub(r"^```(?:sql)?\s*", "", t, flags=re.I)
    t = re.sub(r"\s*```$", "", t)
    return t.strip().rstrip(";")


def norm_sql(text: str) -> str:
    t = strip_fence(text).lower()
    t = re.sub(r"\s+", " ", t).strip()
    return t


def looks_sql(text: str) -> bool:
    return bool(SQL_START.search(strip_fence(text)))


def load_base(tokenizer):
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
    model.eval()
    return model


def load_tuned(tokenizer):
    base = load_base(tokenizer)
    model = PeftModel.from_pretrained(base, str(ADAPTER))
    model.eval()
    return model


def main() -> None:
    OUT_BASE.mkdir(parents=True, exist_ok=True)
    OUT_TUNED.mkdir(parents=True, exist_ok=True)
    tokenizer = AutoTokenizer.from_pretrained(MODEL, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    prompts = all_prompts()
    (ROOT / "prompts.resolved.json").write_text(
        json.dumps(prompts, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    results = []
    for label, loader, out_dir in (
        ("base", load_base, OUT_BASE),
        ("tuned", load_tuned, OUT_TUNED),
    ):
        print("loading", label)
        model = loader(tokenizer)
        for prompt in prompts:
            print(" ", label, prompt["id"])
            text = generate(model, tokenizer, prompt)
            (out_dir / f"{prompt['id']}.txt").write_text(text + "\n", encoding="utf-8")
            results.append((label, prompt, text))
        del model
        torch.cuda.empty_cache()

    by_id: dict[str, dict] = {}
    for label, prompt, text in results:
        rec = by_id.setdefault(
            prompt["id"],
            {"prompt": prompt, "base": "", "tuned": ""},
        )
        rec[label] = text

    lines = [
        "# Eval - 20 prompts, base vs QLoRA",
        "",
        "Temperature 0. Base: `Qwen/Qwen2.5-1.5B-Instruct` 4-bit. Tuned: same + `adapter/`.",
        "In-domain rows: dataset shuffle seed 42, indices 9000-9009 (held-out).",
        "",
        "| id | group | sql-only base | sql-only tuned | exact-match base | exact-match tuned | OOD worse? | notes |",
        "|---|---|---|---|---|---|---|---|",
    ]
    worse = []
    for prompt in prompts:
        rec = by_id[prompt["id"]]
        gold = norm_sql(prompt.get("gold") or "")
        b_sql = looks_sql(rec["base"])
        t_sql = looks_sql(rec["tuned"])
        b_ex = bool(gold) and norm_sql(rec["base"]) == gold
        t_ex = bool(gold) and norm_sql(rec["tuned"]) == gold
        ood_worse = ""
        note = ""
        if prompt["group"] == "out-of-domain":
            if t_sql and not b_sql:
                ood_worse = "yes - tuned answers SQL"
                worse.append(prompt["id"])
            elif t_sql and b_sql:
                ood_worse = "both SQL"
            else:
                ood_worse = "no"
        if prompt["group"] == "in-domain":
            note = "gold SQL held-out"
        elif prompt["group"] == "stretch":
            note = "SQL expected; weaker grounding"
        lines.append(
            f"| {prompt['id']} | {prompt['group']} | {str(b_sql).lower()} | {str(t_sql).lower()} | "
            f"{str(b_ex).lower() if gold else 'n/a'} | {str(t_ex).lower() if gold else 'n/a'} | "
            f"{ood_worse or 'n/a'} | {note} |"
        )

    lines += ["", "## Answers", ""]
    for prompt in prompts:
        rec = by_id[prompt["id"]]
        lines += [
            f"### {prompt['id']} ({prompt['group']})",
            "",
            "**User**",
            "",
            "```",
            prompt["user"][:1200],
            "```",
            "",
            "**Base**",
            "",
            "```",
            rec["base"],
            "```",
            "",
            "**Tuned**",
            "",
            "```",
            rec["tuned"],
            "```",
            "",
        ]
    if worse:
        lines += [
            "## OOD regressions",
            "",
            "Tuned model emitted SQL where the base model answered the actual question: "
            + ", ".join(worse),
            "",
        ]
    TABLE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote", TABLE)
    print("ood worse", worse)


if __name__ == "__main__":
    main()
