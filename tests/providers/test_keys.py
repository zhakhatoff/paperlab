"""Tests for providers/keys.py — API key vault."""

from __future__ import annotations

import stat


def test_save_and_get_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("PAPERLAB_HOME", str(tmp_path))
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    from paperlab.providers.keys import get_key, save_key

    save_key("openrouter", "sk-test-123")
    assert get_key("openrouter") == "sk-test-123"


def test_file_permissions(tmp_path, monkeypatch):
    monkeypatch.setenv("PAPERLAB_HOME", str(tmp_path))

    from paperlab.providers.keys import keys_path, save_key

    save_key("openrouter", "sk-test-999")
    mode = stat.S_IMODE(keys_path().stat().st_mode)
    assert mode == 0o600


def test_env_var_priority_over_file(tmp_path, monkeypatch):
    monkeypatch.setenv("PAPERLAB_HOME", str(tmp_path))
    monkeypatch.setenv("OPENROUTER_API_KEY", "env-key-override")

    from paperlab.providers.keys import get_key, save_key

    save_key("openrouter", "file-key")
    assert get_key("openrouter") == "env-key-override"


def test_get_returns_none_when_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("PAPERLAB_HOME", str(tmp_path))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    from paperlab.providers.keys import get_key

    assert get_key("openai") is None


def test_list_keys_masks(tmp_path, monkeypatch):
    monkeypatch.setenv("PAPERLAB_HOME", str(tmp_path))

    from paperlab.providers.keys import list_keys, save_key

    full_key = "sk-abcdefghijklmnopqrstuvwxyz"
    save_key("openai", full_key)
    result = list_keys()
    assert "openai" in result
    assert full_key not in result["openai"]
    assert result["openai"].startswith("sk-a")
    assert result["openai"].endswith("xyz")
    assert "..." in result["openai"]


def test_delete_key(tmp_path, monkeypatch):
    monkeypatch.setenv("PAPERLAB_HOME", str(tmp_path))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    from paperlab.providers.keys import delete_key, get_key, save_key

    save_key("openai", "sk-test-del")
    assert delete_key("openai") is True
    assert get_key("openai") is None
    assert delete_key("openai") is False


def test_apply_key_to_env_sets_env(tmp_path, monkeypatch):
    monkeypatch.setenv("PAPERLAB_HOME", str(tmp_path))
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    from paperlab.providers.keys import apply_key_to_env, save_key

    save_key("openrouter", "sk-test-apply")
    result = apply_key_to_env("openrouter")
    assert result is True

    import os

    assert os.environ.get("OPENROUTER_API_KEY") == "sk-test-apply"


def test_apply_key_to_env_does_not_overwrite(tmp_path, monkeypatch):
    monkeypatch.setenv("PAPERLAB_HOME", str(tmp_path))
    monkeypatch.setenv("OPENROUTER_API_KEY", "already-set")

    from paperlab.providers.keys import apply_key_to_env, save_key

    save_key("openrouter", "sk-test-other")
    result = apply_key_to_env("openrouter")
    assert result is False

    import os

    assert os.environ["OPENROUTER_API_KEY"] == "already-set"
