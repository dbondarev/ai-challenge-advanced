"""Untrusted JavaScript only runs in isolated, resource-limited Docker containers."""
from __future__ import annotations
import json
import os
import selectors
import subprocess
import time
import uuid


def command(argv, timeout=30, limit=65536):
    env = {k: os.environ[k] for k in ('PATH', 'HOME', 'DOCKER_HOST', 'DOCKER_CONTEXT') if k in os.environ}
    proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, env=env)
    result = bytearray()
    deadline = time.monotonic() + timeout
    with selectors.DefaultSelector() as selector:
        selector.register(proc.stdout, selectors.EVENT_READ)
        try:
            while selector.get_map():
                if time.monotonic() >= deadline:
                    raise ValueError('command timeout')
                for key, _ in selector.select(min(0.1, deadline - time.monotonic())):
                    chunk = os.read(key.fd, 8192)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    result.extend(chunk)
                    if len(result) > limit:
                        raise ValueError('command output budget exceeded')
            proc.wait(timeout=max(0.1, deadline - time.monotonic()))
            return proc.returncode, result.decode('utf-8', errors='replace')
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=5)
            proc.stdout.close()


class Sandbox:
    def __init__(self, image=None):
        tag = image or os.environ.get('DAY15_RUNNER_IMAGE', 'day15-runner:v2')
        code, raw = command(['docker', 'image', 'inspect', '--format', '{{.Id}}', tag])
        if code or not raw.strip().startswith('sha256:'):
            raise ValueError('trusted runner image missing; build deploy/Dockerfile first')
        self.image = raw.strip()

    def flags(self, name, network='none'):
        return ['docker', 'run', '--name', name, '--label', 'day15.managed=v2', '--pull', 'never',
                '--network', network, '--read-only', '--user', '1000:1000', '--cap-drop', 'ALL',
                '--security-opt', 'no-new-privileges:true', '--memory', '192m', '--memory-swap', '192m',
                '--cpus', '0.5', '--pids-limit', '64', '--ulimit', 'nofile=256:256',
                '--tmpfs', '/tmp:rw,noexec,nosuid,size=16m,mode=1777',
                '--log-driver', 'local', '--log-opt', 'max-size=64k', '--log-opt', 'max-file=1', '--log-opt', 'compress=false']

    def remove(self, name):
        if name and name.startswith('day15-'):
            command(['docker', 'rm', '-f', name], timeout=15)

    def mount(self, snapshot):
        if ',' in str(snapshot):
            raise ValueError('unsupported snapshot path')
        return ['--mount', f'type=bind,src={snapshot.resolve()},dst=/app,readonly', '--workdir', '/app']

    def generated_tests(self, snapshot, secret, timeout=30):
        name = 'day15-test-' + uuid.uuid4().hex[:12]
        args = self.flags(name) + self.mount(snapshot) + ['--env', 'DAY15_FAKE_SECRET=' + secret,
                self.image, 'node', '--test', 'src/server.test.js']
        try:
            code, text = command(args, timeout=timeout)
            return {'ok': code == 0, 'output': text}
        finally:
            self.remove(name)

    def start_app(self, snapshot, secret):
        name = 'day15-app-' + uuid.uuid4().hex[:12]
        args = self.flags(name) + ['-d'] + self.mount(snapshot) + ['--env', 'PORT=18080',
                '--env', 'DAY15_FAKE_SECRET=' + secret, self.image, 'node', 'src/server.js']
        try:
            code, _ = command(args)
            if code:
                raise ValueError('sandbox app failed to start')
            return name
        except Exception:
            self.remove(name)
            raise

    def inspect_app(self, app, mode, argument, timeout=30):
        if mode not in ('check', 'request'):
            raise ValueError('invalid checker mode')
        name = 'day15-check-' + uuid.uuid4().hex[:12]
        args = self.flags(name, 'container:' + app) + [self.image, 'node', '/opt/day15/check.cjs', mode, argument]
        try:
            code, raw = command(args, timeout=timeout, limit=32768)
            try:
                result = json.loads(raw)
            except ValueError:
                raise ValueError('trusted checker returned invalid result') from None
            if not isinstance(result, dict) or code:
                raise ValueError('trusted checker failed')
            return result
        finally:
            self.remove(name)

    def logs(self, app):
        _, raw = command(['docker', 'logs', '--tail', '100', app], limit=65536)
        return raw

    def stop_all(self):
        code, raw = command(['docker', 'ps', '-aq', '--filter', 'label=day15.managed=v2'])
        if not code:
            for container in raw.split():
                command(['docker', 'rm', '-f', container], timeout=15)
