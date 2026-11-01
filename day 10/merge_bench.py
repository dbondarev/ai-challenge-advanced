#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Merge day-7 gold adapter and bench load time, VRAM, latency. No prod writes."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

ROOT = Path(__file__).resolve().parent
EVAL_JSONL = Path(os.environ.get("EVAL_JSONL", str(ROOT.parent / "day 07" / "data" / "eval.jsonl")))
ADAPTER = Path(os.environ.get("ADAPTER", str(Path.home() / "day07-rerun" / "adapter-gold")))
OUT = Path(os.environ.get("MERGE_OUT", str(Path.home() / "day10-serve")))
MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
SYSTEM = (
    "How does the last IN message change the prospect's status in this LinkedIn "
    "sales thread? Reply with one word: no_change, rejection, not_ta, positive, "
    "mql, sql, meeting_held."
)
N_BENCH = int(os.environ.get("N_BENCH", "68"))


def gpu_mem() -> int:
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            text=True,
        )
        return int(out.strip().splitlines()[0])
    except Exception:
        return 0


def dir_mb(path: Path) -> float:
    total = 0
    if not path.exists():
        return 0.0
    for p in path.rglob("*"):
        if p.is_file():
            total += p.stat().st_size
    return total / (1024 * 1024)


def load_rows() -> list[dict]:
    rows = []
    with EVAL_JSONL.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
            if len(rows) >= N_BENCH:
                break
    return rows


def generate(model, tokenizer, user: str) -> str:
    msgs = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user},
    ]
    prompt = tokenizer.apply_chat_template(
        msgs, tokenize=False, add_generation_prompt=True
    )
    device = next(model.parameters()).device
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    with torch.no_grad():
        out = model.generate(
            input_ids=inputs["input_ids"],
            attention_mask=inputs.get("attention_mask"),
            max_new_tokens=8,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
    return tokenizer.decode(out[0, inputs["input_ids"].shape[1] :], skip_special_tokens=True)


def bench(name: str, model, tokenizer, rows: list[dict]) -> dict:
    # warmup
    generate(model, tokenizer, rows[0]["user"])
    torch.cuda.synchronize()
    t0 = time.time()
    peak = gpu_mem()
    for r in rows:
        generate(model, tokenizer, r["user"])
        peak = max(peak, gpu_mem())
    torch.cuda.synchronize()
    wall = time.time() - t0
    n = len(rows)
    rec = {
        "name": name,
        "n": n,
        "wall_s": wall,
        "ms_per_req": (wall / n) * 1000,
        "peak_vram_mib": peak,
    }
    print(json.dumps(rec), flush=True)
    return rec


def load_fp16():
    tok = AutoTokenizer.from_pretrained(MODEL, trust_remote_code=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    t0 = time.time()
    mem0 = gpu_mem()
    model = AutoModelForCausalLM.from_pretrained(
        MODEL,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,
    )
    torch.cuda.synchronize()
    return tok, model, time.time() - t0, gpu_mem() - mem0, gpu_mem()


def main() -> None:
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    OUT.mkdir(parents=True, exist_ok=True)
    rows = load_rows()
    report: dict = {"adapter": str(ADAPTER), "eval_slice": N_BENCH, "modes": []}

    print("=== base fp16 ===", flush=True)
    tok, model, load_s, _, vram = load_fp16()
    rec = bench("base_fp16", model, tok, rows)
    rec["load_s"] = load_s
    rec["disk_mb"] = None
    rec["vram_after_load_mib"] = vram
    report["modes"].append(rec)
    del model
    torch.cuda.empty_cache()

    print("=== peft adapter ===", flush=True)
    tok, base, load_base_s, _, _ = load_fp16()
    t1 = time.time()
    model = PeftModel.from_pretrained(base, str(ADAPTER))
    torch.cuda.synchronize()
    load_s = load_base_s + (time.time() - t1)
    rec = bench("peft_adapter", model, tok, rows)
    rec["load_s"] = load_s
    rec["disk_mb"] = round(dir_mb(ADAPTER), 1)
    rec["vram_after_load_mib"] = gpu_mem()
    report["modes"].append(rec)

    print("=== merge ===", flush=True)
    t0 = time.time()
    merged = model.merge_and_unload()
    merge_s = time.time() - t0
    merged_dir = OUT / "merged-fp16"
    if merged_dir.exists():
        shutil.rmtree(merged_dir)
    t1 = time.time()
    merged.save_pretrained(merged_dir)
    tok.save_pretrained(merged_dir)
    save_s = time.time() - t1
    rec = bench("merged_fp16_inmem", merged, tok, rows)
    rec["load_s"] = load_s
    rec["merge_s"] = merge_s
    rec["save_s"] = save_s
    rec["disk_mb"] = round(dir_mb(merged_dir), 1)
    rec["vram_after_load_mib"] = gpu_mem()
    report["modes"].append(rec)
    del merged, model, base
    torch.cuda.empty_cache()

    print("=== reload merged from disk ===", flush=True)
    t0 = time.time()
    tok = AutoTokenizer.from_pretrained(merged_dir, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        merged_dir,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,
    )
    torch.cuda.synchronize()
    load_s = time.time() - t0
    rec = bench("merged_fp16_reload", model, tok, rows)
    rec["load_s"] = load_s
    rec["disk_mb"] = round(dir_mb(merged_dir), 1)
    rec["vram_after_load_mib"] = gpu_mem()
    report["modes"].append(rec)
    del model
    torch.cuda.empty_cache()

    print("=== 4bit + adapter ===", flush=True)
    t0 = time.time()
    tok = AutoTokenizer.from_pretrained(MODEL, trust_remote_code=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )
    base = AutoModelForCausalLM.from_pretrained(
        MODEL,
        quantization_config=bnb,
        device_map="auto",
        torch_dtype=torch.float16,
        trust_remote_code=True,
    )
    model = PeftModel.from_pretrained(base, str(ADAPTER))
    torch.cuda.synchronize()
    load_s = time.time() - t0
    rec = bench("bnb4_adapter", model, tok, rows)
    rec["load_s"] = load_s
    rec["disk_mb"] = round(dir_mb(ADAPTER), 1)
    rec["vram_after_load_mib"] = gpu_mem()
    report["modes"].append(rec)

    gguf_tools = []
    for cmd in ("llama-quantize", "convert_hf_to_gguf.py", "which"):
        pass
    which = subprocess.run(["bash", "-lc", "command -v llama-quantize; command -v ollama; ls /usr/local/bin/convert* 2>/dev/null; ls ~/llama.cpp/convert_hf_to_gguf.py 2>/dev/null"], capture_output=True, text=True)
    report["gguf_probe"] = which.stdout.strip() or which.stderr.strip()
    report["ollama_tags"] = ""
    try:
        tags = subprocess.check_output(["curl", "-sS", "http://127.0.0.1:11434/api/tags"], text=True, timeout=5)
        report["ollama_tags"] = tags[:500]
    except Exception as exc:
        report["ollama_error"] = str(exc)

    (OUT / "bench.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("wrote", OUT / "bench.json")


if __name__ == "__main__":
    main()
