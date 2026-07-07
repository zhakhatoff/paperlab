"""Tests for paperlab.cli.config."""
from __future__ import annotations

from pathlib import Path

import pytest

from paperlab.cli.config import (
    PaperlabConfig,
    default_config_path,
    get_field,
    load_config,
    save_config,
    set_field,
)


def test_default_config_path_follows_paperlab_home(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERLAB_HOME", str(tmp_path))
    p = default_config_path()
    assert p == tmp_path / "config.toml"


def test_load_config_no_file_returns_defaults(tmp_path):
    nonexistent = tmp_path / "no_such_dir" / "config.toml"
    cfg = load_config(nonexistent)
    assert isinstance(cfg, PaperlabConfig)
    assert cfg.provider == "ollama"
    assert cfg.model == "qwen2.5:7b"
    assert cfg.mode == "rigorous"
    assert cfg.lang == "en"


def test_save_load_roundtrip(tmp_path):
    cfg = PaperlabConfig(provider="openai", model="gpt-4o", mode="learning", lang="ru")
    path = tmp_path / "config.toml"
    saved_path = save_config(cfg, path)
    assert saved_path == path
    loaded = load_config(path)
    assert loaded.provider == "openai"
    assert loaded.model == "gpt-4o"
    assert loaded.mode == "learning"
    assert loaded.lang == "ru"


def test_save_creates_parent_dirs(tmp_path):
    cfg = PaperlabConfig()
    deep = tmp_path / "a" / "b" / "config.toml"
    save_config(cfg, deep)
    assert deep.exists()


def test_get_field_provider():
    cfg = PaperlabConfig()
    assert get_field(cfg, "provider") == "ollama"


def test_get_field_model():
    cfg = PaperlabConfig(model="llama3:8b")
    assert get_field(cfg, "model") == "llama3:8b"


def test_set_field_model():
    cfg = PaperlabConfig()
    new_cfg = set_field(cfg, "model", "llama3:8b")
    assert get_field(new_cfg, "model") == "llama3:8b"
    # original unchanged
    assert cfg.model == "qwen2.5:7b"


def test_get_field_invalid_raises_key_error():
    cfg = PaperlabConfig()
    with pytest.raises(KeyError):
        get_field(cfg, "nonexistent_field")


def test_set_field_invalid_raises_key_error():
    cfg = PaperlabConfig()
    with pytest.raises(KeyError):
        set_field(cfg, "nonexistent_field", "value")


def test_extra_set_and_get(tmp_path):
    cfg = PaperlabConfig()
    cfg2 = set_field(cfg, "extra.foo", "bar")
    assert get_field(cfg2, "extra.foo") == "bar"


def test_extra_key_missing_raises_key_error():
    cfg = PaperlabConfig()
    with pytest.raises(KeyError):
        get_field(cfg, "extra.missing_key")


def test_extra_roundtrip_through_file(tmp_path):
    cfg = PaperlabConfig()
    cfg = set_field(cfg, "extra.custom_base_url", "http://localhost:11434")
    path = tmp_path / "config.toml"
    save_config(cfg, path)
    loaded = load_config(path)
    assert get_field(loaded, "extra.custom_base_url") == "http://localhost:11434"
