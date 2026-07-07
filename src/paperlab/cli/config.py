"""paperlab configuration model and helpers."""
from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Any

import tomli_w
from pydantic import BaseModel, Field


class PaperlabConfig(BaseModel):
    provider: str = "ollama"
    model: str = "qwen2.5:7b"
    mode: str = "rigorous"
    lang: str = "en"
    extra: dict = Field(default_factory=dict)


_TOP_LEVEL_FIELDS: frozenset[str] = frozenset(PaperlabConfig.model_fields)


def default_home() -> Path:
    """Return the paperlab home directory.

    Uses PAPERLAB_HOME environment variable if set, otherwise ~/.paperlab.
    """
    home = os.environ.get("PAPERLAB_HOME")
    if home:
        return Path(home)
    return Path.home() / ".paperlab"


def default_config_path() -> Path:
    """Return the default config.toml path."""
    return default_home() / "config.toml"


def load_config(path: Path | None = None) -> PaperlabConfig:
    """Load configuration from *path*.

    Returns a default ``PaperlabConfig`` if the file does not exist.
    """
    path = path or default_config_path()
    if not path.exists():
        return PaperlabConfig()
    with open(path, "rb") as fh:
        data = tomllib.load(fh)
    return PaperlabConfig(**data)


def save_config(cfg: PaperlabConfig, path: Path | None = None) -> Path:
    """Write *cfg* to *path* in TOML format. Creates parent directories."""
    path = path or default_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as fh:
        tomli_w.dump(cfg.model_dump(), fh, multiline_strings=True)
    return path


def get_field(cfg: PaperlabConfig, dotted: str) -> Any:
    """Return a config value by dotted key.

    Supports top-level keys (``provider``, ``model``, ``mode``, ``lang``,
    ``extra``) and one level of nesting for ``extra`` (e.g. ``extra.foo``).

    Raises
    ------
    KeyError
        If the key is not valid.
    """
    parts = dotted.split(".", 1)
    if parts[0] not in _TOP_LEVEL_FIELDS:
        raise KeyError(f"Unknown config key: {dotted!r}")
    if len(parts) == 1:
        return getattr(cfg, parts[0])
    if parts[0] != "extra":
        raise KeyError(f"Nested access only supported for 'extra', not {parts[0]!r}")
    extra: dict = cfg.extra
    if parts[1] not in extra:
        raise KeyError(f"Key not found in extra: {parts[1]!r}")
    return extra[parts[1]]


def set_field(cfg: PaperlabConfig, dotted: str, value: str) -> PaperlabConfig:
    """Return a new config with *dotted* field set to *value*.

    Raises
    ------
    KeyError
        If the key is not valid.
    """
    parts = dotted.split(".", 1)
    if parts[0] not in _TOP_LEVEL_FIELDS:
        raise KeyError(f"Unknown config key: {dotted!r}")
    data = cfg.model_dump()
    if len(parts) == 1:
        data[parts[0]] = value
    else:
        if parts[0] != "extra":
            raise KeyError(f"Nested access only supported for 'extra', not {parts[0]!r}")
        data["extra"][parts[1]] = value
    return PaperlabConfig(**data)
