"""Tests for agents.base: Agent, AgentReport, and _parse_json behaviour."""

import pytest

from paperlab.agents import SummarizerAgent
from paperlab.providers.fake import FakeProvider

CLEAN_JSON = '{"claims":["a"],"findings":[],"limitations_stated":[]}'
GARBAGE = "total garbage no json"
PROSE_WITH_JSON = 'Analysis:\n{"claims":["x"]}\nEnd'


@pytest.mark.asyncio
async def test_run_returns_parsed_output():
    provider = FakeProvider(default=CLEAN_JSON)
    agent = SummarizerAgent(provider, mode="rigorous", lang="en", model="test-model")
    report = await agent.run("SAMPLE PAPER TEXT")

    assert report.output == {"claims": ["a"], "findings": [], "limitations_stated": []}
    assert report.error is None


@pytest.mark.asyncio
async def test_run_report_metadata():
    provider = FakeProvider(default=CLEAN_JSON)
    agent = SummarizerAgent(provider, mode="rigorous", lang="en", model="test-model")
    report = await agent.run("SAMPLE PAPER TEXT")

    assert report.agent_name == "summarizer"
    assert report.mode == "rigorous"
    assert report.lang == "en"
    assert report.model == "test-model"


@pytest.mark.asyncio
async def test_run_calls_provider_with_system_and_paper_text():
    provider = FakeProvider(default=CLEAN_JSON)
    agent = SummarizerAgent(provider, mode="rigorous", lang="en", model="test-model")
    await agent.run("SAMPLE PAPER TEXT")

    assert len(provider.calls) == 1
    system, user, model = provider.calls[0]
    assert system.strip()  # non-empty system from summarizer.yaml
    assert "SAMPLE PAPER TEXT" in user
    assert model == "test-model"


@pytest.mark.asyncio
async def test_run_garbage_response_produces_empty_output_and_error():
    provider = FakeProvider(default=GARBAGE)
    agent = SummarizerAgent(provider, mode="rigorous", lang="en", model="test-model")
    report = await agent.run("SAMPLE PAPER TEXT")

    assert report.output == {}
    assert report.error is not None
    assert "json" in report.error.lower() or "parse" in report.error.lower()
    assert report.raw == GARBAGE


@pytest.mark.asyncio
async def test_run_prose_with_embedded_json():
    provider = FakeProvider(default=PROSE_WITH_JSON)
    agent = SummarizerAgent(provider, mode="rigorous", lang="en", model="test-model")
    report = await agent.run("SAMPLE PAPER TEXT")

    assert report.output == {"claims": ["x"]}
    assert report.error is None


@pytest.mark.asyncio
async def test_run_raw_matches_provider_response():
    provider = FakeProvider(default=CLEAN_JSON)
    agent = SummarizerAgent(provider, mode="rigorous", lang="en", model="test-model")
    report = await agent.run("SAMPLE PAPER TEXT")

    assert report.raw == CLEAN_JSON
