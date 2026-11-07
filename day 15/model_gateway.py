"""Private model gateway: provider allowlist, limits, no caller-supplied URL/key/model."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from urllib.parse import urlsplit

import guard_patterns


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError('upstream redirect rejected')


def profiles():
    result = {'local': {'model': os.environ.get('OLLAMA_MODEL', 'qwen2.5-coder:7b'), 'enabled': True}}
    result['cloud'] = {'model': os.environ.get('DAY15_CLOUD_MODEL', ''),
                       'enabled': bool(os.environ.get('DAY15_CLOUD_MODEL') and os.environ.get('DAY15_CLOUD_API_KEY'))}
    return result


class Gateway:
    def __init__(self, profile, guard, deadline):
        info = profiles().get(profile)
        if not info or not info['enabled']:
            raise ValueError('model profile is not configured')
        self.profile, self.model, self.guard, self.deadline = profile, info['model'], guard, deadline
        self.calls, self.usage = [], {'prompt_tokens': 0, 'completion_tokens': 0}
        self.url = os.environ.get('UPSTREAM_URL', 'http://127.0.0.1:11434/v1/chat/completions') if profile == 'local' else os.environ.get('DAY15_CLOUD_URL', 'https://api.openai.com/v1/chat/completions')
        parsed = urlsplit(self.url)
        if parsed.username or parsed.password or parsed.fragment or parsed.query:
            raise ValueError('invalid upstream configuration')
        if profile == 'local' and (parsed.scheme != 'http' or parsed.hostname not in ('127.0.0.1', 'localhost', '::1')):
            raise ValueError('local model must be loopback')
        if profile == 'cloud' and parsed.scheme != 'https':
            raise ValueError('cloud model requires HTTPS')
        self.model_revision = self.model
        if profile == 'local':
            try:
                opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
                with opener.open(parsed.scheme + '://' + parsed.netloc + '/api/tags', timeout=3) as response:
                    tags = json.loads(response.read(65536))
                self.model_revision = next(x['digest'] for x in tags.get('models', []) if x.get('name') == self.model)
            except Exception:
                self.model_revision = 'unavailable'

    def complete(self, system, user, max_tokens, step):
        if len(self.calls) >= 8 or time.monotonic() >= self.deadline:
            raise ValueError('model call/deadline budget exhausted')
        if len(system.encode()) + len(user.encode()) > 48000:
            raise ValueError('model context budget exceeded')
        # System is controller-owned and contains the synthetic prompt challenge value.
        if guard_patterns.scan(user):
            raise ValueError('input guard: credential/PII pattern')
        body = {'model': self.model, 'messages': [{'role': 'system', 'content': system}, {'role': 'user', 'content': user}], 'stream': False}
        if step == 'security_review' or step.startswith('tool-'):
            body['response_format'] = {'type': 'json_object'}
        if self.profile == 'local':
            body.update(max_tokens=min(max_tokens, 4096), temperature=0)
        else:
            token_field = os.environ.get('DAY15_CLOUD_TOKEN_FIELD', 'max_completion_tokens')
            if token_field not in ('max_tokens', 'max_completion_tokens'):
                raise ValueError('unsupported cloud token field')
            body[token_field] = min(max_tokens, 4096)
        headers = {'Content-Type': 'application/json'}
        if self.profile == 'cloud':
            headers['Authorization'] = 'Bearer ' + os.environ['DAY15_CLOUD_API_KEY']
        req = urllib.request.Request(self.url, data=json.dumps(body).encode(), headers=headers)
        row = {'step': step, 'profile': self.profile, 'model': self.model, 'status': 'started'}
        self.calls.append(row)
        try:
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
            with opener.open(req, timeout=min(180, max(1, self.deadline - time.monotonic()))) as response:
                raw = response.read(262145)
                if len(raw) > 262144:
                    raise ValueError('upstream response too large')
                data = json.loads(raw)
            choice = data['choices'][0]
            row['returned_model'] = data.get('model', self.model)
            text = choice['message']['content']
            if choice.get('finish_reason') != 'stop' or not isinstance(text, str):
                raise ValueError('incomplete model response')
            for key in self.usage:
                self.usage[key] += max(0, int((data.get('usage') or {}).get(key, 0)))
            if self.guard.clean_text(text, 'model:' + step) != text:
                raise ValueError('output guard blocked model response')
            row['status'] = 'ok'
            return text
        except Exception as exc:
            row['status'] = 'blocked_or_error'
            # Never relay provider error bodies, headers, credentials or raw exceptions.
            if isinstance(exc, ValueError):
                raise
            raise ValueError('model gateway failed (' + type(exc).__name__ + ')') from None
