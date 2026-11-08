#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Input and output scanners. Findings never include the raw secret."""

from __future__ import annotations

import base64
import re
import unicodedata
from dataclasses import dataclass

LABELS = {
    "api_key": "[REDACTED_API_KEY]",
    "aws_key": "[REDACTED_API_KEY]",
    "github_token": "[REDACTED_API_KEY]",
    "email": "[REDACTED_EMAIL]",
    "card": "[REDACTED_CARD]",
    "phone": "[REDACTED_PHONE]",
    "system_prompt": "[BLOCKED_SYSTEM]",
    "suspicious": "[BLOCKED_OUTPUT]",
}

_API = re.compile(r"sk-(?:proj-)?[A-Za-z0-9]{20,}")
_API_PROJ = re.compile(r"sk-proj-[A-Za-z0-9]{3,}")
_API_PROJ_SPLIT = re.compile(r"sk-[ \t\r\n]*proj-[ \t\r\n]*[A-Za-z0-9]{3,}")
# Word / punctuation between sk- and proj- (day-15 hardening of the known miss).
_API_PROJ_GAP = re.compile(r"sk-(?:[\s\w.-]{0,24}?)proj-[A-Za-z0-9]{3,}", re.I)
_GHP = re.compile(r"ghp_[A-Za-z0-9]{16,}")
_AKIA = re.compile(r"AKIA[0-9A-Z]{16}")
_EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
_PHONE = re.compile(
    r"(?:\+\d{1,3}[\s.-]?)?(?:\(\d{3}\)|\d{3})[\s.-]\d{3}[\s.-]\d{2}[\s.-]\d{2}\b"
)
_CARD = re.compile(r"\b(?:\d[ -]?){12,18}\d\b")
_B64 = re.compile(r"(?<![A-Za-z0-9+/])[A-Za-z0-9+/]{24,}={0,2}(?![A-Za-z0-9+/=])")
_IP_URL = re.compile(r"https?://(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?(?:/[^\s]*)?", re.I)
_USERINFO = re.compile(r"https?://[^\s/@]+:[^\s/@]+@[^\s]+", re.I)
_CURL = re.compile(r"curl\b[^|\n]{0,200}\|\s*(?:sh|bash)\b", re.I)
_RM = re.compile(r"\brm\s+-rf\b", re.I)
_UNICODE_SPACE = re.compile(r"[\u00a0\u1680\u2000-\u200a\u202f\u205f\u3000]+")


def normalize(text: str) -> str:
    """NFKC + fold exotic spaces so phone/key regex see ordinary separators."""
    text = unicodedata.normalize("NFKC", text)
    return _UNICODE_SPACE.sub(" ", text)


@dataclass(frozen=True)
class Finding:
    kind: str
    start: int
    end: int

    @property
    def label(self) -> str:
        return LABELS[self.kind]


def _luhn(number: str) -> bool:
    digits = [int(c) for c in number]
    total = 0
    for i, digit in enumerate(reversed(digits)):
        if i % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0 and len(digits) >= 13


def _overlaps(findings: list[Finding], start: int, end: int) -> bool:
    return any(not (end <= item.start or start >= item.end) for item in findings)


def _add(findings: list[Finding], kind: str, start: int, end: int) -> None:
    if start >= end or _overlaps(findings, start, end):
        return
    findings.append(Finding(kind, start, end))


def _direct(text: str, findings: list[Finding]) -> None:
    for match in _AKIA.finditer(text):
        _add(findings, "aws_key", match.start(), match.end())
    for match in _GHP.finditer(text):
        _add(findings, "github_token", match.start(), match.end())
    for match in _API.finditer(text):
        _add(findings, "api_key", match.start(), match.end())
    for match in _API_PROJ.finditer(text):
        _add(findings, "api_key", match.start(), match.end())
    for match in _API_PROJ_SPLIT.finditer(text):
        _add(findings, "api_key", match.start(), match.end())
    for match in _API_PROJ_GAP.finditer(text):
        _add(findings, "api_key", match.start(), match.end())
    for match in _EMAIL.finditer(text):
        _add(findings, "email", match.start(), match.end())
    for match in _CARD.finditer(text):
        digits = re.sub(r"\D", "", match.group())
        if _luhn(digits):
            _add(findings, "card", match.start(), match.end())
    for match in _PHONE.finditer(text):
        _add(findings, "phone", match.start(), match.end())


def _base64(text: str, findings: list[Finding]) -> None:
    for match in _B64.finditer(text):
        token = match.group()
        if len(token) % 4 != 0:
            continue
        try:
            decoded = base64.b64decode(token, validate=True).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            continue
        if scan(decoded):
            _add(findings, "api_key", match.start(), match.end())


def scan(text: str) -> list[Finding]:
    """Secrets and, when asked via scan_output, leak markers. Direct scan is secrets only."""
    text = normalize(text)
    findings: list[Finding] = []
    _direct(text, findings)
    _base64(text, findings)
    findings.sort(key=lambda item: item.start)
    return findings


def scan_output(text: str, system: str) -> list[Finding]:
    text = normalize(text)
    findings = scan(text)
    marker = normalize(system).strip()
    if len(marker) >= 24 and marker in text:
        start = text.find(marker)
        _add(findings, "system_prompt", start, start + len(marker))
    elif len(marker) >= 24:
        window = marker[:32]
        start = text.find(window)
        if start >= 0:
            _add(findings, "system_prompt", start, start + len(window))
    for pattern in (_CURL, _RM, _USERINFO, _IP_URL):
        for match in pattern.finditer(text):
            _add(findings, "suspicious", match.start(), match.end())
    findings.sort(key=lambda item: item.start)
    return findings


def redact(text: str, findings: list[Finding]) -> str:
    # Findings were computed on normalize(text); apply labels on the same view.
    view = normalize(text)
    out = view
    for item in sorted(findings, key=lambda finding: finding.start, reverse=True):
        out = out[: item.start] + item.label + out[item.end :]
    return out


def message_text(messages: list[dict]) -> str:
    parts = []
    for message in messages:
        content = message.get("content")
        if isinstance(content, str):
            parts.append(content)
    return "\n".join(parts)


def system_text(messages: list[dict]) -> str:
    parts = []
    for message in messages:
        if message.get("role") == "system" and isinstance(message.get("content"), str):
            parts.append(message["content"])
    return "\n".join(parts)
