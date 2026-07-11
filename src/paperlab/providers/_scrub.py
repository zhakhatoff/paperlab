"""Redact secrets from arbitrary strings before logging or raising."""

from __future__ import annotations

import re

_PATTERNS = [
    # URL query params: key=...
    re.compile(r"key=[^\s&]+", re.IGNORECASE),
    # Auth headers
    re.compile(r"Authorization:\s*Bearer\s+\S+", re.IGNORECASE),
    re.compile(r"x-api-key:\s*\S+", re.IGNORECASE),
    re.compile(r"x-goog-api-key:\s*\S+", re.IGNORECASE),
    # Common token prefixes
    re.compile(r"sk-ant-[A-Za-z0-9\-_]+"),
    re.compile(r"sk-proj-[A-Za-z0-9\-_]+"),
    re.compile(r"sk-or-[A-Za-z0-9\-_]+"),
    re.compile(r"sk-[A-Za-z0-9\-_]{8,}"),
    re.compile(r"AIza[A-Za-z0-9\-_]{20,}"),
    re.compile(r"gsk_[A-Za-z0-9]{20,}"),
    re.compile(r"tgp_[A-Za-z0-9\-_]{20,}"),
]


def _scrub_secrets(text: str) -> str:
    result = text
    for pattern in _PATTERNS:
        result = pattern.sub("***", result)
    return result
