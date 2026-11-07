"use strict";

const http = require("node:http");
const { URL } = require("node:url");

const PORT = Number(process.env.PORT || 18080);
const VERSION = "1.0.0";

function sendJson(res, status, body) {
  const payload = JSON.stringify(body);
  res.writeHead(status, {
    "Content-Type": "application/json; charset=utf-8",
    "Content-Length": Buffer.byteLength(payload),
  });
  res.end(payload);
}

function handler(req, res) {
  const url = new URL(req.url || "/", "http://localhost");
  const path = url.pathname;

  if (req.method === "GET" && path === "/health") {
    return sendJson(res, 200, { ok: true });
  }
  if (req.method === "GET" && path === "/api/version") {
    return sendJson(res, 200, { version: VERSION });
  }
  if (req.method === "GET" && path === "/api/echo") {
    const q = url.searchParams.get("q") || "";
    if (!q || q.length > 200) {
      return sendJson(res, 400, { error: "q too long" });
    }
    return sendJson(res, 200, { q });
  }
  return sendJson(res, 404, { error: "not found" });
}

const server = http.createServer(handler);

if (require.main === module) {
  server.listen(PORT, "0.0.0.0", () => {
    process.stdout.write(`day15-mini-shop listening on ${PORT}\n`);
  });
}

module.exports = { handler, VERSION };
