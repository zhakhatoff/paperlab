"""paperlab.agents — Agent base class and concrete agents."""

from paperlab.agents.base import Agent, AgentReport
from paperlab.agents.contextualizer import ContextualizerAgent
from paperlab.agents.critic import CriticAgent
from paperlab.agents.methodologist import MethodologistAgent
from paperlab.agents.summarizer import SummarizerAgent

ALL_AGENTS = [SummarizerAgent, MethodologistAgent, CriticAgent, ContextualizerAgent]

__all__ = [
    "Agent",
    "AgentReport",
    "SummarizerAgent",
    "MethodologistAgent",
    "CriticAgent",
    "ContextualizerAgent",
    "ALL_AGENTS",
]
