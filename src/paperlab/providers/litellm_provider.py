from __future__ import annotations

from .base import LLMProvider, ProviderError


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
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=temperature,
            )
        except Exception as exc:
            raise ProviderError(f"litellm error: {exc}") from exc

        return response.choices[0].message.content
