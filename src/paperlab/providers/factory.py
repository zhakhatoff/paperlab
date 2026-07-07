"""Factory function for creating LLM providers by name."""
from __future__ import annotations

from paperlab.providers.base import LLMProvider
from paperlab.providers.fake import FakeProvider
from paperlab.providers.litellm_provider import LiteLLMProvider

SUPPORTED_PROVIDERS: tuple = (
    "fake",
    "ollama",
    "openrouter",
    "together",
    "groq",
    "gemini",
    "anthropic",
    "openai",
    "custom",
)

_LITELLM_PROVIDERS = frozenset(SUPPORTED_PROVIDERS) - {"fake"}


def make_provider(name: str) -> LLMProvider:
    """Return an LLMProvider instance for the given provider name.

    Parameters
    ----------
    name:
        Provider identifier. One of ``SUPPORTED_PROVIDERS``.

    Raises
    ------
    ValueError
        If *name* is not in ``SUPPORTED_PROVIDERS``.
    """
    if name == "fake":
        return FakeProvider()
    if name in _LITELLM_PROVIDERS:
        return LiteLLMProvider()
    raise ValueError(
        f"Unknown provider {name!r}. supported: "
        + ", ".join(SUPPORTED_PROVIDERS)
    )
