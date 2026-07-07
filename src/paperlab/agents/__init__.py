"""paperlab.agents — Agent base class and concrete agents."""

from paperlab.agents.base import Agent, AgentReport
from paperlab.agents.summarizer import SummarizerAgent
from paperlab.agents.methodologist import MethodologistAgent
from paperlab.agents.critic import CriticAgent
from paperlab.agents.contextualizer import ContextualizerAgent

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
