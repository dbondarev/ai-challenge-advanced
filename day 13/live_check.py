#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One clean completion through the gateway to local Ollama."""

from __future__ import annotations

import json
import os
import threading
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
os.environ.setdefault("UPSTREAM_URL", "http://100.82.92.14:11434/v1/chat/completions")
os.environ.setdefault("OLLAMA_MODEL", "qwen2.5:7b")
os.environ.setdefault("AUDIT_LOG", str(HERE / "logs" / "audit.jsonl"))
os.environ.setdefault("RATE_LIMIT", "30")

import gateway  # noqa: E402


def main() -> None:
    httpd = gateway.serve("127.0.0.1", 0)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    host, port = httpd.server_address
    body = json.dumps(
        {
            "messages": [
                {"role": "system", "content": "You are a local test assistant. Reply briefly."},
                {"role": "user", "content": "Reply with the single word pong."},
            ]
        }
    ).encode()
    req = urllib.request.Request(
        f"http://{host}:{port}/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    out = HERE / "eval"
    out.mkdir(parents=True, exist_ok=True)
    dest = out / "live.json"
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read().decode())
        text = data["choices"][0]["message"]["content"]
        record = {
            "ok": True,
            "status": resp.status,
            "model": gateway.MODEL,
            "reply": text,
            "usage": data.get("usage"),
        }
    except Exception as exc:  # noqa: BLE001 — recorded for the report
        record = {"ok": False, "error": str(exc), "model": gateway.MODEL}
    dest.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, ensure_ascii=False), flush=True)
    httpd.shutdown()


if __name__ == "__main__":
    main()
