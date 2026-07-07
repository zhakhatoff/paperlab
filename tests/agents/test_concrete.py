"""Tests for the four concrete agent subclasses."""

import pytest

from paperlab.providers.fake import FakeProvider
from paperlab.agents import (
    AgentReport,
    SummarizerAgent,
    MethodologistAgent,
    CriticAgent,
    ContextualizerAgent,
    ALL_AGENTS,
)

DEFAULT_JSON = '{"result": "ok"}'


# --- NAME class attributes ---

def test_summarizer_name():
    assert SummarizerAgent.NAME == "summarizer"


def test_methodologist_name():
    assert MethodologistAgent.NAME == "methodologist"


def test_critic_name():
    assert CriticAgent.NAME == "critic"


def test_contextualizer_name():
    assert ContextualizerAgent.NAME == "contextualizer"


# --- ALL_AGENTS ---

def test_all_agents_contains_all_four():
    names = {cls.NAME for cls in ALL_AGENTS}
    assert names == {"summarizer", "methodologist", "critic", "contextualizer"}


# --- run() returns AgentReport with correct agent_name ---

@pytest.mark.asyncio
async def test_summarizer_run_agent_name():
    provider = FakeProvider(default=DEFAULT_JSON)
    agent = SummarizerAgent(provider, mode="rigorous", lang="en", model="m")
    report = await agent.run("paper")
    assert isinstance(report, AgentReport)
    assert report.agent_name == "summarizer"


@pytest.mark.asyncio
async def test_methodologist_run_agent_name():
    provider = FakeProvider(default=DEFAULT_JSON)
    agent = MethodologistAgent(provider, mode="rigorous", lang="en", model="m")
    report = await agent.run("paper")
    assert isinstance(report, AgentReport)
    assert report.agent_name == "methodologist"


@pytest.mark.asyncio
async def test_critic_run_agent_name():
    provider = FakeProvider(default=DEFAULT_JSON)
    agent = CriticAgent(provider, mode="rigorous", lang="en", model="m")
    report = await agent.run("paper")
    assert isinstance(report, AgentReport)
    assert report.agent_name == "critic"


@pytest.mark.asyncio
async def test_contextualizer_run_agent_name():
    provider = FakeProvider(default=DEFAULT_JSON)
    agent = ContextualizerAgent(provider, mode="rigorous", lang="en", model="m")
    report = await agent.run("paper")
    assert isinstance(report, AgentReport)
    assert report.agent_name == "contextualizer"


# --- prompt is loaded (non-empty system) for methodologist/critic/contextualizer ---

@pytest.mark.asyncio
async def test_methodologist_loads_prompt():
    provider = FakeProvider(default=DEFAULT_JSON)
    agent = MethodologistAgent(provider, mode="rigorous", lang="en", model="m")
    await agent.run("paper")
    system, _, _ = provider.calls[0]
    assert system.strip()


@pytest.mark.asyncio
async def test_critic_loads_prompt():
    provider = FakeProvider(default=DEFAULT_JSON)
    agent = CriticAgent(provider, mode="rigorous", lang="en", model="m")
    await agent.run("paper")
    system, _, _ = provider.calls[0]
    assert system.strip()


@pytest.mark.asyncio
async def test_contextualizer_loads_prompt():
    provider = FakeProvider(default=DEFAULT_JSON)
    agent = ContextualizerAgent(provider, mode="rigorous", lang="en", model="m")
    await agent.run("paper")
    system, _, _ = provider.calls[0]
    assert system.strip()
