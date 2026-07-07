import pytest
from paperlab.providers import LLMProvider, ProviderError


def test_llmprovider_is_abstract():
    with pytest.raises(TypeError):
        LLMProvider()


def test_subclass_without_complete_is_abstract():
    class Incomplete(LLMProvider):
        pass

    with pytest.raises(TypeError):
        Incomplete()


def test_minimal_subclass_works():
    class Minimal(LLMProvider):
        async def complete(self, system, user, model, temperature=0.2):
            return "ok"

    m = Minimal()
    import asyncio
    result = asyncio.run(m.complete("sys", "user", "model"))
    assert result == "ok"
