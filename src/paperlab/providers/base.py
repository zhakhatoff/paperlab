import abc


class ProviderError(Exception):
    pass


class LLMProvider(abc.ABC):
    @abc.abstractmethod
    async def complete(
        self,
        system: str,
        user: str,
        model: str,
        temperature: float = 0.2,
    ) -> str: ...
