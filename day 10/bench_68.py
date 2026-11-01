#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Latency on full eval.jsonl (68) plus Ollama GGUF. Writes bench68.json."""

from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

EVAL_JSONL = Path(os.environ.get("EVAL_JSONL", str(Path.home() / "day07-rerun" / "data" / "eval.jsonl")))
ADAPTER = Path(os.environ.get("ADAPTER", str(Path.home() / "day07-rerun" / "adapter-gold")))
MERGED = Path(os.environ.get("MERGE_OUT", str(Path.home() / "day10-serve"))) / "merged-fp16"
OUT = Path(os.environ.get("MERGE_OUT", str(Path.home() / "day10-serve")))
MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
OLLAMA = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
SYSTEM = (
    "How does the last IN message change the prospect's status in this LinkedIn "
    "sales thread? Reply with one word: no_change, rejection, not_ta, positive, "
    "mql, sql, meeting_held."
)


def gpu_mem() -> int:
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            text=True,
        )
        return int(out.strip().splitlines()[0])
    except Exception:
        return 0


def load_rows() -> list[dict]:
    rows = []
    with EVAL_JSONL.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
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


def bench_hf(name: str, model, tokenizer, rows: list[dict], load_s: float, extra: dict | None = None) -> dict:
    generate(model, tokenizer, rows[0]["user"])
    torch.cuda.synchronize()
    t0 = time.time()
    peak = gpu_mem()
    for r in rows:
        generate(model, tokenizer, r["user"])
        peak = max(peak, gpu_mem())
    torch.cuda.synchronize()
    wall = time.time() - t0
    rec = {
        "name": name,
        "n": len(rows),
        "wall_s": wall,
        "ms_per_req": (wall / len(rows)) * 1000,
        "peak_vram_mib": peak,
        "load_s": load_s,
        "vram_after_load_mib": gpu_mem(),
    }
    if extra:
        rec.update(extra)
    print(json.dumps({k: rec[k] for k in ("name", "n", "ms_per_req", "peak_vram_mib", "load_s")}), flush=True)
    return rec


def ollama_chat(user: str, timeout: int = 120) -> str:
    body = json.dumps(
        {
            "model": "nexus-reply-status",
            "temperature": 0,
            "max_tokens": 8,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": user},
            ],
        }
    ).encode()
    req = urllib.request.Request(
        f"{OLLAMA}/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode())
    return data["choices"][0]["message"]["content"]


def main() -> None:
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    rows = load_rows()
    report: dict = {"n": len(rows), "modes": []}

    print("=== ollama q4_k_m ===", flush=True)
    mem0 = gpu_mem()
    t0 = time.time()
    _ = ollama_chat(rows[0]["user"], timeout=180)
    cold_s = time.time() - t0
    vram = gpu_mem()
    t1 = time.time()
    peak = gpu_mem()
    for r in rows:
        ollama_chat(r["user"])
        peak = max(peak, gpu_mem())
    wall = time.time() - t1
    rec = {
        "name": "ollama_q4_k_m",
        "n": len(rows),
        "wall_s": wall,
        "ms_per_req": (wall / len(rows)) * 1000,
        "peak_vram_mib": peak,
        "load_s": cold_s,
        "vram_after_load_mib": vram,
        "vram_idle_before_mib": mem0,
        "disk_mb": round(
            (OUT / "qwen25-1.5b-reply-status-q4_k_m.gguf").stat().st_size / (1024 * 1024), 1
        ),
    }
    print(json.dumps(rec), flush=True)
    report["modes"].append(rec)
    # unload so HF benches see a free GPU
    unload = json.dumps({"model": "nexus-reply-status", "keep_alive": 0}).encode()
    try:
        urllib.request.urlopen(
            urllib.request.Request(
                f"{OLLAMA}/api/generate",
                data=unload,
                headers={"Content-Type": "application/json"},
                method="POST",
            ),
            timeout=60,
        ).read()
    except Exception as exc:
        print("unload warn", exc, flush=True)
    time.sleep(2)

    print("=== base fp16 ===", flush=True)
    tok = AutoTokenizer.from_pretrained(MODEL, trust_remote_code=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    t0 = time.time()
    model = AutoModelForCausalLM.from_pretrained(
        MODEL, torch_dtype=torch.float16, device_map="auto", trust_remote_code=True
    )
    torch.cuda.synchronize()
    report["modes"].append(bench_hf("base_fp16", model, tok, rows, time.time() - t0))
    del model
    torch.cuda.empty_cache()

    print("=== peft ===", flush=True)
    t0 = time.time()
    base = AutoModelForCausalLM.from_pretrained(
        MODEL, torch_dtype=torch.float16, device_map="auto", trust_remote_code=True
    )
    model = PeftModel.from_pretrained(base, str(ADAPTER))
    torch.cuda.synchronize()
    report["modes"].append(
        bench_hf("peft_adapter", model, tok, rows, time.time() - t0, extra={"disk_mb": 46.2})
    )
    del model, base
    torch.cuda.empty_cache()

    print("=== merged fp16 ===", flush=True)
    t0 = time.time()
    tok = AutoTokenizer.from_pretrained(MERGED, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        MERGED, torch_dtype=torch.float16, device_map="auto", trust_remote_code=True
    )
    torch.cuda.synchronize()
    report["modes"].append(
        bench_hf("merged_fp16", model, tok, rows, time.time() - t0, extra={"disk_mb": 2955.3})
    )
    del model
    torch.cuda.empty_cache()

    print("=== bnb4 adapter ===", flush=True)
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
        MODEL, quantization_config=bnb, device_map="auto", torch_dtype=torch.float16, trust_remote_code=True
    )
    model = PeftModel.from_pretrained(base, str(ADAPTER))
    torch.cuda.synchronize()
    report["modes"].append(
        bench_hf("bnb4_adapter", model, tok, rows, time.time() - t0, extra={"disk_mb": 46.2})
    )

    path = OUT / "bench68.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("wrote", path)


if __name__ == "__main__":
    main()
