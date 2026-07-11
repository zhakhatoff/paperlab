"""Base Agent class and AgentReport model."""

from __future__ import annotations

import json
from typing import ClassVar

from pydantic import BaseModel

from paperlab.prompts import load_prompt, render
from paperlab.providers.base import LLMProvider


class AgentReport(BaseModel):
    agent_name: str
    mode: str
    lang: str
    model: str
    output: dict
    raw: str
    error: str | None = None


def _parse_json(raw: str) -> tuple[dict, str | None]:
    """Try to parse *raw* as JSON.

    Uses ``json.JSONDecoder().raw_decode`` incrementally from every ``{`` or
    ``[`` in the string until it finds a value that decodes cleanly. If the
    decoded value is a list, it is wrapped as ``{"items": [...]}``. Returns
    ``({}, error_message)`` if nothing decodes.
    """
    decoder = json.JSONDecoder()

    # Direct parse first.
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict):
            return obj, None
        if isinstance(obj, list):
            return {"items": obj}, None
    except json.JSONDecodeError:
        pass

    # Scan every candidate opener.
    for i, ch in enumerate(raw):
        if ch not in "{[":
            continue
        try:
            obj, _end = decoder.raw_decode(raw, i)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            return obj, None
        if isinstance(obj, list):
            return {"items": obj}, None

    return {}, "JSON parse error: could not extract a JSON object from raw response"


class Agent:
    NAME: ClassVar[str] = ""

    def __init__(
        self,
        provider: LLMProvider,
        mode: str,
        lang: str,
        model: str,
    ) -> None:
        self._provider = provider
        self._mode = mode
        self._lang = lang
        self._model = model

    async def run(self, paper_text: str) -> AgentReport:
        name = self.NAME
        prompt = load_prompt(name, self._mode, self._lang)
        user = render(prompt["user_template"], paper_text=paper_text)
        raw = await self._provider.complete(prompt["system"], user, self._model)
        output, error = _parse_json(raw)
        return AgentReport(
            agent_name=name,
            mode=self._mode,
            lang=self._lang,
            model=self._model,
            output=output,
            raw=raw,
            error=error,
        )
