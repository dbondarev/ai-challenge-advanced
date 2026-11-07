#!/usr/bin/env python3
"""Authenticated bounded API; no exposed model/container network ports."""
from __future__ import annotations
import json
import os
import re
import secrets
import socket
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

import agent
from model_gateway import profiles
from sandbox import Sandbox
from security import TASK_LIMIT, OutputGuard, strict_json, validate_files

TOKEN = os.environ.get('DAY15_TOKEN', '')
HOST = os.environ.get('DAY15_HOST', '127.0.0.1')
PORT = int(os.environ.get('DAY15_PORT', '8787'))
_run_lock = threading.Lock()
_jobs_lock = threading.Lock()
_jobs = {}
_staged = {}
_hits = {}
_hits_lock = threading.Lock()
_public_guard = OutputGuard([TOKEN, os.environ.get('DAY15_CLOUD_API_KEY', '')])
TTL = 3600


def allow(bucket, limit):
    with _hits_lock:
        now = time.monotonic()
        hits = _hits.setdefault(bucket, deque())
        while hits and hits[0] < now - 60: hits.popleft()
        if len(hits) >= limit: return False
        hits.append(now)
        return True


def prune():
    # Called under the admission lock. Bound memory, live containers and disk.
    with _jobs_lock:
        expired = [key for key, job in _jobs.items() if time.time() - job['created_at'] > TTL]
        for key in expired:
            session = _jobs.pop(key).get('session')
            if session: session.retire()
        while len(_jobs) >= 24:
            key = next(iter(_jobs))
            session = _jobs.pop(key).get('session')
            if session: session.retire()
    if agent.RUNS.exists():
        runs = sorted((p for p in agent.RUNS.iterdir() if p.is_dir() and re.fullmatch('[a-f0-9]{24}', p.name)), key=lambda p:p.stat().st_mtime)
        count = len(runs)
        for path in runs:
            if path.name not in _jobs and (time.time()-path.stat().st_mtime > 86400 or count > 100):
                agent.remove_run(path)
                count -= 1


def reserve_cloud():
    path = agent.RUNS / 'cloud-budget.json'
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    day = time.strftime('%Y-%m-%d', time.gmtime())
    data = json.loads(path.read_text()) if path.exists() else {'day': day, 'runs': 0}
    if data.get('day') != day: data = {'day': day, 'runs': 0}
    if data['runs'] >= min(50, int(os.environ.get('DAY15_CLOUD_DAILY_RUNS', '5'))):
        raise ValueError('cloud daily run budget exhausted')
    data['runs'] += 1
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(data), encoding='utf-8')
    temp.chmod(0o600)
    temp.replace(path)


def worker(job_id, task, files, profile, objective):
    try:
        session = agent.AgentSession(job_id, task, files, profile, objective)
        with _jobs_lock:
            _jobs[job_id].update(status='running', session=session)
        result = session.run()
        with _jobs_lock:
            _jobs[job_id].update(status='done', result=result, finished_at=time.time())
    except Exception as exc:
        with _jobs_lock:
            _jobs[job_id].update(status='error', error=type(exc).__name__, finished_at=time.time())
    finally:
        _run_lock.release()


class BoundedServer(ThreadingHTTPServer):
    daemon_threads = True
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.slots = threading.BoundedSemaphore(16)
    def process_request(self, request, address):
        if not self.slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try: super().process_request(request, address)
        except Exception:
            self.slots.release()
            raise
    def process_request_thread(self, *args):
        try: super().process_request_thread(*args)
        finally: self.slots.release()


class Handler(BaseHTTPRequestHandler):
    server_version = 'day15/2'
    def setup(self):
        super().setup()
        self.connection.settimeout(5)
        def expire():
            try: self.connection.shutdown(socket.SHUT_RDWR)
            except OSError: pass
        self.read_timer = threading.Timer(10, expire)
        self.read_timer.daemon = True
        self.read_timer.start()
    def finish(self):
        self.read_timer.cancel()
        super().finish()
    def log_message(self, *args):
        pass  # Do not log attacker-controlled URLs, headers or payloads.
    def send(self, status, data):
        raw = json.dumps(_public_guard.clean(data), ensure_ascii=True).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        try: self.wfile.write(raw)
        except (BrokenPipeError, ConnectionResetError): pass
    def authorized(self):
        value = self.headers.get('Authorization', '')
        if not TOKEN or not secrets.compare_digest(value.encode(), ('Bearer ' + TOKEN).encode()):
            self.send(401, {'error': 'unauthorized'})
            return False
        return True
    def body(self):
        if self.headers.get('Transfer-Encoding') or len(self.headers.get_all('Content-Length', [])) != 1:
            raise ValueError('one Content-Length required; transfer encoding unsupported')
        length = int(self.headers['Content-Length'])
        if not 1 <= length <= 64000: raise ValueError('body size invalid')
        if self.headers.get_content_type() != 'application/json': raise ValueError('application/json required')
        raw = self.rfile.read(length)
        if len(raw) != length: raise ValueError('incomplete body')
        data = strict_json(raw.decode('utf-8'))
        if not isinstance(data, dict): raise ValueError('JSON object required')
        return data
    def do_GET(self):
        self.read_timer.cancel()
        parsed = urlsplit(self.path)
        if parsed.path == '/health':
            self.send(200, {'ok': True, 'service': 'day15-v2'})
            return
        if not self.authorized(): return
        if not allow('read', 180):
            self.send(429, {'error': 'read rate limit'})
            return
        if parsed.path == '/v1/profiles':
            self.send(200, {'profiles': profiles()})
            return
        match = re.fullmatch(r'/v1/jobs/([a-f0-9]{24})(/app(/.*))?', parsed.path)
        if not match:
            self.send(404, {'error': 'not found'})
            return
        with _jobs_lock: job = _jobs.get(match.group(1))
        if not job:
            self.send(404, {'error': 'job not found or expired'})
            return
        if match.group(2):
            if not allow('app', 20):
                self.send(429, {'error': 'app rate limit'})
                return
            if not _run_lock.acquire(blocking=False):
                self.send(409, {'error': 'job in progress'})
                return
            try:
                session = job.get('session')
                if not session: raise ValueError('no deployed session')
                path = match.group(3) + ('?' + parsed.query if parsed.query else '')
                if len(path) > 1000: raise ValueError('path too long')
                self.send(200, session.app_request(path))
            except Exception:
                self.send(409, {'error': 'app unavailable or response blocked'})
            finally: _run_lock.release()
            return
        data = {k: v for k, v in job.items() if k not in ('session', 'result')}
        if job['status'] == 'done':
            session = job.get('session')
            data['result'] = session.guard.clean(session.result) if session else job['result']
        self.send(200, data)
    def do_POST(self):
        global _staged
        if not self.authorized(): return
        if not allow('write', 20):
            self.send(429, {'error': 'write rate limit'})
            return
        try: data = self.body()
        except Exception:
            self.send(400, {'error': 'invalid JSON body or size'})
            return
        self.read_timer.cancel()
        if not _run_lock.acquire(blocking=False):
            self.send(409, {'error': 'job in progress; mutations forbidden'})
            return
        handed_off = False
        try:
            prune()
            path = urlsplit(self.path).path
            if path == '/v1/files':
                if set(data) != {'files'}: raise ValueError('files field required')
                _staged = validate_files({**_staged, **validate_files(data['files'])})
                self.send(200, {'staged': sorted(_staged), 'applies_to': 'next job only'})
            elif path == '/v1/reset':
                if data: raise ValueError('reset body must be empty object')
                _staged = {}
                for job in _jobs.values():
                    session = job.get('session')
                    if session:
                        session.retire()
                self.send(200, {'ok': True, 'reset': True, 'evidence_preserved': True})
            elif path == '/v1/run':
                if set(data) - {'task', 'files', 'profile', 'objective'}: raise ValueError('unknown request fields')
                task = data.get('task')
                if not isinstance(task, str) or not 1 <= len(task.encode()) <= TASK_LIMIT:
                    raise ValueError('task size invalid')
                profile, objective = data.get('profile', 'local'), data.get('objective', 'ping')
                if profile not in ('local', 'cloud') or not profiles()[profile]['enabled']:
                    raise ValueError('model profile is not configured')
                if objective not in ('ping', 'quote'): raise ValueError('objective must be ping or quote')
                files = validate_files({**_staged, **validate_files(data.get('files', {}))})
                # Validate complete workspace before accepting a job/billing a cloud reservation.
                validate_files({**agent.read_manifest(agent.SEED), **files})
                if profile == 'cloud': reserve_cloud()
                for old in _jobs.values():
                    session = old.get('session')
                    if session and session.app:
                        session.retire()
                job_id = secrets.token_hex(12)
                with _jobs_lock:
                    _jobs[job_id] = {'job_id': job_id, 'status': 'queued', 'created_at': time.time()}
                _staged = {}
                thread = threading.Thread(target=worker, args=(job_id, task, files, profile, objective), daemon=True)
                thread.start()
                handed_off = True
                self.send(202, {'job_id': job_id, 'status': 'queued', 'poll': '/v1/jobs/' + job_id})
            else:
                proof = re.fullmatch('/v1/jobs/([a-f0-9]{24})/proof', path)
                if not proof:
                    self.send(404, {'error': 'not found'})
                else:
                    job = _jobs.get(proof.group(1))
                    value = data.get('value')
                    if set(data) != {'value'} or not isinstance(value, str) or len(value) > 256:
                        raise ValueError('proof value required')
                    if not job or not job.get('session'): raise ValueError('unknown session')
                    self.send(200, job['session'].proof(value))
        except ValueError as exc:
            self.send(400, {'error': str(exc)})
        except Exception:
            self.send(500, {'error': 'operation failed'})
        finally:
            if not handed_off: _run_lock.release()


def main():
    if not re.fullmatch(r'[A-Za-z0-9_-]{32,128}', TOKEN) or TOKEN.startswith(('replace', 'day15-change')):
        raise SystemExit('DAY15_TOKEN must be a random token of at least 32 characters')
    if HOST not in ('127.0.0.1', '::1'):
        raise SystemExit('bind API to loopback and expose it through the authenticated tunnel')
    agent.RUNS.mkdir(mode=0o700, exist_ok=True)
    agent.RUNS.chmod(0o700)
    Sandbox().stop_all()
    def maintain():
        while True:
            time.sleep(30)
            if _run_lock.acquire(blocking=False):
                try: prune()
                finally: _run_lock.release()
    threading.Thread(target=maintain, daemon=True).start()
    httpd = BoundedServer((HOST, PORT), Handler)
    print('day15 v2 listening on loopback port ' + str(PORT), flush=True)
    try: httpd.serve_forever(poll_interval=0.2)
    finally: httpd.server_close()


if __name__ == '__main__': main()
