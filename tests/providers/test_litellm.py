import asyncio
import sys
import types
import pytest
from unittest.mock import AsyncMock, MagicMock


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
