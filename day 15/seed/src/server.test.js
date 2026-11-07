"use strict";

const { test } = require("node:test");
const assert = require("node:assert/strict");
const http = require("node:http");
const { handler, VERSION } = require("./server.js");

function request(method, path) {
  return new Promise((resolve, reject) => {
    const server = http.createServer(handler);
    server.listen(0, "127.0.0.1", () => {
      const { port } = server.address();
      const req = http.request(
        { hostname: "127.0.0.1", port, path, method },
        (res) => {
          let body = "";
          res.setEncoding("utf8");
          res.on("data", (chunk) => {
            body += chunk;
          });
          res.on("end", () => {
            server.close();
            resolve({ status: res.statusCode, body: JSON.parse(body) });
          });
        }
      );
      req.on("error", (err) => {
        server.close();
        reject(err);
      });
      req.end();
    });
  });
}

test("health ok", async () => {
  const res = await request("GET", "/health");
  assert.equal(res.status, 200);
  assert.equal(res.body.ok, true);
});

test("version", async () => {
  const res = await request("GET", "/api/version");
  assert.equal(res.status, 200);
  assert.equal(res.body.version, VERSION);
});

test("echo", async () => {
  const res = await request("GET", "/api/echo?q=hello");
  assert.equal(res.status, 200);
  assert.equal(res.body.q, "hello");
});
