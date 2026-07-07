from .base import LLMProvider, ProviderError


class LiteLLMProvider(LLMProvider):
    async def complete(
        self,
        system: str,
        user: str,
        model: str,
        temperature: float = 0.2,
    ) -> str:
        import litellm  # lazy import

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
