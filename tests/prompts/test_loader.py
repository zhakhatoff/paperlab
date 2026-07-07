"""Tests for prompts.loader: load_prompt and render."""

import pytest

from paperlab.prompts import load_prompt, render

AGENTS = ["summarizer", "methodologist", "critic", "contextualizer"]
MODES = ["rigorous", "learning"]
LANGS = ["en", "ru"]


@pytest.mark.parametrize("agent", AGENTS)
@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("lang", LANGS)
def test_load_prompt_returns_system_and_user_template(agent, mode, lang):
    result = load_prompt(agent, mode, lang)
    assert isinstance(result, dict), "load_prompt must return a dict"
    assert "system" in result, "result must have 'system' key"
    assert "user_template" in result, "result must have 'user_template' key"
    assert result["system"], f"system must be non-empty for {agent}/{mode}/{lang}"
    assert result["user_template"], f"user_template must be non-empty for {agent}/{mode}/{lang}"
    assert "{paper_text}" in result["user_template"], (
        f"user_template must contain {{paper_text}} for {agent}/{mode}/{lang}"
    )


def test_load_prompt_invalid_agent_raises_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_prompt("nonexistent_agent", "rigorous", "en")


def test_load_prompt_invalid_mode_raises_value_error():
    with pytest.raises(ValueError, match="mode"):
        load_prompt("summarizer", "bad_mode", "en")


def test_load_prompt_invalid_lang_raises_value_error():
    with pytest.raises(ValueError, match="lang"):
        load_prompt("summarizer", "rigorous", "zz")


def test_render_substitutes_named_placeholder():
    assert render("Hello {name}", name="X") == "Hello X"


def test_render_missing_key_raises_key_error():
    with pytest.raises(KeyError):
        render("Hello {name}")
