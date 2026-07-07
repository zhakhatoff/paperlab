"""Base Agent class and AgentReport model."""

from __future__ import annotations

import json
import re
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

    First attempt: parse the whole string directly.
    Second attempt: extract the first ``{...}`` block (greedy, DOTALL) and parse that.
    Failure: return ``({}, error_message)``.
    """
    # Direct parse
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict):
            return obj, None
    except json.JSONDecodeError:
        pass

    # Extract first {...} block
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            obj = json.loads(match.group())
            if isinstance(obj, dict):
                return obj, None
        except json.JSONDecodeError:
            pass

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
