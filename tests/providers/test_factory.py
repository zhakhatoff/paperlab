"""Tests for providers.factory.make_provider."""
from __future__ import annotations

import pytest

from paperlab.providers import FakeProvider, LiteLLMProvider, make_provider, SUPPORTED_PROVIDERS


def test_make_provider_fake_returns_fake_provider():
    p = make_provider("fake")
    assert isinstance(p, FakeProvider)


def test_make_provider_ollama_returns_litellm_provider():
    p = make_provider("ollama")
    assert isinstance(p, LiteLLMProvider)


def test_make_provider_openrouter():
    p = make_provider("openrouter")
    assert isinstance(p, LiteLLMProvider)


def test_make_provider_anthropic():
    p = make_provider("anthropic")
    assert isinstance(p, LiteLLMProvider)


def test_make_provider_unknown_raises_value_error_with_supported():
    with pytest.raises(ValueError, match="supported"):
        make_provider("unknown_xyz_provider")


def test_supported_providers_is_tuple():
    assert isinstance(SUPPORTED_PROVIDERS, tuple)
    assert "fake" in SUPPORTED_PROVIDERS
    assert "ollama" in SUPPORTED_PROVIDERS
