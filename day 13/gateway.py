#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OpenAI-compatible proxy in front of local Ollama. No OpenAI or Anthropic calls."""

from __future__ import annotations

import json
import os
import threading
import time
import urllib.error
import urllib.request
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import guards

HERE = Path(__file__).resolve().parent
UPSTREAM = os.environ.get(
    "UPSTREAM_URL", "http://100.82.92.14:11434/v1/chat/completions"
)
MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")
RATE_LIMIT = int(os.environ.get("RATE_LIMIT", "30"))
AUDIT_PATH = Path(os.environ.get("AUDIT_LOG", str(HERE / "logs" / "audit.jsonl")))
INPUT_USD_PER_M = 0.10
OUTPUT_USD_PER_M = 0.40
WINDOW_S = 60.0

_lock = threading.Lock()
_hits: dict[str, deque[float]] = {}


def cost_usd(prompt_tokens: int, completion_tokens: int) -> float:
    return (prompt_tokens / 1_000_000) * INPUT_USD_PER_M + (
        completion_tokens / 1_000_000
    ) * OUTPUT_USD_PER_M


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4) if text else 0


def _allow(ip: str) -> bool:
    now = time.time()
    with _lock:
        bucket = _hits.setdefault(ip, deque())
        while bucket and now - bucket[0] >= WINDOW_S:
            bucket.popleft()
        if len(bucket) >= RATE_LIMIT:
            return False
        bucket.append(now)
        return True


def _audit(row: dict) -> None:
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(row, ensure_ascii=False) + "\n"
    with _lock:
        with AUDIT_PATH.open("a", encoding="utf-8") as fh:
            fh.write(line)


def _kinds(findings: list[guards.Finding]) -> list[str]:
    seen: list[str] = []
    for item in findings:
        if item.kind not in seen:
            seen.append(item.kind)
    return seen


class App:
    def __init__(self, upstream: str, model: str) -> None:
        self.upstream = upstream
        self.model = model

    def forward(self, payload: dict) -> dict:
        body = dict(payload)
        body["model"] = self.model
        data = json.dumps(body).encode()
        req = urllib.request.Request(
            self.upstream,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=180) as resp:
            return json.loads(resp.read().decode())


def make_handler(app: App):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, fmt: str, *args) -> None:
            return

        def _send(self, code: int, payload: dict) -> None:
            raw = json.dumps(payload, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self) -> None:  # noqa: N802
            if self.path.split("?", 1)[0] != "/health":
                self._send(404, {"error": {"message": "not found"}})
                return
            self._send(200, {"ok": True, "model": app.model})

        def do_POST(self) -> None:  # noqa: N802
            if self.path.split("?", 1)[0] != "/v1/chat/completions":
                self._send(404, {"error": {"message": "not found"}})
                return
            ip = self.client_address[0]
            if not _allow(ip):
                _audit(
                    {
                        "ts": time.time(),
                        "ip": ip,
                        "decision": "rate_limited",
                        "kinds": [],
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "cost_usd": 0,
                    }
                )
                self._send(
                    429,
                    {
                        "error": {
                            "message": f"Rate limit: {RATE_LIMIT} requests per minute.",
                            "type": "rate_limit",
                        }
                    },
                )
                return
            length = int(self.headers.get("Content-Length", "0") or 0)
            raw = self.rfile.read(length) if length else b""
            try:
                payload = json.loads(raw.decode() or "{}")
            except json.JSONDecodeError:
                self._send(400, {"error": {"message": "invalid JSON"}})
                return
            messages = payload.get("messages") or []
            mode = (self.headers.get("X-Guard-Mode") or "block").lower()
            text = guards.message_text(messages)
            findings = guards.scan(text)
            if findings and mode != "redact":
                redacted = guards.redact(text, findings)
                _audit(
                    {
                        "ts": time.time(),
                        "ip": ip,
                        "decision": "blocked",
                        "mode": "block",
                        "kinds": _kinds(findings),
                        "preview": redacted[:160],
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "cost_usd": 0,
                    }
                )
                self._send(
                    400,
                    {
                        "error": {
                            "message": "Request blocked: secret detected. Nothing was sent to the model.",
                            "type": "input_guard",
                            "kinds": _kinds(findings),
                        }
                    },
                )
                return
            if findings and mode == "redact":
                for message in messages:
                    content = message.get("content")
                    if isinstance(content, str):
                        message["content"] = guards.redact(content, guards.scan(content))
                payload["messages"] = messages
            try:
                data = app.forward(payload)
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                _audit(
                    {
                        "ts": time.time(),
                        "ip": ip,
                        "decision": "upstream_error",
                        "kinds": _kinds(findings),
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "cost_usd": 0,
                        "error": str(exc),
                    }
                )
                self._send(502, {"error": {"message": "upstream failed", "type": "upstream"}})
                return
            system = guards.system_text(messages)
            output_findings: list[guards.Finding] = []
            for choice in data.get("choices") or []:
                message = choice.get("message") or {}
                content = message.get("content")
                if not isinstance(content, str):
                    continue
                found = guards.scan_output(content, system)
                output_findings.extend(found)
                if found:
                    message["content"] = guards.redact(content, found)
            usage = data.get("usage") or {}
            prompt_tokens = int(usage.get("prompt_tokens") or estimate_tokens(guards.message_text(messages)))
            completion = data.get("choices") or [{}]
            completion_text = ""
            if completion and isinstance(completion[0].get("message", {}).get("content"), str):
                completion_text = completion[0]["message"]["content"]
            completion_tokens = int(usage.get("completion_tokens") or estimate_tokens(completion_text))
            spent = round(cost_usd(prompt_tokens, completion_tokens), 8)
            _audit(
                {
                    "ts": time.time(),
                    "ip": ip,
                    "decision": "redacted" if findings or output_findings else "allowed",
                    "mode": mode,
                    "kinds": _kinds(findings),
                    "output_kinds": _kinds(output_findings),
                    "preview": guards.redact(guards.message_text(messages), guards.scan(guards.message_text(messages)))[:160]
                    if findings
                    else "",
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "cost_usd": spent,
                }
            )
            data["usage"] = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
                "cost_usd": spent,
            }
            self._send(200, data)

    return Handler


def serve(host: str = "127.0.0.1", port: int = 8780) -> ThreadingHTTPServer:
    app = App(UPSTREAM, MODEL)
    httpd = ThreadingHTTPServer((host, port), make_handler(app))
    return httpd


def main() -> None:
    port = int(os.environ.get("PORT", "8780"))
    httpd = serve(port=port)
    print(f"gateway http://127.0.0.1:{httpd.server_address[1]} -> {UPSTREAM}", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
