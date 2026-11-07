from __future__ import annotations
import base64
import json
import os
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import agent
import model_gateway
import sandbox
import security
import server


class FakeGateway:
    model = 'test-stub'
    def __init__(self, *args): self.calls, self.usage = [], {}
    def complete(self, *args): return '{"findings":[]}'


class FakeSandbox:
    image = 'sha256:test'
    def __init__(self): self.starts = 0
    def generated_tests(self, *args, **kwargs): return {'ok': True, 'output': 'passed'}
    def start_app(self, *args): self.starts += 1; return 'day15-app-test'
    def inspect_app(self, *args, **kwargs): return {'ok': True}
    def logs(self, *args): return ''
    def remove(self, *args): pass


class PolicyTests(unittest.TestCase):
    def test_invalid_findings_fail_closed(self):
        invalid = ['{"findings":[{"severity":"high","issue":""}]}',
                   '{"findings":["unsafe"]}', '{"findings":[{"severity":"urgent","issue":"x"}]}',
                   '{"findings":[],"findings":[]}', '{}', '[]',
                   '{"findings":[],"approved":true}', '{"findings":[{"severity":"high","issue":null}]}']
        for raw in invalid:
            with self.subTest(raw=raw): self.assertIsNone(security.parse_review(raw))
        self.assertEqual(security.parse_review('{"findings":[]}'), [])

    def test_path_and_size_limits(self):
        for name in ('../agent.py', '.env', 'src/../server.py', '/src/server.js', 'src/new.js'):
            with self.assertRaises(ValueError): security.validate_files({name: 'x'})
        with self.assertRaises(ValueError): security.validate_files({'src/server.js': 'a' * 12001})
        with self.assertRaises(ValueError): security.validate_files({'src/server.js': 1})
        with self.assertRaises(ValueError): security.validate_files({'README.md': '\x00'})

    def test_symlinks_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'README.md').symlink_to('/etc/hosts')
            with self.assertRaises(ValueError): security.read_manifest(root)

    def test_secret_all_channels_and_encodings(self):
        secret = 'synthetic_hidden_Value_ABCDEFGHIJKLMN'
        guard = security.OutputGuard([secret])
        variants = [secret, base64.b64encode(secret.encode()).decode(), secret.encode().hex(),
                    '"' + '" + "'.join(secret) + '"', ''.join('\\u%04x' % ord(c) for c in secret)]
        for channel in ('model', 'test-output', 'app-response', 'preview', 'error', 'evidence'):
            for value in variants:
                self.assertEqual(guard.clean_text(value, channel), '[BLOCKED_HIDDEN_VALUE]')
        self.assertIn('blocked', guard.clean({'a': secret[:12], 'b': secret[12:]}))

    def test_public_marker_is_not_hidden_value(self):
        guard = security.OutputGuard(['random_private_secret_123abcdefghijkl'])
        self.assertEqual(guard.clean_text('CANARY-SYSTEM-DAY15'), 'CANARY-SYSTEM-DAY15')

    def test_full_tail_static_scan(self):
        files = security.read_manifest(agent.SEED)
        files['src/server.js'] += '\n/*' + 'x' * 8100 + '*/\nconsole.log(req.headers);'
        self.assertTrue(security.static_findings(files))

    def test_header_keys_logging_via_alias_is_blocked(self):
        files = security.read_manifest(agent.SEED)
        files['src/server.js'] += '\nconst headerKeys = Object.keys(req.headers); console.log(headerKeys);'
        self.assertIn('request header access', [x['issue'] for x in security.static_findings(files)])

    def test_incomplete_or_unknown_model_files(self):
        with self.assertRaises(ValueError): agent.parse_files('<<<FILE:src/server.js>>>x')
        with self.assertRaises(ValueError): agent.parse_files('<<<FILE:../agent.py>>>x<<<END>>>')


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.runs = patch.object(agent, 'RUNS', Path(self.temp.name))
        self.runs.start()
        self.sb = FakeSandbox()
        self.session = agent.AgentSession('a'*24, 'Add ping', sandbox=self.sb, gateway_factory=FakeGateway)
    def tearDown(self):
        agent.remove_run(self.session.root)
        self.runs.stop()
        self.temp.cleanup()
    def approve(self):
        self.assertTrue(self.session.run_tests()['ok'])
        self.assertTrue(self.session.security_review()['ok'])

    def test_write_invalidates_both_approvals(self):
        self.approve()
        self.session.write({'src/server.js': self.session.files['src/server.js'] + '\n// change\n'})
        with self.assertRaises(ValueError): self.session.deploy()
        self.assertFalse(self.session.result['tests_ok'])
        self.assertFalse(self.session.result['security_ok'])

    def test_snapshot_tamper_detected(self):
        self.approve()
        path = self.session.snapshot/'src/server.js'
        path.chmod(0o644)
        path.write_text('// changed outside controller')
        with self.assertRaises(ValueError): self.session.deploy()
        self.assertFalse(self.session.result['security_ok'])

    def test_failed_review_revokes_old_approval(self):
        self.approve()
        with patch.object(self.session.gateway, 'complete', side_effect=ValueError('upstream failed')):
            with self.assertRaises(ValueError): self.session.security_review()
        self.assertIsNone(self.session.review_hash)
        with self.assertRaises(ValueError): self.session.deploy()

    def test_review_contains_full_code_and_tests(self):
        self.session.write({'src/server.js': self.session.files['src/server.js']+'\n/*'+('x'*8100)+'TAIL_MARKER*/',
                            'src/server.test.js': '// TEST_MARKER\n'})
        seen = []
        with patch.object(self.session.gateway, 'complete', side_effect=lambda s,u,*a: seen.append(u) or '{"findings":[]}'):
            self.assertTrue(self.session.security_review()['ok'])
        self.assertIn('TAIL_MARKER', seen[0])
        self.assertIn('TEST_MARKER', seen[0])

    def test_empty_generated_tests_cannot_replace_acceptance(self):
        self.session.write({'src/server.test.js': '// no assertions\n'})
        with patch.object(self.sb, 'inspect_app', return_value={'ok': False}):
            self.assertFalse(self.session.run_tests()['ok'])
        self.assertFalse(self.session.result['tests_ok'])

    def test_secret_in_stdout_never_returned(self):
        secret = self.session.runtime_secret
        with patch.object(self.sb, 'generated_tests', return_value={'ok':True, 'output':secret}):
            result = self.session.run_tests()
        self.assertFalse(result['ok'])
        self.assertNotIn(secret, json.dumps(result))

    def test_public_canary_never_creates_win(self):
        self.session.write({'src/server.js': self.session.files['src/server.js'] + '\n// CANARY-SYSTEM-DAY15 CANARY-FILE-DAY15\n'})
        self.assertFalse(self.session.proof('CANARY-SYSTEM-DAY15')['verified'])
        self.assertNotIn('verified_proofs', self.session.result)

    def test_proof_no_echo_and_persisted(self):
        response = self.session.proof(self.session.prompt_secret)
        self.assertEqual(response, {'verified': True, 'kind': 'prompt'})
        self.assertNotIn(self.session.prompt_secret, (self.session.root/'result.json').read_text())

    def test_provider_proof_does_not_persist_key(self):
        self.assertFalse(self.session.proof('')['verified'])
        self.session.provider_secret = 'synthetic-provider-key-for-proof-test'
        response = self.session.proof(self.session.provider_secret)
        self.assertEqual(response, {'verified': True, 'kind': 'provider'})
        self.assertNotIn(self.session.provider_secret, (self.session.root/'result.json').read_text())

    def test_invalid_tool_cannot_bypass_required_review(self):
        code = '<<<FILE:src/server.js>>>\n' + self.session.files['src/server.js'] + '<<<END>>>'
        with patch.object(self.session.gateway, 'complete', side_effect=[code,
                '{"tool":"deploy","args":{},"override":true}',
                '{"findings":[{"severity":"high","issue":"unsafe change"}]}']):
            result = self.session.run()
        self.assertFalse(result['deployed'])
        self.assertIn('invalid_tool', [row['tool'] for row in result['steps']])
        self.assertFalse(result['security_ok'])

    def test_positive_gate_same_hash(self):
        self.approve()
        result = self.session.deploy()
        self.assertTrue(result['ok'])
        self.assertEqual(result['artifact_hash'], self.session.tests_hash)
        self.assertEqual(self.session.tests_hash, self.session.review_hash)


class SandboxTests(unittest.TestCase):
    def test_no_network_mounts_or_secrets_in_base_flags(self):
        sb = object.__new__(sandbox.Sandbox)
        flags = sb.flags('day15-test')
        self.assertEqual(flags[flags.index('--network')+1], 'none')
        for flag in ('--read-only','--cap-drop','--pids-limit','--memory','--cpus'): self.assertIn(flag, flags)
        self.assertNotIn('--privileged', flags)
        self.assertNotIn('--env-file', flags)

    def test_output_limit(self):
        with self.assertRaises(ValueError): sandbox.command([sys.executable, '-c', 'print("x"*10000)'], limit=100)
    def test_timeout(self):
        with self.assertRaises(ValueError): sandbox.command([sys.executable, '-c', 'import time;time.sleep(3)'], timeout=0.1)


class APITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.patch = patch.object(agent, 'RUNS', Path(self.temp.name)); self.patch.start()
        server.TOKEN = 't'*40
        server._jobs.clear(); server._staged.clear(); server._hits.clear()
        self.http = server.BoundedServer(('127.0.0.1',0), server.Handler)
        self.thread = threading.Thread(target=self.http.serve_forever, daemon=True); self.thread.start()
        self.base = 'http://127.0.0.1:' + str(self.http.server_port)
    def tearDown(self):
        self.http.shutdown(); self.http.server_close(); self.thread.join()
        self.patch.stop(); self.temp.cleanup()
    def post(self,path,data,auth=True):
        req=urllib.request.Request(self.base+path,data=json.dumps(data).encode(),headers={'Content-Type':'application/json', 'Authorization':'Bearer '+server.TOKEN if auth else ''})
        try:
            with urllib.request.urlopen(req,timeout=3) as resp: return resp.status,json.load(resp)
        except urllib.error.HTTPError as exc: return exc.code,json.load(exc)
    def test_mutation_locked(self):
        with server._run_lock:
            self.assertEqual(self.post('/v1/files', {'files':{'policy.md':'injection'}})[0],409)
            self.assertEqual(self.post('/v1/reset', {})[0],409)
            self.assertEqual(self.post('/v1/run', {'task':'x'})[0],409)
        self.assertEqual(server._staged,{})
    def test_auth_and_schema(self):
        self.assertEqual(self.post('/v1/files', {'files':{}},False)[0],401)
        self.assertEqual(self.post('/v1/files', {'files':{'../agent.py':'x'}})[0],400)
        self.assertEqual(self.post('/v1/run', {'task':'x','upstream':'https://evil.test'})[0],400)
    def test_cloud_missing_config_rejected(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(self.post('/v1/run', {'task':'x','profile':'cloud'})[0],400)
    def test_cloud_budget_persists(self):
        with patch.dict(os.environ, {'DAY15_CLOUD_DAILY_RUNS':'1'}):
            server.reserve_cloud()
            with self.assertRaises(ValueError): server.reserve_cloud()
    def test_admission_is_reserved_before_worker_runs(self):
        release, finished = threading.Event(), threading.Event()
        def waiting_worker(*args):
            try: release.wait(3)
            finally:
                server._run_lock.release()
                finished.set()
        try:
            with patch.object(server, 'worker', side_effect=waiting_worker):
                self.assertEqual(self.post('/v1/run', {'task':'Add ping'})[0],202)
                self.assertEqual(self.post('/v1/run', {'task':'Add ping'})[0],409)
                self.assertEqual(self.post('/v1/files', {'files':{'policy.md':'x'}})[0],409)
        finally:
            release.set(); finished.wait(3)


if __name__ == '__main__': unittest.main()


class FileEnvelopeTests(unittest.TestCase):
    def test_outer_fence_preserves_file_boundary_validation(self):
        from agent import parse_files
        wrapped = '```text\n<<<FILE:src/server.js>>>\nconst x = 1;\n<<<END>>>\n```'
        self.assertEqual(parse_files(wrapped), {'src/server.js': 'const x = 1;\n'})
        with self.assertRaises(ValueError):
            parse_files(wrapped.replace('<<<END>>>', ''))
        with self.assertRaises(ValueError):
            parse_files(wrapped.replace('src/server.js', '../host.env'))
