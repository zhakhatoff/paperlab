"""Tests for the provider setup panel pure helpers in paperlab.web.app."""

from __future__ import annotations

from paperlab.providers import discovery, keys
from paperlab.web.app import provider_panel_state, save_key_action

# ---------------------------------------------------------------------------
# provider_panel_state — cloud providers
# ---------------------------------------------------------------------------


def test_openrouter_without_key(monkeypatch):
    monkeypatch.setattr(keys, "get_key", lambda p: None)
    monkeypatch.setattr(keys, "list_keys", lambda: {})
    monkeypatch.setattr(discovery, "list_models_safe", lambda p, api_key=None: (["a", "b"], None))

    state = provider_panel_state("openrouter")

    assert state["is_cloud"] is True
    assert state["key_saved"] is False
    assert state["models"], "openrouter models must load without a key"
    assert state["error"] is None
    assert state["ollama_html"] is None


def test_anthropic_with_saved_key(monkeypatch):
    monkeypatch.setattr(keys, "get_key", lambda p: "sk-x")
    monkeypatch.setattr(keys, "list_keys", lambda: {"anthropic": "sk-x..."})
    monkeypatch.setattr(
        discovery, "list_models_safe", lambda p, api_key=None: (["claude-sonnet-4-5"], None)
    )

    state = provider_panel_state("anthropic")

    assert state["is_cloud"] is True
    assert state["key_saved"] is True
    assert "sk-x..." in state["key_hint"]
    assert "keys.toml" in state["key_hint"]
    assert state["model_default"] == "claude-sonnet-4-5"


def test_cloud_without_key_uses_fallback(monkeypatch):
    monkeypatch.setattr(keys, "get_key", lambda p: None)
    monkeypatch.setattr(keys, "list_keys", lambda: {})

    def _boom(*a, **kw):  # pragma: no cover — must not be called
        raise AssertionError("no network calls without a key")

    monkeypatch.setattr(discovery, "list_models_safe", _boom)

    state = provider_panel_state("openai")

    assert state["key_saved"] is False
    assert state["models"] == list(discovery.STATIC_FALLBACK_MODELS["openai"])
    assert state["model_default"] == "gpt-4o-mini"


# ---------------------------------------------------------------------------
# provider_panel_state — ollama
# ---------------------------------------------------------------------------


def test_ollama_running(monkeypatch):
    monkeypatch.setattr(
        discovery,
        "ollama_status",
        lambda **kw: {
            "installed": True,
            "running": True,
            "models": [
                {"name": "qwen2.5:7b", "size_gb": 4.7},
                {"name": "mistral:7b", "size_gb": 4.1},
            ],
        },
    )
    monkeypatch.setattr(discovery, "system_ram_gb", lambda: 16.0)

    state = provider_panel_state("ollama")

    assert state["is_cloud"] is False
    assert "running" in state["ollama_html"]
    assert "2 models installed" in state["ollama_html"]
    assert "16" in state["ollama_html"]  # RAM shown

    values = [v for _, v in state["models"]]
    assert "qwen2.5:7b" in values
    assert "mistral:7b" in values
    # recommended-for-16GB model that is not installed
    assert "llama3.2:3b" in values
    labels = [label for label, _ in state["models"]]
    assert any("4.7 GB" in label for label in labels)
    assert any("not installed · ollama pull llama3.2:3b" in label for label in labels)
    assert state["model_default"] == "qwen2.5:7b"


def test_ollama_not_installed(monkeypatch):
    monkeypatch.setattr(
        discovery,
        "ollama_status",
        lambda **kw: {"installed": False, "running": False, "models": []},
    )
    monkeypatch.setattr(discovery, "system_ram_gb", lambda: 16.0)

    state = provider_panel_state("ollama")

    assert "not installed" in state["ollama_html"]
    assert "brew install ollama" in state["ollama_html"]
    assert "ollama.com/download" in state["ollama_html"]


def test_ollama_installed_not_running(monkeypatch):
    monkeypatch.setattr(
        discovery,
        "ollama_status",
        lambda **kw: {"installed": True, "running": False, "models": []},
    )
    monkeypatch.setattr(discovery, "system_ram_gb", lambda: 8.0)

    state = provider_panel_state("ollama")

    assert "not running" in state["ollama_html"]
    assert "ollama serve" in state["ollama_html"]


# ---------------------------------------------------------------------------
# save_key_action
# ---------------------------------------------------------------------------


def test_save_key_action_saves_and_loads_models(monkeypatch):
    saved: dict[str, str] = {}
    monkeypatch.setattr(keys, "save_key", lambda p, k: saved.update({p: k}))
    monkeypatch.setattr(
        discovery,
        "list_models_safe",
        lambda p, api_key=None: (["gpt-4o", "gpt-4o-mini"], None),
    )

    status, models, default = save_key_action("openai", "sk-test-123")

    assert "saved" in status.lower()
    assert saved == {"openai": "sk-test-123"}
    assert models == ["gpt-4o", "gpt-4o-mini"]
    assert default == "gpt-4o-mini"


def test_save_key_action_empty_key(monkeypatch):
    def _boom(*a, **kw):  # pragma: no cover
        raise AssertionError("save_key must not be called for an empty key")

    monkeypatch.setattr(keys, "save_key", _boom)

    status, models, default = save_key_action("openai", "   ")

    assert "error" in status
    assert models == []
    assert default == ""


def test_save_key_action_reports_discovery_error(monkeypatch):
    monkeypatch.setattr(keys, "save_key", lambda p, k: None)
    monkeypatch.setattr(
        discovery,
        "list_models_safe",
        lambda p, api_key=None: (["fallback-model"], "HTTP 401 from 'openai' API"),
    )

    status, models, default = save_key_action("openai", "sk-bad")

    assert "saved" in status.lower()
    assert "401" in status
    assert models == ["fallback-model"]
