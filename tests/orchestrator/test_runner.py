"""Tests for paperlab.orchestrator.runner."""
from __future__ import annotations

import pytest
from datetime import datetime, timezone

from paperlab.agents import ALL_AGENTS
from paperlab.ingest import IngestedPaper
from paperlab.orchestrator import ReviewReport, review
from paperlab.providers import FakeProvider, ProviderError


@pytest.fixture
def minimal_paper() -> IngestedPaper:
    return IngestedPaper(source_path="x.pdf", text="SAMPLE PAPER TEXT", backend="docling")


@pytest.mark.asyncio
async def test_happy_path(minimal_paper: IngestedPaper) -> None:
    provider = FakeProvider()
    report = await review(
        paper=minimal_paper,
        provider=provider,
        mode="rigorous",
        lang="en",
        model="test-model",
    )

    assert isinstance(report, ReviewReport)
    # One entry per agent
    assert len(report.agents) == len(ALL_AGENTS)
    expected_names = {cls.NAME for cls in ALL_AGENTS}
    assert set(report.agents.keys()) == expected_names

    # Provider called once per agent
    assert len(provider.calls) == len(ALL_AGENTS)

    # session_id is 12 hex chars
    assert len(report.session_id) == 12
    assert all(c in "0123456789abcdef" for c in report.session_id)

    # created_at parses as ISO datetime with timezone
    dt = datetime.fromisoformat(report.created_at)
    assert dt.tzinfo is not None


@pytest.mark.asyncio
async def test_session_id_passthrough(minimal_paper: IngestedPaper) -> None:
    provider = FakeProvider()
    report = await review(
        paper=minimal_paper,
        provider=provider,
        mode="rigorous",
        lang="en",
        model="test-model",
        session_id="mysession123",
    )
    assert report.session_id == "mysession123"


class OneFailingProvider(FakeProvider):
    """Raises ProviderError for the critic agent by matching its system prompt."""

    async def complete(
        self,
        system: str,
        user: str,
        model: str,
        temperature: float = 0.2,
    ) -> str:
        # The critic system prompt contains "conflicts of interest" (en/rigorous)
        if "conflicts of interest" in system.lower() or "conflicts_of_interest" in user:
            raise ProviderError("boom")
        return await super().complete(system, user, model, temperature)


@pytest.mark.asyncio
async def test_one_agent_fails(minimal_paper: IngestedPaper) -> None:
    provider = OneFailingProvider()
    report = await review(
        paper=minimal_paper,
        provider=provider,
        mode="rigorous",
        lang="en",
        model="test-model",
    )

    assert len(report.agents) == len(ALL_AGENTS)

    # critic failed
    critic_report = report.agents["critic"]
    assert critic_report.error
    assert critic_report.output == {}
    assert critic_report.raw == ""

    # other three succeeded
    for name, agent_report in report.agents.items():
        if name != "critic":
            assert agent_report.error is None, f"{name} should not have errored"
