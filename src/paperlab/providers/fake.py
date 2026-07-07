from __future__ import annotations

import json
from .base import LLMProvider


class FakeProvider(LLMProvider):
    def __init__(
        self,
        responses: dict[tuple[str, str], str] | None = None,
        default: str | None = None,
    ) -> None:
        self._responses = responses or {}
        self._default = default
        self.calls: list[tuple[str, str, str]] = []

    async def complete(
        self,
        system: str,
        user: str,
        model: str,
        temperature: float = 0.2,
    ) -> str:
        self.calls.append((system, user, model))

        for (sys_prefix, usr_prefix), value in self._responses.items():
            if system.startswith(sys_prefix) and user.startswith(usr_prefix):
                return value

        if self._default is not None:
            return self._default

        return json.dumps({"echo": user[:80]})
