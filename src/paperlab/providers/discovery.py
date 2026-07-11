"""Model discovery and Ollama detection for paperlab."""

from __future__ import annotations

import platform
import shutil
import subprocess
from contextlib import nullcontext
from typing import Any

from ._scrub import _scrub_secrets


class MissingKeyError(Exception):
    """Raised when a required API key is not available."""


class DiscoveryError(Exception):
    """Raised when model discovery fails due to a network or HTTP error."""


OLLAMA_RECOMMENDED: list[dict] = [
    {"name": "llama3.2:3b", "min_ram_gb": 8, "note": "fast, weaker analysis"},
    {"name": "qwen2.5:7b", "min_ram_gb": 16, "note": "default, good balance"},
    {"name": "qwen2.5:14b", "min_ram_gb": 32, "note": "stronger reasoning"},
    {"name": "qwen2.5:32b", "min_ram_gb": 64, "note": "best local quality"},
]

STATIC_FALLBACK_MODELS: dict[str, list[str]] = {
    "openai": ["gpt-4o", "gpt-4o-mini", "o3-mini"],
    "anthropic": ["claude-sonnet-4-5", "claude-opus-4-1", "claude-haiku-4-5"],
    "gemini": ["gemini-2.5-pro", "gemini-2.5-flash"],
    "groq": [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
    ],
    "together": [
        "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "Qwen/Qwen2.5-72B-Instruct-Turbo",
    ],
    "openrouter": [
        "openai/gpt-4o",
        "anthropic/claude-3.5-sonnet",
        "meta-llama/llama-3.3-70b-instruct",
        "google/gemini-2.0-flash-exp",
    ],
}

_PROVIDER_BASE: dict[str, str] = {
    "openai": "https://api.openai.com/v1",
    "groq": "https://api.groq.com/openai/v1",
    "together": "https://api.together.xyz/v1",
    "custom": "https://api.openai.com/v1",
}

_PROVIDERS_NEEDING_KEY = frozenset(["openai", "groq", "together", "custom", "anthropic", "gemini"])


def system_ram_gb() -> float:
    system = platform.system()
    try:
        if system == "Darwin":
            out = subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True)
            return round(int(out.strip()) / 1e9, 1)
        if system == "Linux":
            with open("/proc/meminfo") as fh:
                for line in fh:
                    if line.startswith("MemTotal:"):
                        kb = int(line.split()[1])
                        return round(kb * 1024 / 1e9, 1)
    except Exception:
        pass
    return 8.0


def ollama_status(
    base_url: str = "http://localhost:11434",
    client: Any = None,
) -> dict:
    import httpx

    installed = shutil.which("ollama") is not None
    _client = client if client is not None else httpx.Client()
    try:
        resp = _client.get(f"{base_url}/api/tags", timeout=2)
        data = resp.json()
        models = [
            {
                "name": m["name"],
                "size_gb": round(m["size"] / 1e9, 1),
            }
            for m in data.get("models", [])
        ]
        return {"installed": installed, "running": True, "models": models}
    except Exception:
        return {"installed": installed, "running": False, "models": []}


def recommend_ollama_models(ram_gb: float | None = None) -> list[dict]:
    if ram_gb is None:
        ram_gb = system_ram_gb()
    return [m for m in OLLAMA_RECOMMENDED if m["min_ram_gb"] <= ram_gb]


def list_models(
    provider: str,
    api_key: str | None = None,
    client: Any = None,
) -> list[str]:
    import httpx

    if provider in _PROVIDERS_NEEDING_KEY and api_key is None:
        raise MissingKeyError(f"API key required for provider {provider!r}")

    cm = nullcontext(client) if client is not None else httpx.Client()

    try:
        with cm as _client:
            if provider == "openrouter":
                resp = _client.get("https://openrouter.ai/api/v1/models")
                _check_response(resp, provider)
                return sorted(item["id"] for item in resp.json()["data"])

            if provider in ("openai", "groq", "together", "custom"):
                base = _PROVIDER_BASE[provider]
                resp = _client.get(
                    f"{base}/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                _check_response(resp, provider)
                return sorted(item["id"] for item in resp.json()["data"])

            if provider == "anthropic":
                resp = _client.get(
                    "https://api.anthropic.com/v1/models",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                    },
                )
                _check_response(resp, provider)
                return sorted(item["id"] for item in resp.json()["data"])

            if provider == "gemini":
                resp = _client.get(
                    "https://generativelanguage.googleapis.com/v1beta/models",
                    headers={"x-goog-api-key": api_key},
                )
                _check_response(resp, provider)
                return sorted(
                    m["name"].removeprefix("models/") for m in resp.json().get("models", [])
                )

            if provider == "ollama":
                status = ollama_status(client=_client)
                return [m["name"] for m in status["models"]]

    except (MissingKeyError, DiscoveryError):
        raise
    except Exception as exc:
        msg = _scrub_secrets(str(exc))
        raise DiscoveryError(
            f"Discovery failed for {provider!r}: {type(exc).__name__}: {msg}"
        ) from exc

    raise DiscoveryError(f"Unknown provider for discovery: {provider!r}")


def _check_response(resp: Any, provider: str) -> None:
    if resp.status_code >= 400:
        raise DiscoveryError(f"HTTP {resp.status_code} from {provider!r} API")


def list_models_safe(
    provider: str,
    api_key: str | None = None,
    client: Any = None,
) -> tuple[list[str], str | None]:
    try:
        models = list_models(provider, api_key=api_key, client=client)
        return models, None
    except Exception as exc:
        return STATIC_FALLBACK_MODELS.get(provider, []), str(exc)
