#!/usr/bin/env python3
"""Run Day 1 / Day 2 prompts against Ollama on nv307001. No secrets."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

WORKSPACE = Path("/Users/dbondarev/Library/CloudStorage/OneDrive-Personal/dbondarev workspace")
BOOKREADER = WORKSPACE / "bookreader"
DAY = WORKSPACE / "ai-challenge-advanced" / "day 04"
OLLAMA = "http://100.82.92.14:11434"

MODELS = [
    {"id": "qwen2.5-coder:7b", "slug": "qwen25-coder-7b", "num_ctx": 8192},
    {"id": "deepseek-coder:6.7b", "slug": "deepseek-coder-67b", "num_ctx": 8192},
    {"id": "qwen2.5:14b", "slug": "qwen25-14b", "num_ctx": 4096},
]

TEMPERATURE = 0.2
TOP_P = 0.9
NUM_PREDICT = 3072

FEATURE_FILES = [
    "apps/api/src/library.ts",
    "apps/api/src/app.ts",
    "apps/web/src/pages/LibraryPage.tsx",
    "apps/web/src/api.ts",
    "apps/api/test/library.test.ts",
]
BUGFIX_FILES = [
    "apps/api/src/library.ts",
    "apps/api/test/progress.test.ts",
    "apps/api/src/app.ts",
]
RESEARCH_FILES = [
    "apps/api/src/app.ts",
    "apps/api/src/library.ts",
    "apps/api/src/server.ts",
    "packages/shared/src/index.ts",
]


def read_text(path: Path) -> str:
    return path.read_bytes().replace(b"\r\n", b"\n").decode("utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.replace("\r\n", "\n").encode("utf-8"))


CLAUDE = read_text(BOOKREADER / "CLAUDE.md")
SYSTEM = """You are a local coding assistant for the Bookreader repo. Follow CLAUDE.md and these hard rules:

- Progress is per bookId. Never one global row or localStorage.progress.
- List filters belong on GET /books. q matches title or any author after JSON.parse, case-insensitive, in memory. Do not LIKE the authors JSON column.
- The search field on LibraryPage has a visible <label>, not only a placeholder.
- No any, no console.log, no raw SQL in Library/routes/pages, no EPUB parse in a page.
- Do not edit scripts/check.sh. Do not add sign-in, fb2, or mobi.
- Views fetch through apps/web/src/api.ts.

When you change code, output every changed file in full (not a patch) using this wrapper:

===FILE path/relative/to/bookreader===
<complete file>
===END===

You may add a short Cause/Fix/Verified or review sections AFTER the files if the user asked for that shape.
"""
SYSTEM_FULL = SYSTEM + "\n\n# CLAUDE.md\n\n" + CLAUDE

FEATURE_PROMPT = read_text(WORKSPACE / "ai-challenge-advanced/day 01/prompt.txt").strip()
BUGFIX_PROMPT = read_text(WORKSPACE / "ai-challenge-advanced/day 02/prompt-bug-fix.txt").strip()
BUGFIX_PROFILE = read_text(WORKSPACE / "ai-challenge-advanced/day 02/profiles/bug-fix.md")
RESEARCH_PROMPT = read_text(WORKSPACE / "ai-challenge-advanced/day 02/prompt-research.txt").strip()
RESEARCH_PROFILE = read_text(WORKSPACE / "ai-challenge-advanced/day 02/profiles/research.md")
REVIEW_PROMPT = read_text(WORKSPACE / "ai-challenge-advanced/day 02/prompt-review.txt").strip()
REVIEW_PROFILE = read_text(WORKSPACE / "ai-challenge-advanced/day 02/profiles/review.md")
REVIEW_DIRTY = read_text(
    WORKSPACE / "ai-challenge-advanced/day 02/review/apps/web/src/pages/ReaderPage.tsx"
)

PLANT_OLD = """    this.store.db
      .insert(progress)
      .values({ bookId: id, spineIndex, scrollRatio, updatedAt })
      .onConflictDoUpdate({
        target: progress.bookId,
        set: { spineIndex, scrollRatio, updatedAt },
      })
      .run();"""
PLANT_NEW = """    this.store.db.delete(progress).run();
    this.store.db.insert(progress).values({ bookId: id, spineIndex, scrollRatio, updatedAt }).run();"""


def pack_files(root: Path, rels: list[str]) -> str:
    chunks = []
    for rel in rels:
        chunks.append(f"### {rel}\n```\n{read_text(root / rel)}\n```")
    return "\n\n".join(chunks)


def copy_tree(dest: Path, plant_bug: bool) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    subprocess.check_call(
        [
            "rsync",
            "-a",
            "--exclude",
            "node_modules",
            "--exclude",
            ".git",
            "--exclude",
            "data",
            "--exclude",
            "dist",
            "--exclude",
            ".continue",
            str(BOOKREADER) + "/",
            str(dest) + "/",
        ]
    )
    os.symlink(BOOKREADER / "node_modules", dest / "node_modules")
    if plant_bug:
        lib = dest / "apps/api/src/library.ts"
        text = read_text(lib)
        if PLANT_OLD not in text:
            raise SystemExit("plant pattern missing in library.ts")
        write_text(lib, text.replace(PLANT_OLD, PLANT_NEW, 1))


def parse_files(reply: str) -> dict[str, str]:
    found: dict[str, str] = {}
    for match in re.finditer(
        r"===FILE\s+([^\n=]+)===\n(.*?)===END===",
        reply,
        re.S,
    ):
        rel = match.group(1).strip().lstrip("./")
        found[rel] = match.group(2)
    if found:
        return found
    for match in re.finditer(
        r"```(?:[\w.+-]+)?\s+([^\n]+)\n(.*?)```",
        reply,
        re.S,
    ):
        rel = match.group(1).strip().strip("`").lstrip("./")
        if "/" in rel or rel.endswith((".ts", ".tsx", ".js")):
            found[rel] = match.group(2)
    return found


def allowed(rel: str) -> bool:
    if rel in {"scripts/check.sh", "package.json"}:
        return False
    if ".." in Path(rel).parts:
        return False
    return rel.startswith(("apps/", "packages/"))


def apply_files(root: Path, files: dict[str, str]) -> list[str]:
    applied = []
    for rel, body in files.items():
        rel = rel.replace("\\", "/").lstrip("/")
        if rel.startswith("bookreader/"):
            rel = rel[len("bookreader/") :]
        if not allowed(rel):
            continue
        target = root / rel
        if not str(target.resolve()).startswith(str(root.resolve())):
            continue
        write_text(target, body.rstrip() + "\n")
        applied.append(rel)
    return applied


def chat(model: str, system: str, user: str, num_ctx: int, timeout: int = 300) -> dict:
    payload = {
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "options": {
            "temperature": TEMPERATURE,
            "top_p": TOP_P,
            "num_ctx": num_ctx,
            "num_predict": NUM_PREDICT,
        },
    }
    req = urllib.request.Request(
        OLLAMA + "/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        ms = int((time.time() - t0) * 1000)
        content = (body.get("message") or {}).get("content") or ""
        return {
            "ok": True,
            "ms": ms,
            "content": content,
            "eval_count": body.get("eval_count"),
            "eval_duration": body.get("eval_duration"),
            "error": None,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "ms": int((time.time() - t0) * 1000),
            "content": "",
            "eval_count": None,
            "eval_duration": None,
            "error": str(exc),
        }


def run_check(root: Path) -> dict:
    t0 = time.time()
    proc = subprocess.run(
        ["zsh", "scripts/check.sh"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    return {
        "exit": proc.returncode,
        "ms": int((time.time() - t0) * 1000),
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def save_run(folder: Path, meta: dict, reply: str, check: dict | None) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    write_text(folder / "reply.md", reply)
    write_text(folder / "meta.json", json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
    if check is not None:
        write_text(
            folder / "check.log",
            (check.get("stdout") or "") + (check.get("stderr") or ""),
        )


def quality_feature(root: Path) -> dict:
    lib = read_text(root / "apps/api/src/library.ts")
    page = read_text(root / "apps/web/src/pages/LibraryPage.tsx")
    app = read_text(root / "apps/api/src/app.ts")
    api = read_text(root / "apps/web/src/api.ts")
    like_json = "like(" in lib.lower() or "LIKE" in lib
    parsed_authors = "authors.some" in lib or "JSON.parse" in lib
    label = "<label" in page
    query = "q" in app and "list(" in app
    return {
        "has_q_on_get_books": "request.query" in app or "q?" in app,
        "calls_list_with_q": "list(q" in app or "list(q)" in app,
        "in_memory_author_filter": parsed_authors and not like_json,
        "likes_authors_json": like_json,
        "visible_label": label,
        "listBooks_passes_q": "q" in api and "listBooks" in api,
    }


def quality_bugfix(root: Path) -> dict:
    lib = read_text(root / "apps/api/src/library.ts")
    return {
        "wipes_whole_table": "delete(progress).run()" in lib.replace(" ", ""),
        "keeps_per_book": "onConflictDoUpdate" in lib
        or "eq(progress.bookId" in lib
        and "delete(progress).run()" not in lib.replace(" ", ""),
    }


def run_code_task(kind: str, model: dict) -> dict:
    dest = DAY / "runs" / f"{kind}-{model['slug']}"
    plant = kind == "bugfix"
    copy_tree(dest, plant_bug=plant)
    if kind == "feature":
        user = (
            FEATURE_PROMPT
            + "\n\nCurrent files:\n\n"
            + pack_files(dest, FEATURE_FILES)
        )
        system = SYSTEM_FULL
    else:
        user = (
            BUGFIX_PROMPT
            + "\n\nCurrent files:\n\n"
            + pack_files(dest, BUGFIX_FILES)
        )
        system = SYSTEM_FULL + "\n\n# Agent profile\n\n" + BUGFIX_PROFILE
    result = chat(model["id"], system, user, model["num_ctx"])
    applied = []
    if result["ok"] and result["content"]:
        applied = apply_files(dest, parse_files(result["content"]))
    check = run_check(dest) if applied else None
    meta = {
        "kind": kind,
        "model": model["id"],
        "num_ctx": model["num_ctx"],
        "temperature": TEMPERATURE,
        "top_p": TOP_P,
        "chat_ok": result["ok"],
        "chat_ms": result["ms"],
        "eval_count": result["eval_count"],
        "error": result["error"],
        "applied": applied,
        "check_exit": None if check is None else check["exit"],
        "check_ms": None if check is None else check["ms"],
        "quality": quality_feature(dest) if kind == "feature" else quality_bugfix(dest),
    }
    save_run(dest / "_run", meta, result["content"] or result["error"] or "", check)
    return meta


def run_chat_only(name: str, model: dict, system: str, user: str) -> dict:
    dest = DAY / "runs" / f"{name}-{model['slug']}"
    dest.mkdir(parents=True, exist_ok=True)
    result = chat(model["id"], system, user, model["num_ctx"])
    meta = {
        "kind": name,
        "model": model["id"],
        "num_ctx": model["num_ctx"],
        "chat_ok": result["ok"],
        "chat_ms": result["ms"],
        "eval_count": result["eval_count"],
        "error": result["error"],
    }
    save_run(dest, meta, result["content"] or result["error"] or "", None)
    return meta


def run_fim() -> dict:
    prefix = '''  list(q?: string): Book[] {
    const rows = this.store.db
      .select()
      .from(books)
      .all()
      .map((row) => ({
        id: row.id,
        title: row.title,
        authors: JSON.parse(row.authors) as string[],
        createdAt: row.createdAt,
      }));
    if (!q) {
      return rows;
    }
    const needle = q.toLowerCase();
    return rows.filter(
'''
    suffix = '''
    );
  }
'''
    payload = {
        "model": "qwen2.5-coder:1.5b",
        "prompt": prefix,
        "suffix": suffix,
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 80, "num_ctx": 2048},
    }
    req = urllib.request.Request(
        OLLAMA + "/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    ms = int((time.time() - t0) * 1000)
    completion = body.get("response") or ""
    folder = DAY / "runs" / "autocomplete-qwen25-coder-15b"
    folder.mkdir(parents=True, exist_ok=True)
    write_text(
        folder / "fim.md",
        f"# FIM autocomplete qwen2.5-coder:1.5b ({ms} ms)\n\n"
        f"## Prefix\n\n```ts\n{prefix}\n```\n\n"
        f"## Suffix\n\n```ts\n{suffix}\n```\n\n"
        f"## Completion\n\n```ts\n{completion}\n```\n",
    )
    meta = {"model": "qwen2.5-coder:1.5b", "ms": ms, "completion": completion}
    write_text(folder / "meta.json", json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
    return meta


def main() -> None:
    DAY.mkdir(parents=True, exist_ok=True)
    shutil.copy2(BOOKREADER / ".continue/config.yaml", DAY / "continue-config.yaml")
    results = []
    for model in MODELS:
        print("FEATURE", model["id"], flush=True)
        results.append(run_code_task("feature", model))
        print("BUGFIX", model["id"], flush=True)
        results.append(run_code_task("bugfix", model))
    best = "qwen2.5-coder:7b"
    feature_pass = [r for r in results if r["kind"] == "feature" and r.get("check_exit") == 0]
    if feature_pass:
        best = min(feature_pass, key=lambda r: r["chat_ms"])["model"]
    best_model = next(m for m in MODELS if m["id"] == best)
    print("RESEARCH", best, flush=True)
    results.append(
        run_chat_only(
            "research",
            best_model,
            SYSTEM_FULL + "\n\n# Agent profile\n\n" + RESEARCH_PROFILE,
            RESEARCH_PROMPT + "\n\nCurrent files:\n\n" + pack_files(BOOKREADER, RESEARCH_FILES),
        )
    )
    print("REVIEW", best, flush=True)
    results.append(
        run_chat_only(
            "review",
            best_model,
            SYSTEM_FULL + "\n\n# Agent profile\n\n" + REVIEW_PROFILE,
            REVIEW_PROMPT
            + "\n\n### apps/web/src/pages/ReaderPage.tsx\n```\n"
            + REVIEW_DIRTY
            + "\n```\n",
        )
    )
    print("FIM", flush=True)
    fim = run_fim()
    write_text(
        DAY / "runs/summary.json",
        json.dumps({"results": results, "fim": fim, "best": best}, indent=2, ensure_ascii=False)
        + "\n",
    )
    print(json.dumps({"best": best, "n": len(results)}, indent=2))


if __name__ == "__main__":
    main()
