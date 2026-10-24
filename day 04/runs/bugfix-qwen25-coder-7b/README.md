# Bookreader

Personal EPUB library and a simple reader. Web + API now. Native iOS, iPad, and Windows clients later talk to the same API.

Add an EPUB, read title and authors from the file, open it, and resume from the saved chapter and scroll.

```
npm install
./scripts/check.sh
npm -w @bookreader/api run dev
npm -w @bookreader/web run dev
```

QA: `./scripts/check.sh` for typecheck, API tests, lint. Smoke scenarios are in `qa/smoke.md` — an agent using Playwright MCP (`qa-runner`) clicks through the UI. After a new feature, use the `update-smoke` skill to extend those scenarios and re-run both levels.
