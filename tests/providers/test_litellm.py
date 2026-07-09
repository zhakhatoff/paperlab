import asyncio
import os
import sys
import types
from unittest.mock import MagicMock

import pytest


def _make_fake_litellm(content="hi", raise_exc=None):
    fake = types.ModuleType("litellm")

    async def acompletion(**kwargs):
        if raise_exc is not None:
            raise raise_exc
        msg = MagicMock()
        msg.content = content
        choice = MagicMock()
        choice.message = msg
        response = MagicMock()
        response.choices = [choice]
        return response

    fake.acompletion = acompletion
    return fake


def test_complete_returns_content(monkeypatch):
    fake_litellm = _make_fake_litellm("hi")
    monkeypatch.setitem(sys.modules, "litellm", fake_litellm)

    # Import after patching so lazy import picks it up
    from paperlab.providers import LiteLLMProvider

    provider = LiteLLMProvider()
    result = asyncio.run(provider.complete("s", "u", "m"))
    assert result == "hi"


def test_litellm_exception_wrapped_in_provider_error(monkeypatch):
    fake_litellm = _make_fake_litellm(raise_exc=Exception("boom"))
    monkeypatch.setitem(sys.modules, "litellm", fake_litellm)

    from paperlab.providers import LiteLLMProvider, ProviderError

    provider = LiteLLMProvider()
    with pytest.raises(ProviderError) as exc_info:
        asyncio.run(provider.complete("s", "u", "m"))
    assert "boom" in str(exc_info.value)


def test_litellm_apply_key_to_env_before_complete(tmp_path, monkeypatch):
    """LiteLLMProvider with provider_name applies saved key to env before calling litellm."""
    monkeypatch.setenv("PAPERLAB_HOME", str(tmp_path))
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    from paperlab.providers.keys import save_key

    save_key("openrouter", "sk-test-or-key")

    fake_litellm = _make_fake_litellm("result")
    monkeypatch.setitem(sys.modules, "litellm", fake_litellm)

    from paperlab.providers.litellm_provider import LiteLLMProvider

    provider = LiteLLMProvider(provider_name="openrouter")
    asyncio.run(provider.complete("s", "u", "m"))

    assert os.environ.get("OPENROUTER_API_KEY") == "sk-test-or-key"


def _capture_fake_litellm(captured: dict, content="ok"):
    fake = types.ModuleType("litellm")

    async def acompletion(**kwargs):
        captured.update(kwargs)
        msg = MagicMock()
        msg.content = content
        choice = MagicMock()
        choice.message = msg
        response = MagicMock()
        response.choices = [choice]
        return response

    fake.acompletion = acompletion
    return fake


@pytest.mark.parametrize(
    ("provider_name", "model", "expected"),
    [
        ("ollama", "qwen3:4b-instruct-2507-q4_K_M", "ollama/qwen3:4b-instruct-2507-q4_K_M"),
        ("ollama", "ollama/qwen2.5:7b", "ollama/qwen2.5:7b"),
        ("openrouter", "anthropic/claude-3.5-sonnet", "openrouter/anthropic/claude-3.5-sonnet"),
        (
            "openrouter",
            "openrouter/anthropic/claude-3.5-sonnet",
            "openrouter/anthropic/claude-3.5-sonnet",
        ),
        ("groq", "llama-3.1-70b-versatile", "groq/llama-3.1-70b-versatile"),
        ("gemini", "gemini-2.5-flash", "gemini/gemini-2.5-flash"),
        (
            "together",
            "meta-llama/Llama-3-70b-chat-hf",
            "together_ai/meta-llama/Llama-3-70b-chat-hf",
        ),
        ("anthropic", "claude-sonnet-4-5", "anthropic/claude-sonnet-4-5"),
        ("openai", "gpt-4o-mini", "gpt-4o-mini"),
        ("custom", "my-endpoint-model", "my-endpoint-model"),
        (None, "qwen2.5:7b", "qwen2.5:7b"),
    ],
)
def test_model_prefixed_for_litellm(monkeypatch, provider_name, model, expected):
    """LiteLLM requires provider-prefixed model strings; provider adds them."""
    captured: dict = {}
    monkeypatch.setitem(sys.modules, "litellm", _capture_fake_litellm(captured))

    from paperlab.providers.litellm_provider import LiteLLMProvider

    provider = LiteLLMProvider(provider_name=provider_name)
    asyncio.run(provider.complete("s", "u", model))
    assert captured["model"] == expected
