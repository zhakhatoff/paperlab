"""API key vault for paperlab providers."""

from __future__ import annotations

import contextlib
import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

import tomllib

import tomli_w

from paperlab.cli.config import default_home

ENV_VAR_BY_PROVIDER: dict[str, str] = {
    "openrouter": "OPENROUTER_API_KEY",
    "together": "TOGETHERAI_API_KEY",
    "groq": "GROQ_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "custom": "OPENAI_API_KEY",
}


def keys_path() -> Path:
    return default_home() / "keys.toml"


def _load_keys() -> dict[str, str]:
    p = keys_path()
    if not p.exists():
        return {}
    with open(p, "rb") as fh:
        return tomllib.load(fh)


def _save_keys(data: dict[str, str]) -> Path:
    p = keys_path()
    parent = p.parent
    if not parent.exists():
        parent.mkdir(parents=True, exist_ok=True)
        with contextlib.suppress(OSError):
            parent.chmod(0o700)
    if p.exists():
        p.unlink()
    flags = os.O_CREAT | os.O_WRONLY | os.O_TRUNC
    fd = os.open(p, flags, 0o600)
    with os.fdopen(fd, "wb") as fh:
        tomli_w.dump(data, fh)
    os.chmod(p, 0o600)
    return p


def save_key(provider: str, key: str) -> Path:
    data = _load_keys()
    data[provider] = key
    return _save_keys(data)


def get_key(provider: str) -> str | None:
    env_var = ENV_VAR_BY_PROVIDER.get(provider)
    if env_var:
        val = os.environ.get(env_var)
        if val:
            return val
    data = _load_keys()
    return data.get(provider)


def delete_key(provider: str) -> bool:
    data = _load_keys()
    if provider not in data:
        return False
    del data[provider]
    _save_keys(data)
    return True


def _mask(key: str) -> str:
    if len(key) <= 7:
        return key[:4] + "..."
    return key[:4] + "..." + key[-3:]


def list_keys() -> dict[str, str]:
    data = _load_keys()
    return {provider: _mask(key) for provider, key in data.items()}


def apply_key_to_env(provider: str) -> bool:
    env_var = ENV_VAR_BY_PROVIDER.get(provider)
    if not env_var:
        return False
    if os.environ.get(env_var):
        return False
    data = _load_keys()
    key = data.get(provider)
    if key is None:
        return False
    os.environ[env_var] = key
    return True
