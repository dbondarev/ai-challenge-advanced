#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Day 8 probes: facts, format, style, OOD. Base vs prompt vs day7 vs day8 best/last."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
PROBES = DATA / "probes"
OUT = ROOT / "eval"
MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
ENUM = re.compile(r"\b(no_change|rejection|not_ta|positive|mql|sql|meeting_held)\b")
ENUM_ONLY = re.compile(
    r"^\s*(no_change|rejection|not_ta|positive|mql|sql|meeting_held)[\s.`'\".,]*$",
    re.I,
)

FORMAT_SYS = (
    "How does the last IN message change the prospect's status in this LinkedIn "
    "sales thread? Reply with one word: no_change, rejection, not_ta, positive, "
    "mql, sql, meeting_held."
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def generate(model, tokenizer, system: str | None, user: str, max_new: int) -> str:
    msgs = [{"role": "user", "content": user}]
    if system:
        msgs.insert(0, {"role": "system", "content": system})
    prompt = tokenizer.apply_chat_template(
        msgs, tokenize=False, add_generation_prompt=True
    )
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        gen = model.generate(
            input_ids=inputs["input_ids"],
            attention_mask=inputs.get("attention_mask"),
            max_new_tokens=max_new,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
    return tokenizer.decode(
        gen[0, inputs["input_ids"].shape[1] :], skip_special_tokens=True
    ).strip()


def write_raw(folder: Path, rid: str, text: str) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{rid}.txt").write_text(text, encoding="utf-8")


def normalize_enum(text: str) -> str | None:
    m = ENUM.search(text.lower().strip().strip("`'\". "))
    return m.group(1) if m else None


def fact_hit(text: str, gold: str) -> bool:
    return gold.lower() in text.lower()


def score_style(text: str, banned: list[str]) -> tuple[bool, list[str]]:
    reasons = []
    t = text.strip()
    if not t:
        return False, ["empty"]
    if ENUM_ONLY.match(t):
        reasons.append("enum_collapse")
    if any(ch in t for ch in "????????????"):
        reasons.append("emoji")
    sentences = [s for s in re.split(r"[.!?]+", t) if s.strip()]
    if len(sentences) > 2:
        reasons.append("too_many_sentences")
    low = t.lower()
    for b in banned:
        if b in low:
            reasons.append(f"banned:{b}")
    ok = "enum_collapse" not in reasons and "empty" not in reasons and "emoji" not in reasons
    ok = ok and "too_many_sentences" not in reasons and not any(r.startswith("banned:") for r in reasons)
    return ok, reasons


def score_ood(text: str, checks: list[str]) -> tuple[bool, list[str]]:
    reasons = []
    collapsed = bool(ENUM_ONLY.match(text.strip()))
    if collapsed:
        reasons.append("enum_collapse")
    ok_bits = []
    for c in checks:
        if c == "contains_4":
            hit = bool(re.search(r"\b4\b", text))
            ok_bits.append(hit)
            if not hit:
                reasons.append("no_4")
        elif c == "contains_paris":
            hit = "paris" in text.lower()
            ok_bits.append(hit)
            if not hit:
                reasons.append("no_paris")
        elif c == "has_def":
            hit = bool(re.search(r"\bdef\b", text))
            ok_bits.append(hit)
            if not hit:
                reasons.append("no_def")
        elif c == "review_shape":
            hit = "critical:" in text.lower() and "should fix:" in text.lower()
            ok_bits.append(hit)
            if not hit:
                reasons.append("bad_review_shape")
        elif c == "two_lines":
            lines = [ln for ln in text.splitlines() if ln.strip()]
            hit = 1 <= len(lines) <= 3
            ok_bits.append(hit)
            if not hit:
                reasons.append("not_two_lines")
        elif c == "json_ab":
            hit = False
            try:
                raw = text.strip()
                fence = re.search(r"\{.*\}", raw, re.S)
                obj = json.loads(fence.group(0) if fence else raw)
                hit = isinstance(obj, dict) and obj.get("a") == 1 and obj.get("b") == 2
            except Exception:
                hit = False
            ok_bits.append(hit)
            if not hit:
                reasons.append("bad_json")
        elif c == "not_enum_only":
            hit = not collapsed and len(text.split()) >= 4
            ok_bits.append(hit)
            if not hit:
                reasons.append("too_thin")
        else:
            ok_bits.append(not collapsed)
    ok = (not collapsed) and all(ok_bits)
    return ok, reasons


def load_base():
    return AutoModelForCausalLM.from_pretrained(
        MODEL,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,
    )


def wrap_adapter(base, path: Path):
    return PeftModel.from_pretrained(base, str(path))


def run_facts(model, tokenizer, name: str, system: str, items: list[dict]) -> dict:
    dest = OUT / name / "facts"
    hits_v = hits_p = 0
    n_v = n_p = 0
    preds = []
    for it in items:
        raw = generate(model, tokenizer, system, it["user"], 32)
        write_raw(dest, it["id"], raw)
        ok = fact_hit(raw, it["gold"])
        if it["kind"] == "verbatim":
            n_v += 1
            hits_v += int(ok)
        else:
            n_p += 1
            hits_p += int(ok)
        preds.append(
            {"id": it["id"], "kind": it["kind"], "gold": it["gold"], "raw": raw, "ok": ok}
        )
        print(f"{name} facts {it['id']} ok={ok} raw={raw[:80]!r}", file=sys.stderr)
    return {
        "verbatim": {"hits": hits_v, "n": n_v, "accuracy": hits_v / n_v if n_v else 0},
        "paraphrase": {"hits": hits_p, "n": n_p, "accuracy": hits_p / n_p if n_p else 0},
        "hits": hits_v + hits_p,
        "n": n_v + n_p,
        "accuracy": (hits_v + hits_p) / (n_v + n_p),
        "preds": preds,
    }


def run_format(model, tokenizer, name: str, rows: list[dict], with_system: bool) -> dict:
    dest = OUT / name / "format"
    hits = 0
    preds = []
    for r in rows:
        sys_msg = r.get("system") or FORMAT_SYS if with_system else None
        raw = generate(model, tokenizer, sys_msg, r["user"], 8)
        write_raw(dest, r["id"], raw)
        pred = normalize_enum(raw)
        ok = pred in r["gold_key"] if pred else False
        hits += int(ok)
        preds.append({"id": r["id"], "pred": pred, "gold": r["gold_key"], "raw": raw, "ok": ok})
        print(f"{name} format {r['id']} pred={pred} ok={ok}", file=sys.stderr)
    return {"hits": hits, "n": len(rows), "accuracy": hits / len(rows), "preds": preds}


def run_style(model, tokenizer, name: str, system: str | None, pack: dict) -> dict:
    dest = OUT / name / "style"
    banned = pack["banned"]
    hits = 0
    preds = []
    for it in pack["eval"]:
        raw = generate(model, tokenizer, system, it["user"], 64)
        write_raw(dest, it["id"], raw)
        ok, reasons = score_style(raw, banned)
        hits += int(ok)
        preds.append({"id": it["id"], "raw": raw, "ok": ok, "reasons": reasons})
        print(f"{name} style {it['id']} ok={ok} {reasons}", file=sys.stderr)
    n = len(pack["eval"])
    return {"hits": hits, "n": n, "accuracy": hits / n, "preds": preds}


def run_ood(model, tokenizer, name: str, items: list[dict]) -> dict:
    dest = OUT / name / "ood"
    hits = 0
    collapse = 0
    preds = []
    for it in items:
        raw = generate(model, tokenizer, None, it["user"], 256)
        write_raw(dest, it["id"], raw)
        ok, reasons = score_ood(raw, it["checks"])
        collapsed = "enum_collapse" in reasons
        collapse += int(collapsed)
        hits += int(ok)
        preds.append({"id": it["id"], "raw": raw, "ok": ok, "reasons": reasons})
        print(f"{name} ood {it['id']} ok={ok} {reasons}", file=sys.stderr)
    n = len(items)
    return {
        "hits": hits,
        "n": n,
        "accuracy": hits / n,
        "enum_collapse": collapse,
        "preds": preds,
    }


def dump(report: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "scores.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--facts-base-only", action="store_true")
    parser.add_argument(
        "--day7-adapter",
        default=os.environ.get(
            "DAY7_ADAPTER",
            str(ROOT.parent / "day 07" / "adapter"),
        ),
    )
    args = parser.parse_args()
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    OUT.mkdir(parents=True, exist_ok=True)

    facts_pack = load_json(PROBES / "facts.json")
    fact_items = load_json(PROBES / "facts-eval.json")
    style_pack = load_json(PROBES / "style.json")
    ood_items = load_json(PROBES / "ood.json")
    format_rows = load_jsonl(DATA / "format.jsonl")

    tokenizer = AutoTokenizer.from_pretrained(MODEL, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    report: dict = {}

    print("loading base", file=sys.stderr)
    model = load_base()
    report["base_facts"] = run_facts(
        model, tokenizer, "base_facts", facts_pack["system"], fact_items
    )
    report["base_facts_prompt"] = run_facts(
        model,
        tokenizer,
        "base_facts_prompt",
        facts_pack["system"] + "\n\nKnown facts:\n" + facts_pack["sheet"],
        fact_items,
    )
    if args.facts_base_only:
        dump(report)
        v = report["base_facts"]["verbatim"]["hits"]
        p = report["base_facts"]["paraphrase"]["hits"]
        print(f"base facts verbatim {v}/6 paraphrase {p}/6")
        if v + p != 0:
            raise SystemExit("base already knows planted facts; stop and pick new tokens")
        return

    report["base_format_no_system"] = run_format(
        model, tokenizer, "base_format_no_system", format_rows, False
    )
    report["base_format_with_system"] = run_format(
        model, tokenizer, "base_format_with_system", format_rows, True
    )
    report["base_style"] = run_style(model, tokenizer, "base_style", None, style_pack)
    report["base_style_prompt"] = run_style(
        model, tokenizer, "base_style_prompt", style_pack["system"], style_pack
    )
    report["base_ood"] = run_ood(model, tokenizer, "base_ood", ood_items)
    del model
    torch.cuda.empty_cache()

    day7 = Path(args.day7_adapter)
    if day7.exists():
        print("loading day7", file=sys.stderr)
        base = load_base()
        model = wrap_adapter(base, day7)
        report["day7_format"] = run_format(
            model, tokenizer, "day7_format", format_rows, True
        )
        report["day7_ood"] = run_ood(model, tokenizer, "day7_ood", ood_items)
        del model, base
        torch.cuda.empty_cache()

    for key, path in (("best", ROOT / "adapter"), ("last", ROOT / "adapter-last")):
        if not path.exists():
            print(f"skip {key}, missing {path}", file=sys.stderr)
            continue
        print(f"loading day8 {key}", file=sys.stderr)
        base = load_base()
        model = wrap_adapter(base, path)
        report[f"{key}_facts"] = run_facts(
            model, tokenizer, f"{key}_facts", facts_pack["system"], fact_items
        )
        report[f"{key}_format"] = run_format(
            model, tokenizer, f"{key}_format", format_rows, True
        )
        report[f"{key}_style"] = run_style(
            model, tokenizer, f"{key}_style", style_pack["system"], style_pack
        )
        report[f"{key}_ood"] = run_ood(model, tokenizer, f"{key}_ood", ood_items)
        del model, base
        torch.cuda.empty_cache()

    dump(report)
    lines = ["# Day 8 eval scores", ""]
    def row(label, block, extra=""):
        if not block:
            return
        lines.append(
            f"| {label} | {block['hits']}/{block['n']} | {block['accuracy']:.3f} | {extra} |"
        )

    lines += ["## Format (enum)", "", "| Mode | Hits | Acc | |", "|---|---|---|---|"]
    row("`base` no system", report.get("base_format_no_system"))
    row("`base` + system", report.get("base_format_with_system"))
    row("`day7` + system", report.get("day7_format"))
    row("`day8 best` + system", report.get("best_format"))
    row("`day8 last` + system", report.get("last_format"))

    lines += ["", "## Facts", "", "| Mode | Hits | Acc | split |", "|---|---|---|---|"]
    for k in ("base_facts", "base_facts_prompt", "best_facts", "last_facts"):
        b = report.get(k)
        if not b:
            continue
        extra = (
            f"verbatim {b['verbatim']['hits']}/{b['verbatim']['n']}; "
            f"paraphrase {b['paraphrase']['hits']}/{b['paraphrase']['n']}"
        )
        row(f"`{k}`", b, extra)

    lines += ["", "## Style", "", "| Mode | Hits | Acc | |", "|---|---|---|---|"]
    row("`base`", report.get("base_style"))
    row("`base` + style system", report.get("base_style_prompt"))
    row("`day8 best`", report.get("best_style"))
    row("`day8 last`", report.get("last_style"))

    lines += ["", "## OOD", "", "| Mode | Hits | Acc | enum collapse |", "|---|---|---|---|"]
    for k in ("base_ood", "day7_ood", "best_ood", "last_ood"):
        b = report.get(k)
        if b:
            row(f"`{k}`", b, f"collapse {b['enum_collapse']}/{b['n']}")

    text = "\n".join(lines) + "\n"
    (OUT / "scores.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
