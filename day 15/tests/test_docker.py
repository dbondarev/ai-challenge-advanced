"""Real isolation/acceptance tests. Opt in on the disposable challenge Docker host."""
from __future__ import annotations
import json
import os
from pathlib import Path
import secrets
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import agent
from sandbox import Sandbox, command

class StubGateway:
    model = 'docker-integration-stub'
    def __init__(self, *args): self.calls, self.usage = [], {}
    def complete(self, *args): return '{"findings":[]}'

@unittest.skipUnless(os.environ.get('DAY15_DOCKER_TESTS') == '1', 'set DAY15_DOCKER_TESTS=1 on Docker host')
class DockerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='day15-docker-')
        self.patch = patch.object(agent, 'RUNS', Path(self.tmp.name)); self.patch.start()
        self.sb = Sandbox()
        self.s = agent.AgentSession(secrets.token_hex(12), 'Add ping', sandbox=self.sb, gateway_factory=StubGateway)
    def tearDown(self):
        if self.s.app: self.sb.remove(self.s.app)
        agent.remove_run(self.s.root)
        self.patch.stop(); self.tmp.cleanup()
    def ping(self):
        code = self.s.files['src/server.js'].replace('if (req.method === "GET" && path === "/health") {',
            'if (req.method === "GET" && path === "/api/ping") return sendJson(res, 200, {pong:true});\n  if (req.method === "GET" && path === "/health") {')
        self.s.write({'src/server.js':code})
    def test_real_positive_pipeline_and_container_constraints(self):
        self.ping()
        self.assertTrue(self.s.run_tests()['ok'])
        self.assertTrue(self.s.security_review()['ok'])
        self.assertTrue(self.s.deploy()['ok'])
        response = self.s.app_request('/api/ping')
        self.assertEqual(response['status'],200)
        self.assertTrue(json.loads(response['body'])['pong'])
        code, raw = command(['docker','inspect','--format','{{json .HostConfig}}',self.s.app])
        info=json.loads(raw)
        self.assertEqual(info['NetworkMode'],'none')
        self.assertTrue(info['ReadonlyRootfs'])
        self.assertEqual(info['PidsLimit'],64)
        self.assertEqual(info['Memory'],192*1024*1024)
        self.assertFalse(info['Privileged'])
        self.assertFalse(info['PortBindings'])
    def test_host_env_files_and_network_are_unreachable(self):
        test = '''const assert=require('node:assert/strict');
const fs=require('node:fs'); const net=require('node:net');
assert.equal(process.env.DAY15_TOKEN, undefined);
assert.equal(process.env.DAY15_CLOUD_API_KEY, undefined);
assert.equal(fs.existsSync('/home/cursor/.ssh'), false);
assert.throws(()=>fs.writeFileSync('/app/pwned','x'));
assert.throws(()=>fs.writeFileSync('/opt/day15/check.cjs','x'));
assert.throws(()=>fs.writeFileSync('/outside-workspace','x'));
const socket=net.connect({host:'100.82.92.14',port:22});
socket.on('connect',()=>{process.exitCode=1;socket.destroy();});
socket.on('error',()=>{});
socket.setTimeout(500,()=>socket.destroy());
'''
        self.s.write({'src/server.test.js':test}); self.s.freeze()
        with patch.dict(os.environ, {'DAY15_TOKEN':'host_dummy_auth','DAY15_CLOUD_API_KEY':'host_dummy_cloud'}):
            result=self.sb.generated_tests(self.s.snapshot,self.s.runtime_secret)
        self.assertTrue(result['ok'],result)
    def test_empty_tests_do_not_pass_missing_feature(self):
        self.s.write({'src/server.test.js':'// no assertions\n'})
        self.assertFalse(self.s.run_tests()['ok'])
    def test_timeout_removes_entire_test_container(self):
        self.s.write({'src/server.test.js':'setInterval(()=>{},100);\n'}); self.s.freeze()
        with self.assertRaises(ValueError):
            self.sb.generated_tests(self.s.snapshot,self.s.runtime_secret,timeout=1)
        _, raw=command(['docker','ps','-aq','--filter','name=day15-test-'])
        self.assertEqual(raw.strip(),'')
    def test_actual_runtime_secret_is_blocked_in_stdout(self):
        self.s.write({'src/server.test.js':'console.log(process.env.DAY15_FAKE_SECRET);\n'})
        result=self.s.run_tests()
        self.assertFalse(result['ok'])
        self.assertNotIn(self.s.runtime_secret,json.dumps(result))
    def test_real_quote_acceptance(self):
        self.s.objective='quote'
        code=self.s.files['src/server.js'].replace('if (req.method === "GET" && path === "/health") {', '''if(req.method==='GET' && path==='/api/quote') {
    const sku=url.searchParams.get('sku'); const raw=url.searchParams.get('qty') || '';
    const qty=Number(raw);
    if(sku!=='book' || !/^[0-9]+$/.test(raw) || !Number.isInteger(qty) || qty<1 || qty>10) return sendJson(res,400,{error:'invalid quote'});
    return sendJson(res,200,{sku,qty,total_cents:1000*qty});
  }
  if (req.method === "GET" && path === "/health") {''')
        self.s.write({'src/server.js':code})
        self.assertTrue(self.s.run_tests()['ok'])

if __name__=='__main__': unittest.main()
