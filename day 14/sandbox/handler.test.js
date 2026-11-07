const { test } = require('node:test');
const assert = require('node:assert/strict');
const handler = require('./handler.js');

test('apiUrl returns the correct URL', () => {
  assert.strictEqual(handler.apiUrl('/endpoint'), 'https://api.example.com/endpoint');
});
