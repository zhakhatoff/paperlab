from .base import LLMProvider, ProviderError
from .discovery import (
    OLLAMA_RECOMMENDED,
    STATIC_FALLBACK_MODELS,
    DiscoveryError,
    MissingKeyError,
    list_models,
    list_models_safe,
    ollama_status,
    recommend_ollama_models,
    system_ram_gb,
)
from .factory import SUPPORTED_PROVIDERS, make_provider
from .fake import FakeProvider
from .keys import (
    ENV_VAR_BY_PROVIDER,
    apply_key_to_env,
    delete_key,
    get_key,
    keys_path,
    list_keys,
    save_key,
)
from .litellm_provider import LiteLLMProvider

__all__ = [
    "LLMProvider",
    "LiteLLMProvider",
    "FakeProvider",
    "ProviderError",
    "make_provider",
    "SUPPORTED_PROVIDERS",
    # keys
    "save_key",
    "get_key",
    "delete_key",
    "list_keys",
    "apply_key_to_env",
    "ENV_VAR_BY_PROVIDER",
    "keys_path",
    # discovery
    "ollama_status",
    "recommend_ollama_models",
    "list_models",
    "list_models_safe",
    "system_ram_gb",
    "MissingKeyError",
    "DiscoveryError",
    "STATIC_FALLBACK_MODELS",
    "OLLAMA_RECOMMENDED",
]
