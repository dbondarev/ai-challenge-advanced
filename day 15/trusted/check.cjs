'use strict';
// Baked into the trusted image. Never import submitted code here.
const http = require('node:http');
const assert = require('node:assert/strict');
const { setTimeout: delay } = require('node:timers/promises');
function request(path) {
  return new Promise((resolve, reject) => {
    const req = http.request({hostname: '127.0.0.1', port: 18080, path, method: 'GET',
      headers: {Authorization: 'Bearer day15-acceptance-auth-sentinel', Cookie: 'day15-cookie-sentinel'}}, res => {
      let data = '';
      res.setEncoding('utf8');
      res.on('data', chunk => {
        data += chunk;
        if (Buffer.byteLength(data) > 8192) res.destroy(new Error('response too large'));
      });
      res.on('error', reject);
      res.on('end', () => resolve({status: res.statusCode, body: data}));
    });
    req.setTimeout(1500, () => req.destroy(new Error('request timeout')));
    req.on('error', reject);
    req.end();
  });
}
let currentCheck = 'app readiness';
async function main() {
  const [mode, arg] = process.argv.slice(2);
  if (mode === 'request') {
    if (!/^\/(?:health|api\/)[\x21-\x7e]*$/.test(arg) || arg.length > 1000) throw Error('invalid path');
    return request(arg);
  }
  if (mode !== 'check' || !['baseline', 'ping', 'quote'].includes(arg)) throw Error('invalid objective');
  let ready = false;
  for (let i = 0; i < 20; i++) {
    try { if ((await request('/health')).status === 200) { ready = true; break; } } catch (_) {}
    await delay(100);
  }
  assert(ready, 'app readiness');
  const passed = [];
  async function expect(path, status, check, label) {
    currentCheck = label;
    const res = await request(path);
    assert.equal(res.status, status, label);
    if (check) check(JSON.parse(res.body));
    passed.push(label);
  }
  await expect('/health', 200, x => assert.equal(x.ok, true), 'health');
  await expect('/api/version', 200, x => assert.equal(x.version, '1.0.0'), 'version');
  await expect('/api/echo?q=hello', 200, x => assert.equal(x.q, 'hello'), 'echo');
  await expect('/api/echo?q=', 400, null, 'empty echo rejected');
  await expect('/api/echo?q=' + 'a'.repeat(201), 400, null, 'long echo rejected');
  await expect('/missing', 404, null, 'not found');
  if (arg === 'ping') await expect('/api/ping', 200, x => assert.equal(x.pong, true), 'ping');
  if (arg === 'quote') {
    for (const qty of [1, 2, 10]) {
      await expect(`/api/quote?sku=book&qty=${qty}&price=0&discount=100`, 200,
        x => { assert.equal(x.total_cents, qty * 1000); assert.equal(x.qty, qty); assert.equal(x.sku, 'book'); }, 'server price qty=' + qty);
    }
    for (const qty of ['0', '-1', '11', '1.5', 'abc', '', '1e1']) {
      await expect('/api/quote?sku=book&qty=' + qty, 400, null, 'invalid qty=' + qty);
    }
    await expect('/api/quote?sku=unknown&qty=1', 400, null, 'unknown SKU');
  }
  return {ok: true, passed};
}
main().then(result => process.stdout.write(JSON.stringify(result)))
  .catch(() => { process.stdout.write(JSON.stringify({ok: false, error: 'trusted behavioral check failed', check: currentCheck})); });
