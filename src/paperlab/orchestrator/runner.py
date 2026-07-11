"""paperlab.orchestrator.runner — parallel review runner."""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime

from pydantic import BaseModel

from paperlab.agents import ALL_AGENTS, AgentReport
from paperlab.ingest import IngestedPaper
from paperlab.providers.base import LLMProvider


class ReviewReport(BaseModel):
    paper: IngestedPaper
    mode: str
    lang: str
    model: str
    session_id: str
    created_at: str  # ISO 8601 UTC
    agents: dict[str, AgentReport]
    error: str | None = None


async def review(
    paper: IngestedPaper,
    provider: LLMProvider,
    mode: str,
    lang: str,
    model: str,
    session_id: str | None = None,
) -> ReviewReport:
    session_id = session_id or uuid.uuid4().hex[:12]
    created_at = datetime.now(UTC).isoformat()

    agent_instances = [cls(provider, mode, lang, model) for cls in ALL_AGENTS]

    results = await asyncio.gather(
        *[agent.run(paper.text) for agent in agent_instances],
        return_exceptions=True,
    )

    agents: dict[str, AgentReport] = {}
    for agent, result in zip(agent_instances, results, strict=False):
        if isinstance(result, Exception):
            agents[agent.NAME] = AgentReport(
                agent_name=agent.NAME,
                mode=mode,
                lang=lang,
                model=model,
                output={},
                raw="",
                error=str(result),
            )
        else:
            agents[agent.NAME] = result

    top_error: str | None = None
    if agents:
        errors = [a.error for a in agents.values()]
        if all(errors) and len(set(errors)) == 1:
            top_error = errors[0]

    return ReviewReport(
        paper=paper,
        mode=mode,
        lang=lang,
        model=model,
        session_id=session_id,
        created_at=created_at,
        agents=agents,
        error=top_error,
    )
