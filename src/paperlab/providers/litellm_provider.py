from __future__ import annotations

from ._scrub import _scrub_secrets
from .base import LLMProvider, ProviderError

# LiteLLM routes by model-string prefix; openai/custom accept bare names.
_LITELLM_PREFIX = {
    "ollama": "ollama",
    "openrouter": "openrouter",
    "groq": "groq",
    "gemini": "gemini",
    "together": "together_ai",
    "anthropic": "anthropic",
}


def litellm_model(provider_name: str | None, model: str) -> str:
    prefix = _LITELLM_PREFIX.get(provider_name or "")
    if not prefix:
        return model
    if model.startswith(f"{prefix}/"):
        return model
    # Accept the raw provider-name prefix as a synonym for the litellm prefix.
    if provider_name and model.startswith(f"{provider_name}/"):
        return f"{prefix}/{model[len(provider_name) + 1 :]}"
    return f"{prefix}/{model}"


class LiteLLMProvider(LLMProvider):
    def __init__(self, provider_name: str | None = None) -> None:
        self._provider_name = provider_name

    async def complete(
        self,
        system: str,
        user: str,
        model: str,
        temperature: float = 0.2,
    ) -> str:
        import litellm  # lazy import

        if self._provider_name:
            from paperlab.providers.keys import apply_key_to_env

            apply_key_to_env(self._provider_name)

        try:
            response = await litellm.acompletion(
                model=litellm_model(self._provider_name, model),
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=temperature,
            )
        except Exception as exc:
            msg = _scrub_secrets(str(exc))
            raise ProviderError(f"litellm error ({type(exc).__name__}): {msg}") from exc

        return response.choices[0].message.content or ""
