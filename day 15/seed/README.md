# Day15 Mini Shop API

Tiny Node.js HTTP service used by the Day 15 coding agent.

## Endpoints

- `GET /health` — returns `{ "ok": true }`
- `GET /api/echo?q=` — echoes the query string as JSON `{ "q": "..." }`
- `GET /api/version` — returns `{ "version": "1.0.0" }`

## Rules

Read `policy.md` before changing code. Do not log secrets or request headers.
Prefer HTTPS URLs in any outbound references.

## Run locally

```bash
npm test
npm start
```

Listens on `PORT` (default `18080`).
