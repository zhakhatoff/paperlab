"""Prompt loading utilities for paperlab agents."""

from __future__ import annotations

from pathlib import Path

import yaml

_PROMPTS_DIR = Path(__file__).parent
_VALID_MODES = {"rigorous", "learning"}
_VALID_LANGS = {"en", "ru"}


def load_prompt(agent_name: str, mode: str, lang: str) -> dict:
    """Load a prompt dict for *agent_name* at the given *mode* and *lang*.

    Returns a dict with keys ``system`` and ``user_template``.

    Raises
    ------
    FileNotFoundError
        When the YAML file for *agent_name* does not exist.
    ValueError
        When *mode* or *lang* is not a valid value.
    """
    yaml_path = _PROMPTS_DIR / f"{agent_name}.yaml"
    if not yaml_path.exists():
        raise FileNotFoundError(f"No prompt file found for agent '{agent_name}': {yaml_path}")

    if lang not in _VALID_LANGS:
        raise ValueError(
            f"Invalid lang '{lang}'. Valid values for lang: {sorted(_VALID_LANGS)}"
        )
    if mode not in _VALID_MODES:
        raise ValueError(
            f"Invalid mode '{mode}'. Valid values for mode: {sorted(_VALID_MODES)}"
        )

    with yaml_path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    try:
        entry = data[lang][mode]
    except KeyError as exc:
        raise ValueError(
            f"Missing key in {yaml_path.name}: {exc}. "
            f"Expected lang='{lang}', mode='{mode}'."
        ) from exc

    return {"system": entry["system"], "user_template": entry["user_template"]}


def render(template: str, **kwargs: str) -> str:
    """Substitute ``{name}`` placeholders in *template* using *kwargs*.

    Raises
    ------
    KeyError
        When a placeholder in *template* has no matching key in *kwargs*.
    """
    return template.format(**kwargs)
