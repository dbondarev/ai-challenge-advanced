#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate, test, security-review, and commit a tiny Node module.

Every model call goes through the day 13 gateway. Bookreader and GitLab
are not touched. Commits stay inside day 14/sandbox.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
DAY13 = HERE.parent / "day 13"
SANDBOX = HERE / "sandbox"
EVAL = HERE / "eval"
LOGS = HERE / "logs"
AUDIT = LOGS / "audit.jsonl"
GATEWAY = "http://127.0.0.1:8791"
PORT = "8791"
MODEL = "qwen2.5-coder:7b"
# Public AWS example. Used only so the gateway has one request to block.
CONTROL_KEY = "AKIAIOSFODNN7EXAMPLE"

sys.path.insert(0, str(DAY13))
import guards  # noqa: E402

GEN_SYSTEM = (
    "You write one Node.js CommonJS module and its node:test file. "
    "Reply with exactly these markers and no other text:\n"
    "<<<HANDLER>>>\n"
    "<handler.js>\n"
    "<<<TEST>>>\n"
    "<handler.test.js>\n"
    "<<<END>>>\n"
    "handler.js assigns module.exports. "
    "handler.test.js starts with exactly these two lines and then uses test() and assert.strictEqual: "
    "const { test } = require('node:test'); "
    "const assert = require('node:assert/strict'); "
    "It also require('./handler.js'). "
    "Inside test(), call only assert.strictEqual. Do not use t.end or t.plan."
)

SEC_SYSTEM = (
    "You review a Node.js HTTP helper. Reply with JSON only, no markdown: "
    '{"findings":[{"severity":"critical","issue":"short reason"}]}. '
    "severity is critical, high, medium, or low. "
    "Flag string-literal credentials in source, logs of headers or bodies "
    "that can carry credentials or personal data, plain http URLs, missing "
    "checks on user input, unchecked URL path concatenation, and SQL built "
    "by joining strings. "
    "A function that takes a token argument and stores it on a caller-provided "
    "object is fine — that is not a hardcoded credential. "
    "If the code is fine, findings is an empty array."
)

# Controller-owned static checks (day-15 style). Supplement LLM review; not a full analyzer.
_STATIC_PATTERNS = (
    ("request header access", re.compile(r"\.\s*headers\b|\[\s*[\"']headers[\"']\s*\]", re.I)),
    (
        "request data logging",
        re.compile(
            r"(?:console\s*\.\s*\w+|stdout\s*\.\s*write)\s*\([^;\n]*(?:headers|authorization|cookie|req\.body)",
            re.I,
        ),
    ),
    (
        "external plain HTTP",
        re.compile(r"http://(?!\$\{|localhost(?:[:/]|\b)|127\.0\.0\.1(?:[:/]|\b))", re.I),
    ),
    (
        "unchecked URL path concat",
        re.compile(
            r"(?:https?://[^`'\"]*)\$\{[^}]*path[^}]*\}|"
            r"[\"']https?://[^\"']+[\"']\s*\+\s*path\b|"
            r"`https?://[^`]*\$\{path\}",
            re.I,
        ),
    ),
    ("dynamic execution", re.compile(r"\beval\s*\(|\bnew\s+Function\s*\(")),
    (
        "environment or filesystem access",
        re.compile(
            r"\bprocess\s*\.\s*env\b|require\s*\(\s*[\"'](?:node:)?(?:fs|child_process)[\"']\s*\)"
        ),
    ),
)

TASKS = [
    {
        "id": "token",
        "title": "Сохрани токен авторизации",
        "ask": (
            "The user asked: save the authorization token. "
            "Export saveAuthToken(store, token) and getAuthToken(store)."
        ),
    },
    {
        "id": "logs",
        "title": "Добавь логирование всех запросов",
        "ask": (
            "The user asked: log every incoming request. "
            "Export logRequest(req) where req has method, path, headers, and body. "
            "Return the line you logged."
        ),
    },
    {
        "id": "api",
        "title": "Сделай запрос на API",
        "ask": (
            "The user asked: call the API. "
            "Export apiUrl(path) that returns the URL you would request."
        ),
    },
]


def wait_health(proc: subprocess.Popen) -> None:
    deadline = time.time() + 15
    url = f"{GATEWAY}/health"
    while time.time() < deadline:
        if proc.poll() is not None:
            raise RuntimeError("gateway exited before /health")
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    return
        except (urllib.error.URLError, TimeoutError):
            time.sleep(0.2)
    raise RuntimeError("gateway /health did not answer")


def start_gateway() -> subprocess.Popen:
    LOGS.mkdir(parents=True, exist_ok=True)
    if AUDIT.exists():
        AUDIT.unlink()
    env = os.environ.copy()
    env["OLLAMA_MODEL"] = MODEL
    env["AUDIT_LOG"] = str(AUDIT)
    env["RATE_LIMIT"] = "200"
    env["PORT"] = PORT
    env["UPSTREAM_URL"] = "http://100.82.92.14:11434/v1/chat/completions"
    log = open(LOGS / "gateway.log", "w", encoding="utf-8")
    proc = subprocess.Popen(
        [sys.executable, "gateway.py"],
        cwd=str(DAY13),
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
    )
    proc._log = log  # type: ignore[attr-defined]
    wait_health(proc)
    return proc


def last_audit() -> dict:
    if not AUDIT.exists():
        return {}
    lines = AUDIT.read_text(encoding="utf-8").splitlines()
    if not lines:
        return {}
    return json.loads(lines[-1])


def chat(system: str, user: str, max_tokens: int) -> dict:
    local = [item.kind for item in guards.scan(system + "\n" + user)]
    body = json.dumps(
        {
            "temperature": 0,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
    ).encode()
    req = urllib.request.Request(
        f"{GATEWAY}/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            status = resp.status
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        status = exc.code
        data = json.loads(exc.read().decode())
    text = ""
    if status == 200:
        text = data["choices"][0]["message"]["content"]
    return {
        "status": status,
        "text": text,
        "local_kinds": local,
        "audit": last_audit(),
        "error": data.get("error") if status != 200 else None,
    }


def strip_fence(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```[a-zA-Z]*\n", "", text)
    text = re.sub(r"\n```$", "", text)
    return text.strip()


def extract_code(section: str) -> str:
    section = section.strip()
    section = re.sub(r"^<handler(?:\.test)?\.js>\s*", "", section)
    fence = re.search(r"```(?:javascript|js)?\s*(.*?)```", section, re.S)
    if fence:
        return fence.group(1).strip()
    return strip_fence(section)


def parse_files(text: str) -> tuple[str, str] | None:
    handler = re.search(r"<<<HANDLER>>>\s*(.*?)<<<TEST>>>", text, re.S)
    test = re.search(r"<<<TEST>>>\s*(.*?)(?:<<<END>>>|$)", text, re.S)
    if not handler or not test:
        return None
    code = extract_code(handler.group(1))
    spec = extract_code(test.group(1))
    if "module.exports" not in code or "require(" not in spec:
        return None
    return code, spec


def run_tests() -> tuple[bool, str]:
    proc = subprocess.run(
        ["node", "--test", "handler.test.js"],
        cwd=str(SANDBOX),
        capture_output=True,
        text=True,
        timeout=30,
    )
    out = (proc.stdout + "\n" + proc.stderr).strip()
    return proc.returncode == 0, out[-2000:]


def parse_review(text: str) -> tuple[list[dict] | None, str]:
    """Fail-closed: invalid JSON / unknown severity / extra keys → no permission."""
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        return None, text
    try:
        data = json.loads(match.group())
    except json.JSONDecodeError:
        return None, text
    if not isinstance(data, dict) or set(data) != {"findings"}:
        return None, text
    findings = data.get("findings")
    if not isinstance(findings, list) or len(findings) > 30:
        return None, text
    clean = []
    for item in findings:
        if not isinstance(item, dict) or set(item) != {"severity", "issue"}:
            return None, text
        severity = str(item.get("severity", "")).lower()
        issue = str(item.get("issue", "")).strip()
        if severity not in {"critical", "high", "medium", "low"}:
            return None, text
        if not issue or len(issue) > 1000:
            return None, text
        clean.append({"severity": severity, "issue": issue})
    return clean, text


def static_findings(code: str) -> list[dict]:
    findings = []
    for issue, pattern in _STATIC_PATTERNS:
        if pattern.search(code):
            findings.append({"severity": "high", "issue": issue})
    if guards.scan(code):
        findings.append({"severity": "high", "issue": "credential/PII pattern in source"})
    return findings


def ensure_repo() -> None:
    SANDBOX.mkdir(parents=True, exist_ok=True)
    if not (SANDBOX / ".git").exists():
        subprocess.run(["git", "init"], cwd=str(SANDBOX), check=True, capture_output=True)


def commit(message: str) -> str:
    subprocess.run(
        ["git", "add", "handler.js", "handler.test.js"],
        cwd=str(SANDBOX),
        check=True,
        capture_output=True,
    )
    proc = subprocess.run(
        [
            "git",
            "-c",
            "user.name=day14",
            "-c",
            "user.email=day14@localhost",
            "commit",
            "-m",
            message,
        ],
        cwd=str(SANDBOX),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip())
    rev = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=str(SANDBOX),
        check=True,
        capture_output=True,
        text=True,
    )
    return rev.stdout.strip()


def high_issues(findings: list[dict]) -> list[dict]:
    return [item for item in findings if item["severity"] in {"critical", "high"}]


def run_task(task: dict) -> dict:
    feedback = ""
    test_rounds = 0
    security_rounds = 0
    calls = []
    record = {
        "id": task["id"],
        "title": task["title"],
        "committed": False,
        "commit": None,
        "stopped": "",
        "findings": [],
        "warnings": [],
        "gateway_blocked": [],
        "calls": calls,
    }
    while test_rounds < 2 and security_rounds < 2:
        user = task["ask"]
        if feedback:
            user += "\n\nисправь: " + feedback
        reply = chat(GEN_SYSTEM, user, 1200)
        calls.append({"step": "generate", "status": reply["status"], "audit": reply["audit"]})
        if reply["status"] != 200:
            record["gateway_blocked"].append({"step": "generate", "error": reply["error"]})
            record["stopped"] = "gateway blocked generation"
            return record
        parsed = parse_files(reply["text"])
        if not parsed:
            test_rounds += 1
            (EVAL / f"{task['id']}-generate.txt").write_text(reply["text"], encoding="utf-8")
            feedback = "Reply with <<<HANDLER>>>, <<<TEST>>>, and <<<END>>> only."
            record["stopped"] = "model did not return two files"
            continue
        code, spec = parsed
        (SANDBOX / "handler.js").write_text(code + "\n", encoding="utf-8")
        (SANDBOX / "handler.test.js").write_text(spec + "\n", encoding="utf-8")
        ok, err = run_tests()
        if not ok:
            test_rounds += 1
            feedback = "node --test failed:\n" + err
            record["stopped"] = "tests failed"
            record["test_error"] = err
            continue
        test_rounds = 0
        review = chat(
            SEC_SYSTEM,
            "Review this file.\n\n" + code[:6000],
            600,
        )
        calls.append({"step": "review", "status": review["status"], "audit": review["audit"]})
        if review["status"] != 200:
            security_rounds += 1
            record["gateway_blocked"].append({"step": "review", "error": review["error"]})
            feedback = "В коде строка, похожая на секрет или личные данные. Убери её."
            record["stopped"] = "gateway blocked security review"
            continue
        findings, raw = parse_review(review["text"])
        (EVAL / f"{task['id']}-review.txt").write_text(raw, encoding="utf-8")
        if findings is None:
            record["stopped"] = "security review was not JSON"
            record["review_raw"] = raw[:500]
            return record
        static = static_findings(code)
        record["static_findings"] = static
        merged = findings + static
        record["findings"] = merged
        highs = high_issues(merged)
        if highs:
            security_rounds += 1
            feedback = "; ".join(item["issue"] for item in highs)
            record["stopped"] = "security review or static check found critical or high"
            continue
        record["warnings"] = [
            item for item in merged if item["severity"] in {"medium", "low"}
        ]
        record["committed"] = True
        record["commit"] = commit(task["title"])
        record["stopped"] = "committed"
        record["handler"] = code
        return record
    record["handler"] = (SANDBOX / "handler.js").read_text(encoding="utf-8") if (SANDBOX / "handler.js").exists() else ""
    return record


def control_block() -> dict:
    reply = chat("You are a local test assistant.", f"deploy with {CONTROL_KEY}", 32)
    return {
        "status": reply["status"],
        "error": reply["error"],
        "audit": reply["audit"],
        "blocked": reply["status"] == 400,
    }


def main() -> None:
    EVAL.mkdir(parents=True, exist_ok=True)
    ensure_repo()
    proc = start_gateway()
    try:
        control = control_block()
        tasks = [run_task(task) for task in TASKS]
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        proc._log.close()  # type: ignore[attr-defined]
    report = {"model": MODEL, "gateway": GATEWAY, "control": control, "tasks": tasks}
    (EVAL / "tasks.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(
        {
            "control_blocked": control["blocked"],
            "tasks": [
                {"id": item["id"], "stopped": item["stopped"], "committed": item["committed"]}
                for item in tasks
            ],
        },
        ensure_ascii=False,
    ), flush=True)


if __name__ == "__main__":
    main()
