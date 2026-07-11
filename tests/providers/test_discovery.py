"""Tests for providers/discovery.py."""

from __future__ import annotations

from unittest.mock import MagicMock

import httpx
import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fake_response(status_code: int, payload: dict):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = payload
    return resp


class _FakeClient:
    """Minimal httpx-compatible client for tests."""

    def __init__(self, responses: dict | None = None, raise_on_get: Exception | None = None):
        self._responses = responses or {}
        self._raise = raise_on_get
        self.last_get_url = None
        self.last_get_headers = None

    def get(self, url: str, *, timeout=None, headers=None, **kwargs):
        self.last_get_url = url
        self.last_get_headers = headers or {}
        if self._raise is not None:
            raise self._raise
        for pattern, resp in self._responses.items():
            if pattern in url:
                return resp
        status = MagicMock()
        status.status_code = 404
        status.json.return_value = {}
        return status


# ---------------------------------------------------------------------------
# system_ram_gb
# ---------------------------------------------------------------------------


def test_system_ram_gb_returns_positive_float():
    from paperlab.providers.discovery import system_ram_gb

    result = system_ram_gb()
    assert isinstance(result, float)
    assert result > 0


# ---------------------------------------------------------------------------
# ollama_status
# ---------------------------------------------------------------------------


def test_ollama_status_running_with_models():
    from paperlab.providers.discovery import ollama_status

    payload = {
        "models": [
            {"name": "qwen2.5:7b", "size": 4_500_000_000},
            {"name": "llama3.2:3b", "size": 2_000_000_000},
        ]
    }
    client = _FakeClient({"/api/tags": _fake_response(200, payload)})
    result = ollama_status(client=client)

    assert result["running"] is True
    assert len(result["models"]) == 2
    assert result["models"][0]["name"] == "qwen2.5:7b"
    assert result["models"][0]["size_gb"] == round(4_500_000_000 / 1e9, 1)


def test_ollama_status_connect_error_gives_not_running():
    from paperlab.providers.discovery import ollama_status

    client = _FakeClient(raise_on_get=httpx.ConnectError("refused"))
    result = ollama_status(client=client)

    assert result["running"] is False
    assert result["models"] == []


# ---------------------------------------------------------------------------
# recommend_ollama_models
# ---------------------------------------------------------------------------


def test_recommend_ollama_models_8gb():
    from paperlab.providers.discovery import recommend_ollama_models

    models = recommend_ollama_models(8)
    names = [m["name"] for m in models]
    assert names == ["llama3.2:3b"]


def test_recommend_ollama_models_16gb():
    from paperlab.providers.discovery import recommend_ollama_models

    models = recommend_ollama_models(16)
    names = [m["name"] for m in models]
    assert "llama3.2:3b" in names
    assert "qwen2.5:7b" in names
    assert "qwen2.5:14b" not in names


def test_recommend_ollama_models_64gb():
    from paperlab.providers.discovery import recommend_ollama_models

    models = recommend_ollama_models(64)
    assert len(models) == 4


# ---------------------------------------------------------------------------
# list_models — openrouter (no key needed)
# ---------------------------------------------------------------------------


def test_list_models_openrouter_sorted():
    from paperlab.providers.discovery import list_models

    payload = {"data": [{"id": "z-model"}, {"id": "a-model"}, {"id": "m-model"}]}
    client = _FakeClient({"openrouter.ai": _fake_response(200, payload)})

    models = list_models("openrouter", client=client)
    assert models == ["a-model", "m-model", "z-model"]


# ---------------------------------------------------------------------------
# list_models — openai missing key
# ---------------------------------------------------------------------------


def test_list_models_openai_missing_key():
    from paperlab.providers.discovery import MissingKeyError, list_models

    with pytest.raises(MissingKeyError):
        list_models("openai", api_key=None)


# ---------------------------------------------------------------------------
# list_models — openai with key, checks auth header
# ---------------------------------------------------------------------------


def test_list_models_openai_with_key():
    from paperlab.providers.discovery import list_models

    payload = {"data": [{"id": "gpt-4o"}, {"id": "gpt-4o-mini"}]}
    client = _FakeClient({"api.openai.com": _fake_response(200, payload)})

    models = list_models("openai", api_key="sk-test-abc", client=client)
    assert "gpt-4o" in models
    assert client.last_get_headers.get("Authorization") == "Bearer sk-test-abc"


# ---------------------------------------------------------------------------
# list_models — gemini strips "models/" prefix
# ---------------------------------------------------------------------------


def test_list_models_gemini_strips_prefix():
    from paperlab.providers.discovery import list_models

    payload = {
        "models": [
            {"name": "models/gemini-2.5-pro"},
            {"name": "models/gemini-2.5-flash"},
        ]
    }
    client = _FakeClient({"generativelanguage": _fake_response(200, payload)})

    models = list_models("gemini", api_key="gemini-key", client=client)
    assert "gemini-2.5-pro" in models
    assert "gemini-2.5-flash" in models
    assert all(not m.startswith("models/") for m in models)
    # Key travels in header, not URL query
    assert client.last_get_headers.get("x-goog-api-key") == "gemini-key"
    assert "key=" not in client.last_get_url


def test_discovery_error_scrubs_secrets_from_exception():
    from paperlab.providers.discovery import DiscoveryError, list_models

    secret = "sk-real-secret-abcdefghij"
    google_key = "AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ012345"

    class _BoomClient:
        def get(self, url, **kwargs):
            raise RuntimeError(
                f"connect fail https://api.openai.com/v1/models?key={google_key} "
                f"Authorization: Bearer {secret}"
            )

    with pytest.raises(DiscoveryError) as exc_info:
        list_models("openai", api_key="sk-caller-key", client=_BoomClient())

    msg = str(exc_info.value)
    assert secret not in msg
    assert google_key not in msg
    assert "key=AIza" not in msg


# ---------------------------------------------------------------------------
# list_models_safe
# ---------------------------------------------------------------------------


def test_list_models_safe_success():
    from paperlab.providers.discovery import list_models_safe

    payload = {"data": [{"id": "z-model"}, {"id": "a-model"}]}
    client = _FakeClient({"openrouter.ai": _fake_response(200, payload)})

    models, err = list_models_safe("openrouter", client=client)
    assert err is None
    assert "a-model" in models


def test_list_models_safe_fallback_on_error():
    from paperlab.providers.discovery import STATIC_FALLBACK_MODELS, list_models_safe

    # missing key → MissingKeyError → fallback
    models, err = list_models_safe("openai", api_key=None)
    assert err is not None
    assert models == STATIC_FALLBACK_MODELS["openai"]


def test_list_models_safe_http_500_returns_fallback():
    from paperlab.providers.discovery import STATIC_FALLBACK_MODELS, list_models_safe

    client = _FakeClient({"openrouter.ai": _fake_response(500, {})})

    models, err = list_models_safe("openrouter", client=client)
    assert err is not None
    assert models == STATIC_FALLBACK_MODELS.get("openrouter", [])


def test_list_models_http_500_raises_discovery_error():
    from paperlab.providers.discovery import DiscoveryError, list_models

    client = _FakeClient({"openrouter.ai": _fake_response(500, {})})

    with pytest.raises(DiscoveryError):
        list_models("openrouter", client=client)
